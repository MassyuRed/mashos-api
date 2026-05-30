# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 3 loader for the Emlis reception assistance dictionary.

The reception assistance dictionary is internal material for the
``Emlisから`` section.  It is not a general dictionary and it does not contain
completed reply text.  It can connect explicit user reactions and event hints
into later reception-mode resolution, while preserving the public feedback
contract: no public response keys, no route changes, no RN visibility contract
changes, and no raw user text in exported meta.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
from typing import Any, Final

Draft202012Validator = None  # kept for tests/tools that may introspect loader modules

RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION: Final = "emlis.reception_assistance_dictionary.v1"
RECEPTION_ASSISTANCE_DICTIONARY_ID: Final = "emlis_reception_assistance_dictionary"
RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID: Final = "emlis_reception_assistance_dictionary_material"
RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE: Final = "Phase3_Reception_Assistance_Dictionary_Loader"
RECEPTION_ASSISTANCE_DICTIONARY_CONTRACT_STEP: Final = "Phase3_Reception_Assistance_Dictionary_Skeleton"

_CONFIG_DIR: Final = Path(__file__).resolve().parent / "config"
DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_PATH: Final = (
    _CONFIG_DIR / "emlis_reception_assistance_dictionary.schema.json"
)
DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_PATH: Final = (
    _CONFIG_DIR / "emlis_reception_assistance_dictionary.v1.json"
)

_IDENTIFIER_RE: Final = re.compile(r"^[a-z0-9_\-]+$")
_SPACE_RE: Final = re.compile(r"\s+")
_UNDEFINED_MARKERS: Final = frozenset({"", "undefined", "null", "none", "todo", "tbd", "未定義", "未設定", "あとで"})

_REQUIRED_TOP_LEVEL_KEYS: Final = (
    "schema_version",
    "dictionary_id",
    "dictionary_version",
    "purpose",
    "non_goals",
    "global_policies",
    "unknown_word_policy",
    "reaction_cues",
    "event_hints",
    "reception_modes",
    "tone_families",
    "follow_shape_families",
    "contract_boundaries",
)
_REQUIRED_GLOBAL_POLICY_TRUE_FLAGS: Final = frozenset(
    {
        "not_general_dictionary",
        "user_reaction_is_primary",
        "event_hint_must_not_create_emotion",
        "unknown_word_meaning_must_not_be_asserted",
        "completed_reply_template_forbidden",
    }
)
_REQUIRED_UNKNOWN_WORD_POLICY_FALSE_FLAGS: Final = frozenset(
    {
        "general_dictionary_used",
        "unknown_word_meaning_asserted",
        "meaning_assertion_allowed",
    }
)
_REQUIRED_UNKNOWN_WORD_POLICY_TRUE_FLAGS: Final = frozenset(
    {
        "event_hint_can_support_mode_only",
        "event_hint_must_not_create_emotion",
    }
)
_REQUIRED_CONTRACT_FALSE_FLAGS: Final = frozenset(
    {
        "public_response_key_added",
        "comment_text_generated_by_dictionary",
        "raw_input_included",
        "raw_text_included",
        "general_knowledge_primary",
        "completed_reply_generated",
        "observation_status_enum_extended",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_response_key_added",
        "comment_text_generated_by_dictionary",
        "raw_input_included",
        "raw_text_included",
        "general_dictionary_used",
        "general_knowledge_primary",
        "completed_reply_generated",
        "completed_reply_template_stored",
        "unknown_word_meaning_asserted",
        "meaning_assertion_allowed",
        "event_hint_created_emotion",
        "event_hint_alone_can_create_emotion",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
    }
)
_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset(
    {
        "comment_text",
        "commentText",
        "input_feedback.comment_text",
        "public_comment_text",
        "candidate_comment_text",
        "observation_text",
        "reception_text",
        "reply_text",
        "replyText",
        "completed_reply_text",
        "completed_surface_text",
        "fixed_reply_text",
        "template_text",
        "example_reply_text",
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
    }
)
_FORBIDDEN_GENERAL_DICTIONARY_KEYS: Final = frozenset(
    {
        "meaning",
        "definition",
        "word_meaning",
        "meaning_definition",
        "meaning_explanation",
        "semantic_definition",
        "gloss",
    }
)
_EVENT_HINT_EMOTION_CREATION_KEYS: Final = frozenset(
    {
        "creates_emotion",
        "creates_reaction",
        "creates_reaction_cue",
        "creates_reaction_cues",
        "allowed_reaction_cues",
        "inferred_emotion_ids",
        "inferred_reaction_cue_ids",
    }
)

_FORBIDDEN_COMPLETED_REPLY_FRAGMENTS: Final = frozenset(
    {
        "見えたこと：",
        "Emlisから：",
        "うわ、それは嫌でしたね",
        "怖さも怒りも残るのは自然です",
        "不快で怖さもある出来事に出くわして",
        "何があったか残してみませんか",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _as_mapping_list(values: Any, *, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ValueError(f"reception assistance dictionary {label} must be an array")
    out: list[Mapping[str, Any]] = []
    for item in values:
        if not isinstance(item, Mapping):
            raise ValueError(f"reception assistance dictionary {label} must contain objects")
        out.append(item)
    if not out:
        raise ValueError(f"reception assistance dictionary {label} must not be empty")
    return out


def _require_identifier(value: Any, *, label: str) -> str:
    identifier = _clean(value)
    if not identifier or not _IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"invalid reception assistance dictionary {label}: {identifier or '<empty>'}")
    return identifier


def _require_non_empty_strings(values: Any, *, label: str) -> tuple[str, ...]:
    items = _dedupe(values)
    if not items:
        raise ValueError(f"reception assistance dictionary {label} must contain at least one non-empty item")
    undefined_items = [item for item in items if item.lower() in _UNDEFINED_MARKERS]
    if undefined_items:
        raise ValueError(
            f"reception assistance dictionary {label} contains undefined marker(s): "
            + ", ".join(undefined_items)
        )
    return items


def _ensure_no_duplicates(ids: Sequence[str], *, label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise ValueError(f"duplicate reception assistance dictionary {label}: {item_id}")
        seen.add(item_id)


def _contains_forbidden_key(value: Any, forbidden_keys: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in forbidden_keys:
                return True
            if _contains_forbidden_key(item, forbidden_keys):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(item, forbidden_keys) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_forbidden_key(vars(value), forbidden_keys)
    return False


def _contains_completed_reply_fragment(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_completed_reply_fragment(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_completed_reply_fragment(item) for item in value)
    if isinstance(value, str):
        return any(fragment in value for fragment in _FORBIDDEN_COMPLETED_REPLY_FRAGMENTS)
    return False


def _walk_mappings(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_mappings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_mappings(item)


def _matches_surface(text: str, patterns: Sequence[str]) -> bool:
    if not text:
        return False
    return any(pattern and pattern in text for pattern in patterns)


def _validate_schema(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Validate the bundled schema contract subset without importing jsonschema."""

    if not isinstance(schema, Mapping):
        raise ValueError("reception assistance dictionary schema root must be an object")
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise ValueError("reception assistance dictionary schema must contain properties")
    expected_schema_version = properties.get("schema_version", {}).get("const") if isinstance(properties.get("schema_version"), Mapping) else None
    expected_dictionary_id = properties.get("dictionary_id", {}).get("const") if isinstance(properties.get("dictionary_id"), Mapping) else None
    if expected_schema_version != RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("unexpected reception assistance dictionary schema_version const")
    if expected_dictionary_id != RECEPTION_ASSISTANCE_DICTIONARY_ID:
        raise ValueError("unexpected reception assistance dictionary dictionary_id const")
    required = tuple(schema.get("required") or ())
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in required:
            raise ValueError(f"reception assistance dictionary schema missing required key: {key}")
        if key not in payload:
            raise ValueError(f"reception assistance dictionary payload missing required key: {key}")


def load_reception_assistance_dictionary_schema(
    path: str | Path = DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_PATH,
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError("reception assistance dictionary schema must be a JSON object")
    return payload


def load_reception_assistance_dictionary_payload(
    path: str | Path = DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_PATH,
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError("reception assistance dictionary must be a JSON object")
    return payload


def validate_reception_assistance_dictionary_payload(
    payload: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
) -> None:
    """Validate Phase 3 reception assistance dictionary material.

    Validation is intentionally semantic and Cocolon-specific: the dictionary
    may contain reaction cue and event hint patterns, but it must not become a
    general dictionary, completed reply template store, or public response body.
    """

    if not isinstance(payload, Mapping):
        raise ValueError("reception assistance dictionary payload must be an object")
    if schema is None:
        schema = load_reception_assistance_dictionary_schema()
    _validate_schema(payload, schema)

    if payload.get("schema_version") != RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("unexpected reception assistance dictionary schema version")
    if payload.get("dictionary_id") != RECEPTION_ASSISTANCE_DICTIONARY_ID:
        raise ValueError("unexpected reception assistance dictionary id")
    if not _clean(payload.get("dictionary_version")):
        raise ValueError("reception assistance dictionary_version must not be empty")

    if _contains_forbidden_key(payload, _FORBIDDEN_PAYLOAD_KEYS):
        raise ValueError("reception assistance dictionary must not contain completed reply or public text payload keys")
    if _contains_completed_reply_fragment(payload):
        raise ValueError("reception assistance dictionary must not contain completed reply text fragments")
    if _contains_forbidden_key(payload, _FORBIDDEN_GENERAL_DICTIONARY_KEYS):
        raise ValueError("reception assistance dictionary must not contain general dictionary meaning-definition keys")

    global_policies = payload.get("global_policies")
    if not isinstance(global_policies, Mapping):
        raise ValueError("reception assistance dictionary global_policies must be an object")
    for key in _REQUIRED_GLOBAL_POLICY_TRUE_FLAGS:
        if global_policies.get(key) is not True:
            raise ValueError(f"reception assistance dictionary global policy must be true: {key}")

    unknown_word_policy = payload.get("unknown_word_policy")
    if not isinstance(unknown_word_policy, Mapping):
        raise ValueError("reception assistance dictionary unknown_word_policy must be an object")
    for key in _REQUIRED_UNKNOWN_WORD_POLICY_FALSE_FLAGS:
        if unknown_word_policy.get(key) is not False:
            raise ValueError(f"reception assistance dictionary unknown word policy must be false: {key}")
    for key in _REQUIRED_UNKNOWN_WORD_POLICY_TRUE_FLAGS:
        if unknown_word_policy.get(key) is not True:
            raise ValueError(f"reception assistance dictionary unknown word policy must be true: {key}")

    contract_boundaries = payload.get("contract_boundaries")
    if not isinstance(contract_boundaries, Mapping):
        raise ValueError("reception assistance dictionary contract_boundaries must be an object")
    for key in _REQUIRED_CONTRACT_FALSE_FLAGS:
        if contract_boundaries.get(key) is not False:
            raise ValueError(f"reception assistance dictionary contract boundary must be false: {key}")

    for key, value in _walk_mappings(payload):
        if key in _FORBIDDEN_TRUE_FLAGS and value is True:
            raise ValueError(f"forbidden true flag in reception assistance dictionary: {key}")

    reaction_cues = _as_mapping_list(payload.get("reaction_cues"), label="reaction_cues")
    event_hints = _as_mapping_list(payload.get("event_hints"), label="event_hints")
    reception_modes = _as_mapping_list(payload.get("reception_modes"), label="reception_modes")
    tone_families = _as_mapping_list(payload.get("tone_families"), label="tone_families")
    follow_shape_families = _as_mapping_list(payload.get("follow_shape_families"), label="follow_shape_families")

    mode_ids = [_require_identifier(mode.get("mode_id"), label="mode_id") for mode in reception_modes]
    tone_family_ids = [_require_identifier(tone.get("tone_family_id"), label="tone_family_id") for tone in tone_families]
    _ensure_no_duplicates(mode_ids, label="mode_id")
    _ensure_no_duplicates(tone_family_ids, label="tone_family_id")
    mode_id_set = set(mode_ids)
    tone_family_id_set = set(tone_family_ids)

    cue_ids: list[str] = []
    for cue in reaction_cues:
        cue_id = _require_identifier(cue.get("cue_id"), label="cue_id")
        cue_ids.append(cue_id)
        _require_non_empty_strings(cue.get("surface_patterns"), label=f"{cue_id}.surface_patterns")
        _require_identifier(cue.get("reaction_family"), label=f"{cue_id}.reaction_family")
        allowed_modes = _require_non_empty_strings(cue.get("allowed_reception_modes"), label=f"{cue_id}.allowed_reception_modes")
        _require_non_empty_strings(cue.get("must_not_infer"), label=f"{cue_id}.must_not_infer")
        undefined = [mode_id for mode_id in allowed_modes if mode_id not in mode_id_set]
        if undefined:
            raise ValueError(f"reaction cue {cue_id} references undefined reception mode(s): {', '.join(undefined)}")
    _ensure_no_duplicates(cue_ids, label="cue_id")

    hint_ids: list[str] = []
    for hint in event_hints:
        hint_id = _require_identifier(hint.get("hint_id"), label="hint_id")
        hint_ids.append(hint_id)
        _require_non_empty_strings(hint.get("surface_patterns"), label=f"{hint_id}.surface_patterns")
        _require_identifier(hint.get("event_family"), label=f"{hint_id}.event_family")
        support_modes = _require_non_empty_strings(hint.get("can_support_modes"), label=f"{hint_id}.can_support_modes")
        cannot_alone_infer = _require_non_empty_strings(hint.get("cannot_alone_infer"), label=f"{hint_id}.cannot_alone_infer")
        undefined = [mode_id for mode_id in support_modes if mode_id not in mode_id_set]
        if undefined:
            raise ValueError(f"event hint {hint_id} references undefined reception mode(s): {', '.join(undefined)}")
        if not cannot_alone_infer:
            raise ValueError(f"event hint {hint_id} must define cannot_alone_infer")
        for key in _EVENT_HINT_EMOTION_CREATION_KEYS:
            if key in hint:
                raise ValueError(f"event hint {hint_id} must not define emotion-creation key: {key}")
    _ensure_no_duplicates(hint_ids, label="hint_id")

    for mode in reception_modes:
        mode_id = _require_identifier(mode.get("mode_id"), label="mode_id")
        activation = mode.get("activation")
        observation_policy = mode.get("observation_policy")
        reception_policy = mode.get("reception_policy")
        if not isinstance(activation, Mapping):
            raise ValueError(f"reception mode {mode_id}.activation must be an object")
        if not isinstance(observation_policy, Mapping):
            raise ValueError(f"reception mode {mode_id}.observation_policy must be an object")
        if not isinstance(reception_policy, Mapping):
            raise ValueError(f"reception mode {mode_id}.reception_policy must be an object")
        _require_identifier(mode.get("ratio_preset"), label=f"{mode_id}.ratio_preset")
        _require_non_empty_strings(mode.get("forbidden"), label=f"{mode_id}.forbidden")
        allowed_tone = _require_identifier(reception_policy.get("allowed_tone_family"), label=f"{mode_id}.allowed_tone_family")
        if allowed_tone not in tone_family_id_set:
            raise ValueError(f"reception mode {mode_id} references undefined tone family: {allowed_tone}")
        if activation.get("event_hint_alone_can_activate") is not False:
            raise ValueError(f"reception mode {mode_id} must not allow event hint alone activation")
        if "completed_reply" in json.dumps(mode, ensure_ascii=False):
            raise ValueError(f"reception mode {mode_id} must not contain completed reply material")

    for tone in tone_families:
        tone_id = _require_identifier(tone.get("tone_family_id"), label="tone_family_id")
        if not _clean(tone.get("description")):
            raise ValueError(f"tone family {tone_id}.description must not be empty")
        _require_non_empty_strings(tone.get("allowed_surface_features"), label=f"{tone_id}.allowed_surface_features")
        _require_non_empty_strings(tone.get("forbidden_surface_features"), label=f"{tone_id}.forbidden_surface_features")

    shape_ids: list[str] = []
    for shape in follow_shape_families:
        shape_id = _require_identifier(shape.get("shape_family_id"), label="shape_family_id")
        shape_ids.append(shape_id)
        if shape.get("template_text_forbidden") is not True:
            raise ValueError(f"follow shape {shape_id} must forbid template text")
        shape_mode_ids = _require_non_empty_strings(shape.get("mode_ids"), label=f"{shape_id}.mode_ids")
        _require_non_empty_strings(shape.get("allowed_intents"), label=f"{shape_id}.allowed_intents")
        _require_non_empty_strings(shape.get("forbidden_intents"), label=f"{shape_id}.forbidden_intents")
        undefined = [mode_id for mode_id in shape_mode_ids if mode_id not in mode_id_set]
        if undefined:
            raise ValueError(f"follow shape {shape_id} references undefined reception mode(s): {', '.join(undefined)}")
    _ensure_no_duplicates(shape_ids, label="shape_family_id")

    json.dumps(dict(payload), ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class EmlisReceptionAssistanceDictionary:
    """Validated internal material for later reception-section phases."""

    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        validate_reception_assistance_dictionary_payload(self.payload)

    @property
    def reaction_cues(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(_as_mapping_list(self.payload.get("reaction_cues"), label="reaction_cues"))

    @property
    def event_hints(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(_as_mapping_list(self.payload.get("event_hints"), label="event_hints"))

    @property
    def reception_modes(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(_as_mapping_list(self.payload.get("reception_modes"), label="reception_modes"))

    @property
    def tone_families(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(_as_mapping_list(self.payload.get("tone_families"), label="tone_families"))

    @property
    def follow_shape_families(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(_as_mapping_list(self.payload.get("follow_shape_families"), label="follow_shape_families"))

    def as_payload(self) -> dict[str, Any]:
        return copy.deepcopy(dict(self.payload))

    def as_meta(self) -> dict[str, Any]:
        global_policies = dict(self.payload.get("global_policies") or {})
        unknown_word_policy = dict(self.payload.get("unknown_word_policy") or {})
        contract_boundaries = dict(self.payload.get("contract_boundaries") or {})
        meta: dict[str, Any] = {
            "schema_version": RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION,
            "dictionary_id": RECEPTION_ASSISTANCE_DICTIONARY_ID,
            "dictionary_version": _clean(self.payload.get("dictionary_version")),
            "material_id": RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID,
            "contract_step": RECEPTION_ASSISTANCE_DICTIONARY_CONTRACT_STEP,
            "loader_phase": RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE,
            "reception_assistance_dictionary_ready": True,
            "dictionary_material_only": True,
            "reaction_cue_count": len(self.reaction_cues),
            "event_hint_count": len(self.event_hints),
            "reception_mode_count": len(self.reception_modes),
            "tone_family_count": len(self.tone_families),
            "follow_shape_family_count": len(self.follow_shape_families),
            "reaction_cue_ids": [str(cue["cue_id"]) for cue in self.reaction_cues],
            "event_hint_ids": [str(hint["hint_id"]) for hint in self.event_hints],
            "reception_mode_ids": [str(mode["mode_id"]) for mode in self.reception_modes],
            "tone_family_ids": [str(tone["tone_family_id"]) for tone in self.tone_families],
            "follow_shape_family_ids": [str(shape["shape_family_id"]) for shape in self.follow_shape_families],
            "global_policies": global_policies,
            "unknown_word_policy": unknown_word_policy,
            "contract_boundaries": contract_boundaries,
            "not_general_dictionary": global_policies.get("not_general_dictionary") is True,
            "user_reaction_is_primary": global_policies.get("user_reaction_is_primary") is True,
            "completed_reply_template_forbidden": global_policies.get("completed_reply_template_forbidden") is True,
            "event_hint_must_not_create_emotion": global_policies.get("event_hint_must_not_create_emotion") is True,
            "general_dictionary_used": False,
            "general_knowledge_primary": False,
            "unknown_word_meaning_asserted": False,
            "event_hint_created_emotion": False,
            "event_hint_alone_can_create_emotion": False,
            "completed_reply_generated": False,
            "completed_reply_template_stored": False,
            "comment_text_generated_by_dictionary": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_reception_assistance_dictionary_contract(meta)
        return meta


def load_reception_assistance_dictionary(
    path: str | Path = DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_PATH,
    *,
    schema_path: str | Path = DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_PATH,
) -> EmlisReceptionAssistanceDictionary:
    payload = load_reception_assistance_dictionary_payload(path)
    schema = load_reception_assistance_dictionary_schema(schema_path)
    validate_reception_assistance_dictionary_payload(payload, schema=schema)
    return EmlisReceptionAssistanceDictionary(copy.deepcopy(payload))


def assert_emlis_reception_assistance_dictionary_contract(meta: Mapping[str, Any]) -> None:
    """Validate exported meta stays public-safe and text-free."""

    if meta.get("schema_version") != RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("unexpected reception assistance dictionary schema version")
    if meta.get("dictionary_id") != RECEPTION_ASSISTANCE_DICTIONARY_ID:
        raise ValueError("unexpected reception assistance dictionary id")
    if meta.get("material_id") != RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID:
        raise ValueError("unexpected reception assistance dictionary material id")
    if meta.get("loader_phase") != RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE:
        raise ValueError("unexpected reception assistance dictionary loader phase")

    if _contains_forbidden_key(meta, _FORBIDDEN_PAYLOAD_KEYS):
        raise ValueError("reception assistance dictionary meta must not contain public or raw text payload keys")

    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in reception assistance dictionary meta: {flag}")

    if meta.get("not_general_dictionary") is not True:
        raise ValueError("reception assistance dictionary meta must mark not_general_dictionary=true")
    if meta.get("user_reaction_is_primary") is not True:
        raise ValueError("reception assistance dictionary meta must mark user_reaction_is_primary=true")
    if meta.get("completed_reply_template_forbidden") is not True:
        raise ValueError("reception assistance dictionary meta must forbid completed reply templates")
    if meta.get("event_hint_must_not_create_emotion") is not True:
        raise ValueError("reception assistance dictionary meta must prevent event hint emotion creation")
    if meta.get("general_dictionary_used") is not False:
        raise ValueError("reception assistance dictionary meta must not use a general dictionary")
    if meta.get("unknown_word_meaning_asserted") is not False:
        raise ValueError("reception assistance dictionary meta must not assert unknown-word meaning")

    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


def dump_reception_assistance_dictionary_contract(
    dictionary: EmlisReceptionAssistanceDictionary | None = None,
) -> str:
    if dictionary is None:
        dictionary = load_reception_assistance_dictionary()
    return json.dumps(dictionary.as_meta(), ensure_ascii=False, sort_keys=True)


def select_reception_assistance_reaction_cues(
    dictionary: EmlisReceptionAssistanceDictionary,
    *,
    cue_id: str | None = None,
    reaction_family: str | None = None,
    surface_text: str | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    text = _clean(surface_text)
    for cue in dictionary.reaction_cues:
        if cue_id is not None and cue.get("cue_id") != cue_id:
            continue
        if reaction_family is not None and cue.get("reaction_family") != reaction_family:
            continue
        if surface_text is not None and not _matches_surface(text, tuple(cue.get("surface_patterns") or ())) :
            continue
        selected.append(copy.deepcopy(dict(cue)))
    return selected


def select_reception_assistance_event_hints(
    dictionary: EmlisReceptionAssistanceDictionary,
    *,
    hint_id: str | None = None,
    event_family: str | None = None,
    surface_text: str | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    text = _clean(surface_text)
    for hint in dictionary.event_hints:
        if hint_id is not None and hint.get("hint_id") != hint_id:
            continue
        if event_family is not None and hint.get("event_family") != event_family:
            continue
        if surface_text is not None and not _matches_surface(text, tuple(hint.get("surface_patterns") or ())) :
            continue
        selected.append(copy.deepcopy(dict(hint)))
    return selected


def select_reception_assistance_modes(
    dictionary: EmlisReceptionAssistanceDictionary,
    *,
    mode_id: str | None = None,
    candidate_mode_ids: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    candidate_set = set(_dedupe(candidate_mode_ids)) if candidate_mode_ids is not None else None
    selected: list[dict[str, Any]] = []
    for mode in dictionary.reception_modes:
        current_mode_id = str(mode.get("mode_id"))
        if mode_id is not None and current_mode_id != mode_id:
            continue
        if candidate_set is not None and current_mode_id not in candidate_set:
            continue
        selected.append(copy.deepcopy(dict(mode)))
    return selected


def event_hint_can_create_emotion(
    dictionary: EmlisReceptionAssistanceDictionary,
    hint_id: str,
) -> bool:
    """Return whether a configured event hint is allowed to create emotion.

    A valid Phase 3 dictionary should always answer ``False``.  The helper is
    explicit so Phase 4 can guard against using event hints as reaction sources.
    """

    hints = select_reception_assistance_event_hints(dictionary, hint_id=hint_id)
    if not hints:
        raise ValueError(f"unknown reception assistance event hint: {hint_id}")
    hint = hints[0]
    if any(key in hint for key in _EVENT_HINT_EMOTION_CREATION_KEYS):
        return True
    return not bool(hint.get("cannot_alone_infer"))


def get_reception_assistance_unknown_word_policy(
    dictionary: EmlisReceptionAssistanceDictionary,
) -> dict[str, Any]:
    policy = dictionary.payload.get("unknown_word_policy")
    if not isinstance(policy, Mapping):
        raise ValueError("reception assistance dictionary missing unknown_word_policy")
    return copy.deepcopy(dict(policy))


__all__ = [
    "DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_PATH",
    "DEFAULT_RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_PATH",
    "EmlisReceptionAssistanceDictionary",
    "RECEPTION_ASSISTANCE_DICTIONARY_CONTRACT_STEP",
    "RECEPTION_ASSISTANCE_DICTIONARY_ID",
    "RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE",
    "RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID",
    "RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION",
    "assert_emlis_reception_assistance_dictionary_contract",
    "dump_reception_assistance_dictionary_contract",
    "event_hint_can_create_emotion",
    "get_reception_assistance_unknown_word_policy",
    "load_reception_assistance_dictionary",
    "load_reception_assistance_dictionary_payload",
    "load_reception_assistance_dictionary_schema",
    "select_reception_assistance_event_hints",
    "select_reception_assistance_modes",
    "select_reception_assistance_reaction_cues",
    "validate_reception_assistance_dictionary_payload",
]
