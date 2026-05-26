# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 9 PieceComposer input contract adapter.

The adapter is design-only. It converts PieceCoreQuestionAnswerPlan-like data
into separate question/answer CoreTextPayload objects and does not connect the
Piece preview/publish runtime.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.evidence import make_evidence_span_like, source_anchors_for_evidence
from cocolon_text_generation_core.policies import CORE_ID_PIECE, compact_tokens
from cocolon_text_generation_core.result import CoreTextCandidate, json_safe_mapping
from cocolon_text_generation_core.sentence_plan import build_sentence_plan
from cocolon_text_generation_core.types import CoreTextPayload, EvidenceSpanLike, PhraseUnit, SentencePlan
from .piece_environment_state_output_guard import build_piece_environment_state_output_guard

ADAPTER_NAME = "piece_composer_input_contract.v0"
PIECE_INPUT_CONTRACT_MODEL = "cocolon_text_generation_core.piece_input_contract.v0"
PHASE_LABEL = "phase9_input_contract_only"
CHANNEL_QUESTION = "question"
CHANNEL_ANSWER = "answer"
PAYLOAD_KIND_QUESTION = "piece_question_payload"
PAYLOAD_KIND_ANSWER = "piece_answer_payload"
LEGACY_BOUNDARY_NAMES = ("reflection", "mymodel_qna")
PIECE_FORBIDDEN_SURFACE_PATTERNS = (
    "Emlisです",
    "Emlisの観測",
    "Emlisには",
    "Emlisは",
    "Emlisの感想",
    "あなたはこういう人",
    "性格診断",
    "心理診断",
)
COVERAGE_SCOPE_QUESTION = "piece_question_contract"
COVERAGE_SCOPE_ANSWER = "piece_answer_contract"
REJECTION_PIECE_PLAN_MISSING = "piece_question_answer_plan_missing"
REJECTION_PIECE_QUESTION_MISSING = "piece_question_missing"
REJECTION_PIECE_ANSWER_MISSING = "piece_answer_missing"
REJECTION_PIECE_SOURCE_MISSING = "piece_source_claims_missing"
REJECTION_PIECE_SOURCE_CLAIMS_MISSING = REJECTION_PIECE_SOURCE_MISSING

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』「」\"'"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _tokens(value: Any) -> tuple[str, ...]:
    return compact_tokens(_as_list(value))


def _texts(value: Any, *, limit: int = 180) -> tuple[str, ...]:
    out: list[str] = []
    for item in _as_list(value):
        text = _clean(item, limit=limit)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "risk", "high"}
    return bool(value)


def _environment_state_output_piece_guard_from_plan(plan: Any) -> dict[str, Any]:
    material = _get(plan, "environment_state_output_piece_guard", None)
    if isinstance(material, Mapping):
        return build_piece_environment_state_output_guard(material)
    frame = _get(plan, "environment_state_output_frame", None)
    return build_piece_environment_state_output_guard(
        frame,
        apply_must_keep=_bool(_get(plan, "environment_state_output_must_keep_enabled", True)),
    )


def _plan_meta(plan: Any, *, source_texts: Sequence[str], source_id: str) -> dict[str, Any]:
    eso_guard = _environment_state_output_piece_guard_from_plan(plan)
    eso_applied = bool(eso_guard.get("must_keep_signal_keys_applied", False))
    eso_keys = list(_tokens(eso_guard.get("must_keep_signal_keys", ()))) if eso_applied else []
    must_keep = list(_tokens([*_as_list(_get(plan, "must_keep_signal_keys", ())), *eso_keys]))
    source_claims = list(
        _texts(
            [
                *_as_list(eso_guard.get("source_claim_values", ())),
                *_as_list(_get(plan, "source_claims", ())),
            ],
            limit=180,
        )
    )
    preservation = _clean(_get(plan, "answer_preservation_policy", "source_scaled")) or "source_scaled"
    if eso_applied:
        preservation = "preserve_user_claims"
    return {
        "adapter_name": ADAPTER_NAME,
        "phase": PHASE_LABEL,
        "source_core": CORE_ID_PIECE,
        "source_id": source_id,
        "focus_key": _clean(_get(plan, "focus_key", "")),
        "selected_block_keys": list(_tokens(_get(plan, "selected_block_keys", ()))),
        "coverage_roles": list(_tokens([*_as_list(_get(plan, "coverage_roles", ())), *eso_keys])),
        "must_keep_signal_keys": must_keep,
        "source_claims": source_claims,
        "source_text_count": len(source_texts),
        "answer_preservation_policy": preservation,
        "minimum_detail_level": _clean(_get(plan, "minimum_detail_level", "source_scaled")) or "source_scaled",
        "overcompression_risk": bool(_bool(_get(plan, "overcompression_risk", False)) or eso_guard.get("overcompression_risk", False)),
        "environment_state_output_piece_guard": eso_guard,
        "environment_state_output_frame_connected": bool(eso_guard.get("connected", False)),
        "environment_state_output_must_keep_signal_keys": list(eso_keys),
        "environment_state_output_must_keep_applied": bool(eso_applied),
        "environment_state_output_overcompression_risk": bool(eso_guard.get("overcompression_risk", False)),
        "environment_state_output_output_theme_ids": list(eso_guard.get("output_theme_ids", ()) or ()),
        "environment_state_output_single_record_only": bool(eso_guard.get("single_record_only", False)),
        "question_answer_separated": True,
        "runtime_connected": False,
        "piece_composer_connected": False,
        "preview_publish_mutation_allowed": False,
        "preview_publish_contract_touched": False,
        "preview_publish_contract_untouched": True,
        "legacy_boundary_kept": {"reflection": "compat_name_only_not_renamed", "mymodel_qna": "compat_name_only_not_renamed"},
    }


def _evidence_pairs(plan: Any, source_texts: Sequence[str]) -> tuple[tuple[str, str], ...]:
    """Return grounded Piece evidence without dropping the original input.

    Phase 9 exposed ``source_claims`` as the compact Piece contract.  Phase 10
    connects the contract to common GroundingGuard, so the full current-input
    anchors are also kept when available.  This lets a readable Piece answer
    paraphrase from the original user wording while still retaining the compact
    claims that protect must_keep signal keys.
    """

    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for claim in _texts(_get(plan, "source_claims", ()), limit=180):
        key = _clean(claim)
        if key and key not in seen:
            seen.add(key)
            pairs.append(("source_claims", claim))
    for text in source_texts:
        key = _clean(text)
        if key and key not in seen:
            seen.add(key)
            pairs.append(("current_input", text))
    return tuple(pairs)


def _role(index: int, *, must_keep: Sequence[str], coverage_roles: Sequence[str], sequential_must_keep: bool = False) -> str:
    if must_keep:
        if sequential_must_keep:
            return must_keep[index - 1] if index <= len(must_keep) else "piece_source_claim"
        return must_keep[0] if len(must_keep) == 1 else must_keep[min(index - 1, len(must_keep) - 1)]
    if coverage_roles:
        return coverage_roles[min(index - 1, len(coverage_roles) - 1)]
    return "piece_source_claim"


def _build_evidence(plan: Any, *, source_id: str, source_texts: Sequence[str], meta: Mapping[str, Any] | None = None) -> tuple[EvidenceSpanLike, ...]:
    material_meta = meta if isinstance(meta, Mapping) else {}
    must_keep = _tokens(material_meta.get("must_keep_signal_keys") or _get(plan, "must_keep_signal_keys", ()))
    coverage_roles = _tokens(material_meta.get("coverage_roles") or _get(plan, "coverage_roles", ()))
    must_keep_set = set(must_keep)
    sequential_must_keep = bool(material_meta.get("environment_state_output_must_keep_applied", False))
    spans: list[EvidenceSpanLike] = []
    for index, (field_name, raw_text) in enumerate(_evidence_pairs(plan, source_texts), start=1):
        role = _role(index, must_keep=must_keep, coverage_roles=coverage_roles, sequential_must_keep=sequential_must_keep)
        span = make_evidence_span_like(
            span_id=f"piece-source-{index}",
            source_id=source_id,
            field_name=field_name,
            raw_text=raw_text,
            role=role,
            meta={"source_adapter": ADAPTER_NAME, "source_kind": field_name, "phase": PHASE_LABEL, "must_keep": role in must_keep_set, "signal_key": role if role in must_keep_set else ""},
        )
        if span.usable:
            spans.append(span)
    return tuple(spans)


def _build_units(spans: Sequence[EvidenceSpanLike], must_keep_roles: Sequence[str]) -> tuple[PhraseUnit, ...]:
    units: list[PhraseUnit] = []
    keep = set(must_keep_roles)
    for index, span in enumerate(spans, start=1):
        text = _clean(span.raw_text, limit=180)
        if not text:
            continue
        units.append(
            PhraseUnit(
                phrase_unit_id=f"pu{index}",
                evidence_span_id=span.span_id,
                text=text,
                role=span.role,
                must_keep=span.role in keep,
                meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL},
            )
        )
    return tuple(units)


def _channel_plan(channel: str, units: Sequence[PhraseUnit]) -> tuple[SentencePlan, ...]:
    plan = build_sentence_plan(
        sentence_plan_id=f"piece-{channel}-plan-1",
        phrase_unit_ids=[unit.phrase_unit_id for unit in units],
        relation_type=f"piece_{channel}_input_contract",
        line_role=channel,
        max_chars=160 if channel == CHANNEL_QUESTION else 240,
        must_include=True,
        meta={"source_adapter": ADAPTER_NAME, "phase": PHASE_LABEL, "piece_text_channel": channel},
    )
    return (plan,) if plan is not None else tuple()


def _candidate(channel: str, text: str, spans: Sequence[EvidenceSpanLike], units: Sequence[PhraseUnit], meta: Mapping[str, Any]) -> CoreTextCandidate:
    return CoreTextCandidate(
        text=text,
        used_evidence_span_ids=[span.span_id for span in spans],
        used_phrase_unit_ids=[unit.phrase_unit_id for unit in units],
        coverage_scope=COVERAGE_SCOPE_QUESTION if channel == CHANNEL_QUESTION else COVERAGE_SCOPE_ANSWER,
        composer_model=PIECE_INPUT_CONTRACT_MODEL,
        meta={"adapter_name": ADAPTER_NAME, "phase": PHASE_LABEL, "piece_text_channel": channel, "question_answer_separated": True, "runtime_connected": False, "answer_preservation_policy": meta.get("answer_preservation_policy"), "overcompression_risk": bool(meta.get("overcompression_risk", False))},
    )


def _requires_must_keep_text(channel: str, meta: Mapping[str, Any]) -> bool:
    return bool(
        channel == CHANNEL_ANSWER
        and meta.get("overcompression_risk", False)
        and str(meta.get("answer_preservation_policy") or "").strip() == "preserve_user_claims"
        and len(tuple(meta.get("must_keep_signal_keys") or ())) > 1
    )


def _payload(channel: str, spans: Sequence[EvidenceSpanLike], units: Sequence[PhraseUnit], plans: Sequence[SentencePlan], meta: Mapping[str, Any], candidate: CoreTextCandidate) -> CoreTextPayload:
    payload_meta = dict(meta)
    payload_meta.update({"piece_text_channel": channel, "payload_kind": f"piece_{channel}_payload", "candidate": candidate.as_meta()})
    return CoreTextPayload(
        core_id=CORE_ID_PIECE,
        source_anchors=source_anchors_for_evidence(spans),
        evidence_spans=spans,
        phrase_units=units,
        sentence_plans=plans,
        tone_policy={"core_id": CORE_ID_PIECE, "piece_text_channel": channel, "voice_distance": "user_subject_public_qna", "emlis_observation_voice_allowed": False, "question_answer_separated": True},
        safety_policy={"core_id": CORE_ID_PIECE, "piece_text_channel": channel, "answer_preservation_policy": meta.get("answer_preservation_policy"), "minimum_detail_level": meta.get("minimum_detail_level"), "overcompression_risk": bool(meta.get("overcompression_risk", False)), "must_keep_signal_keys": list(meta.get("must_keep_signal_keys") or ()), "source_claims": list(meta.get("source_claims") or ()), "environment_state_output_piece_guard": dict(meta.get("environment_state_output_piece_guard") or {}), "environment_state_output_must_keep_applied": bool(meta.get("environment_state_output_must_keep_applied", False)), "environment_state_output_overcompression_risk": bool(meta.get("environment_state_output_overcompression_risk", False)), "legacy_boundary_names_kept": list(LEGACY_BOUNDARY_NAMES), "no_emlis_voice_leakage": True, "no_user_claim_addition": True, "require_text_for_must_keep": _requires_must_keep_text(channel, meta)},
        must_keep_roles=meta.get("must_keep_signal_keys") or (),
        forbidden_surface_patterns=PIECE_FORBIDDEN_SURFACE_PATTERNS,
        composer_model=PIECE_INPUT_CONTRACT_MODEL,
        meta=payload_meta,
    )


@dataclass(frozen=True)
class PieceComposerInputContract:
    question_payload: CoreTextPayload
    answer_payload: CoreTextPayload
    question_candidate: CoreTextCandidate
    answer_candidate: CoreTextCandidate
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    adapter_name: str = ADAPTER_NAME
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejection_reasons", compact_tokens(self.rejection_reasons))
        object.__setattr__(self, "meta", json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(not self.rejection_reasons and self.question_payload.valid_minimum and self.answer_payload.valid_minimum and self.question_candidate.usable_text and self.answer_candidate.usable_text)

    @property
    def connected_to_runtime(self) -> bool:
        return False

    def as_meta(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "phase": PHASE_LABEL,
            "usable": self.usable,
            "rejection_reasons": list(self.rejection_reasons),
            "core_id": CORE_ID_PIECE,
            "question_answer_separated": True,
            "question_answer_payloads_separated": True,
            "piece_composer_connected": False,
            "preview_publish_contract_touched": False,
            "preview_publish_contract_untouched": True,
            "connected_to_runtime": False,
            "legacy_boundary_names": list(LEGACY_BOUNDARY_NAMES),
            "payloads": {
                "question": {"core_id": self.question_payload.core_id, "valid_minimum": self.question_payload.valid_minimum, "rejection_reasons": list(self.question_payload.validate_minimum()), "evidence_span_count": len(self.question_payload.evidence_spans), "phrase_unit_count": len(self.question_payload.phrase_units), "sentence_plan_count": len(self.question_payload.sentence_plans), "must_keep_roles": list(self.question_payload.must_keep_roles)},
                "answer": {"core_id": self.answer_payload.core_id, "valid_minimum": self.answer_payload.valid_minimum, "rejection_reasons": list(self.answer_payload.validate_minimum()), "evidence_span_count": len(self.answer_payload.evidence_spans), "phrase_unit_count": len(self.answer_payload.phrase_units), "sentence_plan_count": len(self.answer_payload.sentence_plans), "must_keep_roles": list(self.answer_payload.must_keep_roles)},
            },
            "candidates": {"question": self.question_candidate.as_meta(), "answer": self.answer_candidate.as_meta()},
            "environment_state_output_frame_connected": bool(self.meta.get("environment_state_output_frame_connected", False)),
            "environment_state_output_must_keep_applied": bool(self.meta.get("environment_state_output_must_keep_applied", False)),
            "environment_state_output_must_keep_signal_keys": list(self.meta.get("environment_state_output_must_keep_signal_keys") or ()),
            "environment_state_output_overcompression_risk": bool(self.meta.get("environment_state_output_overcompression_risk", False)),
            "environment_state_output_output_theme_ids": list(self.meta.get("environment_state_output_output_theme_ids") or ()),
            "environment_state_output_piece_guard": dict(self.meta.get("environment_state_output_piece_guard") or {}),
            "input_contract": dict(self.meta),
        }


def empty_piece_composer_input_contract(reason: str = REJECTION_PIECE_PLAN_MISSING) -> PieceComposerInputContract:
    candidate = CoreTextCandidate(composer_model=PIECE_INPUT_CONTRACT_MODEL)
    payload = CoreTextPayload(core_id=CORE_ID_PIECE, composer_model=PIECE_INPUT_CONTRACT_MODEL, meta={"adapter_name": ADAPTER_NAME, "phase": PHASE_LABEL, "candidate": candidate.as_meta()})
    return PieceComposerInputContract(payload, payload, candidate, candidate, rejection_reasons=(reason,), meta={"adapter_name": ADAPTER_NAME, "phase": PHASE_LABEL, "runtime_connected": False, "piece_composer_connected": False, "preview_publish_contract_touched": False})


def build_piece_composer_input_contract(plan: Any, *, source_texts: Iterable[Any] | Any | None = None, source_id: Any = "") -> PieceComposerInputContract:
    if plan is None:
        return empty_piece_composer_input_contract(REJECTION_PIECE_PLAN_MISSING)
    question = _clean(_get(plan, "question", ""), limit=240)
    answer = _clean(_get(plan, "answer", ""), limit=0)
    source_values = _texts(source_texts, limit=180)
    resolved_source_id = _clean(source_id) or _clean(_get(plan, "source_id", "")) or "piece_preview_input"
    meta = _plan_meta(plan, source_texts=source_values, source_id=resolved_source_id)
    reasons: list[str] = []
    if not question:
        reasons.append(REJECTION_PIECE_QUESTION_MISSING)
    if not answer:
        reasons.append(REJECTION_PIECE_ANSWER_MISSING)
    spans = _build_evidence(plan, source_id=resolved_source_id, source_texts=source_values, meta=meta)
    if not spans:
        reasons.append(REJECTION_PIECE_SOURCE_MISSING)
    units = _build_units(spans, tuple(meta.get("must_keep_signal_keys") or ()))
    # Phase 9 is input-contract design only. If the contract is incomplete,
    # keep candidate text empty so no ungrounded Piece question/answer can be
    # used by a future caller accidentally.
    candidate_question = question if not reasons else ""
    candidate_answer = answer if not reasons else ""
    q_candidate = _candidate(CHANNEL_QUESTION, candidate_question, spans, units, meta)
    a_candidate = _candidate(CHANNEL_ANSWER, candidate_answer, spans, units, meta)
    q_payload = _payload(CHANNEL_QUESTION, spans, units, _channel_plan(CHANNEL_QUESTION, units), meta, q_candidate)
    a_payload = _payload(CHANNEL_ANSWER, spans, units, _channel_plan(CHANNEL_ANSWER, units), meta, a_candidate)
    return PieceComposerInputContract(q_payload, a_payload, q_candidate, a_candidate, rejection_reasons=tuple(dict.fromkeys(reasons)), meta=meta)


adapt_piece_composer_input_contract = build_piece_composer_input_contract
adapt_piece_core_question_answer_plan = build_piece_composer_input_contract


def build_piece_core_text_payloads(plan: Any, **kwargs: Any) -> tuple[CoreTextPayload, CoreTextPayload]:
    contract = build_piece_composer_input_contract(plan, **kwargs)
    return contract.question_payload, contract.answer_payload

__all__ = [
    "ADAPTER_NAME",
    "CHANNEL_ANSWER",
    "CHANNEL_QUESTION",
    "COVERAGE_SCOPE_ANSWER",
    "COVERAGE_SCOPE_QUESTION",
    "PHASE_LABEL",
    "PIECE_INPUT_CONTRACT_MODEL",
    "PAYLOAD_KIND_QUESTION",
    "PAYLOAD_KIND_ANSWER",
    "LEGACY_BOUNDARY_NAMES",
    "PIECE_FORBIDDEN_SURFACE_PATTERNS",
    "PieceComposerInputContract",
    "REJECTION_PIECE_ANSWER_MISSING",
    "REJECTION_PIECE_PLAN_MISSING",
    "REJECTION_PIECE_QUESTION_MISSING",
    "REJECTION_PIECE_SOURCE_MISSING",
    "REJECTION_PIECE_SOURCE_CLAIMS_MISSING",
    "adapt_piece_composer_input_contract",
    "adapt_piece_core_question_answer_plan",
    "build_piece_core_text_payloads",
    "build_piece_composer_input_contract",
    "empty_piece_composer_input_contract",
]
