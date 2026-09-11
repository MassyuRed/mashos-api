from __future__ import annotations

"""Q1 process-local orchestration. No database, budget writes, or retries."""

from dataclasses import replace

from .contracts import EngineStatus
from .emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from .emlis_question import question_candidate
from .emlis_thread_contracts import EmlisThreadOutcomeV1, EmlisQuestionDecisionV1
from .emlis_thread_surface import realize_emlis_thread_body
from .source_kernel import SourceAdmissionError


def generate_emlis_thread(engine, request) -> EmlisThreadOutcomeV1:
    end = EmlisQuestionDecisionV1("END", decision_reason="free_round_complete")
    try:
        prepared = prepare_emlis_meaning(request)
    except (SourceAdmissionError, ValueError) as exc:
        # All lower-level admission errors are fixed codes, never exception
        # text from arbitrary parsers or private source-bearing objects.
        code = getattr(exc, "reason_code", "emlis_meaning_preparation_unavailable")
        safety = str(exc) == "separate_safety_owner_required"
        return EmlisThreadOutcomeV1(EngineStatus.SEPARATE_SAFETY if safety else EngineStatus.REJECTED,
            None, EmlisQuestionDecisionV1("BLOCKED", decision_reason="source_or_meaning_not_admitted"),
            reason_codes=("separate_safety_owner_required" if safety else code,))
    except Exception:
        return EmlisThreadOutcomeV1(EngineStatus.UNAVAILABLE, None,
            EmlisQuestionDecisionV1("BLOCKED", decision_reason="meaning_read_failed"),
            reason_codes=("emlis_meaning_preparation_unavailable",))
    checkpoint = prepared.checkpoint
    if not prepared.thread.answers:
        if request.emlis_thread.capability_snapshot.startswith("Q3_"):
            try:
                body = realize_emlis_thread_body(prepared)
            except Exception:
                return EmlisThreadOutcomeV1(EngineStatus.UNAVAILABLE, None,
                    EmlisQuestionDecisionV1("BLOCKED", decision_reason="prequestion_body_unavailable"),
                    meaning_checkpoint=checkpoint, reason_codes=("emlis_q3_initial_body_unavailable",))
        else:
            body = engine.generate(replace(request, emlis_thread=None))
        if body.artifact is None:
            return EmlisThreadOutcomeV1(body.status, None,
                EmlisQuestionDecisionV1("BLOCKED", decision_reason="prequestion_body_unavailable"),
                meaning_checkpoint=checkpoint, reason_codes=body.reason_codes)
        sufficiency = "LIMITED" if body.status is EngineStatus.LIMITED else "SUFFICIENT"
        try:
            decision, question = question_candidate(prepared.thread, prepared.original_plan,
                                                     parent_request_id=request.request_id)
        except Exception:
            decision, question = EmlisQuestionDecisionV1("END", decision_reason="question_realization_unavailable"), None
        return EmlisThreadOutcomeV1(EngineStatus.QUESTION_PENDING if question else body.status,
            body, decision, question, checkpoint, sufficiency, "PRE_QUESTION" if question else "FINAL",
            ("emlis_question_candidate_ready" if question else decision.decision_reason,))
    if request.emlis_thread.prepared_meaning_checkpoint_ref is None:
        return EmlisThreadOutcomeV1(EngineStatus.REJECTED, None, end,
            meaning_checkpoint=checkpoint, reason_codes=("emlis_checkpoint_reference_required",))
    update = checkpoint.answer_update
    if update.disposition == "UNRESOLVED":
        return EmlisThreadOutcomeV1(EngineStatus.UNAVAILABLE, None, end,
            meaning_checkpoint=checkpoint, body_state="ANSWER_UNREFLECTED",
            reason_codes=tuple(dict.fromkeys(row.reason_code for row in checkpoint.unresolved_parts)))
    if update.disposition == "NO_MATERIAL_UPDATE":
        if request.emlis_thread.capability_snapshot.startswith("Q3_"):
            return EmlisThreadOutcomeV1(EngineStatus.GENERATED, None, end,
                meaning_checkpoint=checkpoint, body_state="UNCHANGED",
                reason_codes=("reuse_saved_observation_required",))
        body = engine.generate(replace(request, emlis_thread=None))
        return EmlisThreadOutcomeV1(body.status, body if body.artifact else None, end,
            meaning_checkpoint=checkpoint,
            body_sufficiency="LIMITED" if body.status is EngineStatus.LIMITED else "SUFFICIENT" if body.artifact else None,
            body_state="UNCHANGED" if body.artifact else "UNAVAILABLE",
            reason_codes=("assessed_no_material_update",))
    try:
        body = realize_emlis_thread_body(prepared)
    except Exception:
        # R1: the independently validated checkpoint survives every body
        # failure. There is no return of an old artifact as current meaning.
        return EmlisThreadOutcomeV1(EngineStatus.UNAVAILABLE, None, end,
            meaning_checkpoint=checkpoint, body_state="MEANING_UPDATED_BODY_UNAVAILABLE",
            reason_codes=("emlis_refined_body_unavailable",))
    question = None
    if (request.emlis_thread.capability_snapshot == "Q3_PREMIUM"
            and checkpoint.assessment_status == "RESOLVED"):
        end, question = question_candidate(prepared.thread, build_updated_grounded_plan(prepared),
                                           parent_request_id=request.request_id)
    return EmlisThreadOutcomeV1(body.status, body, end, question=question, meaning_checkpoint=checkpoint,
        body_sufficiency="LIMITED" if body.status is EngineStatus.LIMITED else "SUFFICIENT",
        body_state="PARTIALLY_REFINED" if checkpoint.assessment_status == "PARTIAL" else "REFINED",
        reason_codes=body.reason_codes)
