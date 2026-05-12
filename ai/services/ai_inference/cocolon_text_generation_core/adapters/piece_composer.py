# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 10 PieceComposer adapter.

PieceComposer validates Piece question/answer candidates through the common
CoreTextComposer guard layer. It does not rename legacy contracts, add public
routes, change DB write paths, or regenerate text at publish time.
"""

from dataclasses import dataclass, field, replace
import re
from typing import Any, Iterable, Mapping

from cocolon_text_generation_core.composer import CORE_TEXT_COMPOSER_NAME, CoreTextComposer
from cocolon_text_generation_core.policies import CORE_ID_PIECE, PASSING_STATUSES, compact_tokens
from cocolon_text_generation_core.result import CoreTextCandidate, json_safe_mapping
from cocolon_text_generation_core.sentence_plan import build_sentence_plan
from cocolon_text_generation_core.types import CoreTextPayload, PhraseUnit, TextGenerationResult

from .piece_composer_input_contract import (
    CHANNEL_ANSWER,
    CHANNEL_QUESTION,
    COVERAGE_SCOPE_ANSWER,
    COVERAGE_SCOPE_QUESTION,
    LEGACY_BOUNDARY_NAMES,
    PIECE_FORBIDDEN_SURFACE_PATTERNS,
    PieceComposerInputContract,
    build_piece_composer_input_contract,
)

ADAPTER_NAME = "piece_composer.v1"
PIECE_COMPOSER_MODEL = "cocolon_text_generation_core.piece_composer.v1"
PHASE_LABEL = "phase10_piece_composer_runtime_connected"
REJECTION_PIECE_COMMON_CORE_REJECTED = "piece_common_core_rejected"
REJECTION_PIECE_COMPOSER_NOT_CONNECTED = "piece_composer_not_connected"

_EXTRA_FORBIDDEN_SURFACE_PATTERNS = (
    "Emlisです",
    "Emlisの観測",
    "あなたはこういう人",
    "性格診断",
    "心理診断",
)
_SPACE_RE = re.compile(r"\s+")
_SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_TRIM = " \t\r\n　、,。.!！?？『』「」\"'"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _as_list(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _tokens(value: Iterable[Any] | Any | None) -> tuple[str, ...]:
    return compact_tokens(_as_list(value))


def _texts(value: Iterable[Any] | Any | None, *, limit: int = 180) -> tuple[str, ...]:
    out: list[str] = []
    for item in _as_list(value):
        text = _clean(item, limit=limit)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _contract_meta(contract: PieceComposerInputContract) -> Mapping[str, Any]:
    return contract.meta if isinstance(contract.meta, Mapping) else {}


class _RuntimePlan(dict):
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None


def build_runtime_piece_plan(
    *,
    question: Any,
    answer: Any,
    focus_key: Any = "piece_runtime",
    source_claims: Iterable[Any] | Any | None = None,
    source_texts: Iterable[Any] | Any | None = None,
    must_keep_signal_keys: Iterable[Any] | Any | None = None,
    coverage_roles: Iterable[Any] | Any | None = None,
    answer_preservation_policy: str = "source_scaled",
    overcompression_risk: bool = False,
    minimum_detail_level: str = "source_scaled",
) -> Mapping[str, Any]:
    keep = _tokens(must_keep_signal_keys or coverage_roles or ("piece_runtime_claim",))
    roles = _tokens(coverage_roles or keep)
    claims = _texts([*_as_list(source_texts), *_as_list(source_claims)], limit=180)
    return _RuntimePlan(
        {
            "focus_key": _clean(focus_key) or "piece_runtime",
            "question": _clean(question, limit=240),
            "answer": _clean(answer),
            "selected_block_keys": list(roles),
            "coverage_roles": list(roles),
            "must_keep_signal_keys": list(keep),
            "source_claims": list(claims),
            "answer_preservation_policy": _clean(answer_preservation_policy) or "source_scaled",
            "overcompression_risk": bool(overcompression_risk),
            "minimum_detail_level": _clean(minimum_detail_level) or "source_scaled",
            "reason": "phase10_runtime_piece_plan",
        }
    )


def _plan_with_runtime_text(plan: Any, *, question_text: Any, answer_text: Any) -> Mapping[str, Any]:
    keys = (
        "focus_key",
        "selected_block_keys",
        "coverage_roles",
        "must_keep_signal_keys",
        "source_claims",
        "answer_preservation_policy",
        "overcompression_risk",
        "minimum_detail_level",
        "reason",
    )
    data = {key: _get(plan, key) for key in keys}
    data["question"] = _clean(question_text or _get(plan, "question", ""), limit=240)
    data["answer"] = _clean(answer_text or _get(plan, "answer", ""))
    return _RuntimePlan(data)




def _question_validation_text(value: Any) -> str:
    text = _clean(value, limit=240)
    compact = _SPACE_RE.sub("", text)
    if compact and compact[-1:] in {"を", "が", "に", "は", "へ", "で"}:
        return text + "何ですか"
    return text

def _sentences(text: Any) -> tuple[str, ...]:
    source = str(text or "").strip()
    if not source:
        return tuple()
    out: list[str] = []
    for match in _SENTENCE_RE.finditer(source):
        sentence = _clean(match.group(0), limit=240)
        if sentence and sentence not in out:
            out.append(sentence)
    if not out:
        one = _clean(source, limit=240)
        if one:
            out.append(one)
    return tuple(out)


def _add_candidate_sentence_units(payload: CoreTextPayload, *, channel: str, candidate_text: str) -> CoreTextPayload:
    spans = tuple(payload.evidence_spans or ())
    if not spans or not candidate_text:
        return payload
    base_span_id = spans[0].span_id
    original_units = tuple(payload.phrase_units or ())
    derived_units: list[PhraseUnit] = []
    for index, sentence in enumerate(_sentences(candidate_text), start=len(original_units) + 1):
        derived_units.append(
            PhraseUnit(
                phrase_unit_id=f"piece-{channel}-candidate-sentence-{index}",
                evidence_span_id=base_span_id,
                text=sentence,
                role=f"piece_{channel}_candidate_sentence",
                must_keep=False,
                meta={
                    "source_adapter": ADAPTER_NAME,
                    "phase": PHASE_LABEL,
                    "piece_text_channel": channel,
                    "derived_from": "piece_candidate_sentence",
                },
            )
        )
    if not derived_units:
        return payload
    runtime_plan = build_sentence_plan(
        sentence_plan_id=f"piece-{channel}-candidate-runtime-plan-1",
        phrase_unit_ids=[unit.phrase_unit_id for unit in derived_units],
        relation_type=f"piece_{channel}_candidate_validation",
        line_role=channel,
        max_chars=240,
        must_include=True,
        meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL, "piece_text_channel": channel},
    )
    return replace(
        payload,
        phrase_units=tuple([*original_units, *derived_units]),
        sentence_plans=tuple(payload.sentence_plans or ()) + ((runtime_plan,) if runtime_plan is not None else tuple()),
    )


def _requires_must_keep_text(contract: PieceComposerInputContract, channel: str) -> bool:
    """Enable text-level must_keep coverage only for high-risk Piece answers.

    Routine Piece answers, sanitized fallbacks, and low-information previews can
    still be valid without mirroring every compact signal key in the final text.
    Phase 13 only tightens the boundary where Piece explicitly marks multiple
    user claims as must_keep under an overcompression-risk preservation policy.
    """

    meta = _contract_meta(contract)
    return bool(
        channel == CHANNEL_ANSWER
        and meta.get("overcompression_risk", False)
        and str(meta.get("answer_preservation_policy") or "").strip() == "preserve_user_claims"
        and len(tuple(meta.get("must_keep_signal_keys") or ())) > 1
    )


def _runtime_payload(
    *,
    channel: str,
    payload: CoreTextPayload,
    candidate_text: str,
    contract: PieceComposerInputContract,
) -> CoreTextPayload:
    payload = _add_candidate_sentence_units(payload, channel=channel, candidate_text=candidate_text)
    meta = dict(payload.meta or {})
    meta.update(
        {
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "core_id": CORE_ID_PIECE,
            "piece_text_channel": channel,
            "piece_composer_connected": True,
            "runtime_connected": True,
            "question_answer_separated": True,
            "preview_publish_no_regeneration": True,
            "preview_publish_mutation_allowed": False,
            "preview_publish_contract_maintained": True,
            "preview_publish_route_unchanged": True,
            "legacy_boundary_names": list(LEGACY_BOUNDARY_NAMES),
            "input_contract": contract.as_meta(),
        }
    )
    tone_policy = dict(payload.tone_policy or {})
    tone_policy.update(
        {
            "core_id": CORE_ID_PIECE,
            "piece_text_channel": channel,
            "voice_distance": "user_subject_public_qna",
            "emlis_observation_voice_allowed": False,
            "piece_composer_connected": True,
        }
    )
    safety_policy = dict(payload.safety_policy or {})
    safety_policy.update(
        {
            "core_id": CORE_ID_PIECE,
            "piece_text_channel": channel,
            "answer_preservation_policy": _contract_meta(contract).get("answer_preservation_policy"),
            "minimum_detail_level": _contract_meta(contract).get("minimum_detail_level"),
            "overcompression_risk": bool(_contract_meta(contract).get("overcompression_risk", False)),
            "must_keep_signal_keys": list(_contract_meta(contract).get("must_keep_signal_keys") or ()),
            "source_claims": list(_contract_meta(contract).get("source_claims") or ()),
            "no_emlis_voice_leakage": True,
            "no_user_claim_addition": True,
            "require_text_for_must_keep": _requires_must_keep_text(contract, channel),
            "preview_publish_no_regeneration": True,
            "preview_publish_mutation_allowed": False,
        }
    )
    forbidden = tuple(
        dict.fromkeys(
            tuple(payload.forbidden_surface_patterns or ())
            + tuple(PIECE_FORBIDDEN_SURFACE_PATTERNS)
            + tuple(_EXTRA_FORBIDDEN_SURFACE_PATTERNS)
        )
    )
    return replace(
        payload,
        tone_policy=tone_policy,
        safety_policy=safety_policy,
        forbidden_surface_patterns=forbidden,
        composer_model=PIECE_COMPOSER_MODEL,
        meta=meta,
    )


def _runtime_candidate(*, channel: str, text: str, payload: CoreTextPayload, contract: PieceComposerInputContract) -> CoreTextCandidate:
    return CoreTextCandidate(
        text=text,
        used_evidence_span_ids=[span.span_id for span in payload.evidence_spans],
        used_phrase_unit_ids=[unit.phrase_unit_id for unit in payload.phrase_units],
        coverage_scope=COVERAGE_SCOPE_QUESTION if channel == CHANNEL_QUESTION else COVERAGE_SCOPE_ANSWER,
        rejection_reasons=contract.rejection_reasons,
        composer_model=PIECE_COMPOSER_MODEL,
        meta={
            "adapter_name": ADAPTER_NAME,
            "phase": PHASE_LABEL,
            "core_id": CORE_ID_PIECE,
            "piece_text_channel": channel,
            "composer_source": "piece_composer",
            "fixed_string_renderer_used": False,
            "piece_composer_connected": True,
            "runtime_connected": True,
            "question_answer_separated": True,
            "preview_publish_no_regeneration": True,
            "preview_publish_mutation_allowed": False,
            "legacy_boundary_names": list(LEGACY_BOUNDARY_NAMES),
            "answer_preservation_policy": _contract_meta(contract).get("answer_preservation_policy"),
            "minimum_detail_level": _contract_meta(contract).get("minimum_detail_level"),
            "overcompression_risk": bool(_contract_meta(contract).get("overcompression_risk", False)),
            "must_keep_signal_keys": list(_contract_meta(contract).get("must_keep_signal_keys") or ()),
        },
    )


@dataclass(frozen=True)
class PieceComposerEvaluation:
    contract: PieceComposerInputContract
    question_result: TextGenerationResult
    answer_result: TextGenerationResult
    question_candidate: CoreTextCandidate
    answer_candidate: CoreTextCandidate
    adapter_name: str = ADAPTER_NAME
    phase: str = PHASE_LABEL
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def question_passed(self) -> bool:
        return bool(self.question_result.status in PASSING_STATUSES and self.question_result.text)

    @property
    def answer_passed(self) -> bool:
        return bool(self.answer_result.status in PASSING_STATUSES and self.answer_result.text)

    @property
    def passed(self) -> bool:
        # Piece preview/publish text is the answer body.  The question channel is
        # still checked and recorded, but it must not make a grounded answer fail
        # closed only because the question is intentionally short/abstract.
        return self.answer_passed

    @property
    def question_text(self) -> str:
        return self.question_result.text if self.question_passed else ""

    @property
    def answer_text(self) -> str:
        return self.answer_result.text if self.answer_passed else ""

    @property
    def rejection_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.contract.rejection_reasons:
            reasons.extend(self.contract.rejection_reasons)
        if not self.question_passed:
            reasons.append(REJECTION_PIECE_COMMON_CORE_REJECTED + ":question")
            reasons.extend(self.question_result.rejection_reasons)
        if not self.answer_passed:
            reasons.append(REJECTION_PIECE_COMMON_CORE_REJECTED + ":answer")
            reasons.extend(self.answer_result.rejection_reasons)
        return compact_tokens(reasons)

    def as_meta(self) -> dict[str, Any]:
        contract_meta = self.contract.as_meta()
        legacy_boundary_kept = dict(_contract_meta(self.contract).get("legacy_boundary_kept") or {})
        if legacy_boundary_kept and "legacy_boundary_kept" not in contract_meta:
            contract_meta = dict(contract_meta)
            contract_meta["legacy_boundary_kept"] = legacy_boundary_kept
        return {
            "adapter_name": self.adapter_name,
            "phase": self.phase,
            "core_composer": CORE_TEXT_COMPOSER_NAME,
            "core_id": CORE_ID_PIECE,
            "status": "generated" if self.passed else "rejected",
            "passed": self.passed,
            "question_passed": self.question_passed,
            "answer_passed": self.answer_passed,
            "piece_composer_connected": True,
            "runtime_connected": True,
            "question_answer_separated": True,
            "preview_publish_no_regeneration": True,
            "preview_publish_mutation_allowed": False,
            "preview_publish_contract_maintained": True,
            "preview_publish_route_unchanged": True,
            "legacy_boundary_names": list(LEGACY_BOUNDARY_NAMES),
            "legacy_boundary_kept": legacy_boundary_kept,
            "composer_model": PIECE_COMPOSER_MODEL,
            "used_evidence_span_ids": list(self.answer_result.used_evidence_span_ids or self.answer_candidate.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.answer_candidate.used_phrase_unit_ids),
            "quality_flags": list(dict.fromkeys([*self.question_result.quality_flags, *self.answer_result.quality_flags])),
            "rejection_reasons": list(self.rejection_reasons),
            "answer_preservation_policy": _contract_meta(self.contract).get("answer_preservation_policy"),
            "minimum_detail_level": _contract_meta(self.contract).get("minimum_detail_level"),
            "overcompression_risk": bool(_contract_meta(self.contract).get("overcompression_risk", False)),
            "must_keep_signal_keys": list(_contract_meta(self.contract).get("must_keep_signal_keys") or ()),
            "source_claims": list(_contract_meta(self.contract).get("source_claims") or ()),
            "results": {"question": self.question_result.as_meta(), "answer": self.answer_result.as_meta()},
            "input_contract": contract_meta,
            "meta": dict(self.meta),
        }


class PieceComposer:
    adapter_name = ADAPTER_NAME
    composer_model = PIECE_COMPOSER_MODEL

    def __init__(self, *, core_composer: CoreTextComposer | None = None) -> None:
        self.core_composer = core_composer or CoreTextComposer(composer_model=PIECE_COMPOSER_MODEL)

    def compose(
        self,
        plan: Any,
        *,
        question_text: Any = "",
        answer_text: Any = "",
        source_texts: Iterable[Any] | Any | None = None,
        source_id: Any = "",
        meta: Mapping[str, Any] | None = None,
    ) -> PieceComposerEvaluation:
        runtime_plan = _plan_with_runtime_text(plan, question_text=question_text, answer_text=answer_text)
        contract = build_piece_composer_input_contract(runtime_plan, source_texts=source_texts, source_id=source_id)
        q_text = _question_validation_text(question_text or contract.question_candidate.text)
        a_text = _clean(answer_text or contract.answer_candidate.text)
        q_payload = _runtime_payload(channel=CHANNEL_QUESTION, payload=contract.question_payload, candidate_text=q_text, contract=contract)
        a_payload = _runtime_payload(channel=CHANNEL_ANSWER, payload=contract.answer_payload, candidate_text=a_text, contract=contract)
        q_candidate = _runtime_candidate(channel=CHANNEL_QUESTION, text=q_text, payload=q_payload, contract=contract)
        a_candidate = _runtime_candidate(channel=CHANNEL_ANSWER, text=a_text, payload=a_payload, contract=contract)
        question_result = self.core_composer.generate(q_payload, q_candidate)
        answer_result = self.core_composer.generate(a_payload, a_candidate)
        return PieceComposerEvaluation(
            contract=contract,
            question_result=question_result,
            answer_result=answer_result,
            question_candidate=q_candidate,
            answer_candidate=a_candidate,
            meta={"runtime_meta": dict(meta or {}), "contract_rejection_reasons": list(contract.rejection_reasons)},
        )

    def __call__(self, plan: Any, **kwargs: Any) -> PieceComposerEvaluation:
        return self.compose(plan, **kwargs)


def evaluate_piece_composer(
    plan: Any,
    *,
    question_text: Any = "",
    answer_text: Any = "",
    answer_display_text: Any = "",
    source_texts: Iterable[Any] | Any | None = None,
    source_id: Any = "",
    core_composer: CoreTextComposer | None = None,
    meta: Mapping[str, Any] | None = None,
) -> PieceComposerEvaluation:
    return PieceComposer(core_composer=core_composer).compose(
        plan,
        question_text=question_text,
        answer_text=answer_text or answer_display_text,
        source_texts=source_texts,
        source_id=source_id,
        meta=meta,
    )


def compose_piece_answer(plan: Any, **kwargs: Any) -> PieceComposerEvaluation:
    return evaluate_piece_composer(plan, **kwargs)


PieceComposerCoreEvaluation = PieceComposerEvaluation
PieceComposerRuntimeResult = PieceComposerEvaluation
build_piece_composer_evaluation = evaluate_piece_composer
adapt_piece_composer = evaluate_piece_composer
compose_piece_text_generation = evaluate_piece_composer

__all__ = [
    "ADAPTER_NAME",
    "COVERAGE_SCOPE_ANSWER",
    "COVERAGE_SCOPE_QUESTION",
    "PHASE_LABEL",
    "PIECE_COMPOSER_MODEL",
    "PieceComposer",
    "PieceComposerCoreEvaluation",
    "PieceComposerEvaluation",
    "PieceComposerRuntimeResult",
    "REJECTION_PIECE_COMMON_CORE_REJECTED",
    "REJECTION_PIECE_COMPOSER_NOT_CONNECTED",
    "adapt_piece_composer",
    "build_piece_composer_evaluation",
    "build_runtime_piece_plan",
    "compose_piece_answer",
    "compose_piece_text_generation",
    "evaluate_piece_composer",
]
