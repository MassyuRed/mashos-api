from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import emlis_ai_limited_composer_client as limited_composer_module

from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient, EmlisPhraseUnit
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from fixtures.emlis_ai_phase8_cases import PHASE8_CASES
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


_ALLOWED_GUARD_ONLY_CONSTANT_NAMES = {"_FORBIDDEN_SURFACES", "_MARKER_NAMES"}


def _limited_composer_module_source() -> str:
    return inspect.getsource(limited_composer_module)


def _is_guard_only_assignment(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        return bool(names.intersection(_ALLOWED_GUARD_ONLY_CONSTANT_NAMES))
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id in _ALLOWED_GUARD_ONLY_CONSTANT_NAMES
    return False


def _limited_composer_source_without_guard_only_constants() -> str:
    source = _limited_composer_module_source()
    tree = ast.parse(source)
    excluded_lines: set[int] = set()
    for node in tree.body:
        if _is_guard_only_assignment(node):
            start = int(getattr(node, "lineno", 0) or 0)
            end = int(getattr(node, "end_lineno", start) or start)
            excluded_lines.update(range(start, end + 1))
    return "\n".join(
        line
        for lineno, line in enumerate(source.splitlines(), start=1)
        if lineno not in excluded_lines
    )


def _limited_composer_runtime_string_literals() -> list[str]:
    source = _limited_composer_module_source()
    tree = ast.parse(source)
    literals: list[str] = []

    class RuntimeStringVisitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802 - ast visitor API
            if _is_guard_only_assignment(node):
                return
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802 - ast visitor API
            if _is_guard_only_assignment(node):
                return
            self.generic_visit(node)

        def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802 - ast visitor API
            if isinstance(node.value, str):
                literals.append(node.value)

    RuntimeStringVisitor().visit(tree)
    return literals


def _compact_source_text(value: str) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r『』「」（）()\[\]【】]", "", str(value or ""))


def _phase8_example_input_phrases() -> list[str]:
    phrases: set[str] = set()
    for case in PHASE8_CASES:
        memo = str(case.get("memo") or "")
        for phrase in re.split(r"[。！？!?\n]+", memo):
            cleaned = phrase.strip(" 　、,。.!！?？")
            if len(_compact_source_text(cleaned)) >= 8:
                phrases.add(cleaned)
    return sorted(phrases)


def _payload_for(memo: str = SAMPLE_MEMO):
    current_input = {
        "id": "limited-composer-test",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="limited-composer-test",
    )
    return payload, evidence, scope


def test_limited_composer_generates_from_scoped_payload_without_external_ai():
    payload, evidence, scope = _payload_for()
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["response_schema_version"] == "emlis.composer.response.v1"
    assert result["composer_source"] == "ai_generated"
    assert result["composer_model"] == "cocolon_limited_composer.v1"
    assert result["fixed_string_renderer_used"] is False
    assert result["coverage_scope"] in {"partial_observation", "current_input_core"}
    assert result["comment_text"]
    assert set(result["used_evidence_span_ids"]).issubset({span.span_id for span in evidence})
    assert set(result["used_claim_ids"]).issubset(set(scope.included_claim_ids))
    assert set(result["used_relation_ids"]).issubset(set(scope.included_relation_ids))

    for banned in ("そこには", "もありました", "も含まれていました", "と思います", "一緒に見ます", "今の私は", "あなたは"):
        assert banned not in result["comment_text"]


def test_limited_composer_candidate_passes_conversation_composer_contract():
    payload, evidence, scope = _payload_for()
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonLimitedComposerClient(),
        trace_id="limited-composer-contract",
    )

    assert candidate.composer_source == "ai_generated"
    assert candidate.status == "generated"
    assert candidate.ai_generated is True
    assert candidate.fixed_string_renderer_used is False
    assert candidate.composer_model == "cocolon_limited_composer.v1"
    assert candidate.generation_method == "scoped_graph_evidence_composer"
    assert candidate.coverage_scope in {"partial_observation", "current_input_core"}
    assert candidate.used_evidence_span_ids
    assert set(candidate.used_evidence_span_ids).issubset({span.span_id for span in evidence})
    assert set(candidate.used_claim_ids).issubset(set(scope.included_claim_ids))
    assert set(candidate.used_relation_ids).issubset(set(scope.included_relation_ids))


def test_limited_composer_returns_unavailable_for_non_scoped_or_unsafe_payload():
    payload, *_ = _payload_for()
    unsafe_payload = dict(payload)
    unsafe_graph = dict(payload["observation_graph"])
    unsafe_graph["safety_boundaries"] = ["safety_boundary"]
    unsafe_payload["observation_graph"] = unsafe_graph

    result = CocolonLimitedComposerClient().generate(unsafe_payload)

    assert result["composer_source"] == "unavailable"
    assert result["comment_text"] == ""
    assert "limited_composer_safety_boundary" in result["rejection_reasons"]


def test_limited_composer_source_has_no_runtime_fixed_observation_surfaces():
    source = _limited_composer_source_without_guard_only_constants()
    class_source = inspect.getsource(CocolonLimitedComposerClient)
    literals = _limited_composer_runtime_string_literals()
    literal_blob = "\n".join(literals).lower()

    assert "class CocolonLimitedComposerClient" in source
    assert "def _compress_text" in source
    assert "def _compress_text" not in class_source

    for banned in ("そこには", "もありました", "も含まれていました", "と思います", "として見ています", "一緒に見ます"):
        assert banned not in source, banned
        assert all(banned not in literal for literal in literals), banned
    assert "fallback" not in source.lower()
    assert "fallback" not in literal_blob


def test_limited_composer_module_does_not_embed_phase8_example_input_sentences():
    source = _limited_composer_source_without_guard_only_constants()
    compact_source = _compact_source_text(source)
    compact_literals = [_compact_source_text(value) for value in _limited_composer_runtime_string_literals()]

    for phrase in _phase8_example_input_phrases():
        compact_phrase = _compact_source_text(phrase)
        assert compact_phrase not in compact_source, phrase
        assert all(compact_phrase not in literal for literal in compact_literals), phrase


def test_limited_composer_module_has_no_example_phrase_replacement_table():
    source = _limited_composer_source_without_guard_only_constants()
    for marker in (
        "example_phrase_replacement",
        "example_replacement",
        "fixed_observation_template",
        "static_observation_text",
        "role_template",
        "replacement_map",
        "replacements =",
    ):
        assert marker not in source



def _step04_payload(evidence_spans):
    ids = [str(item.get("span_id") or "") for item in evidence_spans if str(item.get("span_id") or "")]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {"claim_id": "c1", "claim_type": "primary_state", "text": "source anchored", "evidence_span_ids": ids[:2]},
            "core_tensions": [],
            "pressure_sources": [],
            "limit_signals": [],
            "self_awareness": [],
            "value_or_strength_signals": [],
            "safety_boundaries": [],
            "forbidden_claims": [],
            "missing_information": [],
        },
        "evidence_spans": evidence_spans,
        "limited_observation_scope": {"scope_status": "eligible", "coverage_scope": "partial_observation"},
        "composition_contract": {"forbidden_output_surfaces": []},
    }


def _step04_profile_evidence():
    return [
        {"span_id": "s1", "raw_text": "友達と話せて楽しかった。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "s2", "raw_text": "夜になって急に不安になった。", "detected_type": "event", "source_field": "memo"},
    ]


def test_step04_limited_composer_diagnostic_marks_missing_phrase_units(monkeypatch):
    monkeypatch.setattr(limited_composer_module, "detect_phase8_profile", lambda _items: "mixed_positive_anxiety")
    monkeypatch.setattr(limited_composer_module, "_build_phrase_units", lambda _items: [])

    result = CocolonLimitedComposerClient().generate(_step04_payload(_step04_profile_evidence()))
    diagnostic = result["composer_meta"]["composer_diagnostic"]

    assert result["composer_source"] == "unavailable"
    assert "limited_composer_missing_phrase_units" in result["rejection_reasons"]
    assert diagnostic["version"] == "emlis.composer_diagnostic.v1"
    assert diagnostic["composer_status"] == "unavailable"
    assert diagnostic["missing_phrase_units"] is True
    assert diagnostic["reason_category"] == "missing_phrase_units"
    assert diagnostic["stop_reason"] == "missing_phrase_units"
    assert "missing_phrase_units" in diagnostic["coverage_matrix_hints"]


def test_step04_limited_composer_diagnostic_marks_required_role_missing(monkeypatch):
    monkeypatch.setattr(limited_composer_module, "detect_phase8_profile", lambda _items: "mixed_positive_anxiety")
    monkeypatch.setattr(
        limited_composer_module,
        "_build_phrase_units",
        lambda _items: [
            EmlisPhraseUnit(
                phrase_unit_id="pu1",
                evidence_span_id="s1",
                raw_text="友達と話せて楽しかった。",
                compressed_text="友達と話せた楽しさ",
                role="positive_state",
                polarity="positive",
                must_keep=True,
            )
        ],
    )

    result = CocolonLimitedComposerClient().generate(_step04_payload(_step04_profile_evidence()))
    diagnostic = result["composer_meta"]["composer_diagnostic"]

    assert result["composer_source"] == "unavailable"
    assert "limited_composer_required_role_missing" in result["rejection_reasons"]
    assert diagnostic["required_role_missing"] is True
    assert diagnostic["missing_roles"] == ["anxiety_return"]
    assert diagnostic["available_roles"] == ["positive_state"]
    assert diagnostic["reason_category"] == "required_role_missing"
    assert "required_role_missing" in diagnostic["coverage_matrix_hints"]


def test_step04_limited_composer_diagnostic_marks_sentence_plan_unavailable(monkeypatch):
    monkeypatch.setattr(limited_composer_module, "detect_phase8_profile", lambda _items: "mixed_positive_anxiety")
    monkeypatch.setattr(
        limited_composer_module,
        "_build_phrase_units",
        lambda _items: [
            EmlisPhraseUnit("pu1", "s1", "友達と話せて楽しかった。", "友達と話せた楽しさ", "positive_state", "positive", True),
            EmlisPhraseUnit("pu2", "s2", "夜になって急に不安になった。", "戻ってきた不安", "anxiety_return", "negative", True),
        ],
    )
    monkeypatch.setattr(limited_composer_module, "_sentence_plans_for_profile", lambda **_kwargs: [])

    result = CocolonLimitedComposerClient().generate(_step04_payload(_step04_profile_evidence()))
    diagnostic = result["composer_meta"]["composer_diagnostic"]

    assert result["composer_source"] == "unavailable"
    assert "limited_composer_sentence_plan_unavailable" in result["rejection_reasons"]
    assert diagnostic["sentence_plan_unavailable"] is True
    assert diagnostic["reason_category"] == "sentence_plan_unavailable"
    assert diagnostic["phrase_unit_count"] == 2
    assert diagnostic["sentence_plan_count"] == 0


def test_step04_limited_composer_diagnostic_marks_shallow_profile_unmatched():
    evidence = [
        {"span_id": "a", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "b", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_step04_payload(evidence))
    diagnostic = result["composer_meta"]["composer_diagnostic"]

    assert result["composer_source"] == "ai_generated"
    assert diagnostic["composer_status"] == "generated"
    assert diagnostic["profile_key"] == "current_input_core"
    assert diagnostic["source_profile_key"] == "unknown"
    assert diagnostic["profile_unmatched"] is True
    assert diagnostic["shallow_observation_path"] is True
    assert diagnostic["phrase_unit_count"] >= 2
    assert "profile_unmatched" in diagnostic["reason_codes"]
    assert "profile_unmatched" in diagnostic["coverage_matrix_hints"]


def test_step04_limited_composer_diagnostic_marks_shallow_insufficient_evidence():
    evidence = [
        {"span_id": "a", "raw_text": "今日は疲れた。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_step04_payload(evidence))
    diagnostic = result["composer_meta"]["composer_diagnostic"]

    assert result["composer_source"] == "unavailable"
    assert "limited_composer_shallow_insufficient_evidence" in result["rejection_reasons"]
    assert diagnostic["shallow_insufficient_evidence"] is True
    assert diagnostic["reason_category"] == "shallow_insufficient_evidence"
    assert diagnostic["stop_reason"] == "shallow_insufficient_evidence"
    assert "shallow_insufficient_evidence" in diagnostic["coverage_matrix_hints"]


def test_step11_phrase_unit_role_expansion_handles_fatigue_value_and_repair_material():
    evidence = [
        {"span_id": "s1", "raw_text": "今日は疲れが溜まっていて、休みたい気持ちが強い。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "s2", "raw_text": "それでも大事にしたい作業を少し選びたい。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "s3", "raw_text": "机を少し整えたら少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]

    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["s1", "s2", "s3"]
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert result["coverage_scope"] in {"current_input_core", "partial_observation"}
    compact = _compact_source_text(result["comment_text"])
    assert "それこと" not in compact
    assert "疲れが溜まっている" in compact
    assert "大事にしたい気持ち" in compact
    assert "机を整えた" in compact

    role_expansion = result["composer_meta"]["step11_role_expansion"]
    assert role_expansion["completion_sentence_templates_added"] is False
    assert role_expansion["role_is_material_only"] is True
    assert set(role_expansion["expanded_roles"]) >= {"fatigue_accumulation", "small_repair", "value_wish"}
    assert {"energy_fatigue", "positive_recovery", "value_wish"}.issubset(set(role_expansion["coverage_groups"]))
    assert {"fatigue_accumulation", "small_repair", "value_wish"}.issubset(
        set(result["composer_meta"]["composer_diagnostic"]["expanded_roles"])
    )


def test_step11_phrase_units_filter_orphan_particles_and_label_only_fragments():
    evidence = [
        {"span_id": "x1", "raw_text": "不安", "detected_type": "event", "source_field": "memo"},
        {"span_id": "x2", "raw_text": "普通に", "detected_type": "event", "source_field": "memo"},
        {"span_id": "x3", "raw_text": "資料が多すぎて頭が回らず、追いつかない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "x4", "raw_text": "少しだけ机を整えた。", "detected_type": "event", "source_field": "memo"},
    ]

    units = limited_composer_module._build_current_input_core_phrase_units(evidence)

    compact_units = {_compact_source_text(unit.compressed_text) for unit in units}
    assert "不安" not in compact_units
    assert "普通にこと" not in compact_units
    assert all("orphan_particle" not in unit.quality_flags for unit in units)
    assert all("unfinished_phrase" not in unit.quality_flags for unit in units)
    assert {"loss_of_control", "small_repair"}.issubset({unit.role for unit in units})

def test_step12_profile_sentence_plan_expansion_handles_energy_fatigue_profile():
    evidence = [
        {"span_id": "ef1", "raw_text": "朝から疲れが溜まっていて体力が残っていない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "ef2", "raw_text": "資料を直そうとしても頭が回らず、集中が切れている。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "ef3", "raw_text": "途中でお茶を飲んだら少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["ef1", "ef2", "ef3"]
    result = CocolonLimitedComposerClient().generate(payload)
    assert result["composer_source"] == "ai_generated"
    assert result["composer_meta"]["profile_key"] == "energy_fatigue"
    compact = _compact_source_text(result["comment_text"])
    assert "疲れが溜まっている" in compact or "疲労が残っている" in compact
    assert "頭が回" in compact or "集中が切れている" in compact
    step12 = result["composer_meta"]["step12_profile_sentence_plan"]
    diagnostic = result["composer_meta"]["composer_diagnostic"]
    assert step12["profile_key"] == "energy_fatigue"
    assert step12["profile_expanded"] is True
    assert step12["completion_sentence_templates_added"] is False
    assert step12["profile_sentence_plan_is_material_only"] is True
    assert {"fatigue_accumulation", "loss_of_control"}.issubset(set(step12["planned_roles"]))
    assert diagnostic["expanded_profile"] is True
    assert "energy_fatigue" in diagnostic["expanded_profiles"]


def test_step12_profile_sentence_plan_expansion_handles_value_wish_profile():
    evidence = [
        {"span_id": "vw1", "raw_text": "大切にしたい作業を今日は選びたい。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "vw2", "raw_text": "でも資料が多すぎて頭が回らず、休みたい気持ちもある。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "vw3", "raw_text": "少しだけ机を整えたら落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["vw1", "vw2", "vw3"]
    result = CocolonLimitedComposerClient().generate(payload)
    assert result["composer_source"] == "ai_generated"
    assert result["composer_meta"]["profile_key"] == "value_wish"
    compact = _compact_source_text(result["comment_text"])
    assert "大切にしたい" in compact or "選びたい" in compact
    assert "頭が回" in compact or "休みたい" in compact
    step12 = result["composer_meta"]["step12_profile_sentence_plan"]
    assert step12["profile_key"] == "value_wish"
    assert step12["expanded_profiles"] == ["value_wish"]
    assert step12["role_combination_based"] is True
    assert step12["completion_sentence_templates_added"] is False
    assert {"value", "pressure"}.issubset(set(step12["sentence_plan_roles"].keys()))
    assert "value_wish" in result["composer_meta"]["available_roles"]


def test_step12_detects_long_meaning_arc_as_structural_profile():
    evidence = [
        {"span_id": "la1", "raw_text": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "la2", "raw_text": "本当は大事にしたい作業を選びたいけれど、休みたい気持ちも強い。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "la3", "raw_text": "少しだけ机を整えてお茶を飲んだら、少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "la4", "raw_text": "このまま一人で抱えるのは限界に近い。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["la1", "la2", "la3", "la4"]
    result = CocolonLimitedComposerClient().generate(payload)
    assert result["composer_source"] == "ai_generated"
    assert result["composer_meta"]["profile_key"] == "long_meaning_arc"
    assert result["coverage_scope"] == "partial_observation"
    assert result["coverage_scope"] != "current_input_core"
    compact = _compact_source_text(result["comment_text"])
    assert "疲れが溜まっている" in compact or "頭が回" in compact
    assert "大事にしたい" in compact or "選びたい" in compact or "休みたい" in compact
    assert "机を整え" in compact or "お茶" in compact or "落ち着いた" in compact
    step12 = result["composer_meta"]["step12_profile_sentence_plan"]
    diagnostic = result["composer_meta"]["composer_diagnostic"]
    assert step12["profile_expanded"] is True
    assert step12["sentence_plan_count"] >= 3
    assert {"state", "tension"}.issubset(set(step12["sentence_plan_roles"].keys()))
    assert diagnostic["expanded_profile"] is True
    assert "long_meaning_arc" in diagnostic["expanded_profiles"]



def test_step13_surface_realizer_uses_grammar_parts_without_completion_templates():
    evidence = [
        {"span_id": "sr1", "raw_text": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr2", "raw_text": "本当は大事にしたい作業を選びたいけれど、休みたい気持ちも強い。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr3", "raw_text": "少しだけ机を整えてお茶を飲んだら、少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr4", "raw_text": "このまま一人で抱えるのは限界に近い。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = [item["span_id"] for item in evidence]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert "中心として書かれています" not in result["comment_text"]
    assert "ことが書かれています" not in result["comment_text"]
    surface = result["composer_meta"]["step13_surface_realizer"]
    diagnostic_surface = result["composer_meta"]["composer_diagnostic"]["step13_surface_realizer"]
    assert surface["version"] == "emlis.surface_realizer.v1"
    assert surface["phase"] == "B-C1"
    assert surface["grammar_parts_only"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert surface["fixed_closing_sentence_added"] is False
    assert surface["generic_closing_added"] is False
    assert surface["claim_relation_derived_tail_only"] is True
    assert surface["raw_evidence_sentence_copy_guarded"] is True
    assert surface["generic_closing_guarded"] is True
    assert surface["length_mode"] in {"short", "medium", "long"}
    assert surface["tail_variation_enabled"] is True
    assert {"connector", "particle", "predicate_tail", "tail_variation"}.issubset(set(surface["surface_unit_types"]))
    assert surface["unique_tail_key_count"] >= 3
    assert diagnostic_surface["predicate_keys"] == surface["predicate_keys"]
    assert result["composer_meta"]["composer_diagnostic"]["surface_realizer_grammar_parts_only"] is True
    assert result["composer_meta"]["composer_diagnostic"]["completion_sentence_templates_added"] is False


def test_step13_surface_realizer_naturalizes_shallow_current_input_core_line():
    evidence = [
        {"span_id": "sh1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sh2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["sh1", "sh2"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert "中心として書かれています" not in result["comment_text"]
    assert "中心にあります" not in result["comment_text"]
    assert "その中でも" not in result["comment_text"]
    assert "仕事で疲れたことが先に出ています" in result["comment_text"]
    surface = result["composer_meta"]["step13_surface_realizer"]
    shallow_v2 = result["composer_meta"]["step5_shallow_surface_realizer_v2"]
    assert surface["shallow_observation_path"] is True
    assert surface["grammar_parts_only"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert "receive_first" in surface["used_tail_keys"]
    assert "center" not in surface["used_tail_keys"]
    assert shallow_v2["realizer_version"] == "shallow_surface_realizer.v2"
    assert shallow_v2["generic_center_phrase_count"] == 0
    assert result["composer_meta"]["composer_diagnostic"]["surface_variation_enabled"] is True



def test_step13_surface_realizer_naturalizes_value_tail_without_completion_templates():
    evidence = [
        {"span_id": "sr1", "raw_text": "大切にしたい作業を今日は選びたい。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr2", "raw_text": "でも資料が多すぎて頭が回らず、休みたい気持ちもある。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr3", "raw_text": "少しだけ机を整えたら落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["sr1", "sr2", "sr3"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    text = result["comment_text"]
    compact = _compact_source_text(text)
    assert "大切にしたい気持ちが書かれています" not in compact
    assert "大切にしたい気持ちが言葉になっています" in compact or "大切にしたい気持ちが前面にあります" in compact

    surface = result["composer_meta"]["step13_surface_realizer"]
    diagnostic = result["composer_meta"]["composer_diagnostic"]
    assert surface["target_step"] == "Step13_surface_realizer"
    assert surface["grammar_parts_only"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert surface["fixed_observation_sentence_added"] is False
    assert surface["role_sentence_templates_added"] is False
    assert surface["example_sentence_match_used"] is False
    assert "worded" in surface["predicate_keys"]
    assert diagnostic["surface_realizer_enabled"] is True
    assert diagnostic["surface_realizer_grammar_parts_only"] is True
    assert diagnostic["completion_sentence_templates_added"] is False
    assert "worded" in diagnostic["surface_tail_keys"]


def test_step13_surface_realizer_uses_relation_aware_tail_variation_for_energy_pressure():
    evidence = [
        {"span_id": "se1", "raw_text": "朝から疲れが溜まっていて体力が残っていない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "se2", "raw_text": "資料を直そうとしても頭が回らず、集中が切れている。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "se3", "raw_text": "途中でお茶を飲んだら少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["se1", "se2", "se3"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    compact = _compact_source_text(result["comment_text"])
    assert "疲れが溜まっていることが書かれています" not in compact
    assert "頭が回りにくいことが混ざっています" not in compact
    assert "疲れが溜まっていることが強く残っています" in compact or "疲れが溜まっていることが続いています" in compact
    assert "頭が回りにくいことも残っています" in compact or "集中が切れていることも残っています" in compact or "頭が回りにくいことも見えています" in compact
    surface = result["composer_meta"]["step13_surface_realizer"]
    assert surface["tail_variation_enabled"] is True
    assert surface["repeated_tail_avoidance"] is True
    assert surface["unique_tail_key_count"] >= 2
    assert {"strong_remain", "continue"}.intersection(set(surface["predicate_keys"]))


def test_step13_surface_realizer_records_shallow_current_input_core_surface_keys():
    evidence = [
        {"span_id": "ss1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "ss2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["ss1", "ss2"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    compact = _compact_source_text(result["comment_text"])
    assert "中心として書かれています" not in compact
    assert "中心にあります" not in compact
    assert "その中でも" not in compact
    assert "先に出ています" in compact
    surface = result["composer_meta"]["step13_surface_realizer"]
    shallow_v2 = result["composer_meta"]["step5_shallow_surface_realizer_v2"]
    assert surface["shallow_observation_path"] is True
    assert "receive_first" in surface["predicate_keys"]
    assert "center" not in surface["predicate_keys"]
    assert surface["completion_sentence_templates_added"] is False
    assert shallow_v2["old_current_input_core_skeleton_disabled"] is True


def test_step5_shallow_surface_realizer_compresses_obligation_and_prediction_relation_line():
    evidence = [
        {"span_id": "sk1", "raw_text": "イベントに出なければいけない予定がある。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sk2", "raw_text": "キャパオーバーしそうな予感がある。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["sk1", "sk2"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    text = result["comment_text"]
    compact = _compact_source_text(text)
    assert "イベント予定の近さ" in text
    assert "キャパオーバーしそうな予感" in text
    assert "なければこと" not in compact
    assert "予感こと" not in compact
    assert "ことも加わっていて" not in compact
    assert "状態が一色" not in compact
    assert "一つの要素" not in compact
    assert "同じ流れ" in text or "同じ場所" in text

    shallow_v2 = result["composer_meta"]["step5_shallow_surface_realizer_v2"]
    assert shallow_v2["phrase_surface_shape_version"] == "emlis.phrase_surface_shape.v1.20260524"
    assert shallow_v2["obligation_or_schedule_count"] == 1
    assert shallow_v2["prediction_or_capacity_count"] == 1
    assert shallow_v2["direct_koto_attachment_disabled"] is True
    assert shallow_v2["unsafe_koto_splice_reaches_relation_line"] is False
    assert shallow_v2["long_raw_clause_relation_line_passthrough"] is False
    assert shallow_v2["mechanical_relation_stack_disabled"] is True
    assert all(row["raw_text_included"] is False for row in shallow_v2["phrase_surface_shape_rows"])
    assert all(row["comment_text_body_included"] is False for row in shallow_v2["phrase_surface_shape_rows"])


def test_step5_shallow_surface_realizer_compresses_relationship_obligation_without_koto_attachment():
    evidence = [
        {"span_id": "srk1", "raw_text": "人とのコミュニケーションも取らなければいけない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "srk2", "raw_text": "キャパオーバーしそうな予感がある。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["srk1", "srk2"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    compact = _compact_source_text(result["comment_text"])
    assert "人との関わりの負荷" in result["comment_text"]
    assert "取らなければこと" not in compact
    assert "予感こと" not in compact
    assert "ことも加わっていて" not in compact
    assert "状態が一色" not in compact
    assert "今見えている範囲" not in compact
    assert "一つの要素" not in compact


def test_step13_surface_realizer_records_componentized_tail_policy():
    evidence = [
        {"span_id": "sr1", "raw_text": "朝から仕事で疲れが溜まっていて、頭が回らない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr2", "raw_text": "途中でお茶を飲んだら少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["sr1", "sr2"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    surface = result["composer_meta"]["step13_surface_realizer"]
    diagnostic = result["composer_meta"]["composer_diagnostic"]
    assert surface["version"] == "emlis.surface_realizer.v1"
    assert surface["target_step"] == "Step13_surface_realizer"
    assert surface["grammar_parts_only"] is True
    assert surface["surface_realizer_is_componentized"] is True
    assert surface["connector_particle_tail_components_only"] is True
    assert surface["relation_aware"] is True
    assert surface["role_aware"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert surface["fixed_closing_sentence_added"] is False
    assert surface["generic_closing_added"] is False
    assert surface["example_sentence_match_used"] is False
    assert surface["naturalized_surface_count"] >= 2
    assert surface["repeated_predicate_keys"] == []
    assert len(surface["predicate_keys"]) == surface["unique_tail_key_count"]
    assert diagnostic["step13_surface_realizer"]["version"] == surface["version"]
    assert diagnostic["surface_realizer_componentized"] is True


def test_step13_surface_realizer_naturalizes_value_profile_without_generic_written_tail():
    evidence = [
        {"span_id": "sv1", "raw_text": "大切にしたい作業を今日は選びたい。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sv2", "raw_text": "でも資料が多すぎて頭が回らず、休みたい気持ちもある。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sv3", "raw_text": "少しだけ机を整えたら落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = ["sv1", "sv2", "sv3"]

    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert result["composer_meta"]["profile_key"] == "value_wish"
    assert "書かれています" not in result["comment_text"]
    surface = result["composer_meta"]["step13_surface_realizer"]
    assert surface["generic_tail_key_count"] == 0
    assert "worded" in surface["predicate_keys"]
    assert {"value", "coexistence", "sequence"}.issubset(set(surface["relation_types"]))
    assert "value_wish" in surface["used_roles"]

