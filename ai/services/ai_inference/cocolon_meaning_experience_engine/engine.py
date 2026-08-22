# -*- coding: utf-8 -*-
from __future__ import annotations

"""Public exact-one orchestration entry for the disabled CMEE candidate."""

from .contracts import (
    CMEE_TERMINAL_GENERATED_DISABLED,
    CoreId,
    EngineOutcome,
    EngineStatus,
    ExecutionMode,
    GenerationRequest,
    ProductJob,
)
from .emlis_v1a import CMEEVerticalError, build_text_grounded_limited_artifact
from .source_kernel import SourceAdmissionError, freeze_text_source


class MeaningExperienceEngine:
    """Run the first source-to-experience CMEE vertical without fallback.

    The callable is deliberately disconnected from API and production routing.
    It accepts only the Emlis offline-candidate job. A narrowly supported input
    can produce a private implementation-proof artifact, but this WIP is not a
    Route-B-complete or Product-Read-eligible candidate.
    """

    def generate(self, request: GenerationRequest) -> EngineOutcome:
        if not isinstance(request, GenerationRequest):
            return self._rejected("generation_request_type_mismatch")
        if request.core_id != CoreId.EMLIS_AI.value:
            return self._rejected("core_id_out_of_scope")
        if request.product_job != ProductJob.OBSERVE_AND_CLARIFY.value:
            return self._rejected("product_job_out_of_scope")
        if request.execution_mode != ExecutionMode.OFFLINE_CANDIDATE.value:
            return self._rejected("execution_mode_out_of_scope")
        if not str(request.request_id or "").strip():
            return self._rejected("request_id_required")

        try:
            source = freeze_text_source(request)
        except SourceAdmissionError as exc:
            return EngineOutcome(
                status=EngineStatus.REJECTED if exc.hard_invalid else EngineStatus.UNAVAILABLE,
                reason_codes=(exc.reason_code,),
                terminal_state=(
                    "CMEE_V1A_I1SX_SOURCE_ADMISSION_REJECTED_STOP"
                    if exc.hard_invalid
                    else "CMEE_V1A_I1SX_TEXT_GROUNDED_INPUT_UNAVAILABLE_STOP"
                ),
                automatic_progression=False,
            )
        except Exception:
            # Source adapters handle private input. Never expose their
            # unexpected exception text, and never continue with a partial
            # envelope.
            return EngineOutcome(
                status=EngineStatus.REJECTED,
                reason_codes=("source_admission_internal_failure",),
                terminal_state="CMEE_V1A_I1SX_SOURCE_ADMISSION_REJECTED_STOP",
                automatic_progression=False,
            )

        try:
            graph, _plan, artifact = build_text_grounded_limited_artifact(source)
        except CMEEVerticalError as exc:
            separate_safety = exc.reason_code == "separate_safety_owner_required"
            return EngineOutcome(
                status=(
                    EngineStatus.SEPARATE_SAFETY
                    if separate_safety
                    else EngineStatus.UNAVAILABLE
                ),
                reason_codes=(exc.reason_code,),
                source_envelope=source.envelope,
                artifact=None,
                terminal_state=(
                    "CMEE_V1A_I1SX_SEPARATE_SAFETY_OWNER_STOP"
                    if separate_safety
                    else "CMEE_V1A_I1SX_TEXT_GROUNDED_REALIZATION_UNAVAILABLE_STOP"
                ),
                automatic_progression=False,
            )
        except Exception:
            # Never expose an exception string: upstream exceptions can include
            # private source material. There is no fallback or retry.
            return EngineOutcome(
                status=EngineStatus.UNAVAILABLE,
                reason_codes=("cmee_vertical_internal_failure",),
                source_envelope=source.envelope,
                artifact=None,
                terminal_state="CMEE_V1A_I1SX_TEXT_GROUNDED_REALIZATION_UNAVAILABLE_STOP",
                automatic_progression=False,
            )

        material_unknown_visible = bool(artifact.visible_unknowns)
        status = (
            EngineStatus.LIMITED
            if material_unknown_visible
            else EngineStatus.GENERATED
        )
        reason_code = (
            "text_grounded_source_explicit_limited"
            if material_unknown_visible
            else "text_grounded_source_explicit_generated"
        )
        return EngineOutcome(
            status=status,
            reason_codes=(reason_code,),
            source_envelope=source.envelope,
            meaning_graph=graph,
            artifact=artifact,
            terminal_state=CMEE_TERMINAL_GENERATED_DISABLED,
            automatic_progression=False,
        )

    @staticmethod
    def _rejected(reason_code: str) -> EngineOutcome:
        return EngineOutcome(
            status=EngineStatus.REJECTED,
            reason_codes=(reason_code,),
            terminal_state="CMEE_V1A_I1SX_REQUEST_REJECTED_STOP",
            automatic_progression=False,
        )


__all__ = ["MeaningExperienceEngine"]
