# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import socket
import unittest
from unittest.mock import patch

from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
)
from emlis_ai_product_readfeel_rubric import (
    assert_product_readfeel_rubric_meta_only,
    build_product_readfeel_rubric,
)
from tests.fixtures.emlis_ai_product_readfeel_fixture_families import (
    assert_product_readfeel_fixture_family_meta_only,
    build_product_readfeel_fixture_family_registry,
)
from tools.cmee_v1a_i1sx_candidate_run import (
    EXACT8,
    PRODUCT_READ_AXES,
    _materialize_im07_formal_case,
)


_HUMAN_AXES = frozenset(
    {
        "IMMEDIATE_OBSERVATION_FEELS_READ",
        "NATURAL_NON_REPETITIVE_SURFACE",
    }
)
_HUMAN_PENDING = ("HUMAN_REVIEW_REQUIRED", "PENDING")
_FAILURE_ASSETS = tuple(
    Path(__file__).parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / f"cycle001_product_read_failure_rc{release}.json"
    for release in ("0020", "0021", "0025", "0026")
)


class CMEEHistoricalFailureAxisReceiptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assets = tuple(
            json.loads(path.read_text(encoding="utf-8"))
            for path in _FAILURE_ASSETS
        )
        cls.historical_assets = assets
        cls.historical_axes = frozenset(
            axis
            for asset in assets
            for axis in asset["failure_axis_codes"]
        )
        cls.human_status = {
            axis: _HUMAN_PENDING
            for axis in cls.historical_axes & _HUMAN_AXES
        }
        cls.network_attempts: list[object] = []

        def deny_network(*args: object, **_kwargs: object) -> None:
            cls.network_attempts.append(args)
            raise AssertionError("exact8 receipt must not use network")

        cls.body_free_cases = []
        with patch.object(socket, "create_connection", side_effect=deny_network):
            for case_id, memo, category, emotion, strength in EXACT8:
                _private, body_free = _materialize_im07_formal_case(
                    case_id=case_id,
                    memo=memo,
                    category=category,
                    emotion=emotion,
                    strength=strength,
                )
                cls.body_free_cases.append(body_free)

    def test_historical_union_and_existing_formal_receipts_stay_body_free(self) -> None:
        self.assertTrue(all(asset.is_file() for asset in _FAILURE_ASSETS))
        self.assertTrue(self.historical_axes <= set(PRODUCT_READ_AXES))
        self.assertTrue(self.historical_axes - _HUMAN_AXES)
        for asset in self.historical_assets:
            self.assertIs(asset["body_free"], True)
            assert_product_readfeel_fixture_family_meta_only(asset)
            assert_product_readfeel_rubric_meta_only(asset)
        self.assertEqual(len(self.body_free_cases), len(EXACT8))
        self.assertTrue(
            all(
                case["formal_trace_valid"]
                and case["machine_invariant_clear"]
                and case["failure_class"] is None
                for case in self.body_free_cases
            )
        )
        for case in self.body_free_cases:
            assert_product_readfeel_fixture_family_meta_only(case)
            assert_product_readfeel_rubric_meta_only(case)
        serialized = json.dumps(self.body_free_cases, ensure_ascii=False)
        self.assertIsNone(re.search(r"[ぁ-んァ-ヶ一-龯]", serialized))

    def test_readfeel_axes_and_p3_exact12_remain_human_pending(self) -> None:
        self.assertEqual(set(self.human_status), _HUMAN_AXES)
        self.assertTrue(
            all(status == _HUMAN_PENDING for status in self.human_status.values())
        )
        registry = build_product_readfeel_fixture_family_registry()
        rubric = build_product_readfeel_rubric()
        assert_product_readfeel_fixture_family_meta_only(registry)
        assert_product_readfeel_rubric_meta_only(rubric)
        families = tuple(registry["required_families"])
        family_status = {family: _HUMAN_PENDING for family in families}
        self.assertEqual(families, PRODUCT_READFEEL_REQUIRED_FAMILIES)
        self.assertEqual(len(family_status), 12)
        self.assertTrue(
            all(status == _HUMAN_PENDING for status in family_status.values())
        )
        self.assertTrue(rubric["read_feeling_requires_blind_qa"])
        self.assertFalse(rubric["machine_metrics_used_for_read_feeling"])
        self.assertFalse(rubric["read_feeling_auto_filled_from_machine_metrics"])

    def test_receipt_path_has_zero_network_or_external_ai_dependency(self) -> None:
        self.assertEqual(self.network_attempts, [])
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            str(node.module).split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertTrue(
            imports.isdisjoint({"anthropic", "cohere", "google", "openai"})
        )
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertTrue(all(memo not in source for _, memo, *_ in EXACT8))


if __name__ == "__main__":
    unittest.main()
