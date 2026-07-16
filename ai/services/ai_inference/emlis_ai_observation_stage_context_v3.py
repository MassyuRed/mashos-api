# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build the body-free NLS v3 Observation Stage Context artifact.

The caller, not NLS v3, selects the observation stage.  This owner only binds
that explicit selection to canonical source commitments and immediately asks
the frozen Step 3 validator to verify the result.  Original and supplemental
bundle bodies are never copied into the returned artifact.
"""

from typing import Any, Final

from emlis_ai_nls_v3_artifact_contract import (
    STAGE_SCHEMA,
    TrustedFutureStageAuthority,
    artifact_sha256,
    validate_observation_stage_context,
)


_NORMAL_STAGE: Final = "normal_observation"
_PRE_QUESTION_STAGE: Final = "pre_question_observation"
_REFINED_STAGE: Final = "refined_observation"
_SUPPORTED_STAGES: Final = frozenset(
    {_NORMAL_STAGE, _PRE_QUESTION_STAGE, _REFINED_STAGE}
)


class ObservationStageContextBuildError(ValueError):
    """Fail-closed stage-context build error with a stable machine code."""

    def __init__(
        self,
        code: str,
        *,
        contract_issue_codes: tuple[str, ...] = (),
    ) -> None:
        self.code = code
        self.contract_issue_codes = contract_issue_codes
        detail = (
            f"{code}:{','.join(contract_issue_codes)}"
            if contract_issue_codes
            else code
        )
        super().__init__(detail)


def _source_commitment(value: Any, *, invalid_code: str) -> str:
    try:
        return artifact_sha256(value)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        # Do not put input values or serializer details in this body-free error.
        raise ObservationStageContextBuildError(invalid_code) from exc


def build_observation_stage_context(
    *,
    stage: str,
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
) -> dict[str, Any]:
    """Build and validate one deterministic Observation Stage Context.

    ``stage`` is mandatory and is never inferred from either bundle.  Normal
    observation accepts only the original input.  Future stages require an
    independently resolved ``TrustedFutureStageAuthority``; refined observation
    additionally requires a distinct supplemental answer bundle.
    """

    if type(stage) is not str or stage not in _SUPPORTED_STAGES:
        raise ObservationStageContextBuildError(
            "NLS3_STAGE_CONTEXT_STAGE_INVALID"
        )

    if stage == _NORMAL_STAGE:
        if trusted_future_authority is not None:
            raise ObservationStageContextBuildError(
                "NLS3_STAGE_CONTEXT_FUTURE_AUTHORITY_FORBIDDEN"
            )
        if supplemental_answer_bundle is not None:
            raise ObservationStageContextBuildError(
                "NLS3_STAGE_CONTEXT_SUPPLEMENT_FORBIDDEN"
            )
        question_need_decision_sha256 = None
        supplemental_answer_bundle_sha256 = None
        allowed_source_roles = ["original_input"]
    else:
        if trusted_future_authority is None:
            raise ObservationStageContextBuildError(
                "NLS3_STAGE_CONTEXT_FUTURE_AUTHORITY_REQUIRED"
            )
        if type(trusted_future_authority) is not TrustedFutureStageAuthority:
            raise ObservationStageContextBuildError(
                "NLS3_STAGE_CONTEXT_FUTURE_AUTHORITY_INVALID"
            )

        question_need_decision_sha256 = (
            trusted_future_authority.question_need_decision_sha256
        )
        if stage == _PRE_QUESTION_STAGE:
            if supplemental_answer_bundle is not None:
                raise ObservationStageContextBuildError(
                    "NLS3_STAGE_CONTEXT_SUPPLEMENT_FORBIDDEN"
                )
            supplemental_answer_bundle_sha256 = None
            allowed_source_roles = [
                "original_input",
                "question_need_decision",
            ]
        else:
            if supplemental_answer_bundle is None:
                raise ObservationStageContextBuildError(
                    "NLS3_STAGE_CONTEXT_SUPPLEMENT_REQUIRED"
                )
            supplemental_answer_bundle_sha256 = _source_commitment(
                supplemental_answer_bundle,
                invalid_code="NLS3_STAGE_CONTEXT_SUPPLEMENT_INVALID",
            )
            allowed_source_roles = [
                "original_input",
                "question_need_decision",
                "supplemental_answer",
            ]

    context: dict[str, Any] = {
        "schema_version": STAGE_SCHEMA,
        "stage": stage,
        "original_input_bundle_sha256": _source_commitment(
            original_input_bundle,
            invalid_code="NLS3_STAGE_CONTEXT_ORIGINAL_BUNDLE_INVALID",
        ),
        "question_need_decision_sha256": question_need_decision_sha256,
        "supplemental_answer_bundle_sha256": supplemental_answer_bundle_sha256,
        "allowed_source_roles": allowed_source_roles,
        "body_free": True,
    }

    issues = validate_observation_stage_context(
        context,
        original_input_bundle=original_input_bundle,
        trusted_future_authority=trusted_future_authority,
        supplemental_answer_bundle=supplemental_answer_bundle,
    )
    if issues:
        raise ObservationStageContextBuildError(
            "NLS3_STAGE_CONTEXT_CONTRACT_REJECTED",
            contract_issue_codes=tuple(sorted({issue.code for issue in issues})),
        )
    return context


__all__ = [
    "ObservationStageContextBuildError",
    "build_observation_stage_context",
]
