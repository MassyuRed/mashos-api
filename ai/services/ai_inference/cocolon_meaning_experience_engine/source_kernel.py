# -*- coding: utf-8 -*-
from __future__ import annotations

"""Source-first admission for the text-bearing Emlis CMEE slice."""

from dataclasses import dataclass
import hashlib
import json
import re
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
    CMEE_OBLIGATION_VERSION,
    CMEE_OWNER_UNIVERSE_SCHEMA_VERSION,
    CMEE_SOURCE_CONTRACT_VERSION,
    EvidenceRef,
    GenerationRequest,
    OwnerClass,
    SourceEnvelope,
    SourceOwnerObligation,
    SourceOwnerUniverse,
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
SOURCE_ENCODING = "CMEE_PRIVATE_FIELD_FRAME_UTF8_V1"
_SOURCE_ENVELOPE_ID_SCHEMA = "cocolon.cmee.source_envelope.identity.v2"
_EVIDENCE_ID_SCHEMA = "cocolon.cmee.evidence_ref.identity.v2"
_FRAME_FIELD_PATHS: Tuple[str, ...] = (
    "memo",
    "memo_action",
    "emotion_details.0.type",
    "emotions.0",
    "category.0",
    "emotion_details.0.strength",
)
_TEXT_SOURCE_FIELD_PATHS = {
    "memo": ("memo", -1),
    "memo_action": ("memo_action", -1),
}
_SPACE_RE = re.compile(r"\s+")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _evidence_id(
    *,
    envelope_id: str,
    source_span_id: str,
    field_path: str,
    element_index: int,
    field_utf8_start: int,
    field_utf8_end: int,
    scalar_start: int,
    scalar_end: int,
    utf8_start: int,
    utf8_end: int,
    field_sha256: str,
    literal_sha256: str,
) -> str:
    material = json.dumps(
        {
            "schema": _EVIDENCE_ID_SCHEMA,
            "envelope_id": envelope_id,
            "source_span_id": source_span_id,
            "field_path": field_path,
            "element_index": element_index,
            "field_utf8_range": (field_utf8_start, field_utf8_end),
            "scalar_range": (scalar_start, scalar_end),
            "utf8_byte_range": (utf8_start, utf8_end),
            "field_sha256": field_sha256,
            "literal_sha256": literal_sha256,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"ev-{_sha256(material.encode('utf-8'))[:24]}"


def _source_envelope_id(
    *,
    source_record_id: str,
    source_role: str,
    source_schema_version: str,
    source_contract_version: str,
    source_encoding: str,
    label_contract_id: str,
    label_contract_digest: str,
    raw_sha256: str,
) -> str:
    material = json.dumps(
        {
            "schema": _SOURCE_ENVELOPE_ID_SCHEMA,
            "source_record_id": source_record_id,
            "source_role": source_role,
            "source_schema_version": source_schema_version,
            "source_contract_version": source_contract_version,
            "source_encoding": source_encoding,
            "label_contract_id": label_contract_id,
            "label_contract_digest": label_contract_digest,
            "raw_sha256": raw_sha256,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"src-{_sha256(material.encode('utf-8'))[:24]}"


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


def validate_evidence_refs(
    envelope: SourceEnvelope,
    evidence_refs: Tuple[EvidenceRef, ...],
) -> None:
    """Rebuild every locator from the canonical frame and compare exactly."""

    expected_refs = _canonical_evidence_refs_from_envelope(envelope)
    if not evidence_refs:
        raise SourceAdmissionError("owner_universe_evidence_empty", hard_invalid=False)
    if len({row.evidence_id for row in evidence_refs}) != len(evidence_refs):
        raise SourceAdmissionError("owner_universe_evidence_duplicate")
    if len({row.source_span_id for row in evidence_refs}) != len(evidence_refs):
        raise SourceAdmissionError("owner_universe_source_span_duplicate")
    if len(evidence_refs) != len(expected_refs):
        raise SourceAdmissionError("owner_universe_evidence_canonical_binding_invalid")
    locator_fields = (
        "source_span_id",
        "source_envelope_id",
        "field_path",
        "element_index",
        "field_utf8_start",
        "field_utf8_end",
        "scalar_start",
        "scalar_end",
        "utf8_start",
        "utf8_end",
    )
    for row, expected in zip(evidence_refs, expected_refs, strict=True):
        if any(
            type(getattr(row, name)) is not type(getattr(expected, name))
            or getattr(row, name) != getattr(expected, name)
            for name in locator_fields
        ):
            raise SourceAdmissionError("owner_universe_evidence_canonical_binding_invalid")
        if (
            row.field_sha256 != expected.field_sha256
            or row.literal_sha256 != expected.literal_sha256
            or row.evidence_id != expected.evidence_id
        ):
            raise SourceAdmissionError("owner_universe_evidence_digest_invalid")


@dataclass(frozen=True, slots=True, repr=False)
class AdmittedTextSource:
    envelope: SourceEnvelope
    normalized_current_input: Mapping[str, Any]
    evidence_spans: Tuple[object, ...]
    evidence_refs: Tuple[EvidenceRef, ...]
    owner_universe: SourceOwnerUniverse
    category: str
    emotion: str
    strength: str

    @property
    def categories(self) -> Tuple[str, ...]:
        """Return every admitted category in original source order."""

        value = self.normalized_current_input.get("category", ())
        return tuple(str(item) for item in value) if isinstance(value, list) else ()

    @property
    def emotions(self) -> Tuple[str, ...]:
        """Return every admitted emotion type in original source order."""

        value = self.normalized_current_input.get("emotion_details", ())
        if not isinstance(value, list):
            return ()
        return tuple(
            str(item.get("type"))
            for item in value
            if isinstance(item, Mapping) and isinstance(item.get("type"), str)
        )

    @property
    def strengths(self) -> Tuple[str, ...]:
        """Return every admitted emotion strength in original source order."""

        value = self.normalized_current_input.get("emotion_details", ())
        if not isinstance(value, list):
            return ()
        return tuple(
            str(item.get("strength"))
            for item in value
            if isinstance(item, Mapping) and isinstance(item.get("strength"), str)
        )

    def evidence_ref(self, source_span_id: str) -> EvidenceRef:
        matches = tuple(row for row in self.evidence_refs if row.source_span_id == source_span_id)
        if len(matches) != 1:
            raise SourceAdmissionError("evidence_span_binding_mismatch")
        return matches[0]

    def owner_obligation(self, meaning_owner_id: str) -> SourceOwnerObligation:
        matches = tuple(
            row
            for row in self.owner_universe.obligations
            if row.meaning_owner_id == meaning_owner_id
        )
        if len(matches) != 1:
            raise SourceAdmissionError("meaning_owner_binding_mismatch")
        return matches[0]

    def meaning_owner_for_span(self, source_span_id: str) -> str:
        matches = tuple(
            row.meaning_owner_id
            for row in self.owner_universe.obligations
            if row.obligation_kind
            in {
                "THOUGHT_MEANING",
                "ACTION_MEANING",
                "EMOTION_CONTEXT",
                "CATEGORY_CONTEXT",
                "EMOTION_STRENGTH_CONTEXT",
            }
            and source_span_id in row.source_span_ids
        )
        if len(matches) != 1:
            raise SourceAdmissionError("source_span_owner_binding_mismatch")
        return matches[0]

    def attachment_unknown_obligation(self) -> SourceOwnerObligation:
        matches = tuple(
            row
            for row in self.owner_universe.obligations
            if row.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        if len(matches) != 1:
            raise SourceAdmissionError("attachment_unknown_owner_binding_mismatch")
        return matches[0]


def _meaning_owner_id(
    envelope: SourceEnvelope,
    obligation_kind: str,
    source_span_id: str,
) -> str:
    material = "|".join(
        (
            CMEE_OWNER_UNIVERSE_SCHEMA_VERSION,
            envelope.envelope_id,
            CMEE_OBLIGATION_VERSION,
            obligation_kind,
            source_span_id,
        )
    )
    return f"mo-{_sha256(material.encode('utf-8'))[:24]}"


def build_source_owner_universe(
    envelope: SourceEnvelope,
    evidence_refs: Tuple[EvidenceRef, ...],
) -> SourceOwnerUniverse:
    """Freeze the source-owner denominator without consulting a resolver.

    Canonical thought/action obligations are required. Emotion aliases are
    one active context owner rather than duplicate meaning owners. The
    structured-context attachment is a conditional, source-evidenced semantic
    open slot; it is not the plan's ``PRESERVE_UNKNOWN`` duty.
    """

    validate_evidence_refs(envelope, evidence_refs)
    snapshot, _segments = _validate_source_envelope_identity(envelope)
    categories, emotions, strengths = _ordered_labels(snapshot)

    def refs_for_path(path: str) -> Tuple[EvidenceRef, ...]:
        return tuple(row for row in evidence_refs if row.field_path == path)

    thought_refs = refs_for_path("memo")
    action_refs = refs_for_path("memo_action")
    text_refs = (*thought_refs, *action_refs)
    if not text_refs:
        raise SourceAdmissionError("owner_universe_required_text_empty", hard_invalid=False)
    emotion_detail_refs = tuple(
        row
        for index in range(len(emotions))
        for row in refs_for_path(f"emotion_details.{index}.type")
    )
    emotion_alias_refs = tuple(
        row
        for index in range(len(emotions))
        for row in refs_for_path(f"emotions.{index}")
    )
    emotion_refs = (*emotion_detail_refs, *emotion_alias_refs)
    category_refs = tuple(
        row
        for index in range(len(categories))
        for row in refs_for_path(f"category.{index}")
    )
    strength_refs = tuple(
        row
        for index in range(len(strengths))
        for row in refs_for_path(f"emotion_details.{index}.strength")
    )
    if (
        len(emotion_detail_refs) != len(emotions)
        or len(emotion_alias_refs) != len(emotions)
        or len(category_refs) != len(categories)
        or len(strength_refs) != len(strengths)
    ):
        raise SourceAdmissionError("owner_universe_structured_context_cardinality")
    if any(
        envelope.raw_utf8[detail.utf8_start : detail.utf8_end]
        != envelope.raw_utf8[alias.utf8_start : alias.utf8_end]
        for detail, alias in zip(
            emotion_detail_refs,
            emotion_alias_refs,
            strict=True,
        )
    ):
        raise SourceAdmissionError("owner_universe_emotion_alias_mismatch")

    required_obligations = tuple(
        SourceOwnerObligation(
            meaning_owner_id=_meaning_owner_id(
                envelope,
                obligation_kind,
                source_key,
            ),
            owner_class=OwnerClass.REQUIRED,
            obligation_kind=obligation_kind,
            source_span_ids=tuple(row.source_span_id for row in refs),
            evidence_refs=tuple(row.evidence_id for row in refs),
        )
        for obligation_kind, source_key, refs in (
            ("THOUGHT_MEANING", "field:memo", thought_refs),
            ("ACTION_MEANING", "field:memo_action", action_refs),
        )
        if refs
    )
    structured_context_obligations = tuple(
        SourceOwnerObligation(
            meaning_owner_id=_meaning_owner_id(envelope, obligation_kind, source_key),
            owner_class=OwnerClass.ACTIVE_OPTIONAL,
            obligation_kind=obligation_kind,
            source_span_ids=tuple(row.source_span_id for row in refs),
            evidence_refs=tuple(row.evidence_id for row in refs),
        )
        for obligation_kind, source_key, refs in (
            ("EMOTION_CONTEXT", "field:emotion", emotion_refs),
            ("CATEGORY_CONTEXT", "field:category", category_refs),
            (
                "EMOTION_STRENGTH_CONTEXT",
                "field:emotion_strength",
                strength_refs,
            ),
        )
    )
    attachment_obligation = SourceOwnerObligation(
        meaning_owner_id=_meaning_owner_id(
            envelope,
            "STRUCTURED_CONTEXT_ATTACHMENT",
            "open-slot:text-to-emotion-category",
        ),
        owner_class=OwnerClass.ACTIVE_OPTIONAL,
        obligation_kind="STRUCTURED_CONTEXT_ATTACHMENT",
        source_span_ids=tuple(
            row.source_span_id
            for row in (*text_refs, *emotion_refs, *category_refs)
        ),
        evidence_refs=tuple(
            row.evidence_id
            for row in (*text_refs, *emotion_refs, *category_refs)
        ),
    )
    active_obligations = (*structured_context_obligations, attachment_obligation)
    obligations = (*required_obligations, *active_obligations)
    required_refs = tuple(row.meaning_owner_id for row in required_obligations)
    active_refs = tuple(row.meaning_owner_id for row in active_obligations)
    credit_refs = tuple(
        _meaning_owner_id(envelope, "EXPLICIT_ABSENCE", source_key)
        for source_key, refs in (
            ("field:memo", thought_refs),
            ("field:memo_action", action_refs),
        )
        if not refs
    )
    base_obligations = (*required_obligations, *structured_context_obligations)
    if (
        tuple(
            evidence_id
            for row in base_obligations
            for evidence_id in row.evidence_refs
        )
        != tuple(row.evidence_id for row in evidence_refs)
    ):
        raise SourceAdmissionError("owner_universe_base_evidence_partition_mismatch")
    all_owner_refs = (*required_refs, *active_refs, *credit_refs)
    if len(all_owner_refs) != len(set(all_owner_refs)):
        raise SourceAdmissionError("owner_universe_owner_duplicate")

    digest_payload = {
        "schema_version": CMEE_OWNER_UNIVERSE_SCHEMA_VERSION,
        "source_envelope_id": envelope.envelope_id,
        "source_version": envelope.source_contract_version,
        "obligation_version": CMEE_OBLIGATION_VERSION,
        "required_owner_refs": required_refs,
        "active_optional_owner_refs": active_refs,
        "credit_only_owner_refs": credit_refs,
        "obligations": [
            {
                "meaning_owner_id": row.meaning_owner_id,
                "owner_class": row.owner_class.value,
                "obligation_kind": row.obligation_kind,
                "source_span_ids": row.source_span_ids,
                "evidence_refs": row.evidence_refs,
            }
            for row in obligations
        ],
    }
    digest = _sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return SourceOwnerUniverse(
        schema_version=CMEE_OWNER_UNIVERSE_SCHEMA_VERSION,
        source_envelope_id=envelope.envelope_id,
        source_version=envelope.source_contract_version,
        obligation_version=CMEE_OBLIGATION_VERSION,
        required_owner_refs=required_refs,
        active_optional_owner_refs=active_refs,
        credit_only_owner_refs=credit_refs,
        obligations=obligations,
        owner_universe_digest=digest,
    )


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


def _ordered_labels(
    raw: Mapping[str, Any],
) -> tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """Validate and retain the complete ordered structured-label source.

    ``emotion_details`` is the strength-bearing canonical field and
    ``emotions`` is its exact ordered type alias.  Keeping both sequences in
    the admitted frame makes alias agreement independently reconstructible;
    neither sequence is collapsed to its first item.
    """

    categories = _alias_list(raw, ("category", "categories"))
    if not categories or any(not isinstance(item, str) for item in categories):
        raise SourceAdmissionError("category_required")
    if len(categories) != len(set(categories)):
        raise SourceAdmissionError("category_duplicate")
    if any(category not in CANONICAL_CATEGORIES for category in categories):
        raise SourceAdmissionError("category_noncanonical")

    details = _alias_list(raw, ("emotion_details", "emotionDetails"))
    if not details or any(not isinstance(item, Mapping) for item in details):
        raise SourceAdmissionError("emotion_detail_required")
    emotions: list[str] = []
    strengths: list[str] = []
    for detail in details:
        if set(detail).difference({"type", "strength"}):
            raise SourceAdmissionError("emotion_detail_unknown_field")
        emotion = detail.get("type")
        strength = detail.get("strength")
        if not isinstance(emotion, str) or not isinstance(strength, str):
            raise SourceAdmissionError("emotion_detail_literal_required")
        if emotion not in CANONICAL_EMOTIONS:
            raise SourceAdmissionError("emotion_noncanonical")
        if strength not in CANONICAL_STRENGTHS:
            raise SourceAdmissionError("emotion_strength_noncanonical")
        if emotion == "自己理解" and strength != "medium":
            raise SourceAdmissionError("self_insight_requires_medium_strength")
        emotions.append(emotion)
        strengths.append(strength)
    if len(emotions) != len(set(emotions)):
        raise SourceAdmissionError("emotion_duplicate")
    if "自己理解" in emotions and len(emotions) != 1:
        raise SourceAdmissionError("self_insight_requires_exclusive")

    simple = _alias_list(raw, ("emotions", "emotion"))
    if tuple(simple) != tuple(emotions):
        raise SourceAdmissionError("emotion_fields_conflict")
    return tuple(categories), tuple(emotions), tuple(strengths)


def _exact_labels(raw: Mapping[str, Any]) -> tuple[str, str, str]:
    """Compatibility view for the existing exact-one Stage 1 consumers.

    Source admission and source ownership use :func:`_ordered_labels`; this
    view intentionally exposes only the historical primary fields so the
    exact-one production representative keeps its byte and object identity.
    """

    categories, emotions, strengths = _ordered_labels(raw)
    return categories[0], emotions[0], strengths[0]


def _source_leaf_values(
    snapshot: Mapping[str, Any],
) -> tuple[
    str,
    str,
    Tuple[str, ...],
    Tuple[str, ...],
    Tuple[str, ...],
    Tuple[str, ...],
]:
    if not (
        isinstance(snapshot.get("memo"), str)
        and isinstance(snapshot.get("memo_action"), str)
        and isinstance(snapshot.get("category"), list)
        and bool(snapshot["category"])
        and isinstance(snapshot.get("emotion_details"), list)
        and bool(snapshot["emotion_details"])
        and all(isinstance(item, Mapping) for item in snapshot["emotion_details"])
        and isinstance(snapshot.get("emotions"), list)
        and bool(snapshot["emotions"])
    ):
        raise SourceAdmissionError("noncanonical_current_input_source_shape")
    categories, emotions, strengths = _ordered_labels(snapshot)
    simple_emotions = tuple(snapshot["emotions"])
    values = (
        snapshot["memo"],
        snapshot["memo_action"],
        emotions,
        simple_emotions,
        categories,
        strengths,
    )
    if not all(
        isinstance(value, str)
        for group in values[2:]
        for value in group
    ):
        raise SourceAdmissionError("noncanonical_current_input_source_leaf")
    return values


def _frame_field_rows(snapshot: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    (
        raw_memo,
        raw_action,
        raw_emotions,
        raw_simple_emotions,
        raw_categories,
        raw_strengths,
    ) = _source_leaf_values(snapshot)
    rows = (
        ("memo", raw_memo),
        ("memo_action", raw_action),
        *tuple(
            (f"emotion_details.{index}.type", value)
            for index, value in enumerate(raw_emotions)
        ),
        *tuple(
            (f"emotions.{index}", value)
            for index, value in enumerate(raw_simple_emotions)
        ),
        *tuple(
            (f"category.{index}", value)
            for index, value in enumerate(raw_categories)
        ),
        *tuple(
            (f"emotion_details.{index}.strength", value)
            for index, value in enumerate(raw_strengths)
        ),
    )
    if len(raw_emotions) == len(raw_categories) == 1:
        if tuple(path for path, _value in rows) != _FRAME_FIELD_PATHS:
            raise SourceAdmissionError("exact1_source_frame_identity_changed")
    return rows


def normalize_evidence_literal(value: str) -> str:
    """Match the legacy ledger's display-only whitespace normalization."""

    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


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
    raw_slice = raw_field_text[raw_character_start:raw_character_end]
    if normalize_evidence_literal(raw_slice) != str(
        getattr(span, "raw_text", "") or ""
    ):
        raise SourceAdmissionError("evidence_scalar_offset_alignment_mismatch")
    return raw_character_start, raw_character_end


def _parse_length_prefixed_segment(
    raw_utf8: bytes,
    cursor: int,
    marker: bytes,
) -> tuple[int, int, int]:
    if not raw_utf8.startswith(marker, cursor):
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    length_start = cursor + len(marker)
    length_end = raw_utf8.find(b"\n", length_start)
    if length_end < 0:
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    length_literal = raw_utf8[length_start:length_end]
    if (
        not length_literal
        or not length_literal.isdigit()
        or length_literal != str(int(length_literal)).encode("ascii")
    ):
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    body_start = length_end + 1
    body_end = body_start + int(length_literal)
    if body_end > len(raw_utf8):
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    return body_start, body_end, body_end


def _parse_canonical_frame(
    raw_utf8: bytes,
) -> tuple[Mapping[str, Any], Mapping[str, tuple[int, int, str]]]:
    if not isinstance(raw_utf8, bytes):
        raise SourceAdmissionError("owner_universe_source_envelope_invalid")
    prefix = f"{SOURCE_ENCODING}\n@raw_json:".encode("ascii")
    raw_json_start, raw_json_end, cursor = _parse_length_prefixed_segment(
        raw_utf8,
        0,
        prefix,
    )
    canonical_raw = raw_utf8[raw_json_start:raw_json_end]
    try:
        snapshot = json.loads(canonical_raw.decode("utf-8"))
        raw_utf8.decode("utf-8")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SourceAdmissionError("owner_universe_source_frame_invalid") from None
    if not isinstance(snapshot, Mapping) or _canonical_json(snapshot) != canonical_raw:
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    field_rows = _frame_field_rows(snapshot)
    expected_values = dict(field_rows)
    segments: dict[str, tuple[int, int, str]] = {}
    for path, _expected_value in field_rows:
        start, end, cursor = _parse_length_prefixed_segment(
            raw_utf8,
            cursor,
            f"\n@original.{path}:".encode("utf-8"),
        )
        try:
            value = raw_utf8[start:end].decode("utf-8")
        except UnicodeDecodeError:
            raise SourceAdmissionError("owner_universe_source_frame_invalid") from None
        if value != expected_values[path]:
            raise SourceAdmissionError("owner_universe_source_field_frame_mismatch")
        segments[path] = (start, end, value)
    if cursor != len(raw_utf8):
        raise SourceAdmissionError("owner_universe_source_frame_invalid")
    return snapshot, segments


def _validate_source_envelope_identity(
    envelope: SourceEnvelope,
) -> tuple[Mapping[str, Any], Mapping[str, tuple[int, int, str]]]:
    raw_digest = _sha256(envelope.raw_utf8) if isinstance(envelope.raw_utf8, bytes) else ""
    if (
        envelope.source_role != "CURRENT_INPUT"
        or envelope.source_schema_version != EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION
        or envelope.source_contract_version != CMEE_SOURCE_CONTRACT_VERSION
        or envelope.source_encoding != SOURCE_ENCODING
        or envelope.label_contract_id != LABEL_CONTRACT_ID
        or envelope.label_contract_digest != LABEL_CONTRACT_DIGEST
        or raw_digest != envelope.raw_sha256
    ):
        raise SourceAdmissionError("owner_universe_source_envelope_invalid")
    snapshot, segments = _parse_canonical_frame(envelope.raw_utf8)
    categories, emotions, strengths = _ordered_labels(snapshot)
    (
        raw_memo,
        raw_action,
        raw_emotions,
        raw_simple_emotions,
        raw_categories,
        raw_strengths,
    ) = _source_leaf_values(snapshot)
    if (
        raw_categories != categories
        or raw_emotions != emotions
        or raw_simple_emotions != emotions
        or raw_strengths != strengths
    ):
        raise SourceAdmissionError("owner_universe_source_label_binding_mismatch")
    source_record_id = _alias_text(
        snapshot,
        ("id", "source_record_id", "sourceRecordId"),
    )
    thought = _alias_text(
        snapshot,
        ("memo", "thought_text", "thoughtText", "memo_text", "memoText"),
    )
    action = _alias_text(
        snapshot,
        ("memo_action", "action_text", "actionText", "memoAction"),
    )
    if thought != _clean(raw_memo) or action != _clean(raw_action):
        raise SourceAdmissionError("owner_universe_source_text_binding_mismatch")
    if not thought and not action:
        raise SourceAdmissionError("text_grounded_material_required", hard_invalid=False)
    if bool(snapshot.get("is_secret", snapshot.get("isSecret", False))):
        raise SourceAdmissionError("secret_input_out_of_scope", hard_invalid=False)
    expected_envelope_id = _source_envelope_id(
        source_record_id=source_record_id,
        source_role=envelope.source_role,
        source_schema_version=envelope.source_schema_version,
        source_contract_version=envelope.source_contract_version,
        source_encoding=envelope.source_encoding,
        label_contract_id=envelope.label_contract_id,
        label_contract_digest=envelope.label_contract_digest,
        raw_sha256=envelope.raw_sha256,
    )
    if (
        not source_record_id
        or envelope.source_record_id != source_record_id
        or envelope.envelope_id != expected_envelope_id
    ):
        raise SourceAdmissionError("owner_universe_source_envelope_identity_mismatch")
    return snapshot, segments


def _canonical_evidence_refs_from_envelope(
    envelope: SourceEnvelope,
) -> Tuple[EvidenceRef, ...]:
    snapshot, segments = _validate_source_envelope_identity(envelope)
    normalized = normalize_emlis_current_input(snapshot)
    spans = tuple(build_evidence_ledger(normalized))
    if not spans:
        raise SourceAdmissionError("evidence_ledger_empty", hard_invalid=False)
    build_evidence_span_resolver(spans, current_input=normalized)

    categories, emotions, strengths = _ordered_labels(snapshot)
    structured_paths = {
        "emotion_details": tuple(
            f"emotion_details.{index}.type" for index in range(len(emotions))
        ),
        "emotions": tuple(f"emotions.{index}" for index in range(len(emotions))),
        "category": tuple(
            f"category.{index}" for index in range(len(categories))
        ),
    }
    structured_cursors = {field: 0 for field in structured_paths}
    locator_rows: list[tuple[str, str, int, int, int, int, int]] = []
    for span in spans:
        source_field = str(getattr(span, "source_field", "") or "")
        literal = str(getattr(span, "raw_text", "") or "")
        if not literal:
            raise SourceAdmissionError("evidence_original_field_binding_missing")
        if source_field in _TEXT_SOURCE_FIELD_PATHS:
            path, element_index = _TEXT_SOURCE_FIELD_PATHS[source_field]
        elif source_field in structured_paths:
            cursor = structured_cursors[source_field]
            paths = structured_paths[source_field]
            if cursor >= len(paths):
                raise SourceAdmissionError(
                    "evidence_structured_leaf_cardinality_mismatch"
                )
            path = paths[cursor]
            element_index = cursor
            structured_cursors[source_field] = cursor + 1
        else:
            raise SourceAdmissionError("evidence_original_field_binding_missing")
        field_start, field_end, raw_value = segments[path]
        if source_field in {"memo", "memo_action"}:
            scalar_start, scalar_end = _text_span_raw_subrange(
                raw_field_text=raw_value,
                normalized_field_text=str(normalized.get(source_field) or ""),
                span=span,
            )
        else:
            if raw_value != literal:
                raise SourceAdmissionError("evidence_structured_leaf_binding_mismatch")
            scalar_start, scalar_end = 0, len(raw_value)
        locator_rows.append(
            (
                str(getattr(span, "span_id", "") or ""),
                path,
                element_index,
                field_start,
                field_end,
                scalar_start,
                scalar_end,
            )
        )
    if any(
        structured_cursors[field] != len(paths)
        for field, paths in structured_paths.items()
    ):
        raise SourceAdmissionError("evidence_structured_leaf_cardinality_mismatch")
    for index, _strength in enumerate(strengths):
        strength_path = f"emotion_details.{index}.strength"
        strength_start, strength_end, strength_value = segments[strength_path]
        locator_rows.append(
            (
                (
                    "structured:emotion_strength"
                    if index == 0
                    else f"structured:emotion_strength:{index}"
                ),
                strength_path,
                index,
                strength_start,
                strength_end,
                0,
                len(strength_value),
            )
        )

    refs: list[EvidenceRef] = []
    for (
        source_span_id,
        field_path,
        element_index,
        field_start,
        field_end,
        scalar_start,
        scalar_end,
    ) in locator_rows:
        raw_value = segments[field_path][2]
        utf8_start = field_start + len(raw_value[:scalar_start].encode("utf-8"))
        utf8_end = field_start + len(raw_value[:scalar_end].encode("utf-8"))
        literal_bytes = envelope.raw_utf8[utf8_start:utf8_end]
        field_bytes = envelope.raw_utf8[field_start:field_end]
        if raw_value[scalar_start:scalar_end].encode("utf-8") != literal_bytes:
            raise SourceAdmissionError("evidence_scalar_utf8_locator_mismatch")
        literal_digest = _sha256(literal_bytes)
        field_digest = _sha256(field_bytes)
        evidence_id = _evidence_id(
            envelope_id=envelope.envelope_id,
            source_span_id=source_span_id,
            field_path=field_path,
            element_index=element_index,
            field_utf8_start=field_start,
            field_utf8_end=field_end,
            scalar_start=scalar_start,
            scalar_end=scalar_end,
            utf8_start=utf8_start,
            utf8_end=utf8_end,
            field_sha256=field_digest,
            literal_sha256=literal_digest,
        )
        refs.append(
            EvidenceRef(
                evidence_id=evidence_id,
                source_span_id=source_span_id,
                source_envelope_id=envelope.envelope_id,
                field_path=field_path,
                element_index=element_index,
                field_utf8_start=field_start,
                field_utf8_end=field_end,
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                utf8_start=utf8_start,
                utf8_end=utf8_end,
                field_sha256=field_digest,
                literal_sha256=literal_digest,
            )
        )
    return tuple(refs)


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
    (
        raw_memo,
        raw_action,
        _raw_emotions,
        _raw_simple_emotions,
        _raw_categories,
        _raw_strengths,
    ) = _source_leaf_values(snapshot)

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
    categories, emotions, strengths = _ordered_labels(snapshot)
    if tuple(bundle.categories) != categories or len(bundle.emotions) != len(emotions):
        raise SourceAdmissionError("structured_bundle_binding_mismatch")
    if tuple(
        (bundled_emotion.type, bundled_emotion.strength)
        for bundled_emotion in bundle.emotions
    ) != tuple(zip(emotions, strengths, strict=True)):
        raise SourceAdmissionError("emotion_bundle_binding_mismatch")

    normalized = normalize_emlis_current_input(snapshot)
    spans = tuple(build_evidence_ledger(normalized))
    if not spans:
        raise SourceAdmissionError("evidence_ledger_empty", hard_invalid=False)
    build_evidence_span_resolver(spans, current_input=normalized)

    frame = bytearray(f"{SOURCE_ENCODING}\n@raw_json:".encode("ascii"))
    frame.extend(str(len(canonical_raw)).encode("ascii"))
    frame.extend(b"\n")
    frame.extend(canonical_raw)
    # Each segment stores the original admitted field value, not a normalized
    # ledger copy. Evidence ranges below point into these original-value
    # segments and are independently checked byte-for-byte.
    for path, raw_value in _frame_field_rows(snapshot):
        _append_field(frame, f"original.{path}", raw_value)

    raw_utf8 = bytes(frame)
    raw_digest = _sha256(raw_utf8)
    envelope_id = _source_envelope_id(
        source_record_id=source_record_id,
        source_role="CURRENT_INPUT",
        source_schema_version=bundle.schema_version,
        source_contract_version=CMEE_SOURCE_CONTRACT_VERSION,
        source_encoding=SOURCE_ENCODING,
        label_contract_id=LABEL_CONTRACT_ID,
        label_contract_digest=LABEL_CONTRACT_DIGEST,
        raw_sha256=raw_digest,
    )
    envelope = SourceEnvelope(
        envelope_id=envelope_id,
        source_record_id=source_record_id,
        source_role="CURRENT_INPUT",
        source_schema_version=bundle.schema_version,
        source_contract_version=CMEE_SOURCE_CONTRACT_VERSION,
        source_encoding=SOURCE_ENCODING,
        label_contract_id=LABEL_CONTRACT_ID,
        label_contract_digest=LABEL_CONTRACT_DIGEST,
        raw_utf8=raw_utf8,
        raw_sha256=raw_digest,
    )

    refs = list(_canonical_evidence_refs_from_envelope(envelope))
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
            or field_body.decode("utf-8")[
                ref.scalar_start : ref.scalar_end
            ].encode("utf-8")
            != literal
        ):
            raise SourceAdmissionError("evidence_scalar_utf8_locator_mismatch")

    owner_universe = build_source_owner_universe(envelope, tuple(refs))
    return AdmittedTextSource(
        envelope=envelope,
        normalized_current_input=normalized,
        evidence_spans=spans,
        evidence_refs=tuple(refs),
        owner_universe=owner_universe,
        category=categories[0],
        emotion=emotions[0],
        strength=strengths[0],
    )


__all__ = [
    "AdmittedTextSource",
    "CANONICAL_CATEGORIES",
    "CANONICAL_EMOTIONS",
    "CANONICAL_STRENGTHS",
    "LABEL_CONTRACT_DIGEST",
    "LABEL_CONTRACT_ID",
    "SourceAdmissionError",
    "build_source_owner_universe",
    "freeze_text_source",
    "validate_evidence_refs",
]
