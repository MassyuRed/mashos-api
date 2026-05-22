# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 5 Observation Dictionary Schema and loader for EmlisAI.

This module owns the material dictionary contract for observation replies.  It
keeps the dictionary as phrase material, not as completed reply templates:

* positive entries are fragments such as receive phrases, relation phrases,
  humility markers, and question endings;
* forbidden template signatures are guard material only and are never selected
  as positive surface material;
* no public ``observation_status`` enum, API route, DB physical name, RN visible
  contract, Display Gate, or generated ``comment_text`` is changed here.

Step 5 deliberately stops at schema/loader/validator.  Later steps may connect
validated entries to material, sentence planning, surface realization, and
Template Guard.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Final

from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
)

OBSERVATION_DICTIONARY_SCHEMA_VERSION: Final = "emlis.observation_dictionary.v1"
OBSERVATION_DICTIONARY_STEP: Final = "Step5_Observation_Dictionary_Schema"
OBSERVATION_DICTIONARY_DEFAULT_VERSION: Final = "emlis.observation_dictionary.default.2026-05-20"

CATEGORY_RECEIVE_PHRASE: Final = "receive_phrase"
CATEGORY_ARRANGEMENT_CONNECTOR: Final = "arrangement_connector"
CATEGORY_RELATION_PHRASE: Final = "relation_phrase"
CATEGORY_HUMILITY_MARKER: Final = "humility_marker"
CATEGORY_UNKNOWN_SLOT_MARKER: Final = "unknown_slot_marker"
CATEGORY_QUESTION_ENDING: Final = "question_ending"
CATEGORY_KNOWN_SCOPE_PHRASE: Final = "known_scope_phrase"
CATEGORY_BURDEN_PHRASE: Final = "burden_phrase"
CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE: Final = "forbidden_template_signature"

EVIDENCE_ROLE_STATE: Final = "state"
EVIDENCE_ROLE_TARGET: Final = "target"
EVIDENCE_ROLE_WISH: Final = "wish"
EVIDENCE_ROLE_BLOCKAGE: Final = "blockage"
EVIDENCE_ROLE_CONTRAST: Final = "contrast"
EVIDENCE_ROLE_REPETITION: Final = "repetition"
EVIDENCE_ROLE_SELF_AWARENESS: Final = "self_awareness"
EVIDENCE_ROLE_RELATION: Final = "relation"
EVIDENCE_ROLE_UNKNOWN_SLOT: Final = "unknown_slot"
EVIDENCE_ROLE_CURRENT_INPUT: Final = "current_input"
EVIDENCE_ROLE_NONE: Final = "none"

_ALLOWED_CATEGORIES: Final = frozenset(
    {
        CATEGORY_RECEIVE_PHRASE,
        CATEGORY_ARRANGEMENT_CONNECTOR,
        CATEGORY_RELATION_PHRASE,
        CATEGORY_HUMILITY_MARKER,
        CATEGORY_UNKNOWN_SLOT_MARKER,
        CATEGORY_QUESTION_ENDING,
        CATEGORY_KNOWN_SCOPE_PHRASE,
        CATEGORY_BURDEN_PHRASE,
        CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
    }
)
_ALLOWED_REPLY_KINDS: Final = frozenset(
    {
        OBSERVATION_REPLY_KIND_ELIGIBLE,
        OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    }
)
_ALLOWED_EVIDENCE_ROLES: Final = frozenset(
    {
        EVIDENCE_ROLE_STATE,
        EVIDENCE_ROLE_TARGET,
        EVIDENCE_ROLE_WISH,
        EVIDENCE_ROLE_BLOCKAGE,
        EVIDENCE_ROLE_CONTRAST,
        EVIDENCE_ROLE_REPETITION,
        EVIDENCE_ROLE_SELF_AWARENESS,
        EVIDENCE_ROLE_RELATION,
        EVIDENCE_ROLE_UNKNOWN_SLOT,
        EVIDENCE_ROLE_CURRENT_INPUT,
        EVIDENCE_ROLE_NONE,
    }
)
_POSITIVE_CATEGORIES: Final = frozenset(_ALLOWED_CATEGORIES - {CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE})

_CONFIG_DIR: Final = Path(__file__).resolve().parent / "config"
DEFAULT_OBSERVATION_DICTIONARY_SCHEMA_PATH: Final = _CONFIG_DIR / "emlis_observation_dictionary.schema.json"
DEFAULT_OBSERVATION_DICTIONARY_PATH: Final = _CONFIG_DIR / "emlis_observation_dictionary.v1.json"

_ENTRY_ID_RE: Final = re.compile(r"^[a-z0-9_\-]+$")
_SPACE_RE: Final = re.compile(r"\s+")
_JA_TERMINAL_RE: Final = re.compile(r"[。！？!?]$")
_NEWLINE_RE: Final = re.compile(r"[\r\n]")
# These signatures are complete reply/fallback shapes, not phrase material.
_COMPLETE_TEMPLATE_RE: Final = re.compile(
    r"(Emlisです|Emlisでは観測できません|無理しないでくださいね|あなたは十分頑張っています|もっと詳しく教えてください|つらかったですね[。\s]*無理しないでくださいね)"
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
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
        "inputFeedbackComment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "realized_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
        "public_response_key_changed",
        "api_response_key_change",
        "api_response_key_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "completed_sentence_template_used",
        "complete_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
        "comment_text_generated",
        "comment_text_included",
        "comment_text_body_included",
        "raw_input_included",
        "raw_text_included",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_payload_key(item) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_payload_key(vars(value))
    return False


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _is_forbidden_signature_category(category: str) -> bool:
    return category == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE


def _is_positive_material(category: str, value: Any) -> bool:
    if isinstance(value, Mapping) and "positive_material" in value:
        explicit = _as_bool(value.get("positive_material"), default=True)
        if _is_forbidden_signature_category(category) and explicit:
            raise ValueError("forbidden template signatures must not be positive material")
        return explicit
    if _is_forbidden_signature_category(category):
        return False
    return True


def _is_complete_sentence_like(surface: str, category: str) -> bool:
    """Return True when a positive material is too close to a full reply.

    A question ending such as ``何がありましたか`` is allowed because it is a
    question component selected by unknown slot.  Full fallback/reply skeletons
    with sentence punctuation, line breaks, or banned template signatures are
    not allowed as positive dictionary material.
    """

    text = _clean(surface)
    if not text:
        return False
    if _NEWLINE_RE.search(surface):
        return True
    if _JA_TERMINAL_RE.search(text):
        return True
    if _COMPLETE_TEMPLATE_RE.search(text):
        return True
    if category != CATEGORY_QUESTION_ENDING and len(text) >= 34 and any(marker in text for marker in ("ですね", "ます", "ました", "ください")):
        return True
    return False


def _normalize_entry(raw: Mapping[str, Any]) -> dict[str, Any]:
    if _contains_payload_key(raw):
        raise ValueError("observation dictionary entries must not contain raw input/comment payload keys")

    entry_id = _clean(raw.get("entry_id"))
    if not entry_id or not _ENTRY_ID_RE.match(entry_id):
        raise ValueError(f"invalid observation dictionary entry_id: {entry_id or '<empty>'}")

    category = _clean(raw.get("category"))
    if category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported observation dictionary category: {category or '<empty>'}")

    surface = _clean(raw.get("surface"))
    if not surface:
        raise ValueError(f"observation dictionary entry {entry_id} must have surface material")

    reply_kinds = _dedupe(raw.get("allowed_reply_kinds"))
    if not reply_kinds:
        raise ValueError(f"observation dictionary entry {entry_id} must have allowed_reply_kinds")
    unsupported_reply_kinds = [kind for kind in reply_kinds if kind not in _ALLOWED_REPLY_KINDS]
    if unsupported_reply_kinds:
        raise ValueError(f"unsupported observation reply kind(s) for {entry_id}: {', '.join(unsupported_reply_kinds)}")

    evidence_roles = _dedupe(raw.get("requires_evidence_role"))
    if not evidence_roles:
        raise ValueError(f"observation dictionary entry {entry_id} must have requires_evidence_role")
    unsupported_roles = [role for role in evidence_roles if role not in _ALLOWED_EVIDENCE_ROLES]
    if unsupported_roles:
        raise ValueError(f"unsupported evidence role(s) for {entry_id}: {', '.join(unsupported_roles)}")

    try:
        weight = float(raw.get("template_signature_weight", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid template_signature_weight for {entry_id}") from exc
    if weight < 0.0 or weight > 1.0:
        raise ValueError(f"template_signature_weight out of range for {entry_id}")

    positive_material = _is_positive_material(category, raw)
    must_not_be_complete_sentence = _as_bool(raw.get("must_not_be_complete_sentence"), default=True)
    if positive_material and not must_not_be_complete_sentence:
        raise ValueError(f"positive observation dictionary entry {entry_id} must keep must_not_be_complete_sentence=true")
    if positive_material and _is_complete_sentence_like(surface, category):
        raise ValueError(f"positive observation dictionary entry {entry_id} is too close to a complete sentence/template")
    if _is_forbidden_signature_category(category) and positive_material:
        raise ValueError(f"forbidden template signature {entry_id} must not be positive material")
    if _is_forbidden_signature_category(category) and weight < 0.75:
        raise ValueError(f"forbidden template signature {entry_id} must keep high template weight")

    normalized: dict[str, Any] = {
        "entry_id": entry_id,
        "category": category,
        "surface": surface,
        "allowed_reply_kinds": reply_kinds,
        "requires_evidence_role": evidence_roles,
        "must_not_be_complete_sentence": must_not_be_complete_sentence,
        "template_signature_weight": round(weight, 4),
        "positive_material": positive_material,
    }
    unknown_slots = _dedupe(raw.get("unknown_slots"))
    if unknown_slots:
        normalized["unknown_slots"] = unknown_slots
    notes = _clean(raw.get("notes"))
    if notes:
        normalized["notes"] = notes
    return normalized


@dataclass(frozen=True)
class ObservationDictionaryEntry:
    entry_id: str
    category: str
    surface: str
    allowed_reply_kinds: tuple[str, ...]
    requires_evidence_role: tuple[str, ...]
    must_not_be_complete_sentence: bool = True
    template_signature_weight: float = 0.0
    positive_material: bool = True
    unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def as_meta(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "entry_id": self.entry_id,
            "category": self.category,
            "surface": self.surface,
            "allowed_reply_kinds": list(self.allowed_reply_kinds),
            "requires_evidence_role": list(self.requires_evidence_role),
            "must_not_be_complete_sentence": bool(self.must_not_be_complete_sentence),
            "template_signature_weight": round(float(self.template_signature_weight), 4),
            "positive_material": bool(self.positive_material),
        }
        if self.unknown_slots:
            data["unknown_slots"] = list(self.unknown_slots)
        if self.notes:
            data["notes"] = self.notes
        return data


@dataclass(frozen=True)
class ObservationDictionary:
    dictionary_version: str
    entries: tuple[ObservationDictionaryEntry, ...]
    description: str = ""
    schema_version: str = OBSERVATION_DICTIONARY_SCHEMA_VERSION
    contract_step: str = OBSERVATION_DICTIONARY_STEP

    @property
    def version(self) -> str:
        return self.schema_version

    @property
    def step(self) -> str:
        return self.contract_step

    def as_meta(self) -> dict[str, Any]:
        categories: dict[str, int] = {}
        positive_count = 0
        forbidden_count = 0
        for entry in self.entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
            if entry.positive_material:
                positive_count += 1
            if entry.category == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE:
                forbidden_count += 1
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "dictionary_version": self.dictionary_version,
            "contract_step": self.contract_step,
            "source_step": self.contract_step,
            "observation_dictionary_ready": True,
            "description": self.description,
            "entry_count": len(self.entries),
            "positive_material_entry_count": positive_count,
            "forbidden_template_signature_count": forbidden_count,
            "categories": categories,
            "entries": [entry.as_meta() for entry in self.entries],
            "must_not_use_completed_sentence_templates": True,
            "must_not_select_forbidden_signatures_as_material": True,
            "comment_text_generated": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "completed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_observation_dictionary_contract(meta)
        return meta


def _entry_from_meta(meta: Mapping[str, Any]) -> ObservationDictionaryEntry:
    normalized = _normalize_entry(meta)
    return ObservationDictionaryEntry(
        entry_id=normalized["entry_id"],
        category=normalized["category"],
        surface=normalized["surface"],
        allowed_reply_kinds=tuple(normalized["allowed_reply_kinds"]),
        requires_evidence_role=tuple(normalized["requires_evidence_role"]),
        must_not_be_complete_sentence=bool(normalized["must_not_be_complete_sentence"]),
        template_signature_weight=float(normalized["template_signature_weight"]),
        positive_material=bool(normalized["positive_material"]),
        unknown_slots=tuple(normalized.get("unknown_slots", [])),
        notes=_clean(normalized.get("notes")),
    )


def validate_observation_dictionary_payload(payload: Mapping[str, Any]) -> ObservationDictionary:
    if _contains_payload_key(payload):
        raise ValueError("observation dictionary payload must not contain raw input/comment payload keys")
    schema_version = _clean(payload.get("schema_version"))
    if schema_version != OBSERVATION_DICTIONARY_SCHEMA_VERSION:
        raise ValueError(f"unsupported observation dictionary schema_version: {schema_version or '<empty>'}")
    contract_step = _clean(payload.get("contract_step"))
    if contract_step != OBSERVATION_DICTIONARY_STEP:
        raise ValueError(f"unsupported observation dictionary contract_step: {contract_step or '<empty>'}")
    dictionary_version = _clean(payload.get("dictionary_version"))
    if not dictionary_version:
        raise ValueError("observation dictionary must have dictionary_version")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes, bytearray)) or not raw_entries:
        raise ValueError("observation dictionary must have non-empty entries")

    entries = tuple(_entry_from_meta(entry) for entry in raw_entries if isinstance(entry, Mapping))
    if len(entries) != len(raw_entries):
        raise ValueError("observation dictionary entries must be objects")

    seen_ids: set[str] = set()
    categories = {entry.category for entry in entries}
    for entry in entries:
        if entry.entry_id in seen_ids:
            raise ValueError(f"duplicate observation dictionary entry_id: {entry.entry_id}")
        seen_ids.add(entry.entry_id)
    missing_core_categories = {
        CATEGORY_RECEIVE_PHRASE,
        CATEGORY_RELATION_PHRASE,
        CATEGORY_HUMILITY_MARKER,
        CATEGORY_UNKNOWN_SLOT_MARKER,
        CATEGORY_QUESTION_ENDING,
        CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
    } - categories
    if missing_core_categories:
        raise ValueError(f"observation dictionary missing core categories: {', '.join(sorted(missing_core_categories))}")

    positive_entries = [entry for entry in entries if entry.positive_material]
    forbidden_entries = [entry for entry in entries if entry.category == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE]
    if not positive_entries:
        raise ValueError("observation dictionary must include positive material entries")
    if not forbidden_entries:
        raise ValueError("observation dictionary must include forbidden template signatures")
    if any(entry.positive_material for entry in forbidden_entries):
        raise ValueError("forbidden template signatures must not be positive material")

    return ObservationDictionary(
        dictionary_version=dictionary_version,
        description=_clean(payload.get("description")),
        entries=entries,
        schema_version=schema_version,
        contract_step=contract_step,
    )


def load_observation_dictionary(path: str | Path | None = None) -> ObservationDictionary:
    dictionary_path = Path(path) if path is not None else DEFAULT_OBSERVATION_DICTIONARY_PATH
    with dictionary_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, Mapping):
        raise ValueError("observation dictionary root must be an object")
    return validate_observation_dictionary_payload(payload)


def load_observation_dictionary_schema(path: str | Path | None = None) -> dict[str, Any]:
    schema_path = Path(path) if path is not None else DEFAULT_OBSERVATION_DICTIONARY_SCHEMA_PATH
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)
    if not isinstance(schema, Mapping):
        raise ValueError("observation dictionary schema root must be an object")
    if _clean(schema.get("$id")) == "":
        raise ValueError("observation dictionary schema must have $id")
    return dict(schema)


def select_observation_dictionary_entries(
    dictionary: ObservationDictionary | Mapping[str, Any] | None = None,
    *,
    category: str | None = None,
    reply_kind: str | None = None,
    evidence_roles: Iterable[str] | None = None,
    unknown_slots: Iterable[str] | None = None,
    include_forbidden_signatures: bool = False,
) -> list[dict[str, Any]]:
    if dictionary is None:
        resolved = load_observation_dictionary()
    elif isinstance(dictionary, ObservationDictionary):
        resolved = dictionary
    elif isinstance(dictionary, Mapping):
        resolved = validate_observation_dictionary_payload(dictionary)
    else:
        raise ValueError("dictionary must be ObservationDictionary or payload mapping")

    selected_category = _clean(category)
    selected_reply_kind = _clean(reply_kind)
    selected_roles = set(_dedupe(evidence_roles))
    selected_slots = set(_dedupe(unknown_slots))
    if selected_category and selected_category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported observation dictionary category: {selected_category}")
    if selected_reply_kind and selected_reply_kind not in _ALLOWED_REPLY_KINDS:
        raise ValueError(f"unsupported observation reply kind: {selected_reply_kind}")

    out: list[dict[str, Any]] = []
    for entry in resolved.entries:
        if not include_forbidden_signatures and not entry.positive_material:
            continue
        if selected_category and entry.category != selected_category:
            continue
        if selected_reply_kind and selected_reply_kind not in entry.allowed_reply_kinds:
            continue
        if selected_roles and not selected_roles.intersection(entry.requires_evidence_role):
            continue
        if selected_slots and entry.unknown_slots and not selected_slots.intersection(entry.unknown_slots):
            continue
        if selected_slots and entry.category in {CATEGORY_UNKNOWN_SLOT_MARKER, CATEGORY_QUESTION_ENDING} and not entry.unknown_slots:
            continue
        out.append(entry.as_meta())
    return out


def assert_observation_dictionary_contract(value: ObservationDictionary | Mapping[str, Any]) -> None:
    if isinstance(value, ObservationDictionary):
        meta = value.as_meta()
    else:
        meta = dict(value)

    if _contains_payload_key(meta):
        raise ValueError("observation dictionary contract must not include raw input/comment payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if bool(meta.get(flag)):
            raise ValueError(f"observation dictionary contract changed forbidden flag: {flag}")

    if _clean(meta.get("schema_version") or meta.get("version")) != OBSERVATION_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("observation dictionary schema_version mismatch")
    if _clean(meta.get("contract_step") or meta.get("source_step")) != OBSERVATION_DICTIONARY_STEP:
        raise ValueError("observation dictionary step mismatch")
    if bool(meta.get("must_not_use_completed_sentence_templates")) is not True:
        raise ValueError("observation dictionary must forbid completed sentence templates")
    if bool(meta.get("must_not_select_forbidden_signatures_as_material")) is not True:
        raise ValueError("observation dictionary must forbid selecting forbidden signatures")

    entries = meta.get("entries")
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes, bytearray)) or not entries:
        raise ValueError("observation dictionary meta must include entries")

    normalized_entries = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("observation dictionary entries must be mappings")
        normalized_entries.append(_normalize_entry(entry))

    seen_ids: set[str] = set()
    positive_count = 0
    forbidden_count = 0
    for entry in normalized_entries:
        entry_id = entry["entry_id"]
        if entry_id in seen_ids:
            raise ValueError(f"duplicate observation dictionary entry_id: {entry_id}")
        seen_ids.add(entry_id)
        if entry["positive_material"]:
            positive_count += 1
        if entry["category"] == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE:
            forbidden_count += 1
            if entry["positive_material"]:
                raise ValueError("forbidden template signatures must not be positive material")
    if positive_count <= 0:
        raise ValueError("observation dictionary must include positive material")
    if forbidden_count <= 0:
        raise ValueError("observation dictionary must include forbidden template signatures")


def _strip_dump_only_comment_text_flags(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_dump_only_comment_text_flags(item)
            for key, item in value.items()
            if "comment_text" not in str(key)
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_strip_dump_only_comment_text_flags(item) for item in value]
    return value


def dump_observation_dictionary_contract(value: ObservationDictionary | Mapping[str, Any] | None = None) -> str:
    if value is None:
        value = load_observation_dictionary()
    if isinstance(value, ObservationDictionary):
        meta = value.as_meta()
    else:
        meta = dict(value)
        assert_observation_dictionary_contract(meta)
    dump_meta = _strip_dump_only_comment_text_flags(meta)
    return json.dumps(dump_meta, ensure_ascii=False, sort_keys=True)


# Backward-friendly aliases for future integration code.
load_emlis_ai_observation_dictionary = load_observation_dictionary
validate_emlis_ai_observation_dictionary_payload = validate_observation_dictionary_payload
assert_emlis_ai_observation_dictionary_contract = assert_observation_dictionary_contract
dump_emlis_ai_observation_dictionary_contract = dump_observation_dictionary_contract
select_emlis_ai_observation_dictionary_entries = select_observation_dictionary_entries
