"""Evaluate fictional DeepInsight theme issuance without database writes.

Run from the repository root with PYTHONPATH=ai/services/ai_inference.
Without --run, write the case plan and make no provider calls. The explicit
--run option uses the configured natural-reply transport. Use it only with an
authorized provider. Each theme begins with empty history, then uses the
accepted output from earlier cases as its only issued-question history.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from math import ceil
import os
from pathlib import Path
import random
import sys
from typing import TextIO

from cocolon_meaning_experience_engine import deep_insight_question as question


THEMES = ("人間関係", "自分の価値観", "仕事・学び", "日々の過ごし方", "これからのこと")
ATTEMPTS_PER_THEME = 50
CASE_TIMEOUT_SECONDS = 96
SCHEMA = "deep-insight.theme-eval.v1"
Generate = Callable[[str, dict], Awaitable[str]]

_MODEL_PHASES = (
    (question._THEME_PLAN_SYSTEM_MESSAGE, "scene_plan"),
    (question._THEME_WRITE_SYSTEM_MESSAGE, "write"),
    (question._THEME_READ_SYSTEM_MESSAGE, "read"),
    (question._THEME_READ_RETRY_SYSTEM_MESSAGE, "read_retry"),
    (question._THEME_REPAIR_SYSTEM_MESSAGE, "repair"),
    (question._THEME_COMPARE_SYSTEM_MESSAGE, "history_batch"),
    (question._THEME_COMPARE_PAIR_SYSTEM_MESSAGE, "history_pair"),
)


@dataclass(frozen=True)
class Case:
    id: str
    theme: str
    seed: int
    expected: str = "issue"


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(compact(value).encode("utf-8")).hexdigest()


def cases(themes=THEMES, *, attempts=ATTEMPTS_PER_THEME, seed=20261121) -> tuple[Case, ...]:
    return tuple(
        Case(f"theme-{series}-{index:02}", theme, seed * 1000 + series * 100 + index)
        for series, theme in enumerate(THEMES, 1) if theme in themes
        for index in range(1, attempts + 1)
    )


def material_for(history) -> dict:
    """Mirror the theme input: keys and wording for every issued question."""
    return {"questions": [
        {field: prior[field] for field in ("question_key", "text_key", "question_text")}
        for prior in history
    ]}


def emit(output: TextIO, data):
    output.write(compact(data) + "\n")
    output.flush()


async def run_case(case: Case, history, seen_inputs, *, generate: Generate):
    material = material_for(history)
    calls = []
    prepared = None

    async def capture(system, payload):
        phase = next((label for prompt, label in _MODEL_PHASES if system.startswith(prompt)), "unknown")
        call = {"index": len(calls) + 1, "phase": phase,
                "system_sha256": hashlib.sha256(system.encode("utf-8")).hexdigest(),
                "input": copy.deepcopy(payload), "raw": None}
        calls.append(call)
        call["raw"] = await generate(system, payload)
        return call["raw"]

    record = {"kind": "result", **asdict(case), "material": material, "calls": calls}
    try:
        prepared, sources = question.prepare_question_material(
            material, lane="theme", theme=case.theme, choose_theme=random.Random(case.seed).choice)
        fingerprint = digest(prepared)
        record.update(prepared=prepared, prepared_sha256=fingerprint)
        if fingerprint in seen_inputs:
            return {**record, "disposition": "repeated_prepared_input", "final": None}
        seen_inputs.add(fingerprint)
        async with asyncio.timeout(CASE_TIMEOUT_SECONDS):
            result = await question.generate_question(prepared, sources, material=material, generate=capture)
    except Exception as error:
        # Keep the error class. Provider exception text may include configuration.
        return {**record, "prepared": prepared, "disposition": "error",
                "error_type": type(error).__name__, "final": None}

    candidate = result.candidate
    duplicate = candidate is not None and any(
        prior["question_key"] == candidate.question_key or prior["text_key"] == candidate.text_key
        for prior in history
    )
    return {
        **record, "disposition": result.disposition, "candidate": asdict(candidate) if candidate else None,
        "all_history_key_collision": duplicate,
        "final": candidate.text if candidate and not duplicate else None,
    }


async def evaluate(selected, output, *, generate: Generate | None = None, transport="injected"):
    counts = Counter(case.theme for case in selected)
    provenance = hashlib.sha256(Path(question.__file__).read_bytes()).hexdigest()
    max_history = max(0, max(counts.values(), default=0) - 1)
    max_history_batches = ceil(max_history / question._THEME_HISTORY_BATCH_SIZE)
    max_rechecks = min(question._THEME_MAX_PAIR_RECHECKS, 2 + max_history // 8)
    max_splits = min(max_history_batches, max_rechecks // question._THEME_HISTORY_SPLIT_AFTER)
    subbatches = ceil((question._THEME_HISTORY_BATCH_SIZE - question._THEME_HISTORY_SPLIT_AFTER)
                     / question._THEME_HISTORY_SUBBATCH_SIZE)
    # Each split replaces one remaining original-batch scan with smaller scans.
    max_compare_calls = max_history_batches + 2 * max_rechecks + max_splits * (subbatches - 1)
    emit(output, {"kind": "manifest", "schema": SCHEMA, "cases_by_theme": counts,
                  "plan_sha256": digest([asdict(case) for case in selected]),
                  "generator_sha256": provenance,
                  "theme_catalog_sha256": digest({
                      "scenes": question.THEME_SCENES, "angles": question.THEME_ANGLES,
                      "targets": question.THEME_DECISION_TARGETS,
                      "scene_intents": question.THEME_SCENE_ANGLE_TARGETS,
                      "scene_wording": sorted(question.THEME_SCENE_WORDING.items()),
                      "equivalent_positions": question.THEME_EQUIVALENT_POSITIONS,
                      "distinct_positions": question.THEME_DISTINCT_POSITIONS,
                      "verified_bodies": sorted(question.THEME_VERIFIED_BODIES.items()),
                      "forms": question.THEME_QUESTION_FORMS,
                      "overrides": sorted(question.THEME_TARGET_ANGLES.items()),
                      "form_overrides": sorted(question.THEME_TARGET_FORMS.items()),
                      "choice_premises": sorted(question.THEME_CHOICE_PREMISES.items()),
                      "repeated_introductions": sorted(question.THEME_REPEATED_INTRODUCTIONS.items()),
                      "decisions_in_scene": sorted(question.THEME_DECISION_IN_SCENE),
                  }),
                  "fictional": True, "transport": transport if generate is not None else "dry_run",
                  "provider_calls": generate is not None,
                  "max_provider_calls": (7 + max_compare_calls) * len(selected),
                  "same_input_retries": 0})
    if generate is None:
        for case in selected:
            emit(output, {"kind": "case", **asdict(case)})
        return

    histories = {theme: [] for theme in counts}
    totals = {theme: Counter() for theme in counts}
    inputs = {theme: set() for theme in counts}
    for case in selected:
        history = histories[case.theme]
        outcome = await run_case(case, history, inputs[case.theme], generate=generate)
        totals[case.theme]["attempts"] += 1
        totals[case.theme]["provider_calls"] += len(outcome["calls"])
        totals[case.theme][outcome["disposition"]] += 1
        if outcome["disposition"] in ("rejected", "error") and outcome["calls"]:
            phase = outcome["calls"][-1]["phase"]
            totals[case.theme][f"{outcome['disposition']}_after_{phase}"] += 1

        if outcome.get("all_history_key_collision"):
            totals[case.theme]["all_history_key_collision"] += 1
        if outcome["final"] is not None:
            admitted = outcome["candidate"]
            history.insert(0, {"question_key": admitted["question_key"], "text_key": admitted["text_key"],
                               "question_text": admitted["text"]})
            totals[case.theme]["ready_for_product_review"] += 1
        emit(output, outcome)

    emit(output, {"kind": "summary", "cases_by_theme": totals,
                  "issued_history_by_theme": {theme: len(rows) for theme, rows in histories.items()}})


def private_file(path, flags):
    return os.open(path, flags, mode=0o600)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSONL path")
    parser.add_argument("--run", action="store_true", help="Use the configured existing 4B provider")
    parser.add_argument("--theme", action="append", choices=THEMES, help="Limit to the selected themes")
    parser.add_argument("--attempts", type=int, default=ATTEMPTS_PER_THEME, help="Attempts per theme, at most 50")
    parser.add_argument("--seed", type=int, default=20261121, help="Seed for repeatable scene and angle choices")
    args = parser.parse_args(argv)
    if not 1 <= args.attempts <= ATTEMPTS_PER_THEME:
        parser.error("--attempts must be from 1 to 50")

    generate = None
    if args.run:
        from api_deep_insight import _generate_candidate
        generate = _generate_candidate
    selected = cases(args.theme or THEMES, attempts=args.attempts, seed=args.seed)
    with open(args.output, "x", encoding="utf-8", opener=private_file) as output:
        asyncio.run(evaluate(selected, output, generate=generate, transport="configured_natural_reply"))


if __name__ == "__main__":
    sys.exit(main())
