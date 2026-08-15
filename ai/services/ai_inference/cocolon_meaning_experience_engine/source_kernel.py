# -*- coding: utf-8 -*-
from __future__ import annotations

"""Source-first admission for the text-bearing Emlis CMEE slice."""

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

from emlis_ai_current_input_bundle import (
    EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
    EmlisCurrentInputBundle,
    normalize_emlis_current_input,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)

from .contracts import (
    CMEE_SOURCE_CONTRACT_VERSION,
    EvidenceRef,
    GenerationRequest,
    SourceEnvelope,
)


CANONICAL_CATEGORIES: Tuple[str, ...] = (
    "生活",
    "仕事",
    "趣味",
    "人間関係",
    "恋愛",
    "健康",
    "学習",
    "価値観",
    "人生",
)
CANONICAL_EMOTIONS: Tuple[str, ...] = ("喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解")
CANONICAL_STRENGTHS: Tuple[str, ...] = ("weak", "medium", "strong")
LABEL_CONTRACT_ID = (
    "cocolon.input_options.de9c3d985053bbaaa7fc0d396e688cc2097ece40."
    "59f615cbf513d7901b0b1075cc63d4fd799c5b08"
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


LABEL_CONTRACT_DIGEST = _sha256(
    json.dumps(
        {
            "categories": CANONICAL_CATEGORIES,
            "emotions": CANONICAL_EMOTIONS,
            "strengths": CANONICAL_STRENGTHS,
            "self_insight_strength": "medium",
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
)


class SourceAdmissionError(ValueError):
    def __init__(self, reason_code: str, *, hard_invalid: bool = True) -> None:
        self.reason_code = str(reason_code or "source_admission_failed")
        self.hard_invalid = bool(hard_invalid)
        super().__init__(self.reason_code)


@dataclass(frozen=True, slots=True, repr=False)
class AdmittedTextSource:
    envelope: SourceEnvelope
    normalized_current_input: Mapping[str, Any]
    evidence_spans: Tuple[object, ...]
    evidence_refs: Tuple[EvidenceRef, ...]
    category: str
    emotion: str
    strength: str

    def evidence_ref(self, source_span_id: str) -> EvidenceRef:
        matches = tuple(row for row in self.evidence_refs if row.source_span_id == source_span_id)
        if len(matches) != 1:
            raise SourceAdmissionError("evidence_span_binding_mismatch")
        return matches[0]


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    raise SourceAdmissionError("current_input_contains_non_json_value")


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            _json_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise SourceAdmissionError("current_input_canonicalization_failed") from None


def _clean(value: Any) -> str:
    return str(value or "").replace("\u3000", " ").strip()


def _list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return [] if value is None else [value]


def _alias_text(data: Mapping[str, Any], keys: Tuple[str, ...]) -> str:
    present = tuple(_clean(data[key]) for key in keys if key in data and _clean(data[key]))
    if len(set(present)) > 1:
        raise SourceAdmissionError(f"alias_conflict:{keys[0]}")
    return present[0] if present else ""


def _alias_list(data: Mapping[str, Any], keys: Tuple[str, ...]) -> list[Any]:
    present = tuple(_list(data[key]) for key in keys if key in data)
    if not present:
        return []
    canonical = tuple(json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True) for value in present)
    if len(set(canonical)) > 1:
        raise SourceAdmissionError(f"alias_conflict:{keys[0]}")
    return present[0]


def _exact_labels(raw: Mapping[str, Any]) -> tuple[str, str, str]:
    categories = _alias_list(raw, ("category", "categories"))
    if len(categories) != 1 or not isinstance(categories[0], str):
        raise SourceAdmissionError("category_exact1_required")
    category = categories[0]
    if category not in CANONICAL_CATEGORIES:
        raise SourceAdmissionError("category_noncanonical")

    details = _alias_list(raw, ("emotion_details", "emotionDetails"))
    if len(details) != 1 or not isinstance(details[0], Mapping):
        raise SourceAdmissionError("emotion_detail_exact1_required")
    if set(details[0]).difference({"type", "strength"}):
        raise SourceAdmissionError("emotion_detail_unknown_field")
    emotion = details[0].get("type")
    strength = details[0].get("strength")
    if not isinstance(emotion, str) or not isinstance(strength, str):
        raise SourceAdmissionError("emotion_detail_literal_required")
    if emotion not in CANONICAL_EMOTIONS:
        raise SourceAdmissionError("emotion_noncanonical")
    if strength not in CANONICAL_STRENGTHS:
        raise SourceAdmissionError("emotion_strength_noncanonical")
    if emotion == "自己理解" and strength != "medium":
        raise SourceAdmissionError("self_insight_requires_medium_strength")

    simple = _alias_list(raw, ("emotions", "emotion"))
    if simple and (len(simple) != 1 or simple[0] != emotion):
        raise SourceAdmissionError("emotion_fields_conflict")
    return category, emotion, strength


def _append_field(buffer: bytearray, path: str, literal: str) -> tuple[int, int]:
    raw = literal.encode("utf-8")
    header = f"\n@{path}:{len(raw)}\n".encode("utf-8")
    buffer.extend(header)
    start = len(buffer)
    buffer.extend(raw)
    end = len(buffer)
    return start, end


def _text_span_raw_subrange(
    *,
    raw_field_text: str,
    field_start: int,
    normalized_field_text: str,
    span: object,
) -> tuple[int, int]:
    translated = raw_field_text.replace("\u3000", " ")
    left_trim = len(translated) - len(translated.lstrip())
    if translated.strip() != normalized_field_text:
        raise SourceAdmissionError("evidence_raw_field_normalization_mismatch")
    start_index = getattr(span, "start_index", None)
    end_index = getattr(span, "end_index", None)
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        raise SourceAdmissionError("evidence_scalar_offset_missing")
    if start_index < 0 or end_index <= start_index or end_index > len(normalized_field_text):
        raise SourceAdmissionError("evidence_scalar_offset_invalid")
    raw_character_start = left_trim + start_index
    raw_character_end = left_trim + end_index
    translated_slice = translated[raw_character_start:raw_character_end]
    if translated_slice != str(getattr(span, "raw_text", "") or ""):
        raise SourceAdmissionError("evidence_scalar_offset_alignment_mismatch")
    start = field_start + len(raw_field_text[:raw_character_start].encode("utf-8"))
    end = field_start + len(raw_field_text[:raw_character_end].encode("utf-8"))
    return start, end


def freeze_text_source(request: GenerationRequest) -> AdmittedTextSource:
    """Freeze exact private source material, validate it, then build the ledger."""

    bundle = request.current_input_bundle
    if not isinstance(bundle, EmlisCurrentInputBundle):
        raise SourceAdmissionError("emlis_current_input_bundle_required")
    if bundle.schema_version != EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION:
        raise SourceAdmissionError("current_input_bundle_schema_mismatch")
    raw = bundle.raw_current_input
    if not isinstance(raw, Mapping) or not raw:
        raise SourceAdmissionError("raw_current_input_required")

    # The private canonical snapshot is taken before CMEE calls any legacy
    # normalizer, parser or meaning compiler.
    canonical_raw = _canonical_json(raw)
    snapshot = json.loads(canonical_raw.decode("utf-8"))
    if not isinstance(snapshot, Mapping):
        raise SourceAdmissionError("current_input_snapshot_invalid")
    if not (
        isinstance(snapshot.get("memo"), str)
        and isinstance(snapshot.get("memo_action"), str)
        and isinstance(snapshot.get("category"), list)
        and len(snapshot["category"]) == 1
        and isinstance(snapshot.get("emotion_details"), list)
        and len(snapshot["emotion_details"]) == 1
        and isinstance(snapshot["emotion_details"][0], Mapping)
        and isinstance(snapshot.get("emotions"), list)
        and len(snapshot["emotions"]) == 1
    ):
        raise SourceAdmissionError("noncanonical_current_input_source_shape")
    raw_memo = snapshot["memo"]
    raw_action = snapshot["memo_action"]
    raw_category = snapshot["category"][0]
    raw_emotion = snapshot["emotion_details"][0].get("type")
    raw_strength = snapshot["emotion_details"][0].get("strength")
    raw_simple_emotion = snapshot["emotions"][0]
    if not all(
        isinstance(value, str)
        for value in (raw_category, raw_emotion, raw_strength, raw_simple_emotion)
    ):
        raise SourceAdmissionError("noncanonical_current_input_source_leaf")

    source_record_id = _alias_text(snapshot, ("id", "source_record_id", "sourceRecordId"))
    if not source_record_id or source_record_id != _clean(request.expected_source_record_id):
        raise SourceAdmissionError("source_record_binding_mismatch")
    if source_record_id != _clean(bundle.source_record_id):
        raise SourceAdmissionError("source_record_bundle_binding_mismatch")
    if bool(bundle.is_secret) or bool(snapshot.get("is_secret", snapshot.get("isSecret", False))):
        raise SourceAdmissionError("secret_input_out_of_scope", hard_invalid=False)

    thought = _alias_text(snapshot, ("memo", "thought_text", "thoughtText", "memo_text", "memoText"))
    action = _alias_text(snapshot, ("memo_action", "action_text", "actionText", "memoAction"))
    if not thought and not action:
        raise SourceAdmissionError("text_grounded_material_required", hard_invalid=False)
    if thought != _clean(bundle.thought_text) or action != _clean(bundle.action_text):
        raise SourceAdmissionError("text_bundle_binding_mismatch")
    category, emotion, strength = _exact_labels(snapshot)
    if tuple(bundle.categories) != (category,) or len(bundle.emotions) != 1:
        raise SourceAdmissionError("structured_bundle_binding_mismatch")
    bundled_emotion = bundle.emotions[0]
    if bundled_emotion.type != emotion or bundled_emotion.strength != strength:
        raise SourceAdmissionError("emotion_bundle_binding_mismatch")

    normalized = normalize_emlis_current_input(snapshot)
    spans = tuple(build_evidence_ledger(normalized))
    if not spans:
        raise SourceAdmissionError("evidence_ledger_empty", hard_invalid=False)
    build_evidence_span_resolver(spans, current_input=normalized)

    frame = bytearray(b"CMEE_PRIVATE_FIELD_FRAME_UTF8_V1\n@raw_json:")
    frame.extend(str(len(canonical_raw)).encode("ascii"))
    frame.extend(b"\n")
    frame.extend(canonical_raw)
    # Each segment stores the original admitted field value, not a normalized
    # ledger copy. Evidence ranges below point into these original-value
    # segments and are independently checked byte-for-byte.
    original_fields = {
        "memo": ("memo", raw_memo, thought, -1),
        "memo_action": ("memo_action", raw_action, action, -1),
        "emotion_details": ("emotion_details.0.type", raw_emotion, emotion, 0),
        "emotions": ("emotions.0", raw_simple_emotion, emotion, 0),
        "category": ("category.0", raw_category, category, 0),
    }
    field_segments: dict[str, tuple[str, str, str, int, int, int]] = {}
    for source_field, (path, raw_value, normalized_value, element_index) in original_fields.items():
        start, end = _append_field(frame, f"original.{path}", raw_value)
        field_segments[source_field] = (
            path,
            raw_value,
            normalized_value,
            element_index,
            start,
            end,
        )
    strength_start, strength_end = _append_field(
        frame, "original.emotion_details.0.strength", raw_strength
    )

    locations: list[tuple[object, int, int, str, int, int, int]] = []
    for span in spans:
        literal = str(getattr(span, "raw_text", "") or "")
        source_field = str(getattr(span, "source_field", "") or "")
        if source_field not in field_segments or not literal:
            raise SourceAdmissionError("evidence_original_field_binding_missing")
        path, raw_value, normalized_value, element_index, field_start, field_end = field_segments[
            source_field
        ]
        if source_field in {"memo", "memo_action"}:
            start, end = _text_span_raw_subrange(
                raw_field_text=raw_value,
                field_start=field_start,
                normalized_field_text=normalized_value,
                span=span,
            )
        else:
            if raw_value != literal:
                raise SourceAdmissionError("evidence_structured_leaf_binding_mismatch")
            start, end = field_start, field_end
        locations.append(
            (span, start, end, path, element_index, field_start, field_end)
        )

    raw_utf8 = bytes(frame)
    raw_digest = _sha256(raw_utf8)
    envelope_id = f"src-{_sha256((source_record_id + '|' + raw_digest).encode('utf-8'))[:24]}"
    envelope = SourceEnvelope(
        envelope_id=envelope_id,
        source_record_id=source_record_id,
        source_role="CURRENT_INPUT",
        source_schema_version=bundle.schema_version,
        source_contract_version=CMEE_SOURCE_CONTRACT_VERSION,
        source_encoding="CMEE_PRIVATE_FIELD_FRAME_UTF8_V1",
        label_contract_id=LABEL_CONTRACT_ID,
        label_contract_digest=LABEL_CONTRACT_DIGEST,
        raw_utf8=raw_utf8,
        raw_sha256=raw_digest,
    )

    refs: list[EvidenceRef] = []
    for span, start, end, field_path, element_index, field_start, field_end in locations:
        literal_bytes = raw_utf8[start:end]
        span_id = str(getattr(span, "span_id", "") or "")
        literal_digest = _sha256(literal_bytes)
        field_digest = _sha256(raw_utf8[field_start:field_end])
        refs.append(
            EvidenceRef(
                evidence_id=f"ev-{_sha256((envelope_id + '|' + span_id + '|' + field_path + '|' + str(element_index) + '|' + str(start) + ':' + str(end) + '|' + literal_digest).encode('utf-8'))[:24]}",
                source_span_id=span_id,
                source_envelope_id=envelope_id,
                field_path=field_path,
                element_index=element_index,
                field_utf8_start=field_start,
                field_utf8_end=field_end,
                utf8_start=start,
                utf8_end=end,
                field_sha256=field_digest,
                literal_sha256=literal_digest,
            )
        )
    refs.append(
        EvidenceRef(
            evidence_id=f"ev-{_sha256((envelope_id + '|structured:emotion_strength|' + strength).encode('utf-8'))[:24]}",
            source_span_id="structured:emotion_strength",
            source_envelope_id=envelope_id,
            field_path="emotion_details.0.strength",
            element_index=0,
            field_utf8_start=strength_start,
            field_utf8_end=strength_end,
            utf8_start=strength_start,
            utf8_end=strength_end,
            field_sha256=_sha256(raw_utf8[strength_start:strength_end]),
            literal_sha256=_sha256(raw_utf8[strength_start:strength_end]),
        )
    )
    for ref in refs:
        literal = envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
        field_body = envelope.raw_utf8[ref.field_utf8_start : ref.field_utf8_end]
        if (
            _sha256(literal) != ref.literal_sha256
            or _sha256(field_body) != ref.field_sha256
            or not (
                ref.field_utf8_start
                <= ref.utf8_start
                < ref.utf8_end
                <= ref.field_utf8_end
            )
        ):
            raise SourceAdmissionError("evidence_utf8_locator_mismatch")

    return AdmittedTextSource(
        envelope=envelope,
        normalized_current_input=normalized,
        evidence_spans=spans,
        evidence_refs=tuple(refs),
        category=category,
        emotion=emotion,
        strength=strength,
    )


__all__ = [
    "AdmittedTextSource",
    "CANONICAL_CATEGORIES",
    "CANONICAL_EMOTIONS",
    "CANONICAL_STRENGTHS",
    "LABEL_CONTRACT_DIGEST",
    "LABEL_CONTRACT_ID",
    "SourceAdmissionError",
    "freeze_text_source",
]
