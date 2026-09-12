# -*- coding: utf-8 -*-
from __future__ import annotations

"""CMEE offline candidate and admitted Emlis application thread entry."""

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

    Public application execution requires an admitted Emlis thread. The
    existing single-input candidate remains offline-only; route enablement
    belongs to the application config, not this pure meaning engine.
    """

    def generate(self, request: GenerationRequest) -> EngineOutcome:
        if not isinstance(request, GenerationRequest):
            return self._rejected("generation_request_type_mismatch")
        if request.core_id != CoreId.EMLIS_AI.value:
            return self._rejected("core_id_out_of_scope")
        if request.product_job != ProductJob.OBSERVE_AND_CLARIFY.value:
            return self._rejected("product_job_out_of_scope")
        if not self._mode_admitted(request):
            return self._rejected("execution_mode_out_of_scope")
        if not str(request.request_id or "").strip():
            return self._rejected("request_id_required")

        if request.emlis_thread is not None:
            from .emlis_thread_engine import generate_emlis_thread
            return generate_emlis_thread(self, request)

        return self._generate_original_body(request)

    def _generate_original_body(self, request: GenerationRequest) -> EngineOutcome:
        """Shared original-source body after public or thread admission."""
        try:
            source = freeze_text_source(request)
        except SourceAdmissionError as exc:
            return EngineOutcome(
                execution_mode=request.execution_mode,
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
                execution_mode=request.execution_mode,
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
                execution_mode=request.execution_mode,
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
                execution_mode=request.execution_mode,
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
                execution_mode=request.execution_mode,            status=status,
            reason_codes=(reason_code,),
            source_envelope=source.envelope,
            meaning_graph=graph,
            artifact=artifact,
            terminal_state=CMEE_TERMINAL_GENERATED_DISABLED,
            automatic_progression=False,
        )

    @staticmethod
    def _mode_admitted(request):
        return (request.execution_mode == ExecutionMode.OFFLINE_CANDIDATE.value
                or request.execution_mode == ExecutionMode.EMLIS_APPLICATION.value
                and request.emlis_thread is not None)

    @staticmethod
    def _rejected(reason_code: str) -> EngineOutcome:
        return EngineOutcome(
            status=EngineStatus.REJECTED,
            reason_codes=(reason_code,),
            terminal_state="CMEE_V1A_I1SX_REQUEST_REJECTED_STOP",
            automatic_progression=False,
        )

    def prepare_emlis_update(self, request: GenerationRequest):
        """Pure Emlis meaning checkpoint, before body generation or issuance."""
        if (type(request) is not GenerationRequest
                or request.core_id != CoreId.EMLIS_AI.value
                or request.product_job != ProductJob.OBSERVE_AND_CLARIFY.value
                or not self._mode_admitted(request)
                or not str(request.request_id or "").strip()):
            raise ValueError("emlis_update_request_out_of_scope")
        from .emlis_answer_update import prepare_emlis_meaning
        return prepare_emlis_meaning(request).checkpoint


__all__ = ["MeaningExperienceEngine"]
