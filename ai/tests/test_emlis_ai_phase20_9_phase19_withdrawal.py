# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-9 guard: Phase19 C/D dedicated runtime routes are withdrawn.

This is intentionally a regression guard over production files plus generic
contract behavior.  Old Phase19 C/D identifiers may remain in test-only
inventory/quarantine fixtures, but they must not remain in production runtime
services as route, cue, mode, or completed-surface selectors.
"""

import json
from pathlib import Path
from typing import Any

from emlis_ai_observation_eligibility_router import route_emlis_observation_eligibility_by_material
from emlis_ai_response_contract_qa_matrix import (
    PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS,
    build_phase20_8_response_contract_qa_cases,
)
from emlis_ai_safety_triage import build_emlis_safety_triage_decision
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PRODUCTION_ROOT = _BACKEND_ROOT / "ai" / "services" / "ai_inference"

_PHASE20_9_WITHDRAWN_PRODUCTION_TOKENS = (
    "self_understanding_learning_shift",
    "relationship_gratitude_recovery",
    "relationship_end_gratitude_recovery",
    "MODE_SELF_UNDERSTANDING_LEARNING_SHIFT",
    "MODE_RELATIONSHIP_GRATITUDE_RECOVERY",
    "phase19_real_device_C_self_understanding_learning_shift",
    "phase19_real_device_D_relationship_gratitude_recovery",
)

_PHASE20_9_GENERIC_REGRESSION_IDS = {
    "phase19_real_device_C_generic_self_understanding_regression",
    "phase19_real_device_D_generic_relationship_boundary_regression",
}


def _production_text_files() -> list[Path]:
    files: list[Path] = []
    for path in _PRODUCTION_ROOT.rglob("*"):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file() and path.suffix in {".py", ".json"}:
            files.append(path)
    return files


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_withdrawn_runtime_tokens(value: Any) -> None:
    dumped = _dump(value)
    for token in _PHASE20_9_WITHDRAWN_PRODUCTION_TOKENS:
        assert token not in dumped


def test_phase20_9_production_services_do_not_keep_phase19_c_d_dedicated_tokens() -> None:
    files = _production_text_files()
    assert files

    leaked: list[tuple[str, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in _PHASE20_9_WITHDRAWN_PRODUCTION_TOKENS:
            if token in text:
                leaked.append((str(path.relative_to(_BACKEND_ROOT)), token))

    assert leaked == []


def test_phase20_9_c_and_d_materials_are_generic_relation_material_not_dedicated_cues() -> None:
    samples = (
        {
            "memo": "人への興味や、自分の考え方が少し変わってきた気がする。まだ整理しきれていないけど、前より行動に移せた。",
            "memo_action": "気づいたことをメモに残した。",
            "emotions": ["自己理解", "安心"],
            "category": ["価値観", "日常"],
        },
        {
            "memo": "彼氏と別れて悲しいけど、友達が変わらず優しくしてくれてありがたかった。少しずつ返していきたい。",
            "memo_action": "友達にありがとうと伝えた。",
            "emotions": ["悲しみ", "感謝"],
            "category": ["人間関係"],
        },
    )

    for sample in samples:
        shared_meta = build_emlis_shared_reception_evidence_meta(sample)
        _assert_no_withdrawn_runtime_tokens(shared_meta)
        assert shared_meta["dedicated_c_d_cue_runtime_disabled"] is True
        assert shared_meta["dedicated_c_d_mode_runtime_disabled"] is True
        assert shared_meta["phase20_9_phase19_dedicated_c_d_cue_deleted"] is True
        assert shared_meta["phase20_9_phase19_dedicated_c_d_mode_deleted"] is True
        assert shared_meta["phase19_case_route_used"] is False
        assert shared_meta["case_specific_route_used"] is False
        assert shared_meta["generic_relation_material_ids"]

        safety_decision = build_emlis_safety_triage_decision(current_input=sample)
        route = route_emlis_observation_eligibility_by_material(
            sample,
            safety_triage_decision=safety_decision,
        )
        route_meta = route.as_meta()
        _assert_no_withdrawn_runtime_tokens(route_meta)
        assert route_meta["case_specific_route_used"] is False
        assert route.response_kind in {
            "normal_observation",
            "limited_grounding_observation",
            "low_information_observation",
        }


def test_phase20_9_qa_matrix_keeps_exact_fixtures_as_generic_regression_ids() -> None:
    assert _PHASE20_9_GENERIC_REGRESSION_IDS.issubset(set(PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS))
    _assert_no_withdrawn_runtime_tokens(PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS)

    exact_fixture_ids = {
        case.exact_fixture_id
        for case in build_phase20_8_response_contract_qa_cases()
        if case.exact_fixture_id
    }
    assert _PHASE20_9_GENERIC_REGRESSION_IDS.issubset(exact_fixture_ids)
    _assert_no_withdrawn_runtime_tokens(tuple(sorted(exact_fixture_ids)))
