# -*- coding: utf-8 -*-
from __future__ import annotations

"""Local Product QA bootstrap and product-quality measurement runner for EmlisAI.

Phase 1 opens a local, explicit QA profile for Composer resolution and records
whether generation is actually reachable.  Phase 3 runs fixture/local cases
through EmlisAI, normalizes ProductQualityEventV1 rows, and connects existing
Product Read Feel / Blind QA / User Label Connection / Phase11 materials.
Phase 5 adds a blocker-specific generation repair design queue from the Phase 4
Blocker Matrix, without editing generated bodies or relaxing gates.
Phase 8 adds a deterministic validation plan that orders contract, schema,
runner, Blind QA, long-run, blocker, release, and /emotion/submit checks.

The runner never mutates ``os.environ`` and never changes public/RN/DB
contracts.  Raw input and comment bodies are used only as transient renderer
input; they are not retained in run material.
"""

import asyncio
from datetime import datetime, timezone
import inspect
import json
import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Final
from uuid import uuid4

from emlis_ai_composer_client_registry import (
    default_composer_flag_state,
    resolve_emlis_ai_composer_client,
)
from emlis_ai_limited_release_service import evaluate_limited_composer_release
from emlis_ai_product_quality_blocker_matrix import (
    assert_product_quality_blocker_matrix_meta_only,
    build_product_quality_blocker_matrix,
)
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_quality_generation_repair_design import (
    assert_product_quality_generation_repair_design_meta_only,
    build_product_quality_generation_repair_design,
)
from emlis_ai_product_quality_blind_qa_integration import (
    PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE,
    assert_product_quality_blind_qa_integration_meta_only,
    build_product_quality_blind_qa_integration,
)
from emlis_ai_product_release_decision import (
    PRODUCT_RELEASE_DECISION_PHASE,
    assert_product_release_decision_meta_only,
    build_product_release_decision,
)
from emlis_ai_product_quality_validation_plan import (
    PRODUCT_QUALITY_VALIDATION_PLAN_PHASE,
    assert_product_quality_validation_plan_meta_only,
    build_product_quality_validation_plan,
)
from emlis_ai_product_quality_measurement_event import (
    assert_product_quality_measurement_event_meta_only,
    normalize_product_quality_event,
    normalize_product_quality_family,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_scorecard import build_product_readfeel_scorecard
from emlis_ai_product_readfeel_long_run_product_gate import (
    build_product_readfeel_long_run_product_gate,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_runtime_surface_blind_qa_long_run import (
    build_runtime_surface_blind_qa_candidates,
    build_runtime_surface_blind_qa_long_run_summary,
)
from emlis_ai_user_label_connection_product_quality_qa import (
    build_user_label_connection_product_quality_qa_candidates,
    build_user_label_connection_product_quality_qa_summary,
)

PRODUCT_QUALITY_MEASUREMENT_RUNNER_BOOTSTRAP_VERSION: Final = (
    "cocolon.emlis.product_quality.measurement_runner.bootstrap.v1"
)
LOCAL_PRODUCT_QA_PROFILE: Final = "local_product_qa"
LOCAL_PRODUCT_QA_ROLLOUT_STAGE: Final = "internal"
LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER: Final = "limited"
LOCAL_PRODUCT_QA_USER_ID: Final = "local_product_qa_user"
COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER: Final = (
    "composer_generation_path_not_open_for_product_qa"
)
COMPOSER_FEATURE_DISABLED_REASON: Final = "default_limited_composer_feature_disabled"
PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.measurement_run.v1"
)
PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE: Final = "Phase3_ProductQualityMeasurementRunner"
PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE5_CONNECTION: Final = "Phase5_BlockerSpecificGenerationRepairDesign"
PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE6_CONNECTION: Final = PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE
PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE7_CONNECTION: Final = PRODUCT_RELEASE_DECISION_PHASE
PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE8_CONNECTION: Final = PRODUCT_QUALITY_VALIDATION_PLAN_PHASE
PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_DISPLAY_REACH_RATE: Final = 0.90
PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_BINDING_PASS_RATE: Final = 0.98
PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_REASON_COVERAGE_RATE: Final = 1.0
PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES: Final = tuple(PRODUCT_READFEEL_REQUIRED_FAMILIES)

_FEATURE_FLAG_ENV_NAME: Final = "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED"
_ROLLOUT_STAGE_ENV_NAME: Final = "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE"
_DEFAULT_COMPOSER_ENV_NAME: Final = "COCOLON_EMLIS_DEFAULT_COMPOSER"
_ALLOWED_REQUESTED_COMPOSERS: Final = frozenset({"limited", "complete_initial"})

_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "body",
        "text",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _dedupe(values: Sequence[Any] | Any | None) -> list[str]:
    items: Sequence[Any]
    if values is None:
        items = []
    elif isinstance(values, (list, tuple, set)):
        items = list(values)
    else:
        items = [values]
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out




def _safe_identifier(value: Any, *, max_length: int = 96, default: str = "") -> str:
    text = _clean(value)
    if not text:
        return default
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    text = text[:max_length]
    if any(ch not in allowed for ch in text):
        return default
    return text


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "passed", "pass", "green", "allow"}:
        return True
    if text in {"false", "0", "no", "n", "off", "failed", "fail", "red", "blocked", "block"}:
        return False
    return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"pq_{stamp}_{uuid4().hex[:8]}"


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _normalize_requested_composer(value: Any) -> str:
    requested = _clean(value).lower().replace(" ", "_") or LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER
    if requested in {"cocolon_limited", "cocolon_limited_composer", "limited_composer"}:
        return "limited"
    if requested in {"complete", "complete_composer", "complete_composer_initial"}:
        return "complete_initial"
    return requested if requested in _ALLOWED_REQUESTED_COMPOSERS else LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER


def build_local_product_qa_composer_env(
    base_env: Mapping[str, str] | None = None,
    *,
    requested_composer: str = LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER,
    enable_composer: bool = True,
) -> dict[str, str]:
    """Return a local QA env overlay without mutating process environment.

    The profile is intentionally internal, never ``all``.  By default it opens
    the limited Composer path for local product-quality measurement.  Passing
    ``enable_composer=False`` keeps the source environment untouched so the
    caller can record the fail-closed blocker explicitly.
    """

    env = {str(key): str(value) for key, value in dict(base_env or {}).items()}
    if not enable_composer:
        return env

    requested = _normalize_requested_composer(requested_composer)
    env[_FEATURE_FLAG_ENV_NAME] = "true"
    env[_ROLLOUT_STAGE_ENV_NAME] = LOCAL_PRODUCT_QA_ROLLOUT_STAGE
    env[_DEFAULT_COMPOSER_ENV_NAME] = requested
    return env


def build_local_product_qa_release_probe_input() -> dict[str, Any]:
    """Return a text-free current-input stub used only for rollout gating."""

    return {
        "qa_user": True,
        "emlis_internal": True,
        "source_kind": LOCAL_PRODUCT_QA_PROFILE,
        "scope_status": "eligible",
    }


def _build_blockers(
    *,
    composer_path_open: bool,
    resolution_meta: Mapping[str, Any],
    release_meta: Mapping[str, Any],
) -> list[str]:
    if composer_path_open:
        return []

    reasons = _dedupe(
        list(resolution_meta.get("rejection_reasons") or [])
        + list(release_meta.get("rejection_reasons") or [])
    )
    blockers: list[str] = [COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER]
    if COMPOSER_FEATURE_DISABLED_REASON in reasons:
        blockers.append("composer_feature_flag_disabled_for_product_qa")
    if str(release_meta.get("enabled")) == "False" or release_meta.get("enabled") is False:
        blockers.append("composer_rollout_not_open_for_local_product_qa")
    if "complete_initial_ap0_not_green" in reasons:
        blockers.append("complete_initial_not_ready_for_product_qa")
    if "complete_initial_rollout_not_allowed" in reasons:
        blockers.append("complete_initial_rollout_not_allowed_for_product_qa")
    return _dedupe(blockers)


def assert_product_quality_measurement_runner_bootstrap_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "emlis_ai_product_quality_measurement_runner_bootstrap",
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(value, source=source)


def resolve_local_product_qa_composer_bootstrap(
    *,
    env: Mapping[str, str] | None = None,
    requested_composer: str = LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER,
    enable_composer: bool = True,
    user_id: str = LOCAL_PRODUCT_QA_USER_ID,
    ap0_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the local Product QA Composer path and return meta-only status.

    This is the Phase 1 bootstrap layer for the future measurement runner.  It
    intentionally returns a blocked report when Composer is disabled or the
    requested Composer cannot pass its existing gates.
    """

    qa_env = build_local_product_qa_composer_env(
        env if env is not None else os.environ,
        requested_composer=requested_composer,
        enable_composer=enable_composer,
    )
    release_probe_input = build_local_product_qa_release_probe_input()
    flag_state = default_composer_flag_state(qa_env)
    release_decision = evaluate_limited_composer_release(
        user_id=user_id,
        current_input=release_probe_input,
        limited_observation_scope={"scope_status": "eligible", "coverage_scope": LOCAL_PRODUCT_QA_PROFILE},
        feature_flag_enabled=bool(flag_state.get("enabled")),
        env=qa_env,
    )
    release_meta = release_decision.as_meta()
    resolution = resolve_emlis_ai_composer_client(
        env=qa_env,
        release_allowed=bool(release_decision.enabled),
        release_meta=release_meta,
        ap0_decision=ap0_decision or {},
    )
    resolution_meta = resolution.as_meta()
    path_open = bool(resolution_meta.get("default_client_used"))
    blockers = _build_blockers(
        composer_path_open=path_open,
        resolution_meta=resolution_meta,
        release_meta=release_meta,
    )

    requested = _normalize_requested_composer(requested_composer)
    contract_freeze = build_emlis_ai_product_quality_contract_freeze()
    report: dict[str, Any] = {
        "schema_version": PRODUCT_QUALITY_MEASUREMENT_RUNNER_BOOTSTRAP_VERSION,
        "version": PRODUCT_QUALITY_MEASUREMENT_RUNNER_BOOTSTRAP_VERSION,
        "phase": "Phase1_Local_Product_QA_Composer_Bootstrap",
        "run_profile": LOCAL_PRODUCT_QA_PROFILE,
        "qa_profile": LOCAL_PRODUCT_QA_PROFILE,
        "run_status": "ready" if path_open else "blocked",
        "measurement_can_continue": bool(path_open),
        "composer_generation_path_open": bool(path_open),
        "composer_generation_path_not_open": bool(not path_open),
        "requested_composer": requested,
        "rollout_stage": str(release_meta.get("stage") or ""),
        "rollout_stage_defaulted_to_all": False,
        "complete_initial_default": False,
        "contract_freeze": contract_freeze,
        "composer_resolution": {
            "default_limited_enabled": bool(resolution_meta.get("default_limited_enabled")),
            "resolution_source": str(resolution_meta.get("resolution_source") or resolution_meta.get("source") or ""),
            "composer_model": str(resolution_meta.get("composer_model") or ""),
            "requested_composer": str(resolution_meta.get("requested_composer") or requested),
            "complete_initial_client_used": bool(resolution_meta.get("complete_initial_client_used")),
            "default_client_used": bool(resolution_meta.get("default_client_used")),
            "release_allowed": bool(release_decision.enabled),
            "rollout_stage": str(release_meta.get("stage") or ""),
            "rejection_reasons": _dedupe(resolution_meta.get("rejection_reasons")),
            "qa_profile": LOCAL_PRODUCT_QA_PROFILE,
        },
        "composer_flag_state": {
            "enabled": bool(flag_state.get("enabled")),
            "requested_composer": str(flag_state.get("requested_composer") or requested),
            "canonical_requested_composer": str(flag_state.get("canonical_requested_composer") or ""),
            "matched_name": str(flag_state.get("matched_name") or ""),
            "default_composer_matched_name": str(flag_state.get("default_composer_matched_name") or ""),
            "source_kind": str(flag_state.get("source_kind") or ""),
            "explicitly_configured": bool(flag_state.get("explicitly_configured")),
        },
        "limited_composer_release": {
            "stage": str(release_meta.get("stage") or ""),
            "enabled": bool(release_meta.get("enabled")),
            "cohort": str(release_meta.get("cohort") or ""),
            "reason_code": str(release_meta.get("reason_code") or ""),
            "rejection_reasons": _dedupe(release_meta.get("rejection_reasons")),
            "rollout_allowed": bool(release_meta.get("rollout_allowed")),
            "qa_profile": LOCAL_PRODUCT_QA_PROFILE,
        },
        "blockers": blockers,
        "public_contract": {
            "api_route_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
        },
        "product_gate_ready": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert_product_quality_measurement_runner_bootstrap_meta_only(report)
    return report



# ---------------------------------------------------------------------------
# Phase 3: Product Quality Measurement Runner
# ---------------------------------------------------------------------------


def _source_case_id(case: Mapping[str, Any], index: int, family: str) -> str:
    return _safe_identifier(
        case.get("source_case_id")
        or case.get("case_id")
        or case.get("fixture_id")
        or case.get("id")
        or f"{family}_{index:03d}",
        max_length=96,
        default=f"case_{index:03d}",
    )


def _row_id(case: Mapping[str, Any], index: int, family: str) -> str:
    return _safe_identifier(
        case.get("row_id")
        or case.get("event_id")
        or f"row_{index:03d}_{family}",
        max_length=96,
        default=f"row_{index:03d}",
    )


def _source_type(case: Mapping[str, Any]) -> str:
    source = _safe_identifier(case.get("source_type"), max_length=64, default="fixture_family")
    return source if source in {"fixture_family", "local_jsonl", "manual_internal_case", "regression_fixture"} else "fixture_family"


def _source_revision(case: Mapping[str, Any], default_revision: str) -> str:
    return _safe_identifier(case.get("source_revision") or default_revision, max_length=96, default="")


def _case_current_input(case: Mapping[str, Any]) -> dict[str, Any]:
    current_input = case.get("current_input")
    if isinstance(current_input, Mapping):
        return dict(current_input)
    # Accept legacy direct-current-input case rows for local JSONL/manual callers.
    candidate = {
        key: case.get(key)
        for key in ("id", "created_at", "memo", "memo_action", "emotion_details", "emotions", "category", "is_secret")
        if key in case
    }
    return {key: value for key, value in candidate.items() if value is not None}


def build_product_quality_minimum_fixture_family_cases() -> list[dict[str, Any]]:
    """Return one transient local QA input case for each required family.

    These fixture inputs are only renderer inputs for local measurement.  The
    runner never serializes them into MeasurementRunV1 material.
    """

    return [
        {
            "case_id": "low_information_short_001",
            "family": "low_information_short",
            "current_input": {"id": "pq-low-001", "memo": "疲れた", "memo_action": "", "emotions": ["疲れ"], "category": ["生活"]},
        },
        {
            "case_id": "daily_unpleasant_001",
            "family": "daily_unpleasant",
            "current_input": {"id": "pq-dun-001", "memo": "今日は小さなことでずっと引っかかっていた", "memo_action": "", "emotions": ["不快"], "category": ["日常"]},
        },
        {
            "case_id": "daily_positive_001",
            "family": "daily_positive",
            "current_input": {"id": "pq-dpo-001", "memo": "少しだけ前に進めた感じがした", "memo_action": "", "emotions": ["嬉しい"], "category": ["日常"]},
        },
        {
            "case_id": "self_denial_001",
            "family": "self_denial",
            "current_input": {"id": "pq-sdn-001", "memo": "自分は何をやってもだめだと思ってしまう", "memo_action": "", "emotions": ["自己嫌悪"], "category": ["自分"]},
        },
        {
            "case_id": "uncertainty_001",
            "family": "uncertainty",
            "current_input": {"id": "pq-unc-001", "memo": "何が嫌なのかまだうまく言葉にできない", "memo_action": "", "emotions": ["不安"], "category": ["未整理"]},
        },
        {
            "case_id": "mixed_emotion_001",
            "family": "mixed_emotion",
            "current_input": {"id": "pq-mix-001", "memo": "嬉しいはずなのに、同時に少し怖さもある", "memo_action": "", "emotions": ["嬉しい", "不安"], "category": ["変化"]},
        },
        {
            "case_id": "long_meaning_arc_001",
            "family": "long_meaning_arc",
            "current_input": {"id": "pq-lma-001", "memo": "ここ数日、頑張りたい気持ちと止まりたい気持ちが交互に出ていて、どちらも本音のように感じる", "memo_action": "整理したい", "emotions": ["迷い"], "category": ["意味"]},
        },
        {
            "case_id": "relationship_boundary_001",
            "family": "relationship_boundary",
            "current_input": {"id": "pq-rel-001", "memo": "相手に合わせたい気持ちと、これ以上は無理だと言いたい気持ちがぶつかっている", "memo_action": "距離を考える", "emotions": ["葛藤"], "category": ["関係"]},
        },
        {
            "case_id": "structure_question_001",
            "family": "structure_question",
            "current_input": {"id": "pq-str-001", "memo": "この反応がどこから来ているのか、自分の中の構造を見たい", "memo_action": "構造を知りたい", "emotions": ["関心"], "category": ["自己理解"]},
        },
        {
            "case_id": "positive_only_001",
            "family": "positive_only",
            "current_input": {"id": "pq-pos-001", "memo": "よかった", "memo_action": "", "emotions": ["喜び"], "category": ["日常"]},
        },
        {
            "case_id": "self_understanding_follow_001",
            "family": "self_understanding_follow",
            "current_input": {"id": "pq-suf-001", "memo": "前にも似たように、始める前に急に重くなる感じがあった", "memo_action": "自分の流れを見たい", "emotions": ["気づき"], "category": ["自己理解"]},
        },
        {
            "case_id": "input_self_report_only_failure_001",
            "family": "input_self_report_only_failure",
            "current_input": {"id": "pq-isr-001", "memo": "また同じことを言っているだけかもしれない", "memo_action": "", "emotions": ["停滞"], "category": ["自己理解"]},
        },
    ]


def _build_source_set(cases: Sequence[Mapping[str, Any]], *, fixture_family_revision: str, local_jsonl_name: str = "") -> dict[str, Any]:
    source_types = _dedupe([_source_type(case) for case in cases])
    return {
        "fixture_family_revision": _safe_identifier(fixture_family_revision, max_length=96, default="local"),
        "local_jsonl_name": _safe_identifier(local_jsonl_name, max_length=96, default=""),
        "regression_fixtures_included": any(_source_type(case) == "regression_fixture" for case in cases),
        "source_types": source_types,
        "input_case_count": len(cases),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }


def _measurement_contract_assertions() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_body_included_in_release_material": False,
        "raw_input_included_in_release_material": False,
        "candidate_body_included_in_release_material": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }


def _extract_reply_comment_text(reply: Any) -> str:
    if isinstance(reply, Mapping):
        return str(reply.get("comment_text") or reply.get("commentText") or "").strip()
    return str(getattr(reply, "comment_text", "") or "").strip()


def _extract_reply_meta(reply: Any) -> dict[str, Any]:
    if isinstance(reply, Mapping):
        meta = reply.get("meta") or reply.get("emlis_ai") or {}
        return dict(meta) if isinstance(meta, Mapping) else {}
    meta = getattr(reply, "meta", None)
    return dict(meta) if isinstance(meta, Mapping) else {}


def _case_machine_metrics(case: Mapping[str, Any], reply_meta: Mapping[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if isinstance(reply_meta.get("diagnostic_summary"), Mapping):
        metrics.update(dict(reply_meta.get("diagnostic_summary") or {}))
    if isinstance(reply_meta.get("machine_metrics"), Mapping):
        metrics.update(dict(reply_meta.get("machine_metrics") or {}))
    if isinstance(case.get("machine_metrics"), Mapping):
        metrics.update(dict(case.get("machine_metrics") or {}))
    return metrics


def _build_public_meta_for_reply(*, reply_meta: Mapping[str, Any], comment_text: str, subscription_tier: Any) -> dict[str, Any]:
    return build_public_emlis_input_feedback_meta(
        reply_meta,
        comment_text_present=bool(comment_text.strip()),
        subscription_tier=subscription_tier,
    )


def _event_to_qa_bridge_row(event: Mapping[str, Any]) -> dict[str, Any]:
    """Bridge ProductQualityEventV1 to existing QA material row contracts."""

    assert_product_quality_measurement_event_meta_only(event)
    binding = event.get("binding") if isinstance(event.get("binding"), Mapping) else {}
    reason = event.get("reason_coverage") if isinstance(event.get("reason_coverage"), Mapping) else {}
    surface = event.get("surface_quality") if isinstance(event.get("surface_quality"), Mapping) else {}
    safety = event.get("safety") if isinstance(event.get("safety"), Mapping) else {}
    user_label = event.get("user_label_connection") if isinstance(event.get("user_label_connection"), Mapping) else {}
    public_passed = bool(event.get("public_display_reached"))
    family = normalize_product_quality_family(event.get("family"))
    row = {
        "schema_version": "cocolon.emlis.product_quality.measurement_runner.qa_bridge_row.v1",
        "source_schema_version": event.get("schema_version"),
        "run_id": _safe_identifier(event.get("run_id"), max_length=96, default=""),
        "row_id": _safe_identifier(event.get("row_id"), max_length=96, default=""),
        "candidate_id": _safe_identifier(event.get("row_id"), max_length=96, default=""),
        "family": family,
        "product_readfeel_family": family,
        "coverage_group": family,
        "observation_status": "passed" if public_passed else "unavailable",
        "backend_observation_status": _safe_identifier(event.get("observation_status"), max_length=40, default="unavailable"),
        "public_passed": public_passed,
        "backend_public_passed": public_passed,
        "display_confirmed": public_passed,
        "passed_display_count": 1 if public_passed else 0,
        "expected_display": True,
        "comment_text_present": bool(event.get("comment_text_present")),
        "comment_text_length": _to_int(event.get("comment_text_length")),
        "display_gate_passed": public_passed,
        "binding_required_count": _to_int(binding.get("binding_required_count")),
        "binding_supported_sentence_count": _to_int(binding.get("binding_supported_count")),
        "unsupported_binding_count": _to_int(binding.get("unsupported_binding_count")),
        "binding_passed": bool(binding.get("binding_passed")),
        "reason_required_count": _to_int(reason.get("reason_required_count")),
        "reason_covered_count": _to_int(reason.get("reason_covered_count")),
        "reason_coverage_passed": bool(reason.get("reason_coverage_passed")),
        "template_major_count": _to_int(surface.get("template_major_count")),
        "surface_signature_key": _safe_identifier(surface.get("surface_signature_key"), max_length=128, default=""),
        "surface_signature_id": _safe_identifier(surface.get("surface_signature_key"), max_length=128, default=""),
        "surface_signature_family_key": _safe_identifier(surface.get("surface_signature_key"), max_length=128, default=""),
        "generic_comfort_detected": bool(surface.get("generic_comfort_detected")),
        "mirror_only_detected": bool(surface.get("mirror_only_detected")),
        "unsafe_insight_surface_detected": bool(surface.get("unsafe_insight_surface_detected")),
        "safety_major_count": _to_int(safety.get("safety_major_count")),
        "self_denial_safe_state_answer_used": bool(safety.get("self_denial_safe_state_answer_used")),
        "user_label_connection": {
            "limited_visible_surface_connection_applied": bool(user_label.get("limited_visible_surface_connection_applied")),
            "history_connection_applied": bool(user_label.get("history_connection_applied")),
            "connectable_family": _safe_identifier(user_label.get("connectable_family"), max_length=96, default=""),
            "evidence_record_count": _to_int(user_label.get("evidence_record_count")),
            "existing_surface_gates_passed": bool(user_label.get("existing_surface_gates_passed")),
        },
        "blockers": _dedupe(event.get("blockers")),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(row, source="product_quality_measurement_runner_qa_bridge_row")
    return row


def _summary_machine_metrics(events: Sequence[Mapping[str, Any]], qa_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    event_count = len(events)
    display_count = sum(1 for event in events if event.get("public_display_reached") is True)
    binding_pass_count = sum(1 for event in events if (event.get("binding") or {}).get("binding_passed") is True)
    reason_pass_count = sum(1 for event in events if (event.get("reason_coverage") or {}).get("reason_coverage_passed") is True)
    template_major_count = sum(_to_int((event.get("surface_quality") or {}).get("template_major_count")) for event in events)
    safety_major_count = sum(_to_int((event.get("safety") or {}).get("safety_major_count")) for event in events)
    signatures = [_clean(row.get("surface_signature_key")) for row in qa_rows if _clean(row.get("surface_signature_key"))]
    repeat_count = max(0, len(signatures) - len(set(signatures)))
    return {
        "machine_metrics_ready": bool(events),
        "event_count": event_count,
        "display_reach_rate": _rate(display_count, event_count),
        "binding_pass_rate": _rate(binding_pass_count, event_count),
        "reason_coverage_rate": _rate(reason_pass_count, event_count),
        "template_major_count": template_major_count,
        "safety_major_count": safety_major_count,
        "surface_signature_repeat_count": repeat_count,
        "surface_signature_repeat_rate": _rate(repeat_count, len(signatures)),
        "read_feeling_score": None,
        "read_feeling_source": "blind_qa_required_not_machine_metric",
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }


def _family_counts(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        family = normalize_product_quality_family(event.get("family"))
        counts[family] = counts.get(family, 0) + 1
    return dict(sorted(counts.items()))


def _runtime_blind_qa_coverage_rate(summary: Mapping[str, Any]) -> float:
    reviewable = _to_int(summary.get("reviewable_blind_qa_candidate_count") or summary.get("reviewable_candidate_count"))
    reviewed = _to_int(summary.get("blind_qa_review_count"))
    return _rate(reviewed, reviewable)


def _user_label_qa_coverage_rate(summary: Mapping[str, Any]) -> float:
    reviewable = _to_int(summary.get("reviewable_candidate_count"))
    reviewed = _to_int(summary.get("reviewed_candidate_count"))
    return _rate(reviewed, reviewable)


def _collect_measurement_blockers(
    *,
    events: Sequence[Mapping[str, Any]],
    family_counts: Mapping[str, int],
    machine_metrics: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    user_label_summary: Mapping[str, Any],
    blind_qa_integration: Mapping[str, Any],
    phase11_gate: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_dedupe(bootstrap.get("blockers")))
    if not events:
        blockers.append("phase3_events_missing")
    missing = [family for family in PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES if _to_int(family_counts.get(family)) <= 0]
    if missing:
        blockers.append("required_family_cross_coverage_incomplete")
    if float(machine_metrics.get("display_reach_rate") or 0.0) < PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_DISPLAY_REACH_RATE:
        blockers.append("product_readfeel_display_reach_rate_below_target")
    if events and float(machine_metrics.get("binding_pass_rate") or 0.0) < PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_BINDING_PASS_RATE:
        blockers.append("product_readfeel_binding_pass_rate_below_target")
    if events and float(machine_metrics.get("reason_coverage_rate") or 0.0) < PRODUCT_QUALITY_MEASUREMENT_RUN_TARGET_REASON_COVERAGE_RATE:
        blockers.append("product_readfeel_reason_coverage_below_target")
    if _to_int(machine_metrics.get("template_major_count")) > 0:
        blockers.append("template_major_detected")
    if _to_int(machine_metrics.get("safety_major_count")) > 0:
        blockers.append("safety_major_detected")
    blockers.extend(blocker for event in events for blocker in _dedupe(event.get("blockers")))
    blockers.extend(_dedupe(runtime_summary.get("release_blockers") or runtime_summary.get("step11_release_blockers")))
    blockers.extend(_dedupe(user_label_summary.get("release_blockers") or user_label_summary.get("qa_blockers")))
    blockers.extend(_dedupe(blind_qa_integration.get("release_blockers") or blind_qa_integration.get("qa_blockers")))
    blockers.extend(_dedupe(phase11_gate.get("v1_product_pass_blockers")))
    if phase11_gate.get("product_gate_ready") is True or phase11_gate.get("public_release_applied") is True:
        blockers.append("phase11_attempted_to_set_release_flag")
    return _dedupe(blockers)


def _resolve_local_product_qa_runtime_composer(
    *,
    env: Mapping[str, str] | None,
    requested_composer: str,
    enable_composer: bool,
    user_id: str,
    ap0_decision: Mapping[str, Any] | None,
) -> tuple[Any, dict[str, Any]]:
    bootstrap = resolve_local_product_qa_composer_bootstrap(
        env=env,
        requested_composer=requested_composer,
        enable_composer=enable_composer,
        user_id=user_id,
        ap0_decision=ap0_decision,
    )
    if not bootstrap.get("measurement_can_continue"):
        return None, bootstrap

    qa_env = build_local_product_qa_composer_env(
        env if env is not None else os.environ,
        requested_composer=requested_composer,
        enable_composer=enable_composer,
    )
    release_meta = bootstrap.get("limited_composer_release") if isinstance(bootstrap.get("limited_composer_release"), Mapping) else {}
    resolution = resolve_emlis_ai_composer_client(
        env=qa_env,
        release_allowed=bool((release_meta or {}).get("enabled")),
        release_meta=release_meta,
        ap0_decision=ap0_decision or {},
    )
    return resolution.composer_client, bootstrap


async def _call_product_quality_renderer(
    renderer: Callable[..., Any],
    *,
    user_id: str,
    subscription_tier: Any,
    current_input: Mapping[str, Any],
    display_name: str | None,
    timezone_name: str | None,
    composer_client: Any,
) -> Any:
    rendered = renderer(
        user_id=user_id,
        subscription_tier=subscription_tier,
        current_input=dict(current_input),
        display_name=display_name,
        timezone_name=timezone_name,
        composer_client=composer_client,
    )
    if inspect.isawaitable(rendered):
        return await rendered
    return rendered


def _default_renderer() -> Callable[..., Any]:
    from emlis_ai_reply_service import render_emlis_ai_reply

    return render_emlis_ai_reply


async def run_product_quality_measurement_async(
    *,
    input_cases: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    renderer: Callable[..., Any] | None = None,
    run_id: str | None = None,
    created_at: str | None = None,
    fixture_family_revision: str = "local",
    local_jsonl_name: str = "",
    env: Mapping[str, str] | None = None,
    requested_composer: str = LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER,
    enable_composer: bool = True,
    user_id: str = LOCAL_PRODUCT_QA_USER_ID,
    subscription_tier: Any = "free",
    display_name: str | None = None,
    timezone_name: str | None = None,
    ap0_decision: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | None = None,
    user_label_connection_reviews: Sequence[Mapping[str, Any]] | None = None,
    previous_signature_records: Sequence[Mapping[str, Any]] | None = None,
    require_composer_path_open: bool = True,
) -> dict[str, Any]:
    """Run Phase 3 Product Quality measurement and return meta-only material."""

    run_id_value = _safe_identifier(run_id, max_length=96, default="") or _default_run_id()
    created_at_value = _clean(created_at) or _now_iso()
    cases = list(input_cases) if input_cases is not None else build_product_quality_minimum_fixture_family_cases()

    composer_client, bootstrap = _resolve_local_product_qa_runtime_composer(
        env=env,
        requested_composer=requested_composer,
        enable_composer=enable_composer,
        user_id=user_id,
        ap0_decision=ap0_decision,
    )

    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    active_renderer = renderer or _default_renderer()
    can_measure = bool(bootstrap.get("measurement_can_continue")) or not require_composer_path_open

    if can_measure:
        for index, raw_case in enumerate(cases, start=1):
            case = dict(raw_case or {})
            family = normalize_product_quality_family(case.get("family") or case.get("input_family") or case.get("fixture_family"))
            row_id = _row_id(case, index, family)
            source_case_id = _source_case_id(case, index, family)
            current_input = _case_current_input(case)
            case_subscription_tier = case.get("subscription_tier", subscription_tier)
            case_user_id = _safe_identifier(case.get("user_id"), max_length=96, default="") or user_id
            try:
                reply = await _call_product_quality_renderer(
                    active_renderer,
                    user_id=case_user_id,
                    subscription_tier=case_subscription_tier,
                    current_input=current_input,
                    display_name=case.get("display_name", display_name),
                    timezone_name=case.get("timezone_name", timezone_name),
                    composer_client=case.get("composer_client", composer_client),
                )
                comment_text = _extract_reply_comment_text(reply)
                reply_meta = _extract_reply_meta(reply)
                public_meta = case.get("public_meta") if isinstance(case.get("public_meta"), Mapping) else _build_public_meta_for_reply(
                    reply_meta=reply_meta,
                    comment_text=comment_text,
                    subscription_tier=case_subscription_tier,
                )
                event = normalize_product_quality_event(
                    run_id=run_id_value,
                    row_id=row_id,
                    source_type=_source_type(case),
                    source_case_id=source_case_id,
                    source_revision=_source_revision(case, fixture_family_revision),
                    family=family,
                    reply=reply,
                    comment_text=comment_text,
                    public_meta=public_meta,
                    internal_meta=reply_meta,
                    composer_resolution=bootstrap.get("composer_resolution") if isinstance(bootstrap.get("composer_resolution"), Mapping) else {},
                    machine_metrics=_case_machine_metrics(case, reply_meta),
                    blockers=case.get("blockers") if isinstance(case.get("blockers"), Sequence) and not isinstance(case.get("blockers"), (str, bytes, bytearray)) else None,
                    warnings=case.get("warnings") if isinstance(case.get("warnings"), Sequence) and not isinstance(case.get("warnings"), (str, bytes, bytearray)) else None,
                )
            except Exception as exc:  # noqa: BLE001 - measurement must fail closed per row.
                warnings.append(f"renderer_exception:{type(exc).__name__}")
                event = normalize_product_quality_event(
                    run_id=run_id_value,
                    row_id=row_id,
                    source_type=_source_type(case),
                    source_case_id=source_case_id,
                    source_revision=_source_revision(case, fixture_family_revision),
                    family=family,
                    comment_text="",
                    public_meta={"observation_status": "unavailable"},
                    internal_meta={"observation_status": "unavailable"},
                    composer_resolution=bootstrap.get("composer_resolution") if isinstance(bootstrap.get("composer_resolution"), Mapping) else {},
                    blockers=["renderer_exception", f"renderer_exception_{type(exc).__name__}"],
                    warnings=[f"renderer_exception_class:{type(exc).__name__}"],
                )
            events.append(event)
    else:
        warnings.append("measurement_skipped_because_composer_generation_path_not_open")

    for event in events:
        assert_product_quality_measurement_event_meta_only(event)
    qa_bridge_rows = [_event_to_qa_bridge_row(event) for event in events]
    scorecard_rows = [product_quality_event_to_scorecard_row(event) for event in events]
    machine_metrics = _summary_machine_metrics(events, qa_bridge_rows)
    product_readfeel_scorecard = build_product_readfeel_scorecard(
        events=qa_bridge_rows,
        machine_metrics=machine_metrics,
        run_id=run_id_value,
        blind_qa_reviews=list(blind_qa_reviews or []),
    )
    runtime_candidates = build_runtime_surface_blind_qa_candidates(qa_bridge_rows)
    runtime_summary = build_runtime_surface_blind_qa_long_run_summary(
        events=qa_bridge_rows,
        blind_qa_reviews=list(blind_qa_reviews or []),
        blind_qa_candidates=runtime_candidates,
        previous_signature_records=list(previous_signature_records or []),
        run_id=run_id_value,
    )
    user_label_candidates = build_user_label_connection_product_quality_qa_candidates(qa_bridge_rows)
    user_label_summary = build_user_label_connection_product_quality_qa_summary(
        events=qa_bridge_rows,
        qa_candidates=user_label_candidates,
        blind_qa_reviews=list(user_label_connection_reviews or []),
        run_id=run_id_value,
    )
    blind_qa_integration = build_product_quality_blind_qa_integration(
        run_id=run_id_value,
        runtime_surface_candidates=runtime_candidates,
        runtime_surface_reviews=list(blind_qa_reviews or []),
        runtime_surface_summary=runtime_summary,
        user_label_connection_candidates=user_label_candidates,
        user_label_connection_reviews=list(user_label_connection_reviews or []),
        user_label_connection_summary=user_label_summary,
    )
    assert_product_quality_blind_qa_integration_meta_only(blind_qa_integration)
    phase11_gate = build_product_readfeel_long_run_product_gate(
        events=qa_bridge_rows,
        product_readfeel_scorecard=product_readfeel_scorecard,
        runtime_long_run_summary=runtime_summary,
        blind_qa_aggregate=product_readfeel_scorecard.get("blind_qa_metrics") if isinstance(product_readfeel_scorecard, Mapping) else {},
    )

    family_counts = _family_counts(events)
    missing_required_families = [
        family for family in PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES if _to_int(family_counts.get(family)) <= 0
    ]
    summary_metrics = {
        "display_reach_rate": machine_metrics["display_reach_rate"],
        "binding_pass_rate": machine_metrics["binding_pass_rate"],
        "reason_coverage_rate": machine_metrics["reason_coverage_rate"],
        "runtime_surface_blind_qa_coverage_rate": _runtime_blind_qa_coverage_rate(runtime_summary),
        "user_label_connection_qa_coverage_rate": _user_label_qa_coverage_rate(user_label_summary),
        "blind_qa_integration_ready": bool(blind_qa_integration.get("blind_qa_integration_ready")),
        "runtime_surface_blind_qa_read_feeling_score": (blind_qa_integration.get("runtime_surface") or {}).get("read_feeling_score") if isinstance(blind_qa_integration.get("runtime_surface"), Mapping) else None,
        "user_label_connection_read_feeling_score": (blind_qa_integration.get("user_label_connection") or {}).get("read_feeling_score") if isinstance(blind_qa_integration.get("user_label_connection"), Mapping) else None,
        "template_major_count": machine_metrics["template_major_count"],
        "safety_major_count": machine_metrics["safety_major_count"],
        "surface_signature_repeat_rate": machine_metrics["surface_signature_repeat_rate"],
        "read_feeling_score": None,
        "read_feeling_source": "blind_qa_required_not_machine_metric",
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
    }
    blockers = _collect_measurement_blockers(
        events=events,
        family_counts=family_counts,
        machine_metrics=machine_metrics,
        runtime_summary=runtime_summary,
        user_label_summary=user_label_summary,
        blind_qa_integration=blind_qa_integration,
        phase11_gate=phase11_gate,
        bootstrap=bootstrap,
    )
    blocker_matrix = build_product_quality_blocker_matrix(
        run_id=run_id_value,
        measurement_events=events,
        run_blockers=blockers,
        family_counts=family_counts,
        missing_required_families=missing_required_families,
        product_readfeel_scorecard=product_readfeel_scorecard,
        runtime_surface_blind_qa_long_run_summary=runtime_summary,
        user_label_connection_qa_summary=user_label_summary,
        phase11_long_run_product_gate=phase11_gate,
    )
    assert_product_quality_blocker_matrix_meta_only(blocker_matrix)
    generation_repair_design = build_product_quality_generation_repair_design(
        run_id=run_id_value,
        blocker_matrix=blocker_matrix,
    )
    assert_product_quality_generation_repair_design_meta_only(generation_repair_design)
    pending_run_status = "completed"
    if not can_measure:
        pending_run_status = "blocked"
    elif blockers:
        pending_run_status = "completed_with_blockers"
    release_decision_measurement_context = {
        "schema_version": "cocolon.emlis.product_quality.measurement_run.release_decision_context.v1",
        "run_id": run_id_value,
        "run_status": pending_run_status,
        "event_count": len(events),
        "family_counts": family_counts,
        "required_families": list(PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES),
        "missing_required_families": missing_required_families,
        "summary_metrics": summary_metrics,
        "machine_metrics": machine_metrics,
        "blockers": blockers,
        "contract_assertions": _measurement_contract_assertions(),
        "product_gate_ready": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }
    release_decision = build_product_release_decision(
        run_id=run_id_value,
        measurement_run=release_decision_measurement_context,
        product_readfeel_scorecard=product_readfeel_scorecard,
        phase11_long_run_product_gate=phase11_gate,
        runtime_surface_blind_qa_long_run_summary=runtime_summary,
        user_label_connection_qa_summary=user_label_summary,
        blind_qa_integration=blind_qa_integration,
        composer_resolution_summary=bootstrap,
        blocker_matrix=blocker_matrix,
        run_blockers=blockers,
    )
    assert_product_release_decision_meta_only(release_decision)
    release_decision_summary = {
        "release_allowed": bool(release_decision.get("release_allowed")),
        "release_stage": release_decision.get("release_stage"),
        "release_blocker_count": release_decision.get("release_blocker_count"),
        "required_followup_fix_count": release_decision.get("required_followup_fix_count"),
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    validation_plan = build_product_quality_validation_plan(
        run_id=run_id_value,
        measurement_run=release_decision_measurement_context,
        product_readfeel_scorecard=product_readfeel_scorecard,
        runtime_surface_blind_qa_long_run_summary=runtime_summary,
        user_label_connection_qa_summary=user_label_summary,
        phase11_long_run_product_gate=phase11_gate,
        blocker_matrix=blocker_matrix,
        generation_repair_design=generation_repair_design,
        blind_qa_integration=blind_qa_integration,
        release_decision=release_decision,
        composer_bootstrap=bootstrap,
    )
    assert_product_quality_validation_plan_meta_only(validation_plan)
    validation_plan_summary = validation_plan.get("summary", {}) if isinstance(validation_plan.get("summary"), Mapping) else {}
    run_status = pending_run_status

    run = {
        "schema_version": PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION,
        "version": PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION,
        "phase": PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE,
        "run_id": run_id_value,
        "run_profile": LOCAL_PRODUCT_QA_PROFILE,
        "qa_profile": LOCAL_PRODUCT_QA_PROFILE,
        "created_at": created_at_value,
        "run_status": run_status,
        "measurement_can_continue": bool(can_measure),
        "source_set": _build_source_set(cases, fixture_family_revision=fixture_family_revision, local_jsonl_name=local_jsonl_name),
        "contract_assertions": _measurement_contract_assertions(),
        "contract_freeze": build_emlis_ai_product_quality_contract_freeze(),
        "composer_bootstrap": bootstrap,
        "event_count": len(events),
        "family_counts": family_counts,
        "required_families": list(PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES),
        "missing_required_families": missing_required_families,
        "summary_metrics": summary_metrics,
        "machine_metrics": machine_metrics,
        "measurement_events": events,
        "scorecard_rows": scorecard_rows,
        "product_readfeel_scorecard": product_readfeel_scorecard,
        "runtime_surface_blind_qa_candidates": runtime_candidates,
        "runtime_surface_blind_qa_long_run_summary": runtime_summary,
        "user_label_connection_qa_candidates": user_label_candidates,
        "user_label_connection_qa_summary": user_label_summary,
        "blind_qa_integration": blind_qa_integration,
        "blind_qa_integration_summary": blind_qa_integration.get("summary", {}),
        "blind_qa_integration_ready": bool(blind_qa_integration.get("blind_qa_integration_ready")),
        "blind_qa_review_queue": blind_qa_integration.get("blind_qa_review_queue", []),
        "blind_qa_review_queue_count": blind_qa_integration.get("blind_qa_review_queue_count"),
        "blind_qa_release_blockers": blind_qa_integration.get("release_blockers", []),
        "phase6_blind_qa_review_required": bool(blind_qa_integration.get("blind_qa_required")),
        "phase11_long_run_product_gate": phase11_gate,
        "blocker_matrix": blocker_matrix,
        "blocker_matrix_row_count": blocker_matrix.get("row_count"),
        "blocker_matrix_release_blocking_row_count": blocker_matrix.get("release_blocking_row_count"),
        "blocker_matrix_summary": {
            "row_count": blocker_matrix.get("row_count"),
            "release_blocking_row_count": blocker_matrix.get("release_blocking_row_count"),
            "blocker_group_counts": blocker_matrix.get("blocker_group_counts"),
            "owner_area_counts": blocker_matrix.get("owner_area_counts"),
            "all_release_blockers_have_owner_area_and_repair_policy": blocker_matrix.get("all_release_blockers_have_owner_area_and_repair_policy"),
        },
        "blocker_matrix_rows": blocker_matrix.get("rows", []),
        "repair_work_queue": blocker_matrix.get("repair_work_queue", []),
        "generation_repair_design": generation_repair_design,
        "generation_repair_design_row_count": generation_repair_design.get("summary", {}).get("row_count"),
        "generation_repair_design_summary": generation_repair_design.get("summary", {}),
        "generation_repair_design_rows": generation_repair_design.get("rows", []),
        "generation_repair_work_queue": generation_repair_design.get("generation_repair_work_queue", []),
        "phase5_repair_execution_order": generation_repair_design.get("repair_execution_order", []),
        "phase5_focus_tracks": generation_repair_design.get("phase5_focus_tracks", []),
        "product_release_decision": release_decision,
        "release_decision": release_decision,
        "product_release_decision_summary": release_decision_summary,
        "release_decision_summary": release_decision_summary,
        "release_allowed": bool(release_decision.get("release_allowed")),
        "release_stage": release_decision.get("release_stage"),
        "release_blockers": release_decision.get("release_blockers", []),
        "release_decision_release_blockers": release_decision.get("release_blockers", []),
        "release_decision_required_followup_fixes": release_decision.get("required_followup_fixes", []),
        "phase7_release_decision_ready": bool(release_decision.get("release_allowed")),
        "phase7_release_allowed": bool(release_decision.get("release_allowed")),
        "phase7_release_stage": release_decision.get("release_stage"),
        "phase7_release_blockers": release_decision.get("release_blockers", []),
        "phase7_required_followup_fixes": release_decision.get("required_followup_fixes", []),
        "phase7_release_decision_internal_only": True,
        "phase7_public_response_changed": False,
        "phase7_rn_contract_changed": False,
        "phase7_db_schema_changed": False,
        "validation_plan": validation_plan,
        "product_quality_validation_plan": validation_plan,
        "validation_plan_summary": validation_plan_summary,
        "product_quality_validation_plan_summary": validation_plan_summary,
        "validation_execution_order": validation_plan.get("validation_execution_order", []),
        "validation_steps": validation_plan.get("validation_items", []),
        "validation_required_test_files": validation_plan.get("required_test_files", []),
        "validation_acceptance_criteria": validation_plan.get("acceptance_criteria", []),
        "validation_blockers": validation_plan.get("validation_blockers", []),
        "phase8_validation_plan_ready": bool(validation_plan.get("validation_plan_ready")),
        "phase8_validation_status": validation_plan.get("validation_status"),
        "phase8_validation_execution_required": bool(validation_plan.get("validation_execution_required")),
        "phase8_validation_passed": bool(validation_plan.get("validation_passed")),
        "phase8_release_allowed_by_validation_plan": bool(validation_plan.get("release_allowed_by_validation_plan")),
        "phase8_public_response_changed": False,
        "phase8_rn_contract_changed": False,
        "phase8_db_schema_changed": False,
        "release_decision_applied": False,
        "release_rollout_applied": False,
        "rollout_config_changed": False,
        "rollout_stage_mutated": False,
        "all_rollout_applied": False,
        "blockers": blockers,
        "warnings": _dedupe(warnings),
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    assert_product_quality_measurement_run_meta_only(run)
    return run


def run_product_quality_measurement(**kwargs: Any) -> dict[str, Any]:
    """Synchronous wrapper for tests/tools that are not already in an event loop."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_product_quality_measurement_async(**kwargs))
    raise RuntimeError("run_product_quality_measurement_async must be awaited inside an active event loop")


def assert_product_quality_measurement_run_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "emlis_ai_product_quality_measurement_run",
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if value.get("schema_version") != PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid schema_version")
    if value.get("product_gate_ready") is not False:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if value.get("public_release_applied") is not False:
        raise ValueError(f"{source} must keep public_release_applied false")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(value, source=source)


def dump_product_quality_measurement_run(run: Mapping[str, Any]) -> str:
    assert_product_quality_measurement_run_meta_only(run)
    return json.dumps(run, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def dump_local_product_qa_composer_bootstrap(report: Mapping[str, Any] | None = None) -> str:
    data = dict(report or resolve_local_product_qa_composer_bootstrap(env={}, enable_composer=False))
    assert_product_quality_measurement_runner_bootstrap_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "COMPOSER_FEATURE_DISABLED_REASON",
    "COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER",
    "LOCAL_PRODUCT_QA_DEFAULT_REQUESTED_COMPOSER",
    "LOCAL_PRODUCT_QA_PROFILE",
    "LOCAL_PRODUCT_QA_ROLLOUT_STAGE",
    "PRODUCT_QUALITY_MEASUREMENT_RUNNER_BOOTSTRAP_VERSION",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE5_CONNECTION",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE6_CONNECTION",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE7_CONNECTION",
    "PRODUCT_QUALITY_MEASUREMENT_RUN_PHASE8_CONNECTION",
    "PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES",
    "build_product_quality_blocker_matrix",
    "build_product_quality_generation_repair_design",
    "build_product_quality_blind_qa_integration",
    "build_product_quality_validation_plan",
    "assert_product_quality_measurement_runner_bootstrap_meta_only",
    "assert_product_quality_measurement_run_meta_only",
    "build_local_product_qa_composer_env",
    "build_local_product_qa_release_probe_input",
    "build_product_quality_minimum_fixture_family_cases",
    "dump_local_product_qa_composer_bootstrap",
    "dump_product_quality_measurement_run",
    "resolve_local_product_qa_composer_bootstrap",
    "run_product_quality_measurement",
    "run_product_quality_measurement_async",
]
