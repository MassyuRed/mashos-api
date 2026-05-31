# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-1 internal response contract for EmlisAI.

This module is the migration footing from public ``observation_status`` driven
branching to internal ``response_kind`` driven branching.  It is deliberately
meta-only:

* it does not add a public status enum;
* it does not create or store user-facing text;
* it does not expose raw input, evidence text, or comment text;
* it does not relax Display / Safety / Grounding / Template gates.

Public compatibility remains the existing RN contract: displayable EmlisAI
observations are still public ``passed`` plus non-empty
``input_feedback.comment_text``.  Emergency safety and infrastructure failures
must not be converted into normal observations.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import json
import re
from typing import Any, Final

INTERNAL_RESPONSE_CONTRACT_SCHEMA_ID: Final = "cocolon.emlis.internal_response_contract.v1"
INTERNAL_RESPONSE_CONTRACT_PHASE: Final = "Phase20-1_Internal_Response_Contract"
INTERNAL_RESPONSE_CONTRACT_PUBLIC_STATUS_ENUM_EXTENDED: Final = False
INTERNAL_RESPONSE_CONTRACT_PUBLIC_RESPONSE_KEY_CHANGE: Final = False
EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: Final = "internal_response_contract"
EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION: Final = INTERNAL_RESPONSE_CONTRACT_SCHEMA_ID
EMLIS_INTERNAL_RESPONSE_CONTRACT_VERSION_META_KEY: Final = "internal_response_contract_schema_version"


class ResponseKind(str, Enum):
    NORMAL_OBSERVATION = "normal_observation"
    LOW_INFORMATION_OBSERVATION = "low_information_observation"
    LIMITED_GROUNDING_OBSERVATION = "limited_grounding_observation"
    SELF_DENIAL_SAFE_STATE_ANSWER = "self_denial_safe_state_answer"
    SAFETY_SUPPORT_REQUIRED = "safety_support_required"
    SAFETY_BLOCKED_EMERGENCY = "safety_blocked_emergency"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class PublicObservationStatus(str, Enum):
    PASSED = "passed"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    SAFETY_BLOCKED = "safety_blocked"


class SafetyTriageKind(str, Enum):
    SAFE_OBSERVATION = "safe_observation"
    SELF_DENIAL_SAFE_STATE_ANSWER = "self_denial_safe_state_answer"
    SAFETY_SUPPORT_REQUIRED = "safety_support_required"
    SAFETY_BLOCKED_EMERGENCY = "safety_blocked_emergency"
    NOT_EVALUATED = "not_evaluated"


class GroundingScope(str, Enum):
    CURRENT_INPUT_ONLY = "current_input_only"
    CURRENT_INPUT_PLUS_ALLOWED_USER_FACT = "current_input_plus_allowed_user_fact"
    NONE = "none"


class RepairKind(str, Enum):
    SURFACE_SHORTEN = "surface_shorten"
    GROUNDING_NARROW = "grounding_narrow"
    ASSERTION_SOFTEN = "assertion_soften"
    SENTENCE_COUNT_REDUCE = "sentence_count_reduce"
    RELATION_DEPTH_REDUCE = "relation_depth_reduce"
    LOW_INFORMATION_REROUTE = "low_information_reroute"
    SELF_DENIAL_SAFE_REROUTE = "self_denial_safe_reroute"
    SAFETY_EMERGENCY_EXIT = "safety_emergency_exit"
    INFRA_EXIT = "infra_exit"


class RepairResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class ResponseKindPolicy:
    response_kind: ResponseKind
    public_observation_status: PublicObservationStatus
    comment_text_required: bool
    public_input_feedback_allowed: bool
    safety_triage_kind: SafetyTriageKind
    grounding_scope: GroundingScope

    def as_payload(self) -> dict[str, Any]:
        return {
            "response_kind": self.response_kind.value,
            "public_observation_status": self.public_observation_status.value,
            "comment_text_required": bool(self.comment_text_required),
            "public_input_feedback_allowed": bool(self.public_input_feedback_allowed),
            "safety_triage_kind": self.safety_triage_kind.value,
            "grounding_scope": self.grounding_scope.value,
        }


@dataclass(frozen=True)
class RepairAttempt:
    attempt_index: int
    repair_kind: RepairKind | str
    from_gate: str
    result: RepairResult | str

    def as_payload(self) -> dict[str, Any]:
        repair_kind = _enum_value(RepairKind, self.repair_kind, field_name="repair_kind")
        result = _enum_value(RepairResult, self.result, field_name="repair_result")
        return {
            "attempt_index": int(self.attempt_index),
            "repair_kind": repair_kind.value,
            "from_gate": _normalize_identifier_code(self.from_gate, field_name="from_gate", default="not_applicable"),
            "result": result.value,
        }


_DISPLAYABLE_RESPONSE_KINDS: Final = frozenset(
    {
        ResponseKind.NORMAL_OBSERVATION,
        ResponseKind.LOW_INFORMATION_OBSERVATION,
        ResponseKind.LIMITED_GROUNDING_OBSERVATION,
        ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER,
    }
)
_NON_DISPLAYABLE_RESPONSE_KINDS: Final = frozenset(
    {
        ResponseKind.SAFETY_SUPPORT_REQUIRED,
        ResponseKind.SAFETY_BLOCKED_EMERGENCY,
        ResponseKind.INFRASTRUCTURE_ERROR,
    }
)

_RESPONSE_KIND_POLICIES: Final[dict[ResponseKind, ResponseKindPolicy]] = {
    ResponseKind.NORMAL_OBSERVATION: ResponseKindPolicy(
        response_kind=ResponseKind.NORMAL_OBSERVATION,
        public_observation_status=PublicObservationStatus.PASSED,
        comment_text_required=True,
        public_input_feedback_allowed=True,
        safety_triage_kind=SafetyTriageKind.SAFE_OBSERVATION,
        grounding_scope=GroundingScope.CURRENT_INPUT_ONLY,
    ),
    ResponseKind.LOW_INFORMATION_OBSERVATION: ResponseKindPolicy(
        response_kind=ResponseKind.LOW_INFORMATION_OBSERVATION,
        public_observation_status=PublicObservationStatus.PASSED,
        comment_text_required=True,
        public_input_feedback_allowed=True,
        safety_triage_kind=SafetyTriageKind.SAFE_OBSERVATION,
        grounding_scope=GroundingScope.CURRENT_INPUT_ONLY,
    ),
    ResponseKind.LIMITED_GROUNDING_OBSERVATION: ResponseKindPolicy(
        response_kind=ResponseKind.LIMITED_GROUNDING_OBSERVATION,
        public_observation_status=PublicObservationStatus.PASSED,
        comment_text_required=True,
        public_input_feedback_allowed=True,
        safety_triage_kind=SafetyTriageKind.SAFE_OBSERVATION,
        grounding_scope=GroundingScope.CURRENT_INPUT_ONLY,
    ),
    ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER: ResponseKindPolicy(
        response_kind=ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER,
        public_observation_status=PublicObservationStatus.PASSED,
        comment_text_required=True,
        public_input_feedback_allowed=True,
        safety_triage_kind=SafetyTriageKind.SELF_DENIAL_SAFE_STATE_ANSWER,
        grounding_scope=GroundingScope.CURRENT_INPUT_ONLY,
    ),
    ResponseKind.SAFETY_SUPPORT_REQUIRED: ResponseKindPolicy(
        response_kind=ResponseKind.SAFETY_SUPPORT_REQUIRED,
        public_observation_status=PublicObservationStatus.SAFETY_BLOCKED,
        comment_text_required=False,
        public_input_feedback_allowed=False,
        safety_triage_kind=SafetyTriageKind.SAFETY_SUPPORT_REQUIRED,
        grounding_scope=GroundingScope.NONE,
    ),
    ResponseKind.SAFETY_BLOCKED_EMERGENCY: ResponseKindPolicy(
        response_kind=ResponseKind.SAFETY_BLOCKED_EMERGENCY,
        public_observation_status=PublicObservationStatus.SAFETY_BLOCKED,
        comment_text_required=False,
        public_input_feedback_allowed=False,
        safety_triage_kind=SafetyTriageKind.SAFETY_BLOCKED_EMERGENCY,
        grounding_scope=GroundingScope.NONE,
    ),
    ResponseKind.INFRASTRUCTURE_ERROR: ResponseKindPolicy(
        response_kind=ResponseKind.INFRASTRUCTURE_ERROR,
        public_observation_status=PublicObservationStatus.UNAVAILABLE,
        comment_text_required=False,
        public_input_feedback_allowed=False,
        safety_triage_kind=SafetyTriageKind.NOT_EVALUATED,
        grounding_scope=GroundingScope.NONE,
    ),
}

_OBSERVATION_REPLY_KIND_TO_RESPONSE_KIND: Final[dict[str, ResponseKind]] = {
    "eligible_observation": ResponseKind.NORMAL_OBSERVATION,
    "normal_observation": ResponseKind.NORMAL_OBSERVATION,
    "low_information_observation": ResponseKind.LOW_INFORMATION_OBSERVATION,
    "limited_grounding_observation": ResponseKind.LIMITED_GROUNDING_OBSERVATION,
    "self_denial_safe_state_answer": ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER,
}
_SAFETY_TRIAGE_KIND_TO_RESPONSE_KIND: Final[dict[SafetyTriageKind, ResponseKind]] = {
    SafetyTriageKind.SAFE_OBSERVATION: ResponseKind.NORMAL_OBSERVATION,
    SafetyTriageKind.SELF_DENIAL_SAFE_STATE_ANSWER: ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER,
    SafetyTriageKind.SAFETY_SUPPORT_REQUIRED: ResponseKind.SAFETY_SUPPORT_REQUIRED,
    SafetyTriageKind.SAFETY_BLOCKED_EMERGENCY: ResponseKind.SAFETY_BLOCKED_EMERGENCY,
}

_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_.:/\-]+$")
_REQUIRED_CONTRACT_KEYS: Final = frozenset(
    {
        "schema_version",
        "response_kind",
        "public_observation_status",
        "comment_text_required",
        "public_input_feedback_allowed",
        "reason",
        "safety_triage_kind",
        "grounding_scope",
        "repair_attempts",
    }
)
_REPAIR_ATTEMPT_KEYS: Final = frozenset({"attempt_index", "repair_kind", "from_gate", "result"})
_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "surface_text",
        "body",
        "text",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_identifier_code(
    value: Any,
    *,
    field_name: str,
    default: str | None = None,
    max_length: int = 120,
) -> str:
    text = _clean(value)[:max_length]
    if not text and default is not None:
        return default
    if text and _IDENTIFIER_RE.match(text):
        return text
    raise ValueError(f"{field_name} must be an identifier code, not text payload")


def _enum_value(enum_cls: type[Enum], value: Any, *, field_name: str) -> Any:
    if isinstance(value, enum_cls):
        return value
    text = _clean(value)
    for member in enum_cls:  # type: ignore[union-attr]
        if text == str(member.value):
            return member
    raise ValueError(f"unsupported {field_name}: {text or '<empty>'}")


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def normalize_response_kind(value: Any) -> ResponseKind:
    return _enum_value(ResponseKind, value, field_name="response_kind")


def normalize_public_observation_status(value: Any) -> PublicObservationStatus:
    return _enum_value(PublicObservationStatus, value, field_name="public_observation_status")


def response_kind_policy(response_kind: Any) -> ResponseKindPolicy:
    kind = normalize_response_kind(response_kind)
    return _RESPONSE_KIND_POLICIES[kind]


def public_observation_status_for_response_kind(response_kind: Any) -> str:
    return response_kind_policy(response_kind).public_observation_status.value


def comment_text_required_for_response_kind(response_kind: Any) -> bool:
    return bool(response_kind_policy(response_kind).comment_text_required)


def public_input_feedback_allowed_for_response_kind(response_kind: Any) -> bool:
    return bool(response_kind_policy(response_kind).public_input_feedback_allowed)


def safety_triage_kind_for_response_kind(response_kind: Any) -> str:
    return response_kind_policy(response_kind).safety_triage_kind.value


def grounding_scope_for_response_kind(response_kind: Any) -> str:
    return response_kind_policy(response_kind).grounding_scope.value


def public_status_from_internal_response_contract(payload: Mapping[str, Any] | None) -> str | None:
    """Return the mapped public status from a valid internal contract payload."""

    if not isinstance(payload, Mapping):
        return None
    assert_internal_response_contract(payload)
    return str(payload.get("public_observation_status") or "")


def response_kind_for_observation_reply_kind(observation_reply_kind: Any) -> str:
    text = _clean(observation_reply_kind)
    if text not in _OBSERVATION_REPLY_KIND_TO_RESPONSE_KIND:
        raise ValueError(f"unsupported observation_reply_kind: {text or '<empty>'}")
    return _OBSERVATION_REPLY_KIND_TO_RESPONSE_KIND[text].value


def response_kind_for_safety_triage_kind(safety_triage_kind: Any) -> str:
    triage = _enum_value(SafetyTriageKind, safety_triage_kind, field_name="safety_triage_kind")
    if triage == SafetyTriageKind.NOT_EVALUATED:
        raise ValueError("not_evaluated safety_triage_kind does not map to a runtime response_kind")
    return _SAFETY_TRIAGE_KIND_TO_RESPONSE_KIND[triage].value


def build_repair_attempt(
    *,
    attempt_index: Any,
    repair_kind: Any,
    from_gate: Any,
    result: Any,
) -> dict[str, Any]:
    try:
        index = int(attempt_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("repair attempt_index must be an integer") from exc
    if index < 0:
        raise ValueError("repair attempt_index must be >= 0")
    attempt = RepairAttempt(
        attempt_index=index,
        repair_kind=_enum_value(RepairKind, repair_kind, field_name="repair_kind"),
        from_gate=_normalize_identifier_code(from_gate, field_name="from_gate", default="not_applicable"),
        result=_enum_value(RepairResult, result, field_name="repair_result"),
    )
    payload = attempt.as_payload()
    _assert_repair_attempt_payload(payload)
    return payload


def _normalize_repair_attempts(values: Any) -> list[dict[str, Any]]:
    if values is None:
        return []
    if isinstance(values, Mapping):
        source = [values]
    elif isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
        source = list(values)
    else:
        raise ValueError("repair_attempts must be a sequence of mappings")

    attempts: list[dict[str, Any]] = []
    for raw in source:
        if isinstance(raw, RepairAttempt):
            payload = raw.as_payload()
        elif isinstance(raw, Mapping):
            payload = build_repair_attempt(
                attempt_index=raw.get("attempt_index"),
                repair_kind=raw.get("repair_kind"),
                from_gate=raw.get("from_gate"),
                result=raw.get("result"),
            )
        else:
            raise ValueError("repair_attempt entries must be mappings")
        attempts.append(payload)
    return attempts


def _assert_repair_attempt_payload(payload: Mapping[str, Any]) -> None:
    if set(payload.keys()) != _REPAIR_ATTEMPT_KEYS:
        raise ValueError("repair_attempt payload keys must match the Phase20-1 schema")
    try:
        index = int(payload.get("attempt_index"))
    except (TypeError, ValueError) as exc:
        raise ValueError("repair attempt_index must be an integer") from exc
    if index < 0:
        raise ValueError("repair attempt_index must be >= 0")
    _enum_value(RepairKind, payload.get("repair_kind"), field_name="repair_kind")
    _enum_value(RepairResult, payload.get("result"), field_name="repair_result")
    if _normalize_identifier_code(payload.get("from_gate"), field_name="from_gate") != payload.get("from_gate"):
        raise ValueError("repair from_gate must be an identifier, not text payload")


def build_internal_response_contract(
    *,
    response_kind: Any,
    reason: Any,
    repair_attempts: Any = None,
    grounding_scope: Any = None,
) -> dict[str, Any]:
    """Build a schema-shaped internal response contract payload."""

    kind = normalize_response_kind(response_kind)
    policy = response_kind_policy(kind)
    normalized_scope = (
        _enum_value(GroundingScope, grounding_scope, field_name="grounding_scope")
        if grounding_scope is not None
        else policy.grounding_scope
    )
    if kind in _NON_DISPLAYABLE_RESPONSE_KINDS and normalized_scope != GroundingScope.NONE:
        raise ValueError("non-displayable response kinds must keep grounding_scope=none")

    payload: dict[str, Any] = {
        "schema_version": EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
        "response_kind": kind.value,
        "public_observation_status": policy.public_observation_status.value,
        "comment_text_required": bool(policy.comment_text_required),
        "public_input_feedback_allowed": bool(policy.public_input_feedback_allowed),
        "reason": _normalize_identifier_code(
            reason,
            field_name="reason",
            default="unspecified_internal_response_reason",
        ),
        "safety_triage_kind": policy.safety_triage_kind.value,
        "grounding_scope": normalized_scope.value,
        "repair_attempts": _normalize_repair_attempts(repair_attempts),
    }
    assert_internal_response_contract(payload)
    return payload


def build_internal_response_contract_from_observation_reply_kind(
    *,
    observation_reply_kind: Any,
    reason: Any,
    repair_attempts: Any = None,
) -> dict[str, Any]:
    """Bridge existing observation_reply_kind meta into Phase20 response_kind."""

    return build_internal_response_contract(
        response_kind=response_kind_for_observation_reply_kind(observation_reply_kind),
        reason=reason,
        repair_attempts=repair_attempts,
    )


def _legacy_reasons_contain_any(rejection_reasons: Any, needles: tuple[str, ...]) -> bool:
    if not isinstance(rejection_reasons, Sequence) or isinstance(rejection_reasons, (str, bytes, bytearray)):
        return False
    normalized = " ".join(_clean(reason).lower() for reason in rejection_reasons)
    return any(needle in normalized for needle in needles)


def response_kind_from_legacy_public_state(
    *,
    observation_status: Any,
    observation_reply_kind: Any = None,
    rejection_reasons: Any = None,
) -> str:
    """Map existing public-status meta into the Phase20 internal response_kind.

    Emergency safety and infrastructure states never become normal observations.
    Non-safety legacy ``rejected`` states are limited-grounding candidates for
    later recovery; existing public ``rejected`` status still wins at the public
    boundary.
    """

    status = _clean(observation_status)
    reply_kind = _clean(observation_reply_kind)
    if status == PublicObservationStatus.UNAVAILABLE.value:
        return ResponseKind.INFRASTRUCTURE_ERROR.value
    if status == PublicObservationStatus.SAFETY_BLOCKED.value:
        if _legacy_reasons_contain_any(
            rejection_reasons,
            ("emergency", "self_harm", "suicide", "imminent", "urgent"),
        ):
            return ResponseKind.SAFETY_BLOCKED_EMERGENCY.value
        return ResponseKind.SAFETY_SUPPORT_REQUIRED.value
    if status == PublicObservationStatus.REJECTED.value:
        if _legacy_reasons_contain_any(rejection_reasons, ("safety", "self_harm", "danger")):
            return ResponseKind.SAFETY_SUPPORT_REQUIRED.value
        return ResponseKind.LIMITED_GROUNDING_OBSERVATION.value
    if status == PublicObservationStatus.PASSED.value:
        if reply_kind in _OBSERVATION_REPLY_KIND_TO_RESPONSE_KIND:
            return _OBSERVATION_REPLY_KIND_TO_RESPONSE_KIND[reply_kind].value
        return ResponseKind.NORMAL_OBSERVATION.value
    raise ValueError(f"unsupported legacy observation_status: {status or '<empty>'}")


def build_emlis_internal_response_contract(
    response_kind: Any,
    *,
    reason: Any,
    repair_attempts: Any = None,
    grounding_scope: Any = None,
    public_observation_status: Any = None,
) -> dict[str, Any]:
    """Public Phase20-1 builder used by EmlisAI services/tests.

    ``public_observation_status`` is accepted only as a compatibility assertion
    for existing fail-closed branches.  It may not override the fixed mapping
    from response_kind to public status.
    """

    payload = build_internal_response_contract(
        response_kind=response_kind,
        reason=reason,
        repair_attempts=repair_attempts,
        grounding_scope=grounding_scope,
    )
    if public_observation_status is not None:
        expected = normalize_public_observation_status(public_observation_status).value
        if expected != payload["public_observation_status"]:
            raise ValueError("public_observation_status must match the response_kind mapping")
    return payload


def build_emlis_internal_response_contract_from_legacy_state(
    *,
    observation_status: Any,
    observation_reply_kind: Any = None,
    rejection_reasons: Any = None,
    reason: Any = "phase20_1_legacy_public_state_bridge",
    repair_attempts: Any = None,
) -> dict[str, Any]:
    return build_emlis_internal_response_contract(
        response_kind_from_legacy_public_state(
            observation_status=observation_status,
            observation_reply_kind=observation_reply_kind,
            rejection_reasons=rejection_reasons,
        ),
        reason=reason,
        repair_attempts=repair_attempts,
    )


def assert_internal_response_contract(payload: Mapping[str, Any]) -> None:
    """Validate that a Phase20-1 internal response contract is schema-shaped."""

    if not isinstance(payload, Mapping):
        raise ValueError("internal_response_contract must be a mapping")
    if set(payload.keys()) != _REQUIRED_CONTRACT_KEYS:
        raise ValueError("internal_response_contract payload keys must match the Phase20-1 schema")
    if _contains_forbidden_text_payload_key(payload):
        raise ValueError("internal_response_contract must stay meta-only and text-free")
    if payload.get("schema_version") != EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION:
        raise ValueError("internal_response_contract schema_version is unsupported")

    kind = normalize_response_kind(payload.get("response_kind"))
    policy = response_kind_policy(kind)
    public_status = normalize_public_observation_status(payload.get("public_observation_status"))
    safety_triage = _enum_value(SafetyTriageKind, payload.get("safety_triage_kind"), field_name="safety_triage_kind")
    grounding_scope = _enum_value(GroundingScope, payload.get("grounding_scope"), field_name="grounding_scope")

    if public_status != policy.public_observation_status:
        raise ValueError("response_kind public_observation_status mapping was changed")
    if payload.get("comment_text_required") is not policy.comment_text_required:
        raise ValueError("response_kind comment_text_required mapping was changed")
    if payload.get("public_input_feedback_allowed") is not policy.public_input_feedback_allowed:
        raise ValueError("response_kind public_input_feedback_allowed mapping was changed")
    if safety_triage != policy.safety_triage_kind:
        raise ValueError("response_kind safety_triage_kind mapping was changed")
    if kind in _NON_DISPLAYABLE_RESPONSE_KINDS and grounding_scope != GroundingScope.NONE:
        raise ValueError("non-displayable response kinds must keep grounding_scope=none")
    if kind in _DISPLAYABLE_RESPONSE_KINDS and public_status != PublicObservationStatus.PASSED:
        raise ValueError("displayable response kinds must map to public passed")
    if kind == ResponseKind.SAFETY_BLOCKED_EMERGENCY and public_status == PublicObservationStatus.PASSED:
        raise ValueError("safety_blocked_emergency must not be converted to normal observation")
    if kind == ResponseKind.INFRASTRUCTURE_ERROR:
        if payload.get("comment_text_required") is True or payload.get("public_input_feedback_allowed") is True:
            raise ValueError("infrastructure_error must not fake an Emlis observation body")

    if _normalize_identifier_code(payload.get("reason"), field_name="reason") != payload.get("reason"):
        raise ValueError("reason must be an identifier code, not user text")

    attempts = payload.get("repair_attempts")
    if not isinstance(attempts, list):
        raise ValueError("repair_attempts must be a list")
    for attempt in attempts:
        if not isinstance(attempt, Mapping):
            raise ValueError("repair_attempt entries must be mappings")
        _assert_repair_attempt_payload(attempt)


def validate_emlis_internal_response_contract(payload: Mapping[str, Any] | None) -> list[str]:
    try:
        if not isinstance(payload, Mapping):
            raise ValueError("internal_response_contract must be a mapping")
        assert_internal_response_contract(payload)
    except ValueError as exc:
        return [str(exc)]
    return []


def internal_response_contract_from_meta(meta: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(meta, Mapping):
        return None
    raw = meta.get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY)
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("internal_response_contract meta must be a mapping")
    assert_internal_response_contract(raw)
    return dict(raw)


def attach_emlis_internal_response_contract(
    meta: Mapping[str, Any] | None,
    *,
    observation_status: Any,
    observation_reply_kind: Any = None,
    rejection_reasons: Any = None,
    reason: Any = "phase20_1_reply_service_bridge",
    repair_attempts: Any = None,
) -> dict[str, Any]:
    """Attach the Phase20-1 contract to internal meta without public leakage.

    Phase20-5 may pass Gate Recovery Loop ``repair_attempts``. They remain
    internal metadata only; the public observation_status mapping and RN response
    keys are not extended.
    """

    next_meta: dict[str, Any] = dict(meta or {}) if isinstance(meta, Mapping) else {}
    try:
        contract = internal_response_contract_from_meta(next_meta)
    except ValueError:
        contract = None
    if contract is None or repair_attempts is not None:
        contract = build_emlis_internal_response_contract_from_legacy_state(
            observation_status=observation_status,
            observation_reply_kind=observation_reply_kind,
            rejection_reasons=rejection_reasons,
            reason=reason,
            repair_attempts=repair_attempts,
        )
    next_meta[EMLIS_INTERNAL_RESPONSE_CONTRACT_VERSION_META_KEY] = EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION
    next_meta[EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY] = contract
    return next_meta


def dump_internal_response_contract(payload: Mapping[str, Any]) -> str:
    assert_internal_response_contract(payload)
    return json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# Backward-compatible Phase20-1 public aliases.
EmlisInternalResponseKind = ResponseKind
EmlisInternalRepairAttempt = RepairAttempt


__all__ = [
    "INTERNAL_RESPONSE_CONTRACT_SCHEMA_ID",
    "INTERNAL_RESPONSE_CONTRACT_PHASE",
    "INTERNAL_RESPONSE_CONTRACT_PUBLIC_STATUS_ENUM_EXTENDED",
    "INTERNAL_RESPONSE_CONTRACT_PUBLIC_RESPONSE_KEY_CHANGE",
    "EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY",
    "EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION",
    "EMLIS_INTERNAL_RESPONSE_CONTRACT_VERSION_META_KEY",
    "ResponseKind",
    "EmlisInternalResponseKind",
    "PublicObservationStatus",
    "SafetyTriageKind",
    "GroundingScope",
    "RepairKind",
    "RepairResult",
    "ResponseKindPolicy",
    "RepairAttempt",
    "EmlisInternalRepairAttempt",
    "normalize_response_kind",
    "normalize_public_observation_status",
    "response_kind_policy",
    "public_observation_status_for_response_kind",
    "comment_text_required_for_response_kind",
    "public_input_feedback_allowed_for_response_kind",
    "safety_triage_kind_for_response_kind",
    "grounding_scope_for_response_kind",
    "public_status_from_internal_response_contract",
    "response_kind_for_observation_reply_kind",
    "response_kind_for_safety_triage_kind",
    "response_kind_from_legacy_public_state",
    "build_repair_attempt",
    "build_internal_response_contract",
    "build_internal_response_contract_from_observation_reply_kind",
    "build_emlis_internal_response_contract",
    "build_emlis_internal_response_contract_from_legacy_state",
    "validate_emlis_internal_response_contract",
    "internal_response_contract_from_meta",
    "attach_emlis_internal_response_contract",
    "assert_internal_response_contract",
    "dump_internal_response_contract",
]
