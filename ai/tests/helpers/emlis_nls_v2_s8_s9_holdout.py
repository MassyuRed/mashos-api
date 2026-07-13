# -*- coding: utf-8 -*-
from __future__ import annotations

"""One-shot, body-safe Holdout evaluator for NLS v2 Steps 8/9.

The same frozen runner is used for both cohorts.  Candidate/input bodies exist
only in the process-local blind-review packet written outside the repository.
Final receipts contain ids, enums, counts, hashes, and body-free selector meta.
"""

from collections import Counter
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Final, Mapping, Sequence

from helpers.emlis_nls_v2_s2_development import (
    APP_VALID_CATEGORIES,
    APP_VALID_EMOTIONS,
    DEPTH_ORDER,
    EVALUATION_FAMILIES,
    EvaluationCase,
    sha256_file,
    sha256_json,
)
from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception import realize_grounded_human_reception
from emlis_ai_grounded_human_reception_v2 import (
    ReceptionSurfaceCandidateSetV2,
    ReceptionSurfaceCandidateV2,
    generate_reception_surface_candidates_v2,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    build_grounded_observation_plan,
)
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    ReceptionCandidatePlanSetV2,
    build_reception_candidate_plans_v2,
)
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    DISTRIBUTION_THRESHOLD_FREEZE,
    ReceptionCandidateSelectionV2,
    evaluate_and_select_reception_candidate_v2,
    resolve_selected_reception_surface_v2,
    selector_config_as_body_free_meta,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    ReceptionContentPlanV2,
    build_reception_content_plan_v2,
)


_AI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _AI_ROOT.parent
_TEST_ROOT = _AI_ROOT / "tests"
_HOLDOUT_ROOT = _TEST_ROOT / "local_only" / "holdout"
_MANIFEST_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s2_corpus_manifest_20260713.json"
)
_PROTOCOL_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s8_s9_protocol_freeze_20260713.json"
)
_REPLY_SERVICE_PATH = (
    _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
)

HOLDOUT_FIXTURE_PATHS: Final[Mapping[str, Path]] = {
    "holdout_a": _HOLDOUT_ROOT / "emlis_nls_v2_s2_holdout_a14_20260713.json",
    "holdout_b": _HOLDOUT_ROOT / "emlis_nls_v2_s2_holdout_b14_20260713.json",
}
HOLDOUT_SCHEMA_VERSIONS: Final[Mapping[str, str]] = {
    "holdout_a": "cocolon.emlis.nls_v2.evaluation_corpus.holdout_a.v1",
    "holdout_b": "cocolon.emlis.nls_v2.evaluation_corpus.holdout_b.v1",
}
HOLDOUT_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.nls_v2.holdout_evaluation_receipt.v1"
)
BLIND_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.nls_v2.holdout_blind_review_packet.v1"
)
BLIND_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.nls_v2.holdout_blind_decisions.v1"
)
PRIVATE_RUN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.nls_v2.holdout_private_run.v1"
)

PRODUCT_METRIC_NAMES: Final = (
    "read_feeling",
    "naturalness",
    "non_template",
    "wants_more_input_or_accumulation",
    "self_blame_non_amplification",
    "overclaim_absence",
)
ABSOLUTE_FAILURE_CODES: Final = frozenset(
    {
        "meaning_inversion",
        "polarity_inversion",
        "false_causality",
        "reference_scope_confusion",
        "unsupported_personality_diagnosis_cause_future",
        "self_denial_amplification",
        "normal_input_refusal",
        "safety_boundary_regression",
        "raw_body_public_leak",
        "case_specific_route_cue_fixed_sentence",
        "public_contract_break",
    }
)
PAIRED_PREFERENCES: Final = frozenset(
    {"left_clearly_better", "same", "right_clearly_better"}
)

_CASE_ID_RE = re.compile(r"^NLS2-F(0[1-9]|1[0-4])-([AB])01$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_BURDEN_RE = re.compile(r"(?:苦しさ|つらさ|しんどさ|負担)")
_UNCERTAINTY_RE = re.compile(r"(?:分から|わから|不明|まだ|決めつけず)")
_ABSOLUTE_SURFACE_RE = re.compile(
    r"(?:必ず成功|もう解決|回復しました|うつ病|鬱病|パニック障害|"
    r"適応障害|あなたは(?:強い|優しい|立派|素晴らしい)(?:人)?です|"
    r"してください|しましょう|すべき|した方がいい)"
)
_NORMAL_REFUSAL_RE = re.compile(
    r"(?:(?:お答え|応答|対応|判断)(?:できません|できない)|"
    r"AIなので.{0,12}(?:分かりません|わかりません))"
)
_FORBIDDEN_RECEIPT_KEYS = frozenset(
    {
        "current_input",
        "memo",
        "memo_action",
        "text",
        "v1_text",
        "v2_text",
        "left_text",
        "right_text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "expected_text",
        "note",
        "reason",
    }
)
_REQUIRED_CASE_FIELDS = frozenset(
    {
        "case_id",
        "family",
        "current_input",
        "semantic_obligation_codes",
        "forbidden_claim_codes",
        "polarity_contract",
        "topic_separation_codes",
        "response_opportunity_codes",
        "depth_range",
        "safety_boundary_codes",
    }
)


class HoldoutEvaluationError(ValueError):
    """Raised when a sealed evaluation contract cannot be honored."""


@dataclass(frozen=True)
class HoldoutSelectionRow:
    case: EvaluationCase
    observation_plan: GroundedObservationPlan
    content_plan: ReceptionContentPlanV2
    candidate_plan_set: ReceptionCandidatePlanSetV2
    resolver: EvidenceSpanResolver
    surface_candidate_set: ReceptionSurfaceCandidateSetV2
    selection: ReceptionCandidateSelectionV2
    selected_surface: ReceptionSurfaceCandidateV2 | None
    v1_text: str


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _validate_codes(case_id: str, field: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise HoldoutEvaluationError(f"holdout_codes_missing:{case_id}:{field}")
    rows = tuple(str(item) for item in value)
    if len(rows) != len(set(rows)) or any(not _CODE_RE.fullmatch(row) for row in rows):
        raise HoldoutEvaluationError(f"holdout_codes_invalid:{case_id}:{field}")
    return rows


def _assert_no_expected_surface(value: Any, case_id: str) -> None:
    forbidden = {
        "expected_text",
        "expected_surface",
        "expected_sentence",
        "correct_text",
        "correct_wording",
        "correct_predicate",
        "surface_template",
        "candidate_text",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden:
                raise HoldoutEvaluationError(
                    f"holdout_expected_surface_forbidden:{case_id}:{key}"
                )
            _assert_no_expected_surface(child, case_id)
    elif isinstance(value, list):
        for child in value:
            _assert_no_expected_surface(child, case_id)


def _cohort_letter(cohort: str) -> str:
    return {"holdout_a": "A", "holdout_b": "B"}.get(cohort, "")


def load_holdout_cases_for_one_shot(cohort: str) -> tuple[EvaluationCase, ...]:
    """Read and validate exactly one explicitly requested sealed fixture."""

    if cohort not in HOLDOUT_FIXTURE_PATHS:
        raise HoldoutEvaluationError(f"unknown_holdout_cohort:{cohort}")
    path = HOLDOUT_FIXTURE_PATHS[cohort]
    manifest = _json_load(_MANIFEST_PATH)
    expected_hash = manifest["cohorts"][cohort]["fixture_sha256"]
    live_hash = sha256_file(path)
    if live_hash != expected_hash:
        raise HoldoutEvaluationError(
            f"holdout_fixture_hash_mismatch:{cohort}:{expected_hash}:{live_hash}"
        )

    payload = _json_load(path)
    if payload.get("schema_version") != HOLDOUT_SCHEMA_VERSIONS[cohort]:
        raise HoldoutEvaluationError(f"holdout_fixture_schema_mismatch:{cohort}")
    if payload.get("cohort") != cohort:
        raise HoldoutEvaluationError(f"holdout_fixture_cohort_mismatch:{cohort}")
    if payload.get("local_only") is not True:
        raise HoldoutEvaluationError(f"holdout_fixture_not_local_only:{cohort}")
    if payload.get("contains_expected_surface") is not False:
        raise HoldoutEvaluationError(f"holdout_expected_surface_flag_invalid:{cohort}")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 14:
        raise HoldoutEvaluationError(f"holdout_case_count_invalid:{cohort}")
    if payload.get("case_count") != 14:
        raise HoldoutEvaluationError(f"holdout_declared_count_invalid:{cohort}")
    if payload.get("case_order") != [row.get("case_id") for row in raw_cases]:
        raise HoldoutEvaluationError(f"holdout_case_order_invalid:{cohort}")

    cases: list[EvaluationCase] = []
    expected_letter = _cohort_letter(cohort)
    for raw in raw_cases:
        case_id = str(raw.get("case_id") or "")
        match = _CASE_ID_RE.fullmatch(case_id)
        if match is None or match.group(2) != expected_letter:
            raise HoldoutEvaluationError(f"holdout_case_id_invalid:{cohort}:{case_id}")
        if set(raw) != set(_REQUIRED_CASE_FIELDS):
            raise HoldoutEvaluationError(f"holdout_case_shape_invalid:{case_id}")
        _assert_no_expected_surface(raw, case_id)
        family = str(raw.get("family") or "")
        if family not in EVALUATION_FAMILIES:
            raise HoldoutEvaluationError(f"holdout_family_invalid:{case_id}:{family}")
        current_input = raw.get("current_input")
        if not isinstance(current_input, dict) or set(current_input) != {
            "memo",
            "memo_action",
            "emotions",
            "category",
        }:
            raise HoldoutEvaluationError(f"holdout_input_shape_invalid:{case_id}")
        emotions = tuple(str(item) for item in current_input.get("emotions") or ())
        categories = tuple(str(item) for item in current_input.get("category") or ())
        if not emotions or any(item not in APP_VALID_EMOTIONS for item in emotions):
            raise HoldoutEvaluationError(f"holdout_emotion_invalid:{case_id}")
        if not categories or any(item not in APP_VALID_CATEGORIES for item in categories):
            raise HoldoutEvaluationError(f"holdout_category_invalid:{case_id}")
        depth_range = raw.get("depth_range")
        if not isinstance(depth_range, dict) or set(depth_range) != {"min", "max"}:
            raise HoldoutEvaluationError(f"holdout_depth_shape_invalid:{case_id}")
        min_depth = str(depth_range.get("min") or "")
        max_depth = str(depth_range.get("max") or "")
        if (
            min_depth not in DEPTH_ORDER
            or max_depth not in DEPTH_ORDER
            or DEPTH_ORDER[min_depth] > DEPTH_ORDER[max_depth]
        ):
            raise HoldoutEvaluationError(f"holdout_depth_invalid:{case_id}")
        polarity = raw.get("polarity_contract")
        if not isinstance(polarity, dict) or set(polarity) != {
            "source",
            "inversion_forbidden",
        }:
            raise HoldoutEvaluationError(f"holdout_polarity_shape_invalid:{case_id}")
        if polarity.get("source") not in {
            "positive",
            "negative",
            "mixed",
            "neutral",
            "uncertain",
        } or polarity.get("inversion_forbidden") is not True:
            raise HoldoutEvaluationError(f"holdout_polarity_invalid:{case_id}")
        cases.append(
            EvaluationCase(
                case_id=case_id,
                family=family,
                current_input={
                    "memo": str(current_input.get("memo") or ""),
                    "memo_action": str(current_input.get("memo_action") or ""),
                    "emotions": list(emotions),
                    "category": list(categories),
                },
                semantic_obligation_codes=_validate_codes(
                    case_id, "semantic_obligation_codes", raw.get("semantic_obligation_codes")
                ),
                forbidden_claim_codes=_validate_codes(
                    case_id, "forbidden_claim_codes", raw.get("forbidden_claim_codes")
                ),
                polarity_contract=dict(polarity),
                topic_separation_codes=tuple(
                    str(item) for item in raw.get("topic_separation_codes") or ()
                ),
                response_opportunity_codes=_validate_codes(
                    case_id, "response_opportunity_codes", raw.get("response_opportunity_codes")
                ),
                min_depth=min_depth,
                max_depth=max_depth,
                safety_boundary_codes=_validate_codes(
                    case_id, "safety_boundary_codes", raw.get("safety_boundary_codes")
                ),
            )
        )

    if Counter(case.family for case in cases) != Counter(EVALUATION_FAMILIES):
        raise HoldoutEvaluationError(f"holdout_family_distribution_invalid:{cohort}")
    if len({case.case_id for case in cases}) != 14:
        raise HoldoutEvaluationError(f"holdout_case_id_duplicate:{cohort}")
    if len({sha256_json(case.current_input) for case in cases}) != 14:
        raise HoldoutEvaluationError(f"holdout_input_duplicate:{cohort}")
    return tuple(cases)


def evaluate_holdout_once(cohort: str) -> tuple[HoldoutSelectionRow, ...]:
    rows: list[HoldoutSelectionRow] = []
    for case in load_holdout_cases_for_one_shot(cohort):
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        candidate_plan_set = build_reception_candidate_plans_v2(content_plan)
        resolver = build_evidence_span_resolver(
            tuple(build_evidence_ledger(case.current_input)),
            current_input=case.current_input,
        )
        surface_candidate_set = generate_reception_surface_candidates_v2(
            observation_plan,
            content_plan,
            candidate_plan_set,
            resolver,
        )
        selection = evaluate_and_select_reception_candidate_v2(
            observation_plan,
            content_plan,
            candidate_plan_set,
            surface_candidate_set,
            resolver,
        )
        selected_surface = (
            resolve_selected_reception_surface_v2(selection, surface_candidate_set)
            if selection.status == "selected"
            else None
        )
        reception = observation_plan.response_plan.human_reception_plan
        if reception is None:
            raise HoldoutEvaluationError(f"holdout_v1_plan_missing:{case.case_id}")
        v1_text = realize_grounded_human_reception(
            reception,
            {nucleus.nucleus_id: nucleus for nucleus in observation_plan.nuclei},
            resolver,
        ).text
        rows.append(
            HoldoutSelectionRow(
                case=case,
                observation_plan=observation_plan,
                content_plan=content_plan,
                candidate_plan_set=candidate_plan_set,
                resolver=resolver,
                surface_candidate_set=surface_candidate_set,
                selection=selection,
                selected_surface=selected_surface,
                v1_text=v1_text,
            )
        )
    return tuple(rows)


def _machine_failure_codes(row: HoldoutSelectionRow) -> tuple[str, ...]:
    failures: list[str] = []
    if row.selection.status != "selected":
        failures.append("selection_failure")
    selected_eval = next(
        (
            item
            for item in row.selection.evaluations
            if item.candidate_id == row.selection.selected_candidate_id
        ),
        None,
    )
    if selected_eval is None or selected_eval.hard_gate.status != "passed":
        failures.append("selected_hard_gate_failure")
    if not (
        DEPTH_ORDER[row.case.min_depth]
        <= DEPTH_ORDER[row.content_plan.depth]
        <= DEPTH_ORDER[row.case.max_depth]
    ):
        failures.append("depth_out_of_contract")
    normalized_signatures = {
        unit.semantic_signature.removeprefix("emlis_reception_of_")
        for unit in row.content_plan.content_units
    }
    required_distinct = {"minimal": 1, "focused": 2, "layered": 3}[
        row.content_plan.depth
    ]
    if len(normalized_signatures) < required_distinct:
        failures.append("content_distinctness_failure")
    if row.selected_surface is None:
        return tuple(dict.fromkeys(failures))
    text = row.selected_surface.text
    if row.case.polarity_contract["source"] == "positive" and _BURDEN_RE.search(text):
        failures.append("positive_polarity_burden")
    if row.case.polarity_contract["source"] == "uncertain" and not _UNCERTAINTY_RE.search(text):
        failures.append("unknown_not_preserved")
    if row.case.family == "self_denial" and (
        "あなた自身が決まるとは思えません" not in text
    ):
        failures.append("self_denial_boundary_missing")
    if _ABSOLUTE_SURFACE_RE.search(text):
        failures.append("unsupported_claim")
    if _NORMAL_REFUSAL_RE.search(text):
        failures.append("normal_input_refusal")
    if row.selection.runtime_connected:
        failures.append("runtime_connected")
    if row.selection.v1_fallback_used:
        failures.append("v1_fallback_used")
    if row.content_plan.depth in {"focused", "layered"} and row.selected_surface.sentence_count == 1:
        failures.append("rich_single_sentence")
    if row.content_plan.depth == "minimal" and row.selected_surface.sentence_count > 1:
        failures.append("short_meaningless_inflation")
    return tuple(failures)


def _holdout_distribution(rows: Sequence[HoldoutSelectionRow]) -> dict[str, Any]:
    strategies: Counter[str] = Counter()
    terminals: Counter[str] = Counter()
    predicates: Counter[str] = Counter()
    skeletons: Counter[str] = Counter()
    texts: Counter[str] = Counter()
    for row in rows:
        if row.selected_surface is None or row.selection.selected_candidate_id is None:
            continue
        candidate = next(
            item
            for item in row.candidate_plan_set.candidates
            if item.candidate_id == row.selection.selected_candidate_id
        )
        variation = candidate.variation_signature
        strategies[candidate.strategy_code] += 1
        terminals[variation.terminal_family] += 1
        predicates.update(row.selected_surface.predicate_families)
        skeletons[
            "|".join(
                (
                    candidate.strategy_code,
                    variation.opening,
                    variation.speaker_presence,
                    variation.connection,
                    variation.terminal_family,
                    str(row.selected_surface.sentence_count),
                )
            )
        ] += 1
        texts[row.selected_surface.text] += 1

    count = len(rows)
    predicate_total = sum(predicates.values())

    def share(counter: Counter[str], denominator: int) -> float:
        return round(max(counter.values(), default=0) / max(1, denominator), 6)

    return {
        "case_count": count,
        "exact_duplicate_count": sum(value - 1 for value in texts.values() if value > 1),
        "rich_single_sentence_count": sum(
            row.selected_surface is not None
            and row.content_plan.depth in {"focused", "layered"}
            and row.selected_surface.sentence_count == 1
            for row in rows
        ),
        "short_meaningless_inflation_count": sum(
            row.selected_surface is not None
            and row.content_plan.depth == "minimal"
            and row.selected_surface.sentence_count > 1
            for row in rows
        ),
        "strategy_counts": dict(sorted(strategies.items())),
        "terminal_family_counts": dict(sorted(terminals.items())),
        "predicate_family_counts": dict(sorted(predicates.items())),
        "skeleton_counts": dict(sorted(skeletons.items())),
        "max_strategy_share": share(strategies, count),
        "max_terminal_family_share": share(terminals, count),
        "max_predicate_family_share": share(predicates, predicate_total),
        "max_skeleton_share": share(skeletons, count),
    }


def _distribution_pass(distribution: Mapping[str, Any]) -> bool:
    thresholds = DISTRIBUTION_THRESHOLD_FREEZE
    return bool(
        distribution["exact_duplicate_count"] <= thresholds["exact_duplicate_max"]
        and distribution["rich_single_sentence_count"]
        <= thresholds["rich_single_sentence_max"]
        and distribution["short_meaningless_inflation_count"]
        <= thresholds["short_meaningless_inflation_max"]
        and distribution["max_strategy_share"] <= thresholds["strategy_share_max"]
        and distribution["max_terminal_family_share"]
        <= thresholds["terminal_family_share_max"]
        and distribution["max_predicate_family_share"]
        <= thresholds["predicate_family_share_max"]
        and distribution["max_skeleton_share"] <= thresholds["skeleton_share_max"]
    )


def _blind_v1_position(case_id: str) -> str:
    match = _CASE_ID_RE.fullmatch(case_id)
    if match is None:
        raise HoldoutEvaluationError(f"blind_case_id_invalid:{case_id}")
    family_number = int(match.group(1))
    return "left" if family_number % 2 == 1 else "right"


def _review_token(cohort: str, case_id: str) -> str:
    return hashlib.sha256(
        f"{cohort}:{case_id}:nls-v2-blind-v1".encode("utf-8")
    ).hexdigest()[:16]


def _live_protocol_state() -> dict[str, Any]:
    protocol = _json_load(_PROTOCOL_PATH)
    dependency_rows = [
        {
            "path": row["path"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in protocol["dependency_closure"]["files"]
    ]
    fixture_rows = {
        cohort: sha256_file(path)
        for cohort, path in HOLDOUT_FIXTURE_PATHS.items()
    }
    return {
        "dependency_closure_sha256": sha256_json(dependency_rows),
        "selector_config_sha256": sha256_json(selector_config_as_body_free_meta()),
        "evaluation_runner_sha256": sha256_file(Path(__file__)),
        "receipt_test_sha256": sha256_file(
            _TEST_ROOT / "test_emlis_nls_v2_s8_s9_holdout_evaluation.py"
        ),
        "holdout_fixture_sha256": fixture_rows,
        "reply_service_sha256": sha256_file(_REPLY_SERVICE_PATH),
    }


def assert_protocol_unchanged() -> dict[str, Any]:
    protocol = _json_load(_PROTOCOL_PATH)
    live = _live_protocol_state()
    expected = {
        "dependency_closure_sha256": protocol["dependency_closure"]["sha256"],
        "selector_config_sha256": protocol["step7_freeze"]["selector_config_sha256"],
        "evaluation_runner_sha256": protocol["evaluation_protocol"][
            "runner_sha256"
        ],
        "receipt_test_sha256": protocol["evaluation_protocol"][
            "receipt_test_sha256"
        ],
        "holdout_fixture_sha256": {
            cohort: row["fixture_sha256"]
            for cohort, row in protocol["holdout_fixtures"].items()
        },
        "reply_service_sha256": protocol["runtime_boundary"][
            "reply_service_sha256"
        ],
    }
    if live != expected:
        raise HoldoutEvaluationError(
            "protocol_state_changed:" + json.dumps(
                {"expected": expected, "live": live},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return live


def _assert_ephemeral_output(path: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(_REPO_ROOT.resolve())
    except ValueError:
        return
    raise HoldoutEvaluationError(f"body_packet_must_stay_outside_repo:{resolved}")


def prepare_blind_review_once(
    cohort: str,
    *,
    review_output: Path,
    private_output: Path,
    sentinel_dir: Path,
    a_receipt: Path | None = None,
) -> None:
    _assert_ephemeral_output(review_output)
    _assert_ephemeral_output(private_output)
    sentinel_dir.mkdir(parents=True, exist_ok=True)
    sentinel = sentinel_dir / f"{cohort}.executed"
    if sentinel.exists():
        raise HoldoutEvaluationError(f"holdout_already_executed:{cohort}")
    if cohort == "holdout_b":
        if a_receipt is None:
            raise HoldoutEvaluationError("holdout_b_requires_a_receipt")
        a_payload = _json_load(a_receipt)
        if a_payload.get("cohort") != "holdout_a" or a_payload.get("overall_status") != "pass":
            raise HoldoutEvaluationError("holdout_b_blocked_by_a_status")
    before = assert_protocol_unchanged()
    rows = evaluate_holdout_once(cohort)
    after = assert_protocol_unchanged()
    if before != after:
        raise HoldoutEvaluationError(f"protocol_changed_during_run:{cohort}")

    private_rows = []
    review_items = []
    for slot, row in enumerate(rows, start=1):
        token = _review_token(cohort, row.case.case_id)
        v1_position = _blind_v1_position(row.case.case_id)
        v2_text = (
            row.selected_surface.text
            if row.selected_surface is not None
            else "[V2_NO_VALID_CANDIDATE]"
        )
        left_text = row.v1_text if v1_position == "left" else v2_text
        right_text = v2_text if v1_position == "left" else row.v1_text
        machine_failures = _machine_failure_codes(row)
        private_rows.append(
            {
                "slot": slot,
                "review_token": token,
                "case_id": row.case.case_id,
                "case_identity_sha256": sha256_json(row.case.case_id),
                "family": row.case.family,
                "v1_position": v1_position,
                "v1_text_sha256": sha256_json(row.v1_text),
                "v2_text_sha256": sha256_json(v2_text),
                "content_plan_id": row.content_plan.plan_id,
                "depth": row.content_plan.depth,
                "normalized_semantic_signature_count": len(
                    {
                        unit.semantic_signature.removeprefix("emlis_reception_of_")
                        for unit in row.content_plan.content_units
                    }
                ),
                "candidate_count": len(row.candidate_plan_set.candidates),
                "selection_meta": row.selection.as_body_free_meta(),
                "selected_surface_meta": (
                    row.selected_surface.as_body_free_meta()
                    if row.selected_surface is not None
                    else None
                ),
                "machine_failure_codes": list(machine_failures),
            }
        )
        review_items.append(
            {
                "review_token": token,
                "input": dict(row.case.current_input),
                "semantic_obligation_codes": list(row.case.semantic_obligation_codes),
                "forbidden_claim_codes": list(row.case.forbidden_claim_codes),
                "polarity_contract": dict(row.case.polarity_contract),
                "topic_separation_codes": list(row.case.topic_separation_codes),
                "response_opportunity_codes": list(row.case.response_opportunity_codes),
                "depth_range": {"min": row.case.min_depth, "max": row.case.max_depth},
                "safety_boundary_codes": list(row.case.safety_boundary_codes),
                "left_text": left_text,
                "right_text": right_text,
            }
        )

    distribution = _holdout_distribution(rows)
    private = {
        "schema_version": PRIVATE_RUN_SCHEMA_VERSION,
        "cohort": cohort,
        "evaluation_run_count": 1,
        "protocol_state_before": before,
        "protocol_state_after": after,
        "machine_summary": {
            "case_count": len(rows),
            "selected_count": sum(row.selection.status == "selected" for row in rows),
            "v2_no_valid_candidate_count": sum(
                row.selection.status != "selected" for row in rows
            ),
            "machine_failure_case_count": sum(
                bool(_machine_failure_codes(row)) for row in rows
            ),
            "v1_fallback_used_count": sum(row.selection.v1_fallback_used for row in rows),
            "runtime_connected_count": sum(row.selection.runtime_connected for row in rows),
            "distribution": distribution,
            "distribution_pass": _distribution_pass(distribution),
        },
        "rows": private_rows,
    }
    review = {
        "schema_version": BLIND_REVIEW_SCHEMA_VERSION,
        "cohort": cohort,
        "case_count": len(review_items),
        "case_id_hidden": True,
        "variant_identity_hidden": True,
        "display_order_rule": "family_number_parity_v1_left_on_odd_v1_right_on_even",
        "items": review_items,
    }
    _json_write(private_output, private)
    _json_write(review_output, review)
    sentinel.write_text(
        json.dumps(
            {
                "cohort": cohort,
                "evaluation_run_count": 1,
                "private_sha256": sha256_file(private_output),
                "review_sha256": sha256_file(review_output),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _validated_decisions(payload: Any, cohort: str, tokens: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HoldoutEvaluationError("blind_decisions_not_object")
    if payload.get("schema_version") != BLIND_DECISION_SCHEMA_VERSION:
        raise HoldoutEvaluationError("blind_decisions_schema_mismatch")
    if payload.get("cohort") != cohort:
        raise HoldoutEvaluationError("blind_decisions_cohort_mismatch")
    reviewer = payload.get("reviewer")
    if not isinstance(reviewer, dict) or set(reviewer) != {
        "reviewer_id",
        "review_mode",
        "case_id_visible",
        "variant_identity_visible",
        "independent_external_reviewer",
    }:
        raise HoldoutEvaluationError("blind_decisions_reviewer_shape_invalid")
    if reviewer["case_id_visible"] is not False or reviewer["variant_identity_visible"] is not False:
        raise HoldoutEvaluationError("blind_decisions_not_masked")
    raw = payload.get("decisions")
    if not isinstance(raw, list) or len(raw) != 14:
        raise HoldoutEvaluationError("blind_decisions_count_invalid")
    by_token: dict[str, Any] = {}
    for decision in raw:
        if not isinstance(decision, dict) or set(decision) != {
            "review_token",
            "left",
            "right",
            "paired_preference",
        }:
            raise HoldoutEvaluationError("blind_decision_shape_invalid")
        token = str(decision["review_token"])
        if token in by_token:
            raise HoldoutEvaluationError(f"blind_decision_duplicate:{token}")
        for side in ("left", "right"):
            score = decision[side]
            if not isinstance(score, dict) or set(score) != {
                *PRODUCT_METRIC_NAMES,
                "absolute_failure_codes",
            }:
                raise HoldoutEvaluationError(f"blind_side_shape_invalid:{token}:{side}")
            if any(type(score[name]) is not bool for name in PRODUCT_METRIC_NAMES):
                raise HoldoutEvaluationError(f"blind_metric_not_bool:{token}:{side}")
            failures = score["absolute_failure_codes"]
            if not isinstance(failures, list) or any(
                item not in ABSOLUTE_FAILURE_CODES for item in failures
            ) or len(failures) != len(set(failures)):
                raise HoldoutEvaluationError(f"blind_failure_codes_invalid:{token}:{side}")
        if decision["paired_preference"] not in PAIRED_PREFERENCES:
            raise HoldoutEvaluationError(f"blind_preference_invalid:{token}")
        by_token[token] = decision
    if set(by_token) != tokens:
        raise HoldoutEvaluationError("blind_decision_token_set_mismatch")
    return {"reviewer": reviewer, "by_token": by_token}


def _preference_for_v2(preference: str, v1_position: str) -> str:
    if preference == "same":
        return "same"
    better_position = "left" if preference == "left_clearly_better" else "right"
    return "v1_clearly_better" if better_position == v1_position else "v2_clearly_better"


def _assert_body_free_receipt(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_RECEIPT_KEYS:
                raise HoldoutEvaluationError(f"receipt_body_key_forbidden:{key}")
            _assert_body_free_receipt(child)
    elif isinstance(value, list):
        for child in value:
            _assert_body_free_receipt(child)


def finalize_body_free_receipt(
    cohort: str,
    *,
    private_input: Path,
    decisions_input: Path,
    receipt_output: Path,
    a_receipt: Path | None = None,
) -> dict[str, Any]:
    protocol_state = assert_protocol_unchanged()
    private = _json_load(private_input)
    if private.get("schema_version") != PRIVATE_RUN_SCHEMA_VERSION:
        raise HoldoutEvaluationError("private_run_schema_mismatch")
    if private.get("cohort") != cohort or private.get("evaluation_run_count") != 1:
        raise HoldoutEvaluationError("private_run_identity_mismatch")
    if private.get("protocol_state_before") != protocol_state or private.get(
        "protocol_state_after"
    ) != protocol_state:
        raise HoldoutEvaluationError("private_run_protocol_state_mismatch")
    rows = private.get("rows")
    if not isinstance(rows, list) or len(rows) != 14:
        raise HoldoutEvaluationError("private_run_rows_invalid")
    tokens = {str(row["review_token"]) for row in rows}
    decisions = _validated_decisions(_json_load(decisions_input), cohort, tokens)

    result_rows = []
    metric_counts = Counter()
    paired_counts = Counter()
    absolute_failure_counts = Counter()
    for row in rows:
        decision = decisions["by_token"][row["review_token"]]
        v2_position = "right" if row["v1_position"] == "left" else "left"
        v2_score = decision[v2_position]
        verdict = _preference_for_v2(
            decision["paired_preference"], row["v1_position"]
        )
        paired_counts[verdict] += 1
        for metric in PRODUCT_METRIC_NAMES:
            metric_counts[metric] += bool(v2_score[metric])
        for code in v2_score["absolute_failure_codes"]:
            absolute_failure_counts[code] += 1
        result_rows.append(
            {
                "slot": row["slot"],
                "case_identity_sha256": row["case_identity_sha256"],
                "family": row["family"],
                "v1_position": row["v1_position"],
                "v1_text_sha256": row["v1_text_sha256"],
                "v2_text_sha256": row["v2_text_sha256"],
                "content_plan_id": row["content_plan_id"],
                "depth": row["depth"],
                "normalized_semantic_signature_count": row[
                    "normalized_semantic_signature_count"
                ],
                "candidate_count": row["candidate_count"],
                "selection_meta": row["selection_meta"],
                "selected_surface_meta": row["selected_surface_meta"],
                "machine_failure_codes": row["machine_failure_codes"],
                "human_v2_metrics": {
                    metric: bool(v2_score[metric]) for metric in PRODUCT_METRIC_NAMES
                },
                "human_absolute_failure_codes": list(
                    v2_score["absolute_failure_codes"]
                ),
                "paired_verdict": verdict,
            }
        )

    product = {
        "read_feeling_pass_count": metric_counts["read_feeling"],
        "naturalness_pass_count": metric_counts["naturalness"],
        "non_template_pass_count": metric_counts["non_template"],
        "wants_more_input_or_accumulation_pass_count": metric_counts[
            "wants_more_input_or_accumulation"
        ],
        "self_blame_non_amplification_pass_count": metric_counts[
            "self_blame_non_amplification"
        ],
        "overclaim_absence_pass_count": metric_counts["overclaim_absence"],
        "wants_more_floor_pass": metric_counts[
            "wants_more_input_or_accumulation"
        ]
        >= 12,
        "roadmap_product_target_pass": bool(
            metric_counts["read_feeling"] >= 13
            and metric_counts["naturalness"] >= 13
            and metric_counts["non_template"] >= 13
            and metric_counts["wants_more_input_or_accumulation"] >= 13
            and metric_counts["self_blame_non_amplification"] == 14
            and metric_counts["overclaim_absence"] == 14
        ),
    }
    paired = {
        "v2_clearly_better_count": paired_counts["v2_clearly_better"],
        "same_count": paired_counts["same"],
        "v1_clearly_better_count": paired_counts["v1_clearly_better"],
        "pass": bool(
            paired_counts["v2_clearly_better"] >= 10
            and paired_counts["v1_clearly_better"] <= 1
            and paired_counts["same"] <= 3
        ),
    }
    machine = private["machine_summary"]
    human_absolute = {
        "failure_case_count": sum(bool(row["human_absolute_failure_codes"]) for row in result_rows),
        "failure_counts": dict(sorted(absolute_failure_counts.items())),
        "fatal_semantic_failure_count": sum(absolute_failure_counts.values()),
        "pass": not absolute_failure_counts,
    }
    overall_pass = bool(
        machine["selected_count"] == 14
        and machine["v2_no_valid_candidate_count"] == 0
        and machine["machine_failure_case_count"] == 0
        and machine["v1_fallback_used_count"] == 0
        and machine["runtime_connected_count"] == 0
        and machine["distribution_pass"]
        and human_absolute["pass"]
        and product["roadmap_product_target_pass"]
        and paired["pass"]
    )
    receipt: dict[str, Any] = {
        "schema_version": HOLDOUT_RECEIPT_SCHEMA_VERSION,
        "evaluation_date": "2026-07-13",
        "cohort": cohort,
        "case_count": 14,
        "evaluation_run_count": 1,
        "protocol_freeze_sha256": sha256_file(_PROTOCOL_PATH),
        "fixture_sha256": protocol_state["holdout_fixture_sha256"][cohort],
        "dependency_closure_sha256": protocol_state[
            "dependency_closure_sha256"
        ],
        "selector_config_sha256": protocol_state["selector_config_sha256"],
        "evaluation_runner_sha256": protocol_state["evaluation_runner_sha256"],
        "receipt_test_sha256": protocol_state["receipt_test_sha256"],
        "reply_service_sha256": protocol_state["reply_service_sha256"],
        "automatic_gate": machine,
        "human_review": {
            "reviewer": decisions["reviewer"],
            "automatic_gate_separate": True,
            "case_id_hidden_during_review": True,
            "variant_identity_hidden_during_review": True,
            "display_order_rule": (
                "family_number_parity_v1_left_on_odd_v1_right_on_even"
            ),
            "v1_left_count": sum(row["v1_position"] == "left" for row in rows),
            "v1_right_count": sum(row["v1_position"] == "right" for row in rows),
            "absolute_conditions": human_absolute,
            "product_metrics": product,
            "paired_comparison": paired,
        },
        "rows": result_rows,
        "source_or_protocol_change_count": 0,
        "candidate_bodies_included": False,
        "selected_bodies_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "expected_text_included": False,
        "runtime_connected": False,
        "public_contract_changed": False,
        "overall_status": "pass" if overall_pass else "stop",
    }

    if cohort == "holdout_b":
        if a_receipt is None:
            raise HoldoutEvaluationError("holdout_b_finalize_requires_a_receipt")
        a_payload = _json_load(a_receipt)
        if a_payload.get("cohort") != "holdout_a":
            raise HoldoutEvaluationError("holdout_a_receipt_identity_invalid")
        a_family = {row["family"]: row["paired_verdict"] for row in a_payload["rows"]}
        b_family = {row["family"]: row["paired_verdict"] for row in result_rows}
        reversals = sorted(
            family
            for family in EVALUATION_FAMILIES
            if {a_family[family], b_family[family]}
            == {"v2_clearly_better", "v1_clearly_better"}
        )
        combined_pass = bool(
            a_payload.get("overall_status") == "pass"
            and overall_pass
            and not reversals
        )
        receipt["a_b_combined"] = {
            "holdout_a_receipt_sha256": sha256_file(a_receipt),
            "holdout_a_status": a_payload.get("overall_status"),
            "holdout_b_status": "pass" if overall_pass else "stop",
            "family_large_reversal_count": len(reversals),
            "family_large_reversal_codes": reversals,
            "a_to_b_source_or_protocol_change_count": 0,
            "both_holdouts_pass": combined_pass,
        }
        receipt["overall_status"] = "pass" if combined_pass else "stop"

    _assert_body_free_receipt(receipt)
    _json_write(receipt_output, receipt)
    return receipt


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--cohort", choices=tuple(HOLDOUT_FIXTURE_PATHS), required=True)
    prepare.add_argument("--review-output", type=Path, required=True)
    prepare.add_argument("--private-output", type=Path, required=True)
    prepare.add_argument("--sentinel-dir", type=Path, required=True)
    prepare.add_argument("--a-receipt", type=Path)
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--cohort", choices=tuple(HOLDOUT_FIXTURE_PATHS), required=True)
    finalize.add_argument("--private-input", type=Path, required=True)
    finalize.add_argument("--decisions-input", type=Path, required=True)
    finalize.add_argument("--receipt-output", type=Path, required=True)
    finalize.add_argument("--a-receipt", type=Path)
    subparsers.add_parser("verify-lock")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "prepare":
        prepare_blind_review_once(
            args.cohort,
            review_output=args.review_output,
            private_output=args.private_output,
            sentinel_dir=args.sentinel_dir,
            a_receipt=args.a_receipt,
        )
        return 0
    if args.command == "finalize":
        receipt = finalize_body_free_receipt(
            args.cohort,
            private_input=args.private_input,
            decisions_input=args.decisions_input,
            receipt_output=args.receipt_output,
            a_receipt=args.a_receipt,
        )
        print(receipt["overall_status"])
        return 0 if receipt["overall_status"] == "pass" else 2
    assert_protocol_unchanged()
    print("protocol_unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ABSOLUTE_FAILURE_CODES",
    "BLIND_DECISION_SCHEMA_VERSION",
    "HOLDOUT_FIXTURE_PATHS",
    "HOLDOUT_RECEIPT_SCHEMA_VERSION",
    "HoldoutEvaluationError",
    "assert_protocol_unchanged",
    "evaluate_holdout_once",
    "finalize_body_free_receipt",
    "load_holdout_cases_for_one_shot",
    "prepare_blind_review_once",
]
