# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the local-only, body-full Gate 0 R0 baseline artifact.

This helper is test-only.  Its output must remain local and must never be
copied into public metadata or a runtime response.
"""

import asyncio
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

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
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
from emlis_ai_reply_service import render_emlis_ai_reply


BACKEND_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = BACKEND_ROOT / "ai" / "tests" / "local_only" / "emlis_gate0_r0_baseline_20260711.json"
SOURCE_ARCHIVE_SHA256 = "8cdcd9036db92596bd1a1ce47141f3c1af809e957ebe5e6352684413e94d8015"
SOURCE_ARCHIVE_REF = "mashos-api(204).zip"
CANONICAL_SOURCE_SHA256 = {
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py": "4d082b70362b6b36dfa73fcf2fab758f1041432e0ed4736026c497a67d1d49b8",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py": "a4f77c1be5a6228e28fac68ce42a4a70da476e6fda66dc16c977bd8bd4dd36c7",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py": "2ea65ca124b6bcc1879388d8a97cdfb35f6390a8b907386d34361944b6473551",
    "ai/services/ai_inference/emlis_ai_reply_service.py": "1eb3d7b65c72c6c7ba5aee44c2138ae6e7ea38b20228f16821f1a5d2e17ef80c",
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _file_sha256(relative_path: str) -> str:
    return _sha256_bytes((BACKEND_ROOT / relative_path).read_bytes())


def _assert_r0_source_snapshot() -> None:
    actual = {
        path: _file_sha256(path)
        for path in CANONICAL_SOURCE_SHA256
    }
    if actual != CANONICAL_SOURCE_SHA256:
        raise RuntimeError(
            "Gate 0 R0 source drifted; refusing to overwrite the pre-repair baseline"
        )


async def _build_case(case: Any) -> dict[str, Any]:
    current_input = case.as_current_input()
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    reply = await render_emlis_ai_reply(
        user_id="gate0-r0-local-baseline",
        subscription_tier="free",
        current_input=current_input,
    )
    grounded_meta = dict(reply.meta.get("grounded_observation") or {})
    return {
        "case_id": case.case_id,
        "normalized_current_input_sha256": _sha256_bytes(_canonical_json(normalized).encode("utf-8")),
        "normalized_current_input": normalized,
        "current_comment_text": reply.comment_text,
        "current_comment_text_sha256": _sha256_bytes(reply.comment_text.encode("utf-8")),
        "current_body_free_grounded_meta": grounded_meta,
        "current_plan_body_free_debug": plan.as_body_free_meta(),
        "current_sentence_plan_body_free_debug": sentence_plan.as_body_free_meta(),
        "current_surface_body_free_debug": {
            key: value
            for key, value in asdict(surface).items()
            if key not in {"text", "lines"}
        },
    }


async def _main() -> None:
    _assert_r0_source_snapshot()
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    payload = {
        "schema_version": "cocolon.emlis.gate0.r0.local_bodyfull_baseline.v1",
        "artifact_scope": "local_only_body_full_do_not_copy_to_public_meta",
        "source_snapshot": {
            "archive_ref": SOURCE_ARCHIVE_REF,
            "archive_sha256": SOURCE_ARCHIVE_SHA256,
            "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        },
        "execution_contract": {
            "subscription_tier": "free",
            "history": "none",
            "context_mock": "none",
            "case_source_of_truth": [
                "ai/tests/helpers/emlis_ai_grounded_observation_i0_inventory.py",
                "ai/tests/helpers/emlis_ai_grounded_observation_i6_cases.py",
            ],
            "case_count": len(cases),
        },
        "cases": [await _build_case(case) for case in cases],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(_main())
