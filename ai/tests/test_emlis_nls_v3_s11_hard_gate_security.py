# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import emlis_nls_v3_step11_regression as regression_module
import emlis_ai_discourse_graph_planner_v3 as planner_module
import emlis_ai_step11_hard_gate_v3 as hard_gate_module
import emlis_ai_step11_natural_surface_matcher_v3 as matcher_module
import emlis_ai_step11_natural_surface_v3 as surface_module
import emlis_ai_step11_semantic_overlay_v3 as overlay_module
import emlis_ai_step11_surface_catalog_v3 as catalog_module

from emlis_ai_step11_hard_gate_v3 import (
    evaluate_step11_natural_surface_candidate,
    select_step11_natural_surface_candidates,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (
    Step11InverseSurfaceError,
    _quote_projection,
    _scan_quoted,
    _unknown_reference_clause,
    match_step11_natural_surface,
    parse_step11_natural_surface,
)
from emlis_ai_step11_natural_surface_v3 import STEP11_CANDIDATE_VERSION_ID
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
)


_EXPECTED_GATE_FAILURE_CODES = (
    "S11_GATE01_ARTIFACT_SCHEMA_PARENT_HASH",
    "S11_GATE02_VERSION_DEPENDENCY",
    "S11_GATE03_CANONICAL_RENDER_EQUALITY",
    "S11_GATE04_BODY_PARSEABILITY",
    "S11_GATE05_EVIDENCE_RESOLUTION",
    "S11_GATE06_REQUIRED_OBLIGATION_COVERAGE",
    "S11_GATE07_BOUND_RECEPTION",
    "S11_GATE08_POLARITY_MODALITY_TIME",
    "S11_GATE09_RELATION_TYPE_DIRECTION",
    "S11_GATE10_REFERENT_TOPIC",
    "S11_GATE11_UNKNOWN_BOUNDARY",
    "S11_GATE12_SELF_DENIAL",
    "S11_GATE13_UNSUPPORTED_CLAIM",
    "S11_GATE14_SECTION_DISTINCTNESS",
    "S11_GATE15_INPUT_ENUMERATION",
    "S11_GATE16_CONTRIBUTION_DISTINCTNESS",
    "S11_GATE17_DEPTH",
    "S11_GATE18_SURFACE_INTEGRITY",
    "S11_GATE19_NAMING_ADDRESS",
    "S11_GATE20_BODY_FREE_PUBLIC_CONTRACT",
)

_RELATION_SCOPED_UNKNOWN_INPUTS = {
    "future": {
        "thought_text": "朝から予定がずれて、ずっと気持ちがせわしない。",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "strong"}],
        "categories": ["生活"],
    },
    "cause_and_generic": {
        "thought_text": "嬉しいはずなのに、なんで不安なのかはまだ言葉にできない。",
        "action_text": "",
        "emotions": [
            {"type": "喜び", "strength": "medium"},
            {"type": "不安", "strength": "medium"},
        ],
        "categories": ["恋愛"],
    },
    "cause_and_future": {
        "thought_text": "どうして予定を決めた後になると、急に別の選択のほうがよかった気がするんだろう。",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["生活"],
    },
    "cause_and_referent": {
        "thought_text": "楽しかったのに、帰ってから寂しくなったのはなぜだろう。",
        "action_text": "",
        "emotions": [
            {"type": "喜び", "strength": "medium"},
            {"type": "悲しみ", "strength": "medium"},
        ],
        "categories": ["趣味"],
    },
}

_THOUGHT_ONLY_OMITTED_REFERENT_INPUT = {
    "thought_text": "まだよく分からない。",
    "action_text": "",
    "emotions": [{"type": "自己理解", "strength": "medium"}],
    "categories": ["価値観"],
}

_OTHER_PERSON_UNKNOWN_INPUT = {
    "thought_text": (
        "言い過ぎたことを謝った。相手から短い返事は来たけれど、"
        "関係が戻ったかは分からない。返事をもらえたことには"
        "ほっとした。"
    ),
    "action_text": "同じ話を重ねて送らず、次に会う予定だけ確認した。",
    "emotions": [
        {"type": "不安", "strength": "medium"},
        {"type": "平穏", "strength": "medium"},
    ],
    "categories": ["人間関係"],
}

_ACCOUNTABILITY_INPUT = {
    "thought_text": (
        "すれ違った後も、こちらの話を聞く時間を作ってくれたことがうれしかった。"
        "全部分かり合えたとは思わないけれど、関係を諦めずに話せたことで少し安心した。"
    ),
    "action_text": "自分の言い方で傷つけた部分を認め、言い直したかった内容を伝えた。",
    "emotions": [
        {"type": "喜び", "strength": "medium"},
        {"type": "不安", "strength": "weak"},
        {"type": "平穏", "strength": "medium"},
    ],
    "categories": ["人間関係"],
}

_ACTION_SELF_DENIAL_INPUT = {
    "thought_text": "今日は少し落ち込んでいる。",
    "action_text": "自分はダメだと思って、何も手につかなかった。",
    "emotions": [{"type": "悲しみ", "strength": "medium"}],
    "categories": ["生活"],
}

_COMPLETED_ACTION_INPUT = {
    "thought_text": "",
    "action_text": "机の上を片づけた。",
    "emotions": [{"type": "平穏", "strength": "weak"}],
    "categories": ["生活"],
}

_CONTEXT_RESOLVED_TEMPORAL_INPUT = {
    "thought_text": "話してみたら、思っていたより穏やかに聞いてもらえた。",
    "action_text": "帰ってからお礼を短く送った。",
    "emotions": [
        {"type": "喜び", "strength": "medium"},
        {"type": "平穏", "strength": "medium"},
    ],
    "categories": ["人間関係"],
}

_OPTIONAL_UNCERTAIN_INPUT = {
    "thought_text": (
        "近くに人がいても、自分だけつながれていない感じがする。"
        "なぜそう感じるのかは分からない。"
    ),
    "action_text": "昼の誘いには行かず、静かな場所で一人で過ごした。",
    "emotions": [
        {"type": "悲しみ", "strength": "strong"},
        {"type": "不安", "strength": "weak"},
    ],
    "categories": ["生活", "人間関係"],
}

_EXACT_RELATION_ENDPOINT_INPUT = {
    "thought_text": (
        "協力して仕上げたものを褒められてうれしかった。"
        "でも、助けてもらった部分も大きく、自分だけの成果として"
        "受け取ってよいのか迷っている。"
    ),
    "action_text": "自分が担った部分と、助けてもらった部分を分けてメモした。",
    "emotions": [
        {"type": "喜び", "strength": "medium"},
        {"type": "不安", "strength": "medium"},
    ],
    "categories": ["仕事", "人間関係"],
}

_SOURCE_AUTHORITATIVE_RECLASSIFICATION_INPUT = {
    "thought_text": (
        "いろいろ重なっている気はする。でも、どれが一番つらいのかも、"
        "何から話せばいいのかも今は分からない。"
    ),
    "action_text": "書こうとして、出来事を決められないまま画面を閉じた。",
    "emotions": [
        {"type": "悲しみ", "strength": "strong"},
        {"type": "不安", "strength": "strong"},
        {"type": "怒り", "strength": "weak"},
    ],
    "categories": ["生活", "仕事", "人間関係"],
}

_INVALID16_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "contract"
    / "invalid_v1.jsonl"
)


def _write_canonical_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    text = "\n".join(
        json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for row in rows
    )
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def test_s11_invalid16_loader_accepts_frozen_step3_wrapper_contract() -> None:
    assert regression_module.validate_invalid16_inventory_contract() == ()
    rows = regression_module.load_invalid16_fixtures(_INVALID16_FIXTURE_PATH)
    assert len(rows) == 16
    assert len({row["fixture_id"] for row in rows}) == 16
    assert all(
        set(row) == {"expected_issue", "fixture_id", "input"}
        for row in rows
    )
    assert all(
        regression_module.validate_app_reachable_input(row["input"])
        == (row["expected_issue"],)
        for row in rows
    )


def test_s11_invalid16_loader_rejects_wrapper_contract_drift(
    tmp_path: Path,
) -> None:
    base: dict[str, object] = {
        "expected_issue": "input:thought_action_both_empty_after_js_trim",
        "fixture_id": "probe",
        "input": {
            "action_text": "",
            "categories": ["生活"],
            "emotions": [{"strength": "weak", "type": "悲しみ"}],
            "thought_text": "",
        },
    }

    keyset_path = tmp_path / "invalid_keyset.jsonl"
    _write_canonical_jsonl(keyset_path, [{**base, "extra": True}])
    with pytest.raises(
        ValueError,
        match="step11_invalid_fixture_wrapper_keyset_invalid:1",
    ):
        regression_module.load_invalid16_fixtures(keyset_path)

    duplicate_path = tmp_path / "invalid_duplicate.jsonl"
    _write_canonical_jsonl(duplicate_path, [base, deepcopy(base)])
    with pytest.raises(
        ValueError,
        match="step11_invalid_fixture_id_invalid_or_duplicate:2",
    ):
        regression_module.load_invalid16_fixtures(duplicate_path)

    mismatch_path = tmp_path / "invalid_expected_issue.jsonl"
    mismatch = {**base, "expected_issue": "input:keyset_mismatch"}
    _write_canonical_jsonl(mismatch_path, [mismatch])
    with pytest.raises(
        ValueError,
        match="step11_invalid_fixture_expected_issue_mismatch:1",
    ):
        regression_module.load_invalid16_fixtures(mismatch_path)

    reordered_path = tmp_path / "invalid_reordered.jsonl"
    frozen_rows = regression_module.load_canonical_jsonl(
        _INVALID16_FIXTURE_PATH,
        validator=None,
    )
    _write_canonical_jsonl(reordered_path, list(reversed(frozen_rows)))
    with pytest.raises(
        ValueError,
        match="step11_invalid_fixture_inventory_mismatch",
    ):
        regression_module.load_invalid16_fixtures(reordered_path)


def test_multiline_source_ranges_map_to_canonical_display_exactly() -> None:
    source = "前の節。\n\n同じ節。\n  同じ節。\n最後の節。"
    display = overlay_module._normalise_text(source)
    first_start = source.index("同じ節")
    second_start = source.index("同じ節", first_start + 1)
    last_start = source.index("最後の節")
    assert overlay_module._canonical_display_range(
        source,
        display,
        first_start,
        first_start + len("同じ節。"),
    ) == (5, 9)
    assert overlay_module._canonical_display_range(
        source,
        display,
        second_start,
        second_start + len("同じ節。"),
    ) == (10, 14)
    last_range = overlay_module._canonical_display_range(
        source,
        display,
        last_start,
        len(source),
    )
    assert display[slice(*last_range)] == "最後の節。"
    decomposed = "か\u3099  行\r\n次"
    composed_display = overlay_module._normalise_text(decomposed)
    assert composed_display == "が 行 次"
    assert overlay_module._canonical_display_range(
        decomposed,
        composed_display,
        0,
        2,
    ) == (0, 1)

    with pytest.raises(
        overlay_module.Step11SemanticOverlayError,
        match="STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID",
    ):
        overlay_module._canonical_display_range(
            source,
            display + "改変",
            first_start,
            first_start + len("同じ節。"),
        )
    with pytest.raises(
        overlay_module.Step11SemanticOverlayError,
        match="STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID",
    ):
        overlay_module._canonical_display_range(
            source,
            display,
            len(source),
            len(source) + 1,
        )
    with pytest.raises(
        overlay_module.Step11SemanticOverlayError,
        match="STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID",
    ):
        overlay_module._canonical_display_range(
            decomposed,
            composed_display,
            1,
            2,
        )


def test_evidence_span_internal_whitespace_maps_back_to_raw_coordinates() -> None:
    current_input = {
        "thought_text": "同じ  節を\t書いた。",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["生活"],
    }
    projection = overlay_module._input_projection(current_input)
    sources = overlay_module._evidence_source_texts(current_input)
    span = overlay_module._text_evidence_spans(current_input)[0]
    assert span.raw_text == "同じ 節を 書いた"
    source_slot, display, start, end = overlay_module._span_display_range(
        sources,
        projection,
        span,
        0,
        len(span.raw_text),
    )
    assert source_slot == "thought"
    assert display[start:end] == span.raw_text


@pytest.mark.parametrize("case_ref", ("B", "C"))
def test_known28_multiline_projection_has_exact_in_bounds_anchors(
    case_ref: str,
) -> None:
    case = next(
        row
        for row in regression_module.load_baseline_cases()
        if row.case_id == case_ref
    )
    projected, issues = regression_module.project_known28_legacy_input(
        dict(case.current_input)
    )
    assert issues == ()
    assert projected is not None
    execution = execute_step11_offline_v3(
        projected,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="c" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    anchors = execution.selected_candidate.surface_ast.source_fragments
    assert anchors
    canonical = overlay_module._input_projection(projected)
    text_anchors = tuple(
        row for row in anchors if row.source_slot in {"thought", "action"}
    )
    assert text_anchors
    assert all(
        canonical[f"{row.source_slot}_text"][
            row.source_start : row.source_end
        ]
        == row.text
        for row in text_anchors
    )


@pytest.fixture(scope="module")
def selected_execution():
    execution = execute_step11_offline_v3(
        {
            "thought_text": "なんとなく、落ち着かない。",
            "action_text": "",
            "emotions": [{"type": "不安", "strength": "weak"}],
            "categories": ["生活"],
        },
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="1" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    return execution


def test_rc0022_density_malformed_layout_fails_closed_without_arity_error(
    selected_execution,
) -> None:
    candidate = selected_execution.selected_candidate
    assert candidate is not None
    witness = parse_step11_natural_surface(candidate.final_utf8_bytes)
    malformed = candidate.final_utf8_bytes.replace(
        "見えたこと：".encode("utf-8"),
        "壊れた見出し：".encode("utf-8"),
        1,
    )

    assert hard_gate_module._surface_density_metrics(
        malformed, witness
    ) == (999, 999, 999)
    assert hard_gate_module._surface_density_green(
        malformed, witness
    ) is False


@pytest.fixture(scope="module")
def thought_only_omitted_referent_execution():
    execution = execute_step11_offline_v3(
        _THOUGHT_ONLY_OMITTED_REFERENT_INPUT,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="9" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    assert all(
        row.hard_pass for row in execution.selection_result.gate_results
    )
    return execution


@pytest.fixture(scope="module")
def other_person_unknown_execution():
    execution = execute_step11_offline_v3(
        _OTHER_PERSON_UNKNOWN_INPUT,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="6" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    assert all(
        row.hard_pass for row in execution.selection_result.gate_results
    )
    return execution


@pytest.fixture
def relation_scoped_unknown_executions():
    class _LazyExecutions:
        def __getitem__(self, key: str):
            execution = execute_step11_offline_v3(
                _RELATION_SCOPED_UNKNOWN_INPUTS[key],
                candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                source_dependency_closure_sha256="2" * 64,
            )
            assert execution.status == "selected"
            assert execution.selected_candidate is not None
            return execution

        def values(self):
            return (self[key] for key in _RELATION_SCOPED_UNKNOWN_INPUTS)

    return _LazyExecutions()


@pytest.fixture(scope="module")
def self_denial_boundary_executions():
    required_case = next(
        row
        for row in regression_module.load_baseline_cases()
        if row.case_id == "D"
    )
    required_input, required_issues = (
        regression_module.project_known28_legacy_input(
            dict(required_case.current_input)
        )
    )
    assert required_issues == ()
    assert required_input is not None
    return {
        "accountability": execute_step11_offline_v3(
            _ACCOUNTABILITY_INPUT,
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="3" * 64,
        ),
        "action_self_denial": execute_step11_offline_v3(
            _ACTION_SELF_DENIAL_INPUT,
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="3" * 64,
        ),
        "required_self_denial": execute_step11_offline_v3(
            required_input,
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="3" * 64,
        ),
    }


@pytest.fixture(scope="module")
def known_structural_contract_executions():
    cases = {
        row.case_id: row for row in regression_module.load_baseline_cases()
    }
    result = {}
    for case_ref in ("I6-D02", "RR8-U10", "RR8-U11"):
        projected, issues = regression_module.project_known28_legacy_input(
            dict(cases[case_ref].current_input)
        )
        assert issues == ()
        assert projected is not None
        result[case_ref] = execute_step11_offline_v3(
            projected,
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256="7" * 64,
        )
    return result


@pytest.fixture(scope="module")
def completed_action_execution():
    execution = execute_step11_offline_v3(
        _COMPLETED_ACTION_INPUT,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="4" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    return execution


@pytest.fixture(scope="module")
def optional_uncertain_execution():
    execution = execute_step11_offline_v3(
        _OPTIONAL_UNCERTAIN_INPUT,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="8" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    return execution


@pytest.fixture
def source_bound_contract_executions():
    inputs = {
        "temporal_suppression": _CONTEXT_RESOLVED_TEMPORAL_INPUT,
        "endpoint_immutability": _EXACT_RELATION_ENDPOINT_INPUT,
        "unknown_lifecycle": (
            _SOURCE_AUTHORITATIVE_RECLASSIFICATION_INPUT
        ),
    }
    class _LazyExecutions:
        def __getitem__(self, key: str):
            execution = execute_step11_offline_v3(
                inputs[key],
                candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                source_dependency_closure_sha256="5" * 64,
            )
            assert execution.status == "selected"
            assert execution.selected_candidate is not None
            return execution

    return _LazyExecutions()


def _match_witness(execution, witness):
    selected = execution.selected_candidate
    assert selected is not None
    return match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
        current_input=execution.projected_current_input,
    )


def test_forged_candidate_without_ast() -> None:
    forged = SimpleNamespace(
        candidate_id="nls3s11cand_00000000000000000000",
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        discourse_plan={},
        rendered_surface=SimpleNamespace(
            utf8_bytes=b"forged",
            sha256="0" * 64,
            surface_catalog_sha256="0" * 64,
        ),
    )

    result = evaluate_step11_natural_surface_candidate(
        forged,
        inventory_result=None,
        content_plan={},
        current_input={},
    )

    assert result.hard_pass is False
    assert len(result.outcomes) == 20
    assert tuple(row.ordinal for row in result.outcomes) == tuple(range(1, 21))
    assert result.failure_codes == _EXPECTED_GATE_FAILURE_CODES


def test_noncanonical_body_mutation(selected_execution) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    mutated_bytes = selected.rendered_surface.utf8_bytes + "！".encode("utf-8")
    mutated_render = replace(
        selected.rendered_surface,
        utf8_bytes=mutated_bytes,
        sha256=hashlib.sha256(mutated_bytes).hexdigest(),
    )
    mutated_candidate = replace(selected, rendered_surface=mutated_render)

    result = evaluate_step11_natural_surface_candidate(
        mutated_candidate,
        inventory_result=selected_execution.inventory_result,
        content_plan=selected_execution.content_plan,
        current_input=selected_execution.projected_current_input,
    )

    assert result.hard_pass is False
    assert "S11_GATE03_CANONICAL_RENDER_EQUALITY" in result.failure_codes
    assert "S11_GATE18_SURFACE_INTEGRITY" in result.failure_codes


def test_surplus_semantic_atom(selected_execution) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    surplus = replace(
        reception,
        atom_id="s11atom_surplus_security",
        reception_act="unsupported_security_act",
        byte_start=reception.byte_end,
        byte_end=reception.byte_end,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, surplus),
        reception_atom_count=witness.reception_atom_count + 1,
    )

    binding = _match_witness(selected_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_typed_unknown_generic_substitution(selected_execution) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    typed = next(
        atom
        for atom in witness.atoms
        if atom.unknown_dimension_class not in {None, "generic"}
    )
    generic = replace(
        typed,
        form_id="unknown:generic:security_substitution",
        unknown_dimension_class="generic",
    )
    forged_witness = replace(
        witness,
        atoms=tuple(generic if atom is typed else atom for atom in witness.atoms),
    )

    binding = _match_witness(selected_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_UNKNOWN_UNRESOLVED" in binding.issue_codes


@pytest.mark.parametrize("case_key", tuple(_RELATION_SCOPED_UNKNOWN_INPUTS))
def test_relation_scoped_unknown_requires_all_exact_anchors(
    relation_scoped_unknown_executions,
    case_key: str,
) -> None:
    execution = relation_scoped_unknown_executions[case_key]
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    assert all(row.hard_pass for row in execution.selection_result.gate_results)


def test_relation_scoped_unknown_rejects_partial_antecedent(
    relation_scoped_unknown_executions,
) -> None:
    execution = relation_scoped_unknown_executions["cause_and_referent"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    relation = next(
        atom
        for atom in witness.atoms
        if atom.relation_type == "precedes"
        and len(atom.relation_endpoint_references) == 2
    )
    partial_relation = replace(
        relation,
        relation_endpoint_references=(
            relation.relation_endpoint_references[0],
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            partial_relation if atom is relation else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_RELATION_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_UNKNOWN_TARGET_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_UNKNOWN_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_thought_only_omitted_referent_anaphora_closes_end_to_end(
    thought_only_omitted_referent_execution,
) -> None:
    execution = thought_only_omitted_referent_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    thought_owner = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.introduced_reference is not None
        and atom.introduced_reference.endpoint_role == "proposition"
        and "nucleus_notice" in atom.claim_kinds
    )
    unknown = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("unknown_anaphora:referent:")
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    binding = _match_witness(execution, witness)
    required_ids = set(
        execution.content_plan["required_coverage_obligation_ids"]
    )
    ledger_by_id = {
        row["obligation_id"]: row
        for row in execution.inventory_result.ledger["obligations"]
    }

    assert thought_owner.source_fragments == ("まだよく分からない",)
    assert thought_owner.source_slot_hints == ("thought",)
    assert thought_owner.predicate_role == "proposition"
    assert unknown.source_fragments == ()
    assert unknown.unknown_dimension_class == "referent"
    assert reception.form_id.startswith("reception:anaphoric:")
    assert reception.source_fragments == ()
    assert reception.reception_antecedent_references == ()
    assert len(required_ids) == 3
    assert {
        ledger_by_id[obligation_id]["kind"]
        for obligation_id in required_ids
    } == {
        "grounded_nucleus_notice",
        "unknown_boundary_preservation",
        STANCE_KIND,
    }
    assert binding.verified is True
    assert binding.issue_codes == ()
    assert {row.obligation_id for row in binding.binding_rows} == required_ids
    assert all(row.atom_ids for row in binding.binding_rows)


def test_other_person_unknown_anaphora_closes_with_specific_dimension(
    other_person_unknown_execution,
) -> None:
    execution = other_person_unknown_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    unknown = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("unknown_anaphora:referent_other:")
    )
    binding = _match_witness(execution, witness)

    assert unknown.source_fragments == ()
    assert unknown.unknown_dimension_class == "other_person_awareness"
    assert binding.verified is True
    assert binding.issue_codes == ()


def test_other_person_unknown_rejects_generic_referent_substitution(
    other_person_unknown_execution,
) -> None:
    execution = other_person_unknown_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    unknown = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("unknown_anaphora:referent_other:")
    )
    forged_unknown = replace(
        unknown,
        form_id="unknown_anaphora:referent:security_generic_substitution",
        unknown_dimension_class="referent",
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_unknown if atom is unknown else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_UNKNOWN_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_UNKNOWN_SOURCE_ID_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_thought_only_unknown_anaphora_rejects_missing_antecedent(
    thought_only_omitted_referent_execution,
) -> None:
    execution = thought_only_omitted_referent_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    antecedent = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.introduced_reference is not None
        and atom.introduced_reference.endpoint_role == "proposition"
    )
    without_antecedent = replace(antecedent, source_fragments=())
    forged_witness = replace(
        witness,
        atoms=tuple(
            without_antecedent if atom is antecedent else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_REFERENCE_INTRODUCTION_INVALID" in binding.issue_codes
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_COVERAGE_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_UNKNOWN_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_REQUIRED_OBLIGATION_UNBOUND" in binding.issue_codes
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )


def test_thought_only_unknown_anaphora_rejects_duplicate_antecedent(
    thought_only_omitted_referent_execution,
) -> None:
    execution = thought_only_omitted_referent_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    antecedent = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.introduced_reference is not None
        and atom.introduced_reference.endpoint_role == "proposition"
    )
    duplicate = replace(
        antecedent,
        atom_id="nls3s11atom_security_duplicate_unknown_antecedent",
        byte_start=antecedent.byte_end,
        byte_end=antecedent.byte_end,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, duplicate),
        observation_atom_count=witness.observation_atom_count + 1,
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" in binding.issue_codes
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_DUPLICATE"
        in binding.issue_codes
    )
    assert "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED" in binding.issue_codes


def test_thought_only_unknown_anaphora_rejects_dimension_tamper(
    thought_only_omitted_referent_execution,
) -> None:
    execution = thought_only_omitted_referent_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    unknown = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("unknown_anaphora:referent:")
    )
    forged_unknown = replace(
        unknown,
        form_id="unknown_anaphora:cause:security_dimension_tamper",
        unknown_dimension_class="cause",
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_unknown if atom is unknown else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_UNKNOWN_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_UNKNOWN_SOURCE_ID_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_thought_only_unknown_anaphora_rejects_target_ownership_swap(
    thought_only_omitted_referent_execution,
    monkeypatch,
) -> None:
    execution = thought_only_omitted_referent_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    owned = next(
        row
        for row in overlay.unknowns
        if row.unknown_type == "omitted_referent"
        and row.source_unknown_ids
    )
    forged_unknown = replace(
        owned,
        target_nucleus_ids=("nucleus_ffffffffffffffffffff",),
    )
    forged_overlay = replace(
        overlay,
        unknowns=tuple(
            forged_unknown if row is owned else row
            for row in overlay.unknowns
        ),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )

    binding = _match_witness(execution, witness)

    assert binding.verified is False
    assert "S11_MATCH_UNKNOWN_SOURCE_ID_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_REQUIRED_OBLIGATION_UNBOUND" in binding.issue_codes


def test_unique_observation_antecedent_renders_anaphoric_reception(
    completed_action_execution,
) -> None:
    selected = completed_action_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    binding = _match_witness(completed_action_execution, witness)
    overlay = overlay_module.build_step11_semantic_overlay(
        completed_action_execution.projected_current_input,
        inventory_result=completed_action_execution.inventory_result,
        content_plan=completed_action_execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    expected_binding_ids = tuple(
        sorted(row.binding_id for row in overlay.reception_antecedent_bindings)
    )

    assert reception.form_id.startswith("reception:anaphoric:")
    assert reception.source_fragments == ()
    assert reception.reception_antecedent_references == ()
    assert binding.verified is True
    assert binding.integrated_reception_binding_ids == expected_binding_ids
    assert any(
        row.match_basis
        == "bound_reception_anaphoric_unique_exact_source_owner"
        for row in binding.binding_rows
    )


def test_anaphoric_reception_requires_visible_unique_antecedent(
    completed_action_execution,
) -> None:
    selected = completed_action_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    assert reception.form_id.startswith("reception:anaphoric:")
    antecedent = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.source_fragments
        and atom.predicate_role == "action"
    )
    without_antecedent = replace(
        antecedent,
        source_fragments=(),
        introduced_reference=None,
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            without_antecedent if atom is antecedent else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(completed_action_execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_anaphoric_reception_rejects_ambiguous_observation_antecedent(
    completed_action_execution,
) -> None:
    selected = completed_action_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    antecedent = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.source_fragments
        and atom.predicate_role == "action"
    )
    duplicate = replace(
        antecedent,
        atom_id="nls3s11atom_security_duplicate_antecedent",
        byte_start=antecedent.byte_end,
        byte_end=antecedent.byte_end,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, duplicate),
        observation_atom_count=witness.observation_atom_count + 1,
    )

    binding = _match_witness(completed_action_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" in binding.issue_codes
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )


def test_reception_target_is_owned_by_exact_ledger_and_node_ids(
    source_bound_contract_executions,
    monkeypatch,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    reception = overlay.reception_antecedent_bindings[0]
    obligations = {
        row["obligation_id"]: row
        for row in execution.inventory_result.ledger["obligations"]
    }
    nodes = {
        row["obligation_id"]: row
        for row in selected.discourse_plan["nodes"]
    }
    adjacent_id = next(
        obligation_id
        for obligation_id, row in obligations.items()
        if obligation_id in nodes
        and obligation_id not in reception.antecedent_obligation_ids
        and row["kind"] != STANCE_KIND
        and row.get("nucleus_ids")
    )
    adjacent_node_id = str(nodes[adjacent_id]["node_id"])
    adjacent_nucleus_ids = tuple(
        sorted(obligations[adjacent_id]["nucleus_ids"])
    )
    forged_material = {
        "reception_obligation_id": reception.reception_obligation_id,
        "reception_node_id": reception.reception_node_id,
        "antecedent_obligation_ids": [adjacent_id],
        "antecedent_node_ids": [adjacent_node_id],
        "antecedent_nucleus_ids": list(adjacent_nucleus_ids),
        "allowed_response_acts": list(reception.allowed_response_acts),
        "evidence_grade": reception.evidence_grade,
    }
    forged_reception = replace(
        reception,
        binding_id="s11recv_" + artifact_sha256(forged_material)[:16],
        antecedent_obligation_ids=(adjacent_id,),
        antecedent_node_ids=(adjacent_node_id,),
        antecedent_nucleus_ids=adjacent_nucleus_ids,
    )
    forged_overlay = replace(
        overlay,
        reception_antecedent_bindings=(forged_reception,),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )

    binding = _match_witness(execution, witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH"
        in binding.issue_codes
    )


def test_reception_direct_literal_fallback_is_forbidden(
    completed_action_execution,
) -> None:
    execution = completed_action_execution
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    assert reception.form_id.startswith("reception:anaphoric:")
    forged_reception = replace(
        reception,
        form_id=reception.form_id.replace(
            "reception:anaphoric:", "reception:direct:"
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_reception if atom is reception else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_RECEPTION_BINDING_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("relation_type", "supports_without_guarantee"),
        ("relation_direction", "target_to_source"),
        ("relation_endpoint_references", "reverse"),
        ("relation_endpoint_roles", ("proposition", "action")),
    ),
)
def test_relation_requires_exact_type_direction_and_ordered_endpoints(
    relation_scoped_unknown_executions,
    field: str,
    replacement: object,
) -> None:
    execution = relation_scoped_unknown_executions["cause_and_future"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    relation = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.form_id.startswith("relation:")
    )
    value = (
        tuple(reversed(relation.relation_endpoint_references))
        if replacement == "reverse"
        else replacement
    )
    forged_relation = replace(relation, **{field: value})
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_relation if atom is relation else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_RELATION_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes
    if field == "relation_endpoint_references":
        assert (
            "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
            in binding.issue_codes
        )


def test_truncated_relation_endpoint_cannot_be_completed_by_matcher(
    source_bound_contract_executions,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    relation = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("relation:")
        and len(atom.relation_endpoint_references) == 2
    )
    endpoint_reference = relation.relation_endpoint_references[0]
    endpoint_owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference == endpoint_reference
    )
    assert len(endpoint_owner.source_fragments) == 1
    assert len(endpoint_owner.source_fragments[0]) > 1
    forged_owner = replace(
        endpoint_owner,
        source_fragments=(
            endpoint_owner.source_fragments[0][:-1],
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_owner if atom is endpoint_owner else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_FRAGMENT_NOT_SOURCE_BACKED" in binding.issue_codes
    assert "S11_MATCH_REFERENCE_INTRODUCTION_INVALID" in binding.issue_codes
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_COVERAGE_MISMATCH"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_REQUIRED_OBLIGATION_UNBOUND" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_action_endpoint_catalog_rejects_affect_role_lexeme(
    monkeypatch,
) -> None:
    forged = deepcopy(catalog_module.STEP11_SURFACE_CATALOG)
    row = forged["relation_forms"]["coexists_with"]["bidirectional"][
        "action"
    ]["action"][0]
    row["stem"] += "感情"
    digest = artifact_sha256(forged)
    monkeypatch.setattr(catalog_module, "STEP11_SURFACE_CATALOG", forged)
    monkeypatch.setattr(
        catalog_module, "STEP11_SURFACE_CATALOG_SHA256", digest
    )
    monkeypatch.setattr(
        catalog_module, "FROZEN_STEP11_SURFACE_CATALOG_SHA256", digest
    )

    issues = catalog_module.validate_step11_surface_catalog()

    assert "STEP11_SURFACE_CATALOG_ACTION_ROLE_LEXEME_UNSAFE" in issues


def test_mixed_emotion_requires_one_exact_typed_reference_relation(
    relation_scoped_unknown_executions,
) -> None:
    execution = relation_scoped_unknown_executions["cause_and_generic"]
    selected = execution.selected_candidate
    assert selected is not None
    overlay = overlay_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    compound = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("mixed_emotion_compound:")
    )
    expected_references = compound.compound_label_references
    mixed_atoms = tuple(
        atom
        for atom in witness.atoms
        if atom.relation_endpoint_references == expected_references
        and atom.relation_type == "coexists_with"
        and atom.relation_direction == "bidirectional"
    )
    binding = _match_witness(execution, witness)

    assert len(overlay.mixed_emotion_requirements) == 1
    assert len(mixed_atoms) == 1
    assert mixed_atoms[0].source_slot_hints == ("emotion", "emotion")
    assert mixed_atoms[0].source_fragments == ("喜び", "不安")
    assert mixed_atoms[0].compound_label_references == expected_references
    assert mixed_atoms[0].relation_endpoint_references == expected_references
    assert mixed_atoms[0].relation_type == "coexists_with"
    assert mixed_atoms[0].relation_direction == "bidirectional"
    assert mixed_atoms[0].relation_endpoint_roles == ("affect", "affect")
    assert binding.verified is True
    assert binding.integrated_mixed_emotion_requirement_ids == (
        overlay.mixed_emotion_requirements[0].requirement_id,
    )


def test_mixed_emotion_rejects_reversed_label_ownership(
    relation_scoped_unknown_executions,
) -> None:
    execution = relation_scoped_unknown_executions["cause_and_generic"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    mixed = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("mixed_emotion_compound:")
        and atom.relation_type == "coexists_with"
        and atom.relation_direction == "bidirectional"
    )
    forged_mixed = replace(
        mixed,
        compound_label_references=tuple(
            reversed(mixed.compound_label_references)
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_mixed if atom is mixed else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_MIXED_EMOTION_COMPOUND_ORDER_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_MIXED_EMOTION_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_legacy_relation_context_form_cannot_replace_exact_pair(
    relation_scoped_unknown_executions,
) -> None:
    execution = relation_scoped_unknown_executions["future"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    relation = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.form_id.startswith("relation:")
    )
    context_only = replace(
        relation,
        form_id=(
            f"relation_context:{relation.relation_type}:"
            f"{relation.relation_direction}:security"
        ),
        claim_kinds=("relation_notice",),
        source_slot_hints=(),
        source_fragments=(),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            context_only if atom is relation else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_RELATION_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_coexistence_still_requires_exact_from_to_endpoint_order(
    relation_scoped_unknown_executions,
) -> None:
    execution = relation_scoped_unknown_executions["future"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    relation = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.form_id.startswith("relation:")
    )
    assert relation.relation_type == "coexists_with"
    assert relation.relation_direction == "bidirectional"
    reversed_relation = replace(
        relation,
        relation_endpoint_references=tuple(
            reversed(relation.relation_endpoint_references)
        ),
    )
    reversed_witness = replace(
        witness,
        atoms=tuple(
            reversed_relation if atom is relation else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, reversed_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_RELATION_UNRESOLVED" in binding.issue_codes
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_optional_uncertain_relations_are_symmetric_copresence(
    optional_uncertain_execution,
) -> None:
    selected = optional_uncertain_execution.selected_candidate
    assert selected is not None
    overlay = overlay_module.build_step11_semantic_overlay(
        optional_uncertain_execution.projected_current_input,
        inventory_result=optional_uncertain_execution.inventory_result,
        content_plan=optional_uncertain_execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    optional_rows = tuple(
        row
        for row in overlay.relations
        if row.source_relation_kind == "uncertain_connection"
        and row.required is False
        and row.evidence_grade != "cross_field_same_event_restatement"
    )
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    binding = _match_witness(optional_uncertain_execution, witness)

    assert all(
        row.relation_type == "coexists_with"
        and row.relation_direction == "bidirectional"
        and row.evidence_grade
        in {
            "cross_field_copresence_only",
            "source_order_copresence_only",
        }
        for row in optional_rows
    )
    relation_atoms = tuple(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("relation:")
    )
    assert all(
        len(atom.source_fragments) == 2
        and len(atom.relation_endpoint_roles) == 2
        and "relation_chain" not in atom.form_id
        and "relation_context" not in atom.form_id
        for atom in relation_atoms
    )
    assert binding.verified is True
    assert binding.issue_codes == ()


def test_selected_optional_uncertain_relation_cannot_upcast(
    optional_uncertain_execution,
) -> None:
    selected = optional_uncertain_execution.selected_candidate
    assert selected is not None
    overlay = overlay_module.build_step11_semantic_overlay(
        optional_uncertain_execution.projected_current_input,
        inventory_result=optional_uncertain_execution.inventory_result,
        content_plan=optional_uncertain_execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    active_nucleus_ids = frozenset(
        row.nucleus_id for row in overlay.nucleus_anchor_bindings
    )
    source_relation = next(
        row
        for row in optional_uncertain_execution.inventory_result.source_snapshot.relations
        if row.source_relation_kind == "uncertain_connection"
        and row.required is False
        and {row.from_nucleus_id, row.to_nucleus_id} <= active_nucleus_ids
    )
    selected_rows = overlay_module._overlay_relations(
        optional_uncertain_execution.inventory_result,
        active_nucleus_ids,
        active_relation_ids=frozenset({source_relation.source_id}),
        selected_relation_ids=frozenset({source_relation.source_id}),
        content_depth="layered",
        projection=overlay_module._input_projection(
            optional_uncertain_execution.projected_current_input
        ),
        anchor_ids_by_nucleus={
            row.nucleus_id: row.source_anchor_ids
            for row in overlay.nucleus_anchor_bindings
        },
        label_anchor_ids_by_nucleus={
            row.nucleus_id: row.source_label_anchor_ids
            for row in overlay.nucleus_anchor_bindings
        },
        anchor_by_id={row.anchor_id: row for row in overlay.anchors},
    )

    assert len(selected_rows) == 1
    assert selected_rows[0].relation_type == "coexists_with"
    assert selected_rows[0].relation_direction == "bidirectional"
    assert selected_rows[0].evidence_grade in {
        "cross_field_copresence_only",
        "source_order_copresence_only",
    }


def test_same_event_restatement_exception_is_narrow_and_independent() -> None:
    same_left = "机の上を静かに片づけた。"
    same_right = "机の上を片づけた。"
    different = "友人へ短い連絡を送った。"

    assert overlay_module._same_event_restatement(same_left, same_right)
    assert matcher_module._independent_same_event_restatement(
        same_left, same_right
    )
    assert not overlay_module._same_event_restatement(same_left, different)
    assert not matcher_module._independent_same_event_restatement(
        same_left, different
    )


def test_relation_alias_cannot_inherit_a_different_signature(
    relation_scoped_unknown_executions,
    monkeypatch,
) -> None:
    execution = relation_scoped_unknown_executions["cause_and_future"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    real_overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    real_frontier = matcher_module.build_step11_planning_frontier(
        execution.inventory_result,
        execution.content_plan,
        selected.discourse_plan,
    )
    primary = real_overlay.relations[0]
    snapshot_by_id = {
        row.source_id: row
        for row in execution.inventory_result.source_snapshot.relations
    }
    primary_source = snapshot_by_id[primary.source_relation_id]
    alias = replace(
        primary_source,
        source_id="relation_ffffffffffffffffffff",
        relation_type=(
            "qualifies"
            if primary_source.relation_type != "qualifies"
            else "coexists_with"
        ),
    )
    forged_snapshot = replace(
        execution.inventory_result.source_snapshot,
        relations=(
            *execution.inventory_result.source_snapshot.relations,
            alias,
        ),
    )
    forged_inventory = replace(
        execution.inventory_result,
        source_snapshot=forged_snapshot,
    )
    forged_primary = replace(
        primary,
        source_relation_ids=(*primary.source_relation_ids, alias.source_id),
    )
    forged_overlay = replace(
        real_overlay,
        relations=(forged_primary, *real_overlay.relations[1:]),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_planning_frontier",
        lambda *_args, **_kwargs: real_frontier,
    )
    ledger = execution.inventory_result.ledger
    by_id = {row["obligation_id"]: row for row in ledger["obligations"]}
    monkeypatch.setattr(
        matcher_module,
        "_validated_parents",
        lambda *_args, **_kwargs: (ledger, by_id),
    )

    binding = match_step11_natural_surface(
        witness,
        inventory_result=forged_inventory,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
        current_input=execution.projected_current_input,
    )

    assert binding.verified is False
    assert (
        "S11_MATCH_RELATION_SOURCE_CONTRACT_MISMATCH"
        in binding.issue_codes
    )


def test_required_relation_endpoints_remain_exact_source_ids(
    source_bound_contract_executions,
    monkeypatch,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    source_by_id = {
        row.source_id: row
        for row in execution.inventory_result.source_snapshot.relations
    }
    assert overlay.relations
    assert all(
        row.evidence_grade
        not in {"required_action_nearest_nucleus_rebind"}
        and row.from_nucleus_id
        == source_by_id[row.source_relation_id].from_nucleus_id
        and row.to_nucleus_id
        == source_by_id[row.source_relation_id].to_nucleus_id
        for row in overlay.relations
    )
    relation = next(
        row
        for row in overlay.relations
        if row.required is True
    )
    adjacent_nucleus_id = next(
        row.source_id
        for row in execution.inventory_result.source_snapshot.nuclei
        if row.source_id
        not in {relation.from_nucleus_id, relation.to_nucleus_id}
    )
    forged_relation = replace(
        relation,
        from_nucleus_id=adjacent_nucleus_id,
    )
    forged_overlay = replace(
        overlay,
        relations=tuple(
            forged_relation if row is relation else row
            for row in overlay.relations
        ),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )

    binding = _match_witness(execution, witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RELATION_SOURCE_CONTRACT_MISMATCH"
        in binding.issue_codes
    )


def test_quote_budget_quotes_each_endpoint_once_then_uses_typed_references(
    source_bound_contract_executions,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    relation_atoms = tuple(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("relation:")
    )
    introductions = tuple(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
    )
    introduction_by_ordinal = {
        atom.introduced_reference.reference_ordinal: atom
        for atom in introductions
    }
    referenced_ordinals = {
        reference.reference_ordinal
        for atom in relation_atoms
        for reference in atom.relation_endpoint_references
    }
    rendered_text = selected.rendered_surface.utf8_bytes.decode("utf-8")
    binding = _match_witness(execution, witness)

    assert len(relation_atoms) >= 2
    assert all(atom.source_fragments == () for atom in relation_atoms)
    assert all(
        len(atom.relation_endpoint_references) == 2
        for atom in relation_atoms
    )
    assert len(introduction_by_ordinal) == len(introductions)
    assert referenced_ordinals <= set(introduction_by_ordinal)
    assert all(
        len(atom.source_fragments) == 1
        and rendered_text.count(f"『{atom.source_fragments[0]}』") == 1
        for atom in introductions
        if atom.introduced_reference.reference_ordinal
        in referenced_ordinals
    )
    assert binding.verified is True
    assert (
        "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED"
        not in binding.issue_codes
    )


def test_quote_budget_rejects_relation_unknown_span_replay(
    source_bound_contract_executions,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = overlay_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    decision = next(
        row for row in overlay.unknowns if row.unknown_type == "decision_state"
    )
    source_anchor = next(
        row
        for row in overlay.anchors
        if row.anchor_id == decision.source_anchor_ids[0]
    )
    unknown_atom = next(
        atom
        for atom in witness.atoms
        if atom.unknown_dimension_class == "decision_state"
    )
    replay = replace(
        unknown_atom,
        form_id="unknown_bound:decision_state:security_replay",
        claim_kinds=("nucleus_notice", "unknown_boundary"),
        source_slot_hints=(source_anchor.source_slot,),
        source_fragments=(source_anchor.text,),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            replay if atom is unknown_atom else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED" in binding.issue_codes
    )


def test_decision_unknown_lifecycle_and_oracle_are_source_bound(
    source_bound_contract_executions,
    relation_scoped_unknown_executions,
) -> None:
    cases = (
        (
            source_bound_contract_executions["endpoint_immutability"],
            "decision_state",
            "open",
        ),
        (
            relation_scoped_unknown_executions["cause_and_future"],
            "post_decision_comparative_merit",
            "completed",
        ),
    )
    for execution, unknown_type, decision_state in cases:
        selected = execution.selected_candidate
        assert selected is not None
        overlay = overlay_module.build_step11_semantic_overlay(
            execution.projected_current_input,
            inventory_result=execution.inventory_result,
            content_plan=execution.content_plan,
            discourse_plan=selected.discourse_plan,
        )
        unknown = next(
            row for row in overlay.unknowns if row.unknown_type == unknown_type
        )
        witness = parse_step11_natural_surface(
            selected.rendered_surface.utf8_bytes
        )
        binding = _match_witness(execution, witness)

        assert unknown.source_unknown_ids
        assert unknown.decision_state == decision_state
        assert unknown.context_nucleus_ids
        assert unknown.context_anchor_ids
        assert binding.verified is True
        assert len(binding.source_unknown_oracle_sha256) == 64
        int(binding.source_unknown_oracle_sha256, 16)


def test_unknown_lifecycle_forge_fails_independent_oracle(
    source_bound_contract_executions,
    monkeypatch,
) -> None:
    execution = source_bound_contract_executions["endpoint_immutability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    decision = next(
        row for row in overlay.unknowns if row.unknown_type == "decision_state"
    )
    forged_material = {
        "unknown_type": decision.unknown_type,
        "source_slots": list(decision.source_slots),
        "source_anchor_ids": list(decision.source_anchor_ids),
        "target_nucleus_ids": list(decision.target_nucleus_ids),
        "source_unknown_ids": list(decision.source_unknown_ids),
        "source_rules": list(decision.source_rules),
        "epistemic_basis": decision.epistemic_basis,
        "decision_state": "completed",
        "context_nucleus_ids": list(decision.context_nucleus_ids),
        "context_anchor_ids": list(decision.context_anchor_ids),
        "surface_policy": decision.surface_policy,
    }
    forged_unknown = replace(
        decision,
        unknown_id="s11unk_" + artifact_sha256(forged_material)[:16],
        decision_state="completed",
    )
    forged_overlay = replace(
        overlay,
        unknowns=tuple(
            forged_unknown if row is decision else row
            for row in overlay.unknowns
        ),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )

    binding = _match_witness(execution, witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_SOURCE_UNKNOWN_ORACLE_MISMATCH" in binding.issue_codes
    )


def test_temporal_suppression_requires_exact_context_anchor_provenance(
    source_bound_contract_executions,
    monkeypatch,
) -> None:
    execution = source_bound_contract_executions[
        "temporal_suppression"
    ]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    overlay = matcher_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    suppressed = overlay.suppressed_unknowns[0]
    assert suppressed.context_anchor_ids != suppressed.source_anchor_ids
    forged_suppression = replace(
        suppressed,
        context_anchor_ids=suppressed.source_anchor_ids,
    )
    forged_overlay = replace(
        overlay,
        suppressed_unknowns=(forged_suppression,),
    )
    monkeypatch.setattr(
        matcher_module,
        "build_step11_semantic_overlay",
        lambda *_args, **_kwargs: forged_overlay,
    )
    monkeypatch.setattr(
        matcher_module,
        "validate_step11_semantic_overlay",
        lambda *_args, **_kwargs: (),
    )

    binding = _match_witness(execution, witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_UNKNOWN_SUPPRESSION_CONTRACT_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_UNKNOWN_SOURCE_ID_UNRESOLVED" in binding.issue_codes


def test_accountability_is_not_fabricated_as_self_denial(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["accountability"]
    selected = execution.selected_candidate
    assert execution.inventory_result.source_snapshot.identity_claim_must_not_be_accepted_as_fact is True
    assert execution.status == "selected"
    assert selected is not None
    assert selected.surface_ast.identity_claim_must_not_be_accepted_as_fact is False
    assert selected.surface_ast.self_denial_source_slots == ()
    assert selected.surface_ast.self_denial_source_anchor_ids == ()
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    assert not any(atom.self_denial_not_fact for atom in witness.atoms)


def test_unbound_denial_injection_is_surplus(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["accountability"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    source_atom = next(
        atom for atom in witness.atoms if atom.section_role == "observation"
    )
    injected = replace(
        source_atom,
        claim_kinds=(*source_atom.claim_kinds, "self_denial_boundary"),
        self_denial_not_fact=True,
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            injected if atom is source_atom else atom for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_step11_vocabulary_cannot_override_step4_self_denial_authority(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["action_self_denial"]
    selected = execution.selected_candidate
    assert execution.status == "selected"
    assert selected is not None
    required_boundary_kinds = {
        row["kind"]
        for row in execution.inventory_result.ledger["obligations"]
        if row["required"] is True
        and row["kind"]
        in {"self_denial_boundary", "bounded_counterposition"}
    }
    assert required_boundary_kinds == set()
    ast = selected.surface_ast
    assert ast.identity_claim_must_not_be_accepted_as_fact is False
    assert ast.self_denial_source_slots == ()
    assert ast.self_denial_source_anchor_ids == ()
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    assert not any(atom.self_denial_not_fact for atom in witness.atoms)


def test_self_denial_anaphora_binds_unique_source_owned_relation_endpoint_across_labels(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    assert execution.natural_candidates
    candidate = execution.natural_candidates[0]
    witness = parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    denial = next(
        atom
        for atom in witness.atoms
        if atom.form_id.startswith("self_denial_anaphora:")
    )
    owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
        and atom.source_fragments == ("1番自分を傷つけてるのは私だ",)
    )
    relation = next(
        atom
        for atom in witness.atoms
        if atom.relation_type is not None
        and owner.introduced_reference
        in atom.relation_endpoint_references
    )
    intervening = tuple(
        atom
        for atom in witness.atoms
        if owner.byte_end < atom.byte_start < denial.byte_start
    )
    assert intervening
    assert relation in intervening
    assert relation.source_fragments == ()

    binding = match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )

    assert binding.verified is True
    assert binding.issue_codes == ()


def test_required_self_denial_pair_has_exact_source_anchor(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert execution.status == "selected"
    assert selected is not None
    ast = selected.surface_ast
    assert ast.identity_claim_must_not_be_accepted_as_fact is True
    assert ast.self_denial_source_slots == ("thought",)
    assert len(ast.self_denial_source_anchor_ids) == 1
    denial_fragments = tuple(
        row
        for row in ast.source_fragments
        if row.source_anchor_id in ast.self_denial_source_anchor_ids
    )
    assert len(denial_fragments) == 1
    assert denial_fragments[0].fragment_role == "self_evaluation"
    overlay = overlay_module.build_step11_semantic_overlay(
        execution.projected_current_input,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=selected.discourse_plan,
    )
    evaluation = overlay.reported_self_evaluations[0]
    evaluation_anchor = next(
        row
        for row in overlay.anchors
        if row.anchor_id == evaluation.source_anchor_id
    )
    self_row = next(
        row
        for row in execution.inventory_result.ledger["obligations"]
        if row["required"] is True
        and row["kind"] == "self_denial_boundary"
    )
    nucleus_binding = next(
        row
        for row in overlay.nucleus_anchor_bindings
        if row.nucleus_id == self_row["nucleus_ids"][0]
    )
    nucleus_anchor = next(
        row
        for row in overlay.anchors
        if row.anchor_id == nucleus_binding.source_anchor_ids[0]
    )
    assert (
        evaluation_anchor.source_slot,
        evaluation_anchor.start,
        evaluation_anchor.end,
        evaluation_anchor.text_sha256,
    ) == (
        nucleus_anchor.source_slot,
        nucleus_anchor.start,
        nucleus_anchor.end,
        nucleus_anchor.text_sha256,
    )
    forged = replace(overlay, reported_self_evaluations=())
    assert "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_MISMATCH" in (
        overlay_module.validate_step11_semantic_overlay(
            forged,
            current_input=execution.projected_current_input,
            inventory_result=execution.inventory_result,
            content_plan=execution.content_plan,
            discourse_plan=selected.discourse_plan,
        )
    )


def test_removing_required_denial_fails_closed(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(selected.rendered_surface.utf8_bytes)
    denial_atoms = tuple(
        atom for atom in witness.atoms if atom.self_denial_not_fact
    )
    assert denial_atoms
    forged_witness = replace(
        witness,
        atoms=tuple(
            atom for atom in witness.atoms if not atom.self_denial_not_fact
        ),
        observation_atom_count=(
            witness.observation_atom_count - len(denial_atoms)
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_SELF_DENIAL_UNRESOLVED" in binding.issue_codes


def test_duplicate_non_adjacent_self_denial_owner_is_ambiguous(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    denial = next(atom for atom in witness.atoms if atom.self_denial_not_fact)
    owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
        and atom.source_fragments == ("1番自分を傷つけてるのは私だ",)
    )
    duplicate_owner = replace(
        owner,
        atom_id="s11atom_duplicate_self_denial_owner",
        byte_start=denial.byte_start - 1,
        byte_end=denial.byte_start - 1,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, duplicate_owner),
        observation_atom_count=witness.observation_atom_count + 1,
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" in binding.issue_codes
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_DUPLICATE"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_SELF_DENIAL_ANTECEDENT_OWNER_AMBIGUOUS"
        in binding.issue_codes
    )
    assert "S11_MATCH_SELF_DENIAL_UNRESOLVED" in binding.issue_codes


def test_deleting_relation_endpoint_owner_leaves_self_denial_unresolved(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
        and atom.source_fragments == ("1番自分を傷つけてるのは私だ",)
    )
    forged_witness = replace(
        witness,
        atoms=tuple(atom for atom in witness.atoms if atom is not owner),
        observation_atom_count=witness.observation_atom_count - 1,
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_COVERAGE_MISMATCH"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_SELF_DENIAL_ANTECEDENT_UNRESOLVED"
        in binding.issue_codes
    )
    assert "S11_MATCH_SELF_DENIAL_UNRESOLVED" in binding.issue_codes


def test_required_denial_rejects_different_slot_substitution(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
        and atom.source_fragments == ("1番自分を傷つけてるのは私だ",)
    )
    wrong_slot_owner = replace(
        owner,
        source_slot_hints=("action",),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            wrong_slot_owner if atom is owner else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_FRAGMENT_NOT_SOURCE_BACKED" in binding.issue_codes
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_INVALID"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_REFERENCE_INTRODUCTION_COVERAGE_MISMATCH"
        in binding.issue_codes
    )
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )


def test_self_denial_terminal_punctuation_is_not_source_ownership(
    self_denial_boundary_executions,
) -> None:
    execution = self_denial_boundary_executions["required_self_denial"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    denial_atoms = tuple(
        atom for atom in witness.atoms if atom.self_denial_not_fact
    )
    owner = next(
        atom
        for atom in witness.atoms
        if atom.introduced_reference is not None
        and atom.source_fragments == ("1番自分を傷つけてるのは私だ",)
    )
    binding = _match_witness(execution, witness)

    assert len(denial_atoms) == 2
    assert all(atom.source_fragments == () for atom in denial_atoms)
    assert all(atom.byte_start > owner.byte_start for atom in denial_atoms)
    assert denial_atoms[0].form_id.startswith("self_denial_anaphora:")
    assert denial_atoms[1].form_id.startswith("bounded_counter_anaphora:")
    assert binding.verified is True
    assert binding.issue_codes == ()


@pytest.mark.parametrize("case_ref", ("I6-D02", "RR8-U11"))
def test_duplicate_required_receptions_share_one_semantic_atom(
    known_structural_contract_executions,
    case_ref: str,
) -> None:
    execution = known_structural_contract_executions[case_ref]
    selected = execution.selected_candidate
    assert execution.status == "selected"
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    binding = _match_witness(execution, witness)
    kind_by_id = {
        row["obligation_id"]: row["kind"]
        for row in execution.inventory_result.ledger["obligations"]
    }
    stance_bindings = tuple(
        row
        for row in binding.binding_rows
        if kind_by_id[row.obligation_id] == STANCE_KIND
    )
    assert binding.verified is True
    assert binding.issue_codes == ()
    assert witness.reception_atom_count == 1
    assert len(stance_bindings) == 2
    assert all(len(row.atom_ids) == 1 for row in stance_bindings)
    assert len({row.atom_ids[0] for row in stance_bindings}) == 1


def test_split_reception_groups_render_independently_and_fail_duplicate_surface(
    known_structural_contract_executions,
) -> None:
    execution = known_structural_contract_executions["I6-D02"]
    split_plan = next(
        plan
        for plan in execution.discourse_plan_set.plans
        if len(
            [
                group
                for group in plan["sentence_groups"]
                if group["section_role"] == "reception"
            ]
        )
        == 2
    )
    candidate = surface_module.build_step11_natural_surface_candidate(
        split_plan,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        current_input=execution.projected_current_input,
    )
    witness = parse_step11_natural_surface(
        candidate.rendered_surface.utf8_bytes
    )
    binding = match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=split_plan,
        current_input=execution.projected_current_input,
    )
    observation_lines = surface_module._additional_observation_lines(
        candidate.surface_ast
    )
    reception_lines = surface_module._reception_lines(
        candidate.surface_ast,
        observation_lines=observation_lines,
    )
    expected_binding_ids = {
        row.binding_id
        for row in candidate.surface_ast.reception_antecedent_bindings
    }
    expected_obligation_ids = {
        row.reception_obligation_id
        for row in candidate.surface_ast.reception_antecedent_bindings
    }
    reception_sentences = tuple(
        sentence
        for sentence in witness.sentences
        if sentence.section_role == "reception"
    )

    assert len(reception_lines) == 2
    assert all(len(row.binding_ids) == 1 for row in reception_lines)
    assert all(
        len(row.reception_obligation_ids) == 1
        for row in reception_lines
    )
    assert {
        binding_id
        for row in reception_lines
        for binding_id in row.binding_ids
    } == expected_binding_ids
    assert (
        {
            obligation_id
            for row in reception_lines
            for obligation_id in row.reception_obligation_ids
        }
        == expected_obligation_ids
    )
    assert len(reception_sentences) == 2
    assert all(len(row.clause_atom_ids) == 1 for row in reception_sentences)
    assert witness.reception_atom_count == 2
    assert binding.verified is False
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" in binding.issue_codes
    assert "S11_MATCH_RECEPTION_BINDING_UNRESOLVED" in binding.issue_codes


def test_targeted_self_denial_is_a_separate_terminal_boundary_pair(
    known_structural_contract_executions,
) -> None:
    execution = known_structural_contract_executions["RR8-U10"]
    selected = execution.selected_candidate
    assert execution.status == "selected"
    assert selected is not None
    row_by_id = {
        row["obligation_id"]: row
        for row in execution.inventory_result.ledger["obligations"]
    }
    node_kind = {
        node["node_id"]: row_by_id[node["obligation_id"]]["kind"]
        for node in selected.discourse_plan["nodes"]
    }
    observation_groups = tuple(
        tuple(node_kind[node_id] for node_id in group["node_ids"])
        for group in selected.discourse_plan["sentence_groups"]
        if group["section_role"] == "observation"
    )
    flattened = tuple(item for group in observation_groups for item in group)
    assert flattened[-2:] == (
        "self_denial_boundary",
        "bounded_counterposition",
    )
    assert observation_groups[-2][-1] == "self_denial_boundary"
    assert observation_groups[-1] == ("bounded_counterposition",)

    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    binding = _match_witness(execution, witness)
    observation_atoms = tuple(
        sorted(
            (
                atom
                for atom in witness.atoms
                if atom.section_role == "observation"
            ),
            key=lambda atom: atom.byte_start,
        )
    )
    boundary_atom, counter_atom = observation_atoms[-2:]
    owned_observation_lines = surface_module._additional_observation_lines(
        selected.surface_ast
    )
    boundary_line, counter_line = owned_observation_lines[-2:]
    owner_line = next(
        row
        for row in owned_observation_lines[:-2]
        if row.literal_anchor_ids
        and row.owned_nucleus_ids == boundary_line.owned_nucleus_ids
    )
    owner_literals = {
        fragment.text
        for fragment in selected.surface_ast.source_fragments
        if fragment.source_anchor_id in owner_line.literal_anchor_ids
    }
    owner_atom = next(
        atom
        for atom in observation_atoms[:-2]
        if atom.introduced_reference is not None
        and atom.source_fragments
        and set(atom.source_fragments) <= owner_literals
    )
    self_obligation_id = next(
        obligation_id
        for obligation_id, row in row_by_id.items()
        if row["kind"] == "self_denial_boundary"
    )
    counter_obligation_id = next(
        obligation_id
        for obligation_id, row in row_by_id.items()
        if row["kind"] == "bounded_counterposition"
    )
    assert owner_line.literal_anchor_ids
    assert boundary_line.literal_anchor_ids == ()
    assert counter_line.literal_anchor_ids == ()
    assert boundary_line.owned_anchor_ids == counter_line.owned_anchor_ids
    assert boundary_line.owned_nucleus_ids == counter_line.owned_nucleus_ids
    assert boundary_line.owned_obligation_ids == (self_obligation_id,)
    assert counter_line.owned_obligation_ids == (counter_obligation_id,)
    assert owner_atom.byte_start < boundary_atom.byte_start
    assert boundary_atom.self_denial_not_fact is True
    assert boundary_atom.form_id.startswith("self_denial_anaphora:")
    assert boundary_atom.source_fragments == ()
    assert counter_atom.self_denial_not_fact is True
    assert counter_atom.form_id.startswith("bounded_counter_anaphora:")
    assert counter_atom.source_fragments == ()
    safety_bindings = {
        row_by_id[row.obligation_id]["kind"]: row.atom_ids
        for row in binding.binding_rows
        if row_by_id[row.obligation_id]["kind"]
        in {"self_denial_boundary", "bounded_counterposition"}
    }
    assert binding.verified is True
    assert safety_bindings == {
        "self_denial_boundary": (boundary_atom.atom_id,),
        "bounded_counterposition": (counter_atom.atom_id,),
    }
    assert boundary_atom.atom_id != counter_atom.atom_id


def test_terminal_self_denial_requires_anaphoric_then_bounded_counter_forms(
    known_structural_contract_executions,
) -> None:
    execution = known_structural_contract_executions["RR8-U10"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    ordered = tuple(
        sorted(
            (
                atom
                for atom in witness.atoms
                if atom.section_role == "observation"
            ),
            key=lambda atom: atom.byte_start,
        )
    )
    boundary_atom, counter_atom = ordered[-2:]
    assert boundary_atom.form_id.startswith("self_denial_anaphora:")
    assert counter_atom.form_id.startswith("bounded_counter_anaphora:")
    assert boundary_atom.source_fragments == ()
    assert counter_atom.source_fragments == ()
    forged_boundary = replace(
        boundary_atom,
        form_id=counter_atom.form_id,
    )
    wrong_boundary_witness = replace(
        witness,
        atoms=tuple(
            forged_boundary if atom is boundary_atom else atom
            for atom in witness.atoms
        ),
    )
    wrong_boundary_binding = _match_witness(
        execution,
        wrong_boundary_witness,
    )
    assert wrong_boundary_binding.verified is False
    assert "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID" in (
        wrong_boundary_binding.issue_codes
    )

    forged_counter = replace(
        counter_atom,
        form_id=boundary_atom.form_id,
    )
    wrong_counter_witness = replace(
        witness,
        atoms=tuple(
            forged_counter if atom is counter_atom else atom
            for atom in witness.atoms
        ),
    )
    wrong_counter_binding = _match_witness(
        execution,
        wrong_counter_witness,
    )
    assert wrong_counter_binding.verified is False
    assert "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID" in (
        wrong_counter_binding.issue_codes
    )


def test_terminal_self_denial_pair_order_or_removal_fails_closed(
    known_structural_contract_executions,
) -> None:
    execution = known_structural_contract_executions["RR8-U10"]
    selected = execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    ordered = tuple(
        sorted(
            (
                atom
                for atom in witness.atoms
                if atom.section_role == "observation"
            ),
            key=lambda atom: atom.byte_start,
        )
    )
    boundary_atom, counter_atom = ordered[-2:]
    swapped_boundary = replace(
        boundary_atom,
        byte_start=counter_atom.byte_start,
        byte_end=counter_atom.byte_end,
    )
    swapped_counter = replace(
        counter_atom,
        byte_start=boundary_atom.byte_start,
        byte_end=boundary_atom.byte_end,
    )
    swapped = replace(
        witness,
        atoms=tuple(
            swapped_boundary
            if atom is boundary_atom
            else swapped_counter
            if atom is counter_atom
            else atom
            for atom in witness.atoms
        ),
    )
    swapped_binding = _match_witness(execution, swapped)
    assert swapped_binding.verified is False
    assert "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID" in (
        swapped_binding.issue_codes
    )

    removed = replace(
        witness,
        atoms=tuple(atom for atom in witness.atoms if atom is not counter_atom),
        observation_atom_count=witness.observation_atom_count - 1,
    )
    removed_binding = _match_witness(execution, removed)
    assert removed_binding.verified is False
    assert "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID" in (
        removed_binding.issue_codes
    )


def test_nonterminal_self_denial_plan_is_rejected_before_render(
    known_structural_contract_executions,
) -> None:
    execution = known_structural_contract_executions["RR8-U10"]
    selected = execution.selected_candidate
    assert selected is not None
    plan = selected.discourse_plan
    row_by_id = {
        row["obligation_id"]: row
        for row in execution.inventory_result.ledger["obligations"]
    }
    node_by_kind = {
        row_by_id[node["obligation_id"]]["kind"]: node["node_id"]
        for node in plan["nodes"]
        if row_by_id[node["obligation_id"]]["kind"]
        in {
            "grounded_nucleus_notice",
            "self_denial_boundary",
            "bounded_counterposition",
        }
    }
    forged = planner_module._build_plan(
        nodes=plan["nodes"],
        edges=tuple(
            (edge["from"], edge["to"], edge["type"])
            for edge in plan["edges"]
        ),
        observation_groups=(
            (node_by_kind["self_denial_boundary"],),
            (node_by_kind["bounded_counterposition"],),
            (node_by_kind["grounded_nucleus_notice"],),
        ),
        reception_groups=tuple(
            tuple(group["node_ids"])
            for group in plan["sentence_groups"]
            if group["section_role"] == "reception"
        ),
        content_plan=execution.content_plan,
    )
    assert validate_discourse_plan(
        forged,
        content_plan=execution.content_plan,
        obligation_ledger=execution.inventory_result.ledger,
    ) == ()
    assert surface_module._terminal_self_denial_plan_valid(
        forged,
        row_by_id,
    ) is False
    with pytest.raises(
        surface_module.Step11NaturalSurfaceError,
        match="STEP11_DISCOURSE_TERMINAL_BOUNDARY_INVALID",
    ):
        surface_module.build_step11_natural_surface_candidate(
            forged,
            inventory_result=execution.inventory_result,
            content_plan=execution.content_plan,
            current_input=execution.projected_current_input,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("reception_act", "unsupported_security_act"),
        ("reception_scope", "generic"),
        ("realization_status", "reported_completed"),
    ),
)
def test_reception_requires_exact_scope_status_and_target(
    selected_execution,
    field: str,
    replacement: str,
) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    forged_reception = replace(reception, **{field: replacement})
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_reception if atom is reception else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(selected_execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )
    assert "S11_MATCH_SURPLUS_SEMANTIC_ATOM" in binding.issue_codes


def test_completed_action_reception_rejects_status_substitution(
    completed_action_execution,
) -> None:
    selected = completed_action_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    reception = next(
        atom for atom in witness.atoms if atom.section_role == "reception"
    )
    assert reception.reception_scope == "action"
    canonical_status = reception.realization_status
    forged_reception = replace(
        reception,
        realization_status=(
            "intended"
            if canonical_status != "intended"
            else "reported_completed"
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_reception if atom is reception else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(completed_action_execution, forged_witness)

    assert binding.verified is False
    assert (
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH"
        in binding.issue_codes
    )


def test_action_observation_rejects_incompatible_status(
    completed_action_execution,
) -> None:
    selected = completed_action_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    action = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.predicate_role == "action"
    )
    forged_action = replace(
        action,
        realization_status=(
            "intended"
            if action.realization_status != "intended"
            else "reported_completed"
        ),
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_action if atom is action else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(completed_action_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_MODALITY_STATUS_MISMATCH" in binding.issue_codes


def test_state_cannot_be_relabelled_as_action(selected_execution) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    thought = next(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
        and atom.source_fragments
    )
    forged_thought = replace(
        thought,
        predicate_role="action",
        realization_status="undetermined",
    )
    forged_witness = replace(
        witness,
        atoms=tuple(
            forged_thought if atom is thought else atom
            for atom in witness.atoms
        ),
    )

    binding = _match_witness(selected_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_PREDICATE_ROLE_MISMATCH" in binding.issue_codes


def test_duplicate_semantic_atom_fails_closed(selected_execution) -> None:
    selected = selected_execution.selected_candidate
    assert selected is not None
    witness = parse_step11_natural_surface(
        selected.rendered_surface.utf8_bytes
    )
    source = next(
        atom for atom in witness.atoms if atom.section_role == "observation"
    )
    duplicate = replace(
        source,
        atom_id="nls3s11atom_duplicate_security",
        byte_start=source.byte_end,
        byte_end=source.byte_end,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, duplicate),
        observation_atom_count=witness.observation_atom_count + 1,
    )

    binding = _match_witness(selected_execution, forged_witness)

    assert binding.verified is False
    assert "S11_MATCH_DUPLICATE_SEMANTIC_ATOM" in binding.issue_codes


def test_step11_selector_rejects_non_owner_candidate_type() -> None:
    with pytest.raises(Step11InverseSurfaceError) as captured:
        select_step11_natural_surface_candidates(
            (SimpleNamespace(candidate_id="forged"),),
            inventory_result=None,
            content_plan={},
            current_input={},
        )

    assert captured.value.code == "S11_SELECTOR_CANDIDATE_TYPE_INVALID"


@pytest.mark.parametrize(
    "source",
    (
        "通常の断片",
        "内側に「引用」がある",
        "内側に『別の引用』がある",
        "『二種』と「逆側」と\\を同時に含む",
    ),
)
def test_step11_dynamic_quote_projection_is_canonical_and_injective(
    source: str,
) -> None:
    projected = _quote_projection(source)
    skeleton, fragments = _scan_quoted("前" + projected + "後")

    assert skeleton == "前\x00後"
    assert fragments == (source,)
    assert _quote_projection(fragments[0]) == projected


def test_step11_quote_parser_rejects_noncanonical_pair() -> None:
    with pytest.raises(Step11InverseSurfaceError) as captured:
        _scan_quoted("前『primary delimiterなし』後』")

    assert captured.value.code == "S11_PARSE_QUOTE_CLOSE_UNEXPECTED"


@pytest.mark.parametrize(
    ("key", "expected_dimension"),
    (
        ("future", "future"),
        ("referent_other", "other_person_awareness"),
    ),
)
def test_step11_unknown_anaphora_alias_has_specific_canonical_parse(
    key: str,
    expected_dimension: str,
) -> None:
    rule = STEP11_SURFACE_CATALOG["observation_forms"][
        "unknown_anaphora"
    ][key][0]
    assert set(rule) == {"stem"}
    line = rule["stem"].format(target_ref="1つ目の記述内容")
    row = _unknown_reference_clause(line)

    assert row is not None
    assert row[0].startswith(f"unknown_anaphora:{key}:")
    assert row[1] == expected_dimension
    assert row[2] == (
        matcher_module.Step11EndpointReference(1, "proposition"),
    )


def _known28_legacy_input() -> dict[str, object]:
    return {
        "memo": "  考えをそのまま残す。  ",
        "memo_action": "順番を変えずに書いた。",
        "emotions": ["不安", "平穏"],
        "category": ["生活", "価値観"],
    }


def test_known28_projection_is_generic_lossless_and_non_mutating() -> None:
    legacy = _known28_legacy_input()
    frozen = deepcopy(legacy)

    projected, issues = regression_module.project_known28_legacy_input(legacy)

    assert issues == ()
    assert projected == {
        "thought_text": "  考えをそのまま残す。  ",
        "action_text": "順番を変えずに書いた。",
        "emotions": [
            {"type": "不安", "strength": "medium"},
            {"type": "平穏", "strength": "medium"},
        ],
        "categories": ["生活", "価値観"],
    }
    assert legacy == frozen
    assert projected is not legacy
    assert projected["emotions"] is not legacy["emotions"]
    assert projected["categories"] is not legacy["category"]


@pytest.mark.parametrize(
    ("legacy", "expected_issue"),
    (
        (None, "legacy_input:mapping_required"),
        (
            {
                **_known28_legacy_input(),
                "unexpected": "must fail closed",
            },
            "legacy_input:keyset_mismatch",
        ),
        (
            {**_known28_legacy_input(), "memo": 1},
            "legacy_input.memo:string_required",
        ),
        (
            {**_known28_legacy_input(), "memo_action": 1},
            "legacy_input.memo_action:string_required",
        ),
        (
            {**_known28_legacy_input(), "emotions": "不安"},
            "legacy_input.emotions:array_required",
        ),
        (
            {**_known28_legacy_input(), "emotions": [1]},
            "legacy_input.emotions:string_items_required",
        ),
        (
            {**_known28_legacy_input(), "category": "生活"},
            "legacy_input.category:array_required",
        ),
        (
            {**_known28_legacy_input(), "category": [1]},
            "legacy_input.category:string_items_required",
        ),
    ),
)
def test_known28_projection_rejects_malformed_legacy_shape(
    legacy,
    expected_issue: str,
) -> None:
    projected, issues = regression_module.project_known28_legacy_input(legacy)

    assert projected is None
    assert issues == (expected_issue,)


@pytest.mark.parametrize(
    ("overrides", "expected_issues"),
    (
        (
            {"emotions": ["未登録感情"], "category": ["未登録区分"]},
            (
                "input.emotions[0].type:unknown_emotion_type",
                "input.categories[0]:unknown_category",
            ),
        ),
        (
            {"emotions": ["不安", "不安"]},
            ("input.emotions:duplicate_emotion_type",),
        ),
        (
            {"category": ["生活", "生活"]},
            ("input.categories:duplicate_category",),
        ),
        (
            {"emotions": ["自己理解", "不安"]},
            ("input.emotions:self_insight_must_be_exclusive",),
        ),
        (
            {"memo": "", "memo_action": ""},
            ("input:thought_action_both_empty_after_js_trim",),
        ),
        (
            {"memo": "\ud800"},
            ("input.thought_text:string_or_unicode_invalid",),
        ),
    ),
)
def test_known28_projection_preserves_invalid_values_and_fails_closed(
    overrides: dict[str, object],
    expected_issues: tuple[str, ...],
) -> None:
    legacy = {**_known28_legacy_input(), **overrides}
    frozen = deepcopy(legacy)

    projected, issues = regression_module.project_known28_legacy_input(legacy)

    assert projected is not None
    assert issues == expected_issues
    assert legacy == frozen
    assert projected["thought_text"] == legacy["memo"]
    assert projected["action_text"] == legacy["memo_action"]
    assert [row["type"] for row in projected["emotions"]] == legacy["emotions"]
    assert projected["categories"] == legacy["category"]


def test_known28_projection_never_replaces_unknowns_or_completes_text() -> None:
    unknown = {
        **_known28_legacy_input(),
        "emotions": ["置換禁止の感情"],
        "category": ["置換禁止の区分"],
    }
    empty = {**_known28_legacy_input(), "memo": "", "memo_action": ""}

    unknown_projected, unknown_issues = (
        regression_module.project_known28_legacy_input(unknown)
    )
    empty_projected, empty_issues = (
        regression_module.project_known28_legacy_input(empty)
    )

    assert unknown_projected is not None
    assert unknown_projected["emotions"][0]["type"] == "置換禁止の感情"
    assert unknown_projected["categories"] == ["置換禁止の区分"]
    assert unknown_issues == (
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    )
    assert empty_projected is not None
    assert empty_projected["thought_text"] == ""
    assert empty_projected["action_text"] == ""
    assert empty_issues == (
        "input:thought_action_both_empty_after_js_trim",
    )


def test_known28_input_commitments_are_domain_separated_and_bound() -> None:
    key = b"known28-security-key-material-32"
    legacy = _known28_legacy_input()
    projected, issues = regression_module.project_known28_legacy_input(legacy)
    assert projected is not None
    assert issues == ()

    commitments = regression_module._known28_input_commitments(
        commitment_key=key,
        case_ref="security-case",
        legacy_current_input=legacy,
        projected_current_input=projected,
        applicability_status="app_reachable",
        applicability_issue_codes=(),
    )
    issue_tampered = regression_module._known28_input_commitments(
        commitment_key=key,
        case_ref="security-case",
        legacy_current_input=legacy,
        projected_current_input=projected,
        applicability_status="app_reachable",
        applicability_issue_codes=("input:tampered",),
    )
    case_tampered = regression_module._known28_input_commitments(
        commitment_key=key,
        case_ref="security-case-other",
        legacy_current_input=legacy,
        projected_current_input=projected,
        applicability_status="app_reachable",
        applicability_issue_codes=(),
    )

    assert len(set(commitments)) == 3
    assert issue_tampered[:2] == commitments[:2]
    assert issue_tampered[2] != commitments[2]
    assert case_tampered[:2] == commitments[:2]
    assert case_tampered[2] != commitments[2]


@pytest.fixture()
def known28_private_contract_fixture(monkeypatch):
    key = b"known28-private-validator-key-32"
    v3_bytes = b"synthetic-v3-body"

    async def fake_v1(current_input, _case_ref):
        return "v1:" + regression_module.artifact_sha256(current_input)

    def fake_v3(_current_input, **_kwargs):
        return SimpleNamespace(status="selected", final_utf8_bytes=v3_bytes)

    monkeypatch.setattr(regression_module, "_v1_body", fake_v1)
    monkeypatch.setattr(
        regression_module,
        "execute_step11_offline_v3",
        fake_v3,
    )
    monkeypatch.setattr(
        regression_module,
        "validate_step11_runtime_execution",
        lambda _execution: (),
    )
    expected = regression_module._verify_known28_projection_contract()
    private_rows = []
    public_rows = []
    for case in regression_module.load_baseline_cases():
        legacy = regression_module._copy_legacy_current_input(
            dict(case.current_input)
        )
        projected_candidate, projection_issues = (
            regression_module.project_known28_legacy_input(legacy)
        )
        status = "app_reachable" if not projection_issues else (
            "expected_non_applicable"
        )
        assert status == expected[case.case_id]["applicability_status"]
        assert list(projection_issues) == expected[case.case_id][
            "expected_issue_codes"
        ]
        projected = projected_candidate if status == "app_reachable" else None
        legacy_commitment, projected_commitment, binding_commitment = (
            regression_module._known28_input_commitments(
                commitment_key=key,
                case_ref=case.case_id,
                legacy_current_input=legacy,
                projected_current_input=projected,
                applicability_status=status,
                applicability_issue_codes=projection_issues,
            )
        )
        v1_body = "v1:" + regression_module.artifact_sha256(legacy)
        v3_body = v3_bytes.decode("utf-8") if projected is not None else None
        private_rows.append(
            {
                "case_ref": case.case_id,
                "cohort": case.cohort,
                "family": case.family,
                "legacy_current_input": legacy,
                "projected_current_input": projected,
                "applicability_status": status,
                "applicability_issue_codes": list(projection_issues),
                "v1_body": v1_body,
                "v3_body": v3_body,
            }
        )
        public_rows.append(
            {
                "case_ref": case.case_id,
                "legacy_input_commitment": legacy_commitment,
                "projected_input_commitment": projected_commitment,
                "applicability_binding_commitment": binding_commitment,
                "applicability_status": status,
                "applicability_issue_codes": list(projection_issues),
                "v1_baseline_body_commitment": (
                    regression_module.hmac_commit_bytes(
                        key,
                        "v1_baseline_body",
                        v1_body.encode("utf-8"),
                    )
                ),
                "selected_candidate_body_commitment": (
                    regression_module.hmac_commit_bytes(
                        key,
                        "selected_candidate_body",
                        v3_bytes,
                    )
                    if v3_body is not None
                    else None
                ),
                "status": (
                    "selected"
                    if status == "app_reachable"
                    else "expected_non_applicable"
                ),
                "hard_gate_status": (
                    "passed" if status == "app_reachable" else "not_applicable"
                ),
                "failure_codes": [],
                "exception": False,
                "v1_fallback_used": False,
            }
        )
    private_packet = {
        "schema_version": regression_module.STEP11_KNOWN28_PRIVATE_SCHEMA,
        "storage_scope": "private_local_only_outside_repo",
        "body_full": True,
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": "known28-security-run",
        "commitment_key_id": regression_module.commitment_key_id(key),
        "projection_policy_sha256": (
            regression_module.KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        ),
        "cases": private_rows,
    }
    receipt = {
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": private_packet["run_id"],
        "commitment_key_id": regression_module.commitment_key_id(key),
        "generic_projection_policy_sha256": (
            regression_module.KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        ),
        "expected_applicability_inventory_sha256": (
            regression_module.FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
        ),
        "source_dependency_closure_sha256": "a" * 64,
        "rows": public_rows,
    }
    receipt["private_packet_commitment"] = regression_module._commit_json(
        key,
        "step11_known28_private_packet",
        private_packet,
    )
    assert regression_module.validate_known28_private_packet(
        private_packet,
        receipt,
        commitment_key=key,
    ) == ()
    return private_packet, receipt, key


def _recommit_known28_private_packet(packet, receipt, key) -> None:
    receipt["private_packet_commitment"] = regression_module._commit_json(
        key,
        "step11_known28_private_packet",
        packet,
    )


def test_known28_private_validator_rejects_raw_source_mutation(
    known28_private_contract_fixture,
) -> None:
    packet, receipt, key = deepcopy(known28_private_contract_fixture)
    packet["cases"][0]["legacy_current_input"]["memo"] += "改竄"
    _recommit_known28_private_packet(packet, receipt, key)

    issues = regression_module.validate_known28_private_packet(
        packet,
        receipt,
        commitment_key=key,
    )

    assert "STEP11_KNOWN28_PRIVATE_LEGACY_SOURCE_MISMATCH" in issues


def test_known28_private_validator_rejects_v1_projected_route(
    known28_private_contract_fixture,
) -> None:
    packet, receipt, key = deepcopy(known28_private_contract_fixture)
    private = next(
        row
        for row in packet["cases"]
        if row["applicability_status"] == "app_reachable"
    )
    public = next(
        row for row in receipt["rows"] if row["case_ref"] == private["case_ref"]
    )
    private["v1_body"] = "v1:" + regression_module.artifact_sha256(
        private["projected_current_input"]
    )
    public["v1_baseline_body_commitment"] = (
        regression_module.hmac_commit_bytes(
            key,
            "v1_baseline_body",
            private["v1_body"].encode("utf-8"),
        )
    )
    _recommit_known28_private_packet(packet, receipt, key)

    issues = regression_module.validate_known28_private_packet(
        packet,
        receipt,
        commitment_key=key,
    )

    assert "STEP11_KNOWN28_PRIVATE_V1_RECOMPUTATION_MISMATCH" in issues


def test_known28_private_validator_rejects_issue_code_tampering(
    known28_private_contract_fixture,
) -> None:
    packet, receipt, key = deepcopy(known28_private_contract_fixture)
    private = next(
        row
        for row in packet["cases"]
        if row["applicability_status"] == "expected_non_applicable"
    )
    public = next(
        row for row in receipt["rows"] if row["case_ref"] == private["case_ref"]
    )
    tampered_issues = ["input:tampered_issue"]
    private["applicability_issue_codes"] = tampered_issues
    public["applicability_issue_codes"] = tampered_issues
    commitments = regression_module._known28_input_commitments(
        commitment_key=key,
        case_ref=private["case_ref"],
        legacy_current_input=private["legacy_current_input"],
        projected_current_input=None,
        applicability_status="expected_non_applicable",
        applicability_issue_codes=tampered_issues,
    )
    public["applicability_binding_commitment"] = commitments[2]
    _recommit_known28_private_packet(packet, receipt, key)

    issues = regression_module.validate_known28_private_packet(
        packet,
        receipt,
        commitment_key=key,
    )

    assert "STEP11_KNOWN28_PRIVATE_APPLICABILITY_MISMATCH" in issues


def test_known28_private_validator_rejects_nonapplicable_v3_execution(
    known28_private_contract_fixture,
) -> None:
    packet, receipt, key = deepcopy(known28_private_contract_fixture)
    private = next(
        row
        for row in packet["cases"]
        if row["applicability_status"] == "expected_non_applicable"
    )
    private["v3_body"] = "v3-must-not-run"
    _recommit_known28_private_packet(packet, receipt, key)

    issues = regression_module.validate_known28_private_packet(
        packet,
        receipt,
        commitment_key=key,
    )

    assert "STEP11_KNOWN28_PRIVATE_V3_RECOMPUTATION_MISMATCH" in issues
