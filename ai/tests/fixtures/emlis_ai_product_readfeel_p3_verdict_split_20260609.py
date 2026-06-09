# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-4 fixture connector for Product Read Feel verdict split.

This fixture binds the P3-3 body-free inventory connection to the P3-4 verdict
split service. It intentionally keeps local review packet bodies out of the
P3-4 material and exposes only verdict rows, counts, blockers, and body-free
summary data.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p3_verdict_split import (
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609,
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
    assert_product_readfeel_p3_verdict_split_meta_only_20260609,
    build_product_readfeel_p3_verdict_split_20260609,
    build_product_readfeel_p3_verdict_split_public_summary_20260609,
    dump_product_readfeel_p3_verdict_split_public_summary_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_inventory_connection_20260609 import (
    build_product_readfeel_p3_inventory_connection_20260609,
)


def build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
    *,
    connection: Mapping[str, Any] | None = None,
    sanitized_current_output_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    sanitized_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    capture: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if connection is None:
        connection = build_product_readfeel_p3_inventory_connection_20260609(
            sanitized_current_output_events=sanitized_current_output_events,
            sanitized_events=sanitized_events,
            capture=capture,
            renderer=renderer,
            run_id=run_id,
        )
    split = build_product_readfeel_p3_verdict_split_20260609(
        source=connection,
        current_output_inventory=connection.get("current_output_inventory"),
        run_id=run_id or str(connection.get("run_id") or "p3_4_verdict_split_fixture"),
    )
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(split)
    return split


def build_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609(
    *,
    connection: Mapping[str, Any] | None = None,
    sanitized_current_output_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    sanitized_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    capture: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        connection=connection,
        sanitized_current_output_events=sanitized_current_output_events,
        sanitized_events=sanitized_events,
        capture=capture,
        renderer=renderer,
        run_id=run_id,
    )
    return build_product_readfeel_p3_verdict_split_public_summary_20260609(split)


def dump_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609(
    *,
    connection: Mapping[str, Any] | None = None,
    sanitized_current_output_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    sanitized_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    capture: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609(
        connection=connection,
        sanitized_current_output_events=sanitized_current_output_events,
        sanitized_events=sanitized_events,
        capture=capture,
        renderer=renderer,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609",
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609",
    "assert_product_readfeel_p3_verdict_split_meta_only_20260609",
    "build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609",
    "build_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609",
    "dump_product_readfeel_p3_verdict_split_public_summary_20260609",
    "dump_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609",
]
