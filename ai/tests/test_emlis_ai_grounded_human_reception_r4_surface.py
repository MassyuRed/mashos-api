# -*- coding: utf-8 -*-
from __future__ import annotations

"""R4 functional Human Reception Surface Realizer contract tests."""

import ast
from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception import (
    realize_grounded_human_reception,
    reception_terminal_predicate_kind,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import (
    build_grounded_observation_plan,
    validate_grounded_human_reception_plan,
)
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    build_grounded_sentence_plan,
    build_plan_preserving_recovery_sequence,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_TEST_ROOT = Path(__file__).resolve().parent
_FIXTURE = _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
_HASH_MANIFEST = _TEST_ROOT / "fixtures" / "grounded_human_reception_section_hashes_20260712.json"
_REALIZER_SOURCE = (
    _TEST_ROOT.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_human_reception.py"
)
_QUOTE_RE = re.compile(r"「([^」]+)」")
_SENTENCE_END_RE = re.compile(r"[。！？!?]+")
_POLICY_RE = re.compile(
    r"(?:理由|原因).{0,20}(?:決めつけ|断定)|"
    r"入力から言える範囲|診断はしません|ここでは事実として扱いません|"
    r"原因は分かりません"
)
_ADVICE_RE = re.compile(
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"相談して|連絡して|受診して)"
)
_UNSUPPORTED_RE = re.compile(
    r"(?:必ず|確実に|成功|解決|安全です|危険度|診断|"
    r"あなたは(?:強い|優しい|立派|素晴らしい))"
)
_ACT_SURFACE_RESPONSIBILITY = {
    "stay_with_current_burden": re.compile(r"(?:軽く扱|小さくせず)"),
    "honor_concrete_effort": re.compile(r"(?:行動|動いたこと|働きかけ).*(?:大切|受け止)"),
    "protect_retained_intention": re.compile(r"(?:願い|大切にしたい).*(?:大切|なかったこと|埋もれ)"),
    "recognize_lived_change": re.compile(r"変化.*(?:感じ|受け止)"),
    "hold_help_seeking": re.compile(r"(?:助け|踏みとどまり).*(?:大切|受け止)"),
    "bounded_counter_self_denial": re.compile(r"苦しさ.*否定せず.*Emlis"),
    "respect_words_placed": re.compile(r"言葉.*(?:大切|受け止)"),
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return plan, sentence_plan, surface, observation, reception, report, resolver


def _sentence_count(text):
    return len(
        tuple(
            part.strip()
            for part in _SENTENCE_END_RE.split(text)
            if part.strip()
        )
    )


def _human_line(sentence_plan):
    return next(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )


def test_r4_exact8_keeps_observation_hash_and_realizes_distinct_human_acts() -> None:
    fixture = _load(_FIXTURE)
    manifest = _load(_HASH_MANIFEST)
    expected_by_id = {case["case_id"]: case for case in manifest["cases"]}
    visible_receptions = []

    for case in fixture["cases"]:
        plan, sentence_plan, _surface, observation, reception, report, resolver = (
            _artifacts(case["exact_current_input"])
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        expected = expected_by_id[case["case_id"]]
        human_line = _human_line(sentence_plan)

        assert hashlib.sha256(observation.encode("utf-8")).hexdigest() == (
            expected["observation_section_sha256"]
        )
        assert report.public_observation_status == "passed"
        assert report.semantic_quality_gate == "passed"
        assert report.two_stage_contract_gate == "passed"
        assert report.mechanical_restatement_gate == "passed"
        assert reception.strip()
        assert reception == reception.strip()
        assert (
            reception_plan.sentence_policy.min_sentences
            <= _sentence_count(reception)
            <= reception_plan.sentence_policy.max_sentences
        )

        quote_values = tuple(_QUOTE_RE.findall(reception))
        assert len(quote_values) <= reception_plan.quote_policy.max_anchor_count
        assert all(
            len(value) <= reception_plan.quote_policy.max_anchor_visible_chars
            for value in quote_values
        )
        bound_sources = tuple(
            resolver.resolve(span_id).raw_text
            for span_id in human_line.binding.evidence_span_ids
            if not resolver.unresolved_ids((span_id,))
        )
        assert all(
            any(anchor.rstrip("…") in source for source in bound_sources)
            for anchor in quote_values
        )
        observation_quotes = set(_QUOTE_RE.findall(observation))
        assert not any(
            len(anchor) > 16 and anchor in quote_values
            for anchor in observation_quotes
        )
        assert _POLICY_RE.search(reception) is None
        assert _ADVICE_RE.search(reception) is None
        assert _UNSUPPORTED_RE.search(reception) is None
        assert "?" not in reception and "？" not in reception

        primary_act = reception_plan.primary_reception_act
        assert primary_act is not None
        assert _ACT_SURFACE_RESPONSIBILITY[primary_act].search(reception)
        expected_terminal_kinds = tuple(
            reception_terminal_predicate_kind(act)
            for act in (
                reception_plan.primary_reception_act,
                reception_plan.secondary_reception_act,
            )
            if act is not None
        )
        assert tuple(
            atom.split(":", 1)[1]
            for atom in human_line.binding.functional_atom_ids
            if atom.startswith("reception_terminal_predicate:")
        ) == expected_terminal_kinds
        assert human_line.binding.evidence_span_ids == (
            reception_plan.source_evidence_span_ids
        )
        assert not resolver.unresolved_ids(human_line.binding.evidence_span_ids)
        visible_receptions.append(reception)

    assert len(set(visible_receptions)) == len(visible_receptions) == 8


def test_r4_short_state_and_self_denial_keep_their_visible_boundaries() -> None:
    by_id = {case["case_id"]: case for case in _load(_FIXTURE)["cases"]}
    for case_id in ("A", "I6-S03"):
        plan, _sentence_plan, _surface, _observation, reception, _report, _resolver = (
            _artifacts(by_id[case_id]["exact_current_input"])
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert reception_plan.primary_reception_act == "stay_with_current_burden"
        assert _sentence_count(reception) == 1
        assert _POLICY_RE.search(reception) is None
        assert not re.search(r"(?:気持ち|行動).*(?:両方|及ん|重な)", reception)

    for case_id in ("D", "I6-D02"):
        plan, sentence_plan, _surface, _observation, reception, _report, resolver = (
            _artifacts(by_id[case_id]["exact_current_input"])
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert reception_plan.support_nucleus_ids
        assert "Emlis" in reception
        assert "否定せず" in reception
        assert re.search(r"言葉だけで.*自身.*決まる.*思えません", reception)
        human_line = _human_line(sentence_plan)
        support_evidence = {
            span_id
            for nucleus in plan.nuclei
            if nucleus.nucleus_id in reception_plan.support_nucleus_ids
            for span_id in nucleus.source_span_ids
        }
        assert support_evidence <= set(human_line.binding.evidence_span_ids)
        assert not resolver.unresolved_ids(tuple(support_evidence))


def test_r4_labels_only_uses_quiet_words_placed_reception() -> None:
    current_input = {
        "memo": "",
        "memo_action": "",
        "emotions": ["不安"],
        "category": ["生活"],
    }
    plan, _sentence_plan, _surface, _observation, reception, report, _resolver = (
        _artifacts(current_input)
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    assert plan.input_profile.material_quality == "labels_only_limited"
    assert reception_plan.primary_reception_act == "respect_words_placed"
    assert _ACT_SURFACE_RESPONSIBILITY["respect_words_placed"].search(reception)
    assert "大切にそっと" not in reception
    assert "静かにそっと" not in reception
    assert _POLICY_RE.search(reception) is None
    assert report.public_observation_status == "passed"


def test_r4_reception_recovery_is_act_specific_deterministic_and_stays_separate() -> None:
    for case in _load(_FIXTURE)["cases"]:
        plan, _sentence_plan, _surface, _observation, _reception, _report, resolver = (
            _artifacts(case["exact_current_input"])
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        nucleus_index = {nucleus.nucleus_id: nucleus for nucleus in plan.nuclei}
        primary_act = reception_plan.primary_reception_act
        assert primary_act is not None

        for stage in GROUND_RECOVERY_STAGES:
            first = realize_grounded_human_reception(
                reception_plan,
                nucleus_index,
                resolver,
                recovery_stage=stage,
            )
            second = realize_grounded_human_reception(
                reception_plan,
                nucleus_index,
                resolver,
                recovery_stage=stage,
            )
            assert first == second
            assert first.text
            assert first.recovery_stage == stage
            assert first.terminal_predicate_kinds[0] == (
                reception_terminal_predicate_kind(primary_act)
            )
            expected_acts = (
                primary_act,
                *(
                    (reception_plan.secondary_reception_act,)
                    if stage == "full"
                    and reception_plan.secondary_reception_act is not None
                    else ()
                ),
            )
            assert first.realized_reception_acts == expected_acts
            assert (
                reception_plan.sentence_policy.min_sentences
                <= first.sentence_count
                <= reception_plan.sentence_policy.max_sentences
            )
            assert first.source_anchor_count <= (
                reception_plan.quote_policy.max_anchor_count
            )
            if stage in {"integrated", "hedged", "minimal_grounded"}:
                assert first.source_anchor_count == 0
            if stage == "minimal_grounded":
                assert len(first.realized_reception_acts) == 1
                assert len(first.grounded_nucleus_ids) == 1
                assert len(first.grounded_evidence_span_ids) == 1
            assert validate_grounded_human_reception_surface(
                first,
                reception_plan,
                resolver,
            ) == ()


def test_r4_recovery_sequence_preserves_observation_and_changes_only_reception() -> None:
    case = next(case for case in _load(_FIXTURE)["cases"] if case["case_id"] == "B")
    plan, _sp, _sf, observation, _reception, _report, resolver = _artifacts(
        case["exact_current_input"]
    )
    sequence = build_plan_preserving_recovery_sequence(plan, resolver)
    sections = tuple(split_two_stage_surface(item.text) for item in sequence)
    assert all(issues == () for _observation, _reception, issues in sections)
    assert {stage_observation for stage_observation, _reception, _issues in sections} == {
        observation
    }
    assert len({stage_reception for _observation, stage_reception, _issues in sections}) >= 3
    assert tuple(item.recovery_stage for item in sequence) == GROUND_RECOVERY_STAGES


def test_r4_surface_validator_rejects_policy_quote_question_and_role_mutations() -> None:
    by_id = {case["case_id"]: case for case in _load(_FIXTURE)["cases"]}
    plan, _sentence_plan, _surface, _observation, _reception, _report, resolver = (
        _artifacts(by_id["I6-S03"]["exact_current_input"])
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    nucleus_index = {nucleus.nucleus_id: nucleus for nucleus in plan.nuclei}
    valid = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    )
    mutations = (
        (
            replace(valid, text=f"{valid.text} 理由をこちらで決めつけません。"),
            "human_reception_policy_explanation_forbidden",
        ),
        (
            replace(valid, text=f"{valid.text} どうでしょう？"),
            "human_reception_question_forbidden",
        ),
        (
            replace(
                valid,
                text=f"「長い引用を置くことはしません」{valid.text}",
                source_anchor_count=1,
                source_anchor_max_visible_chars=14,
            ),
            "human_reception_quote_anchor_count_exceeded",
        ),
        (
            replace(
                valid,
                terminal_predicate_kinds=("observation_relation_summary",),
            ),
            "human_reception_terminal_predicate_mismatch",
        ),
        (
            replace(
                valid,
                text=f"{valid.text}大切に受け止めます。",
                sentence_count=reception_plan.sentence_policy.max_sentences + 1,
            ),
            "human_reception_sentence_budget_exceeded",
        ),
        (
            replace(
                valid,
                text="大切に受け止めます。",
                sentence_count=1,
                source_anchor_count=0,
                source_anchor_max_visible_chars=0,
            ),
            "human_reception_generic_suffix_forbidden",
        ),
    )
    for mutated, expected_issue in mutations:
        assert expected_issue in validate_grounded_human_reception_surface(
            mutated,
            reception_plan,
            resolver,
        )

    denial_plan, _sp, _sf, _o, _r, _report, denial_resolver = _artifacts(
        by_id["D"]["exact_current_input"]
    )
    denial_reception_plan = denial_plan.response_plan.human_reception_plan
    assert denial_reception_plan is not None
    denial_surface = realize_grounded_human_reception(
        denial_reception_plan,
        {nucleus.nucleus_id: nucleus for nucleus in denial_plan.nuclei},
        denial_resolver,
    )
    without_speaker = replace(
        denial_surface,
        text=denial_surface.text.replace("Emlis", "こちら"),
    )
    assert "self_denial_explicit_stance_missing" in (
        validate_grounded_human_reception_surface(
            without_speaker,
            denial_reception_plan,
            denial_resolver,
        )
    )


def test_r4_general_secondary_act_is_realized_when_the_r2_contract_allows_it() -> None:
    case = next(case for case in _load(_FIXTURE)["cases"] if case["case_id"] == "B")
    plan, _sentence_plan, _surface, _observation, _reception, _report, resolver = (
        _artifacts(case["exact_current_input"])
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    reception_plan = replace(
        reception_plan,
        secondary_reception_act="protect_retained_intention",
    )
    nucleus_index = {nucleus.nucleus_id: nucleus for nucleus in plan.nuclei}
    assert validate_grounded_human_reception_plan(
        reception_plan,
        expected_target_ids=plan.response_plan.human_follow_target_ids,
        nucleus_index=nucleus_index,
        resolver=resolver,
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
    ) == ()
    realized = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    )
    assert realized.realized_reception_acts == (
        "recognize_lived_change",
        "protect_retained_intention",
    )
    assert realized.terminal_predicate_kinds == (
        "human_response_recognize_change",
        "human_response_protect_intention",
    )
    assert realized.sentence_count == 2
    assert validate_grounded_human_reception_surface(
        realized,
        reception_plan,
        resolver,
    ) == ()


def test_r4_same16_and_unseen_inputs_do_not_fall_back_to_one_generic_suffix() -> None:
    unseen_inputs = (
        {
            "memo": "喉の奥が詰まる感じがする。",
            "memo_action": "",
            "emotions": ["不安"],
            "category": ["健康"],
        },
        {
            "memo": (
                "発表資料を作り直した。最初の案には迷いが残る。"
                "ただ残したい図は一つあり、次はそこから組み直したい。"
            ),
            "memo_action": "修正した箇所を一覧に残した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
        {
            "memo": "自分には何もできない。それでも、明日の予約は取り消していない。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        },
        {
            "memo": "前回より手順を一つ減らせそうだ。まだ速くなったとは言えない。",
            "memo_action": "作業時間を表に記録した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
    )
    cases = (
        *(
            case.as_current_input()
            for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES
        ),
        *(case.as_current_input() for case in GROUND_OBSERVATION_I6_BLIND_CASES),
        *unseen_inputs,
    )
    terminal_families: Counter[str] = Counter()
    reception_texts = []
    for current_input in cases:
        plan, sentence_plan, _surface, _observation, reception, report, _resolver = (
            _artifacts(current_input)
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert report.public_observation_status == "passed"
        assert _POLICY_RE.search(reception) is None
        assert _ADVICE_RE.search(reception) is None
        terminal = next(
            atom
            for atom in _human_line(sentence_plan).binding.functional_atom_ids
            if atom.startswith("reception_terminal_predicate:")
        )
        terminal_families[terminal] += 1
        reception_texts.append(reception)

    assert len(cases) == 20
    assert len(terminal_families) >= 5
    assert terminal_families.most_common(1)[0][1] < len(cases) * 0.75
    assert len(set(reception_texts)) >= 8


def test_r4_realizer_source_is_functional_and_has_no_relation_or_fixture_route() -> None:
    source = _REALIZER_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "required_relation_ids" not in source
    assert "relation_surface_role" not in source
    assert ".relations" not in source
    resolver_read_owners = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and "resolver.resolve(" in (ast.get_source_segment(source, node) or "")
    }
    assert resolver_read_owners == {"_short_bound_anchor"}
    assert "case_id" not in source
    assert "I6-" not in source
    assert "random" not in source

    predicate_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_predicate_fragment"
    )
    assert not any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "。" in node.value
        for node in ast.walk(predicate_function)
    )
