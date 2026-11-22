# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine import (
    CMEE_TERMINAL_GENERATED_DISABLED,
    GenerationRequest,
    MeaningExperienceEngine,
)
import cocolon_meaning_experience_engine.contracts as contracts
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response
import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a


def _request(record_id: str = "cmee-active-v2") -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-09-01T00:00:00Z",
        "memo": "仕事が続いて疲れていて、朝から何も手につかない。",
        "memo_action": "",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-{record_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=record_id,
    )


class CMEEActiveStage1V2RouteTest(unittest.TestCase):
    def test_active_contract_aliases_move_together_to_v2(self) -> None:
        self.assertEqual(
            contracts.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            contracts.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        )
        self.assertEqual(
            contracts.CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
            contracts.CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2,
        )
        self.assertEqual(
            contracts.CMEE_STAGE1_EMLIS_OWNER_REF,
            contracts.CMEE_STAGE1_EMLIS_OWNER_REF_V2,
        )

    def test_public_facade_uses_only_v2_compiler_and_final_plan(self) -> None:
        original_v2_compiler = emlis_v1a.compile_stage1_response
        original_final_plan_builder = (
            emlis_v1a.build_final_stage1_grounded_observation_plan
        )
        compiled: list[tuple[object, object]] = []

        def compile_v2(**kwargs):
            result = original_v2_compiler(**kwargs)
            compiled.append(result)
            return result

        with (
            patch.object(
                emlis_v1a,
                "compile_stage1_response",
                side_effect=compile_v2,
            ) as active_v2_compiler,
            patch.object(
                emlis_v1a,
                "build_final_stage1_grounded_observation_plan",
                wraps=original_final_plan_builder,
            ) as final_plan_builder,
            patch.object(
                stage1_response,
                "_compile_stage1_response_v2_candidate",
                side_effect=AssertionError("compatibility compiler reached"),
            ) as compatibility_compiler,
            patch.object(
                stage1_response,
                "_compile_stage1_response_v1_legacy",
                side_effect=AssertionError("legacy v1 compiler reached"),
            ) as legacy_v1_compiler,
            patch.object(
                emlis_v1a,
                "build_grounded_observation_plan",
                side_effect=AssertionError("legacy v1 plan reached"),
            ) as legacy_v1_plan,
            patch.object(
                emlis_v1a,
                "_cmee_nucleus_observation_text",
                side_effect=AssertionError("legacy v1 observation reached"),
            ) as legacy_v1_observation,
            patch.object(
                emlis_v1a,
                "_cmee_relation_observation_text",
                side_effect=AssertionError("legacy v1 relation reached"),
            ) as legacy_v1_relation,
            patch.object(
                emlis_v1a,
                "_cmee_stage1_reception_text",
                side_effect=AssertionError("legacy v1 reception reached"),
            ) as legacy_v1_reception,
            patch.object(
                emlis_v1a,
                "realize_grounded_human_reception",
                side_effect=AssertionError("legacy v1 reception realizer reached"),
            ) as legacy_v1_reception_realizer,
        ):
            outcome = MeaningExperienceEngine().generate(_request())

        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        # Generation compiles once; positive-trace validation deterministically
        # replays that same route instead of accepting a second implementation.
        self.assertEqual(active_v2_compiler.call_count, 2)
        self.assertEqual(final_plan_builder.call_count, 2)
        self.assertEqual(compiled[0], compiled[1])
        for legacy in (
            compatibility_compiler,
            legacy_v1_compiler,
            legacy_v1_plan,
            legacy_v1_observation,
            legacy_v1_relation,
            legacy_v1_reception,
            legacy_v1_reception_realizer,
        ):
            self.assertEqual(legacy.call_count, 0)

        projection, units = compiled[0]
        self.assertEqual(
            projection.schema_version,
            contracts.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        )
        self.assertTrue(units)
        artifact = outcome.artifact
        graph = outcome.meaning_graph
        assert artifact is not None and graph is not None
        self.assertEqual(
            artifact.realizer_contract_ids,
            emlis_v1a._stage1_runtime_contract(
                contracts.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            )[2],
        )
        self.assertEqual(
            artifact.trust_policy_ids,
            emlis_v1a._stage1_trust_policy_ids(
                contracts.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            ),
        )
        positive_extensions = tuple(
            row.emlis_stage1_extension
            for row in artifact.trace
            if row.role in {"OBSERVATION", "RECEPTION"}
        )
        self.assertTrue(positive_extensions)
        self.assertTrue(
            all(
                extension is not None
                and extension.schema_version
                == contracts.CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2
                and extension.owner_ref
                == contracts.CMEE_STAGE1_EMLIS_OWNER_REF_V2
                and extension.user_fact_effect == 0
                and extension.covered_duty_refs
                and extension.composition_candidate_ref
                and extension.composition_layout_ref
                and extension.selected_stage1_artifact_ref
                for extension in positive_extensions
            )
        )
        contracts.validate_stage1_trace_spine(
            artifact.trace,
            projection,
            grounded_graph=graph,
            parent_plan=artifact.plan,
        )
        self.assertEqual(outcome.terminal_state, CMEE_TERMINAL_GENERATED_DISABLED)
        self.assertFalse(outcome.automatic_progression)

    def test_v2_compiler_failure_is_terminal_without_v1_fallback(self) -> None:
        with (
            patch.object(
                emlis_v1a,
                "compile_stage1_response",
                side_effect=contracts.CMEEStage1ContractError(
                    "stage1_no_hard_valid_realization"
                ),
            ) as active_v2_compiler,
            patch.object(
                stage1_response,
                "_compile_stage1_response_v2_candidate",
                side_effect=AssertionError("compatibility fallback reached"),
            ) as compatibility_compiler,
            patch.object(
                stage1_response,
                "_compile_stage1_response_v1_legacy",
                side_effect=AssertionError("legacy v1 fallback reached"),
            ) as legacy_v1_compiler,
            patch.object(
                emlis_v1a,
                "_canonical_r4_observation_lines",
                side_effect=AssertionError("legacy observation fallback reached"),
            ) as legacy_observation,
            patch.object(
                emlis_v1a,
                "_canonical_r4_tail_lines",
                side_effect=AssertionError("legacy tail fallback reached"),
            ) as legacy_tail,
        ):
            outcome = MeaningExperienceEngine().generate(
                _request("cmee-active-v2-failure")
            )

        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertEqual(
            outcome.reason_codes,
            ("stage1_no_hard_valid_realization",),
        )
        self.assertIsNone(outcome.artifact)
        self.assertEqual(active_v2_compiler.call_count, 1)
        self.assertEqual(compatibility_compiler.call_count, 0)
        self.assertEqual(legacy_v1_compiler.call_count, 0)
        self.assertEqual(legacy_observation.call_count, 0)
        self.assertEqual(legacy_tail.call_count, 0)


if __name__ == "__main__":
    unittest.main()
