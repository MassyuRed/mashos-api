# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 3 loader and validator for the Emlis observation structure dictionary.

This module owns only the implementation-time loading contract for
``emlis_observation_structure_dictionary``.  The dictionary is intentionally
separate from the existing phrase/surface material dictionary:

* it validates input-bundle policy, relations, internal questions, inference
  boundaries, and surface-policy material;
* it does not generate or expose public ``input_feedback.comment_text``;
* it does not change public routes, request/response keys, DB physical names,
  RN visible contracts, or Display Gate behavior;
* it stops at load/validate/select helpers.  Gate / Composer connection remains
  a later phase.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
from pathlib import Path
import re
from typing import Any, Final

# Keep the structure dictionary loader independent from jsonschema at import time.
# In the local Python 3.13 regression environment, importing jsonschema eagerly can
# trigger a very slow rfc3987/lark grammar compile during pytest collection.  The
# semantic validator below already owns the Cocolon-specific contract checks, so
# _validate_schema performs the small top-level schema checks this module needs
# without importing the external validator on hot paths.
Draft202012Validator = None  # retained for legacy imports/tests that may introspect the symbol

OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION: Final = "emlis.observation_structure_dictionary.v1"
OBSERVATION_STRUCTURE_DICTIONARY_ID: Final = "emlis_observation_structure_dictionary"
OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP: Final = "Phase2_Observation_Structure_Dictionary_Schema"
OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE: Final = "Phase3_Loader_Validator"
OBSERVATION_STRUCTURE_DICTIONARY_BASE: Final = "cocolon_foundation_structure_dictionary"
OBSERVATION_STRUCTURE_DICTIONARY_STATUS: Final = "implementation_schema_phase2"

_CONFIG_DIR: Final = Path(__file__).resolve().parent / "config"
DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_PATH: Final = (
    _CONFIG_DIR / "emlis_observation_structure_dictionary.schema.json"
)
DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_PATH: Final = (
    _CONFIG_DIR / "emlis_observation_structure_dictionary.v1.json"
)

_ENTRY_ID_RE: Final = re.compile(r"^[a-z0-9_\-]+$")
_SPACE_RE: Final = re.compile(r"\s+")

_REQUIRED_CURRENT_INPUT_FIELDS: Final = frozenset({"memo", "memo_action", "emotion_details", "category"})
_REQUIRED_NORMALIZED_FIELDS: Final = frozenset(
    {
        "thought_text",
        "action_text",
        "emotions",
        "emotion_strength_summary",
        "categories",
        "selected_at",
        "source_record_id",
    }
)
_REQUIRED_SOURCE_PRIORITY: Final = (
    "current_input_explicit_fields",
    "current_input_direct_relations",
    "connected_user_facts",
    "dictionary_candidates",
    "general_knowledge_not_primary",
)

_EXPECTED_FIELD_MAPPING: Final = {
    "thought_text": "memo",
    "action_text": "memo_action",
    "emotions": "emotion_details",
    "emotion_strength_summary": "emotion_details",
    "categories": "category",
    "selected_at": "created_at",
    "source_record_id": "id",
}
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_route_changed",
        "request_key_changed",
        "response_key_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "raw_text_added_to_public_metadata",
        "existing_surface_dictionary_modified",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "comment_text_generated",
        "comment_text_included",
        "comment_text_body_included",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "completed_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
    }
)
_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset(
    {
        "input_feedback.comment_text",
        "comment_text",
        "commentText",
        "public_comment_text",
        "candidate_comment_text",
        "input_feedback_comment",
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_current_input",
        "reply_text",
        "replyText",
        "completed_reply_text",
        "fixed_fallback_sentence",
        "body_text",
    }
)
_UNDEFINED_INFERENCE_MARKERS: Final = frozenset({"", "undefined", "null", "none", "todo", "tbd", "未定義", "未設定", "あとで"})


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


def _as_list_of_mappings(values: Any, *, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ValueError(f"observation structure dictionary {label} must be an array")
    out: list[Mapping[str, Any]] = []
    for item in values:
        if not isinstance(item, Mapping):
            raise ValueError(f"observation structure dictionary {label} must contain objects")
        out.append(item)
    if not out:
        raise ValueError(f"observation structure dictionary {label} must not be empty")
    return out


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_forbidden_payload_key(vars(value))
    return False


def _walk_mappings(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_mappings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_mappings(item)


def _require_identifier(value: Any, *, label: str) -> str:
    identifier = _clean(value)
    if not identifier or not _ENTRY_ID_RE.match(identifier):
        raise ValueError(f"invalid observation structure dictionary {label}: {identifier or '<empty>'}")
    return identifier


def _require_non_empty_strings(values: Any, *, label: str) -> tuple[str, ...]:
    items = tuple(_dedupe(values))
    if not items:
        raise ValueError(f"observation structure dictionary {label} must contain at least one non-empty item")
    undefined_items = [item for item in items if _clean(item).lower() in _UNDEFINED_INFERENCE_MARKERS]
    if undefined_items:
        raise ValueError(
            f"observation structure dictionary {label} contains undefined marker(s): "
            + ", ".join(undefined_items)
        )
    return items


def _ensure_no_duplicates(ids: Sequence[str], *, label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise ValueError(f"duplicate observation structure dictionary {label}: {item_id}")
        seen.add(item_id)


def _validate_schema(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Validate the schema subset used by the bundled dictionary without jsonschema.

    The Cocolon-specific contract remains enforced by the semantic validators
    that follow this function.  This recursive pass covers the JSON-schema
    features present in ``emlis_observation_structure_dictionary.schema.json``
    so regression tests keep schema-drift protection without importing
    jsonschema/rfc3987/lark during pytest collection.
    """
    if not isinstance(schema, Mapping):
        raise ValueError("observation structure dictionary schema root must be an object")

    defs = schema.get("$defs")
    if not isinstance(defs, Mapping):
        defs = {}

    def _fail(path: str, message: str) -> None:
        raise ValueError(
            f"observation structure dictionary schema validation failed at {path or '<root>'}: {message}"
        )

    def _resolve_ref(ref: Any, path: str) -> Mapping[str, Any]:
        ref_text = _clean(ref)
        prefix = "#/$defs/"
        if not ref_text.startswith(prefix):
            _fail(path, f"unsupported schema ref {ref_text or '<empty>'}")
        key = ref_text[len(prefix) :]
        target = defs.get(key)
        if not isinstance(target, Mapping):
            _fail(path, f"missing schema ref {ref_text}")
        return target

    def _matches_type(value: Any, declared_type: Any) -> bool:
        if isinstance(declared_type, Sequence) and not isinstance(declared_type, (str, bytes, bytearray)):
            return any(_matches_type(value, item) for item in declared_type)
        if declared_type == "object":
            return isinstance(value, Mapping)
        if declared_type == "array":
            return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        if declared_type == "string":
            return isinstance(value, str)
        if declared_type == "boolean":
            return isinstance(value, bool)
        if declared_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if declared_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return True

    def _stable_item(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:  # pragma: no cover - defensive for non-json values
            return repr(value)

    def _validate(value: Any, spec: Mapping[str, Any], path: str) -> None:
        if "$ref" in spec:
            _validate(value, _resolve_ref(spec.get("$ref"), path), path)
            return

        if "const" in spec and value != spec.get("const"):
            _fail(path, f"expected const {spec.get('const')!r}")
        if "enum" in spec:
            enum_values = spec.get("enum")
            if isinstance(enum_values, Sequence) and not isinstance(enum_values, (str, bytes, bytearray)):
                if value not in enum_values:
                    _fail(path, f"value {value!r} is not one of the allowed enum values")
        if "type" in spec and not _matches_type(value, spec.get("type")):
            _fail(path, f"expected type {spec.get('type')}")

        if isinstance(value, str):
            min_length = spec.get("minLength")
            if isinstance(min_length, int) and len(value) < min_length:
                _fail(path, f"string is shorter than minLength {min_length}")
            pattern = spec.get("pattern")
            if isinstance(pattern, str) and not re.match(pattern, value):
                _fail(path, f"string does not match pattern {pattern}")

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            min_items = spec.get("minItems")
            if isinstance(min_items, int) and len(value) < min_items:
                _fail(path, f"array has fewer than minItems {min_items}")
            if spec.get("uniqueItems") is True:
                seen: set[str] = set()
                for item in value:
                    marker = _stable_item(item)
                    if marker in seen:
                        _fail(path, "array items must be unique")
                    seen.add(marker)
            item_spec = spec.get("items")
            if isinstance(item_spec, Mapping):
                for index, item in enumerate(value):
                    _validate(item, item_spec, f"{path}.{index}" if path else str(index))

        if isinstance(value, Mapping):
            required = spec.get("required")
            if isinstance(required, Sequence) and not isinstance(required, (str, bytes, bytearray)):
                for key in required:
                    item_key = _clean(key)
                    if item_key and item_key not in value:
                        _fail(path, f"missing required property {item_key}")
            properties = spec.get("properties")
            if isinstance(properties, Mapping):
                if spec.get("additionalProperties") is False:
                    allowed = {_clean(key) for key in properties.keys()}
                    for key in value.keys():
                        item_key = _clean(key)
                        if item_key not in allowed:
                            _fail(f"{path}.{item_key}" if path else item_key, "additional properties are not allowed")
                for key, child_spec in properties.items():
                    item_key = _clean(key)
                    if item_key in value and isinstance(child_spec, Mapping):
                        _validate(value[item_key], child_spec, f"{path}.{item_key}" if path else item_key)

    _validate(payload, schema, "")


def _normalize_question(raw: Mapping[str, Any], *, owner_id: str, index: int) -> dict[str, Any]:
    question = _clean(raw.get("question"))
    if not question:
        raise ValueError(f"observation question {owner_id}[{index}] must have question")
    answer_sources = _require_non_empty_strings(raw.get("answer_sources"), label=f"answer_sources for {owner_id}[{index}]")
    allowed = _require_non_empty_strings(raw.get("allowed_inference"), label=f"allowed_inference for {owner_id}[{index}]")
    forbidden = _require_non_empty_strings(raw.get("forbidden_inference"), label=f"forbidden_inference for {owner_id}[{index}]")
    return {
        "question": question,
        "answer_sources": list(answer_sources),
        "allowed_inference": list(allowed),
        "forbidden_inference": list(forbidden),
    }


def _normalize_relation(raw: Mapping[str, Any]) -> dict[str, Any]:
    relation_id = _require_identifier(raw.get("relation_id"), label="relation_id")
    allowed = _require_non_empty_strings(raw.get("allowed_inference"), label=f"allowed_inference for {relation_id}")
    forbidden = _require_non_empty_strings(raw.get("forbidden_inference"), label=f"forbidden_inference for {relation_id}")
    evidence = _require_non_empty_strings(raw.get("evidence_requirements"), label=f"evidence_requirements for {relation_id}")
    surface_policy = dict(raw.get("surface_policy") or {})
    if surface_policy.get("must_not_return_directly") is not True:
        raise ValueError(f"relation {relation_id} must keep surface_policy.must_not_return_directly=true")
    return {
        "relation_id": relation_id,
        "definition": _clean(raw.get("definition")),
        "evidence_requirements": list(evidence),
        "allowed_inference": list(allowed),
        "forbidden_inference": list(forbidden),
        "surface_policy": surface_policy,
    }


def _normalize_entry(raw: Mapping[str, Any]) -> dict[str, Any]:
    entry_id = _require_identifier(raw.get("entry_id"), label="entry_id")
    entry_type = _clean(raw.get("entry_type"))
    relation_candidates = _require_non_empty_strings(
        raw.get("relation_candidates"), label=f"relation_candidates for {entry_id}"
    )
    questions = raw.get("observation_questions")
    raw_questions = _as_list_of_mappings(questions, label=f"observation_questions for {entry_id}")
    allowed = _require_non_empty_strings(raw.get("allowed_inference"), label=f"allowed_inference for {entry_id}")
    forbidden = _require_non_empty_strings(raw.get("forbidden_inference"), label=f"forbidden_inference for {entry_id}")
    surface_policy = dict(raw.get("surface_policy") or {})
    if surface_policy.get("must_not_return_directly") is not True:
        raise ValueError(f"entry {entry_id} must keep surface_policy.must_not_return_directly=true")

    normalized: dict[str, Any] = {
        "entry_id": entry_id,
        "entry_type": entry_type,
        "relation_candidates": list(relation_candidates),
        "observation_questions": [
            _normalize_question(question, owner_id=entry_id, index=index)
            for index, question in enumerate(raw_questions)
        ],
        "allowed_inference": list(allowed),
        "forbidden_inference": list(forbidden),
        "surface_policy": surface_policy,
    }
    input_words = _dedupe(raw.get("input_words"))
    if input_words:
        normalized["input_words"] = input_words
    base_structure_terms = _dedupe(raw.get("base_structure_terms"))
    if base_structure_terms:
        normalized["base_structure_terms"] = base_structure_terms
    if "low_information_boundary" in raw:
        boundary = dict(raw.get("low_information_boundary") or {})
        if boundary.get("prompt_policy") != "user_agency_prompt":
            raise ValueError(f"entry {entry_id} low_information_boundary must use user_agency_prompt")
        normalized["low_information_boundary"] = boundary
    return normalized


@dataclass(frozen=True)
class ObservationStructureQuestion:
    question: str
    answer_sources: tuple[str, ...]
    allowed_inference: tuple[str, ...]
    forbidden_inference: tuple[str, ...]

    def as_meta(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer_sources": list(self.answer_sources),
            "allowed_inference": list(self.allowed_inference),
            "forbidden_inference": list(self.forbidden_inference),
        }


@dataclass(frozen=True)
class ObservationStructureRelation:
    relation_id: str
    definition: str
    evidence_requirements: tuple[str, ...]
    allowed_inference: tuple[str, ...]
    forbidden_inference: tuple[str, ...]
    surface_policy: Mapping[str, Any]

    def as_meta(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "definition": self.definition,
            "evidence_requirements": list(self.evidence_requirements),
            "allowed_inference": list(self.allowed_inference),
            "forbidden_inference": list(self.forbidden_inference),
            "surface_policy": copy.deepcopy(dict(self.surface_policy)),
        }


@dataclass(frozen=True)
class ObservationStructureEntry:
    entry_id: str
    entry_type: str
    relation_candidates: tuple[str, ...]
    observation_questions: tuple[ObservationStructureQuestion, ...]
    allowed_inference: tuple[str, ...]
    forbidden_inference: tuple[str, ...]
    surface_policy: Mapping[str, Any]
    input_words: tuple[str, ...] = field(default_factory=tuple)
    base_structure_terms: tuple[str, ...] = field(default_factory=tuple)
    low_information_boundary: Mapping[str, Any] | None = None

    def as_meta(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "relation_candidates": list(self.relation_candidates),
            "observation_questions": [question.as_meta() for question in self.observation_questions],
            "allowed_inference": list(self.allowed_inference),
            "forbidden_inference": list(self.forbidden_inference),
            "surface_policy": copy.deepcopy(dict(self.surface_policy)),
        }
        if self.input_words:
            data["input_words"] = list(self.input_words)
        if self.base_structure_terms:
            data["base_structure_terms"] = list(self.base_structure_terms)
        if self.low_information_boundary is not None:
            data["low_information_boundary"] = copy.deepcopy(dict(self.low_information_boundary))
        return data


@dataclass(frozen=True)
class ObservationStructureDictionary:
    dictionary_version: str
    purpose: str
    non_goals: tuple[str, ...]
    input_bundle_policy: Mapping[str, Any]
    global_policies: Mapping[str, Any]
    relations: tuple[ObservationStructureRelation, ...]
    entries: tuple[ObservationStructureEntry, ...]
    contract_boundaries: Mapping[str, Any]
    implementation_notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION
    dictionary_id: str = OBSERVATION_STRUCTURE_DICTIONARY_ID
    contract_step: str = OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP
    base_dictionary: str = OBSERVATION_STRUCTURE_DICTIONARY_BASE
    status: str = OBSERVATION_STRUCTURE_DICTIONARY_STATUS

    @property
    def version(self) -> str:
        return self.schema_version

    @property
    def loader_phase(self) -> str:
        return OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "dictionary_id": self.dictionary_id,
            "dictionary_version": self.dictionary_version,
            "contract_step": self.contract_step,
            "source_step": self.contract_step,
            "loader_phase": OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE,
            "loader_step": OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE,
            "base_dictionary": self.base_dictionary,
            "status": self.status,
            "purpose": self.purpose,
            "non_goals": list(self.non_goals),
            "input_bundle_policy": copy.deepcopy(dict(self.input_bundle_policy)),
            "global_policies": copy.deepcopy(dict(self.global_policies)),
            "relation_count": len(self.relations),
            "entry_count": len(self.entries),
            "relation_ids": [relation.relation_id for relation in self.relations],
            "entry_ids": [entry.entry_id for entry in self.entries],
            "relations": [relation.as_meta() for relation in self.relations],
            "entries": [entry.as_meta() for entry in self.entries],
            "contract_boundaries": copy.deepcopy(dict(self.contract_boundaries)),
            "implementation_notes": list(self.implementation_notes),
            "observation_structure_dictionary_ready": True,
            "structure_dictionary_ready": True,
            "schema_validation_passed": True,
            "reference_integrity_checked": True,
            "forbidden_inference_checked": True,
            "input_bundle_policy_checked": True,
            "comment_text_generated": False,
            "comment_text_included": False,
            "raw_text_added_to_public_metadata": False,
            "gate_or_composer_connected": False,
        }
        assert_observation_structure_dictionary_contract(meta)
        return meta


def _relation_from_meta(meta: Mapping[str, Any]) -> ObservationStructureRelation:
    normalized = _normalize_relation(meta)
    return ObservationStructureRelation(
        relation_id=normalized["relation_id"],
        definition=_clean(normalized.get("definition")),
        evidence_requirements=tuple(normalized["evidence_requirements"]),
        allowed_inference=tuple(normalized["allowed_inference"]),
        forbidden_inference=tuple(normalized["forbidden_inference"]),
        surface_policy=copy.deepcopy(normalized["surface_policy"]),
    )


def _entry_from_meta(meta: Mapping[str, Any]) -> ObservationStructureEntry:
    normalized = _normalize_entry(meta)
    return ObservationStructureEntry(
        entry_id=normalized["entry_id"],
        entry_type=normalized["entry_type"],
        input_words=tuple(normalized.get("input_words", [])),
        base_structure_terms=tuple(normalized.get("base_structure_terms", [])),
        relation_candidates=tuple(normalized["relation_candidates"]),
        observation_questions=tuple(
            ObservationStructureQuestion(
                question=question["question"],
                answer_sources=tuple(question["answer_sources"]),
                allowed_inference=tuple(question["allowed_inference"]),
                forbidden_inference=tuple(question["forbidden_inference"]),
            )
            for question in normalized["observation_questions"]
        ),
        allowed_inference=tuple(normalized["allowed_inference"]),
        forbidden_inference=tuple(normalized["forbidden_inference"]),
        low_information_boundary=copy.deepcopy(normalized.get("low_information_boundary")),
        surface_policy=copy.deepcopy(normalized["surface_policy"]),
    )


def _validate_contract_boundaries(boundaries: Mapping[str, Any]) -> None:
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if flag in boundaries and bool(boundaries.get(flag)):
            raise ValueError(f"observation structure dictionary contract changed forbidden boundary: {flag}")


def _validate_global_policies(policies: Mapping[str, Any]) -> None:
    emotion_policy = policies.get("emotion_policy")
    category_policy = policies.get("category_policy")
    thought_action_policy = policies.get("thought_action_policy")
    low_information_policy = policies.get("low_information_policy")
    surface_policy = policies.get("surface_policy")
    if not isinstance(emotion_policy, Mapping) or emotion_policy.get("selected_emotion_is_state_premise") is not True:
        raise ValueError("emotion_policy must keep selected_emotion_is_state_premise=true")
    if emotion_policy.get("emotion_strength_must_not_create_cause") is not True:
        raise ValueError("emotion_policy must keep emotion_strength_must_not_create_cause=true")
    if not isinstance(category_policy, Mapping) or category_policy.get("category_is_topic_direction_not_cause") is not True:
        raise ValueError("category_policy must keep category_is_topic_direction_not_cause=true")
    if category_policy.get("multiple_categories_default_relation") != "category_parallel":
        raise ValueError("category_policy must keep category_parallel as the default multiple-category relation")
    if category_policy.get("category_overlap_requires_textual_evidence") is not True:
        raise ValueError("category_policy must require textual evidence for category overlap")
    if not isinstance(thought_action_policy, Mapping) or thought_action_policy.get("memo_is_self_world_event") is not True:
        raise ValueError("thought_action_policy must keep memo_is_self_world_event=true")
    if thought_action_policy.get("memo_action_is_real_world_event") is not True:
        raise ValueError("thought_action_policy must keep memo_action_is_real_world_event=true")
    if not isinstance(low_information_policy, Mapping) or low_information_policy.get("must_not_fill_unknown_event") is not True:
        raise ValueError("low_information_policy must keep must_not_fill_unknown_event=true")
    if not isinstance(surface_policy, Mapping) or surface_policy.get("dictionary_is_not_completed_reply_template") is not True:
        raise ValueError("surface_policy must keep dictionary_is_not_completed_reply_template=true")
    if surface_policy.get("must_not_return_entry_text_directly") is not True:
        raise ValueError("surface_policy must keep must_not_return_entry_text_directly=true")


def _validate_input_bundle_policy(input_bundle_policy: Mapping[str, Any]) -> None:
    required_fields = frozenset(_dedupe(input_bundle_policy.get("required_current_input_fields")))
    if required_fields != _REQUIRED_CURRENT_INPUT_FIELDS:
        raise ValueError(
            "input_bundle_policy.required_current_input_fields must be memo/memo_action/emotion_details/category only"
        )
    mapping = input_bundle_policy.get("normalized_field_mapping")
    if not isinstance(mapping, Mapping):
        raise ValueError("input_bundle_policy.normalized_field_mapping must be an object")
    if frozenset(mapping.keys()) != _REQUIRED_NORMALIZED_FIELDS:
        raise ValueError("input_bundle_policy.normalized_field_mapping does not match the Phase 1 bundle fields")
    for normalized_field, expected_source in _EXPECTED_FIELD_MAPPING.items():
        field_mapping = mapping.get(normalized_field)
        if not isinstance(field_mapping, Mapping):
            raise ValueError(f"input_bundle_policy mapping for {normalized_field} must be an object")
        if field_mapping.get("source_field") != expected_source:
            raise ValueError(
                f"input_bundle_policy mapping for {normalized_field} must use source_field={expected_source}"
            )
    source_priority = tuple(_dedupe(input_bundle_policy.get("source_priority")))
    if source_priority != _REQUIRED_SOURCE_PRIORITY:
        raise ValueError("input_bundle_policy.source_priority must preserve the fixed current-input-first order")


def _validate_relations_and_entries(
    relations: Sequence[ObservationStructureRelation],
    entries: Sequence[ObservationStructureEntry],
    *,
    global_policies: Mapping[str, Any],
) -> None:
    relation_ids = [relation.relation_id for relation in relations]
    entry_ids = [entry.entry_id for entry in entries]
    _ensure_no_duplicates(relation_ids, label="relation_id")
    _ensure_no_duplicates(entry_ids, label="entry_id")
    relation_id_set = set(relation_ids)

    missing_references: list[str] = []
    for entry in entries:
        missing = [relation_id for relation_id in entry.relation_candidates if relation_id not in relation_id_set]
        if missing:
            missing_references.append(f"{entry.entry_id}: {', '.join(missing)}")
        if not entry.forbidden_inference:
            raise ValueError(f"entry {entry.entry_id} must define forbidden_inference")
        if not entry.observation_questions:
            raise ValueError(f"entry {entry.entry_id} must define observation_questions")
        for question in entry.observation_questions:
            if not question.forbidden_inference:
                raise ValueError(f"entry {entry.entry_id} observation question must define forbidden_inference")
    if missing_references:
        raise ValueError(
            "observation structure dictionary relation_candidates reference undefined relation_id(s): "
            + "; ".join(missing_references)
        )

    for relation in relations:
        if not relation.forbidden_inference:
            raise ValueError(f"relation {relation.relation_id} must define forbidden_inference")

    category_policy = global_policies.get("category_policy")
    if isinstance(category_policy, Mapping):
        default_relation = _clean(category_policy.get("multiple_categories_default_relation"))
        if default_relation and default_relation not in relation_id_set:
            raise ValueError("category_policy.multiple_categories_default_relation must reference a defined relation_id")
    low_information_policy = global_policies.get("low_information_policy")
    if isinstance(low_information_policy, Mapping):
        prompt_relation = _clean(low_information_policy.get("prompt_relation"))
        if prompt_relation and prompt_relation not in relation_id_set:
            raise ValueError("low_information_policy.prompt_relation must reference a defined relation_id")


def assert_observation_structure_dictionary_contract(value: ObservationStructureDictionary | Mapping[str, Any]) -> None:
    if isinstance(value, ObservationStructureDictionary):
        meta = value.as_meta()
    else:
        meta = dict(value)

    if _contains_forbidden_payload_key(meta):
        raise ValueError("observation structure dictionary contract must not include public comment/raw payload keys")
    for key, item in _walk_mappings(meta):
        if key in _FORBIDDEN_TRUE_FLAGS and bool(item):
            raise ValueError(f"observation structure dictionary contract changed forbidden flag: {key}")

    if _clean(meta.get("schema_version") or meta.get("version")) != OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("observation structure dictionary schema_version mismatch")
    if _clean(meta.get("dictionary_id")) != OBSERVATION_STRUCTURE_DICTIONARY_ID:
        raise ValueError("observation structure dictionary_id mismatch")
    if _clean(meta.get("contract_step")) != OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP:
        raise ValueError("observation structure dictionary contract_step mismatch")
    if _clean(meta.get("base_dictionary")) != OBSERVATION_STRUCTURE_DICTIONARY_BASE:
        raise ValueError("observation structure dictionary base_dictionary mismatch")

    boundaries = meta.get("contract_boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("observation structure dictionary must include contract_boundaries")
    _validate_contract_boundaries(boundaries)

    input_bundle_policy = meta.get("input_bundle_policy")
    if not isinstance(input_bundle_policy, Mapping):
        raise ValueError("observation structure dictionary must include input_bundle_policy")
    _validate_input_bundle_policy(input_bundle_policy)

    policies = meta.get("global_policies")
    if not isinstance(policies, Mapping):
        raise ValueError("observation structure dictionary must include global_policies")
    _validate_global_policies(policies)

    relation_metas = _as_list_of_mappings(meta.get("relations"), label="relations")
    entry_metas = _as_list_of_mappings(meta.get("entries"), label="entries")
    relations = tuple(_relation_from_meta(relation) for relation in relation_metas)
    entries = tuple(_entry_from_meta(entry) for entry in entry_metas)
    _validate_relations_and_entries(relations, entries, global_policies=policies)


def validate_observation_structure_dictionary_payload(
    payload: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    validate_schema: bool = True,
) -> ObservationStructureDictionary:
    if not isinstance(payload, Mapping):
        raise ValueError("observation structure dictionary root must be an object")
    if _contains_forbidden_payload_key(payload):
        raise ValueError("observation structure dictionary payload must not contain public comment/raw payload keys")

    if validate_schema:
        resolved_schema = schema if schema is not None else load_observation_structure_dictionary_schema()
        _validate_schema(payload, resolved_schema)

    if _clean(payload.get("schema_version")) != OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION:
        raise ValueError("unsupported observation structure dictionary schema_version")
    if _clean(payload.get("dictionary_id")) != OBSERVATION_STRUCTURE_DICTIONARY_ID:
        raise ValueError("unsupported observation structure dictionary_id")
    if _clean(payload.get("contract_step")) != OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP:
        raise ValueError("unsupported observation structure dictionary contract_step")
    if _clean(payload.get("base_dictionary")) != OBSERVATION_STRUCTURE_DICTIONARY_BASE:
        raise ValueError("unsupported observation structure dictionary base_dictionary")

    dictionary_version = _clean(payload.get("dictionary_version"))
    if not dictionary_version:
        raise ValueError("observation structure dictionary must have dictionary_version")

    relation_metas = _as_list_of_mappings(payload.get("relations"), label="relations")
    entry_metas = _as_list_of_mappings(payload.get("entries"), label="entries")
    relations = tuple(_relation_from_meta(relation) for relation in relation_metas)
    entries = tuple(_entry_from_meta(entry) for entry in entry_metas)

    input_bundle_policy = payload.get("input_bundle_policy")
    global_policies = payload.get("global_policies")
    contract_boundaries = payload.get("contract_boundaries")
    if not isinstance(input_bundle_policy, Mapping):
        raise ValueError("observation structure dictionary must include input_bundle_policy")
    if not isinstance(global_policies, Mapping):
        raise ValueError("observation structure dictionary must include global_policies")
    if not isinstance(contract_boundaries, Mapping):
        raise ValueError("observation structure dictionary must include contract_boundaries")

    _validate_input_bundle_policy(input_bundle_policy)
    _validate_global_policies(global_policies)
    _validate_contract_boundaries(contract_boundaries)
    _validate_relations_and_entries(relations, entries, global_policies=global_policies)

    dictionary = ObservationStructureDictionary(
        dictionary_version=dictionary_version,
        purpose=_clean(payload.get("purpose")),
        non_goals=tuple(_require_non_empty_strings(payload.get("non_goals"), label="non_goals")),
        input_bundle_policy=copy.deepcopy(dict(input_bundle_policy)),
        global_policies=copy.deepcopy(dict(global_policies)),
        relations=relations,
        entries=entries,
        contract_boundaries=copy.deepcopy(dict(contract_boundaries)),
        implementation_notes=tuple(_dedupe(payload.get("implementation_notes"))),
        schema_version=_clean(payload.get("schema_version")),
        dictionary_id=_clean(payload.get("dictionary_id")),
        contract_step=_clean(payload.get("contract_step")),
        base_dictionary=_clean(payload.get("base_dictionary")),
        status=_clean(payload.get("status")),
    )
    assert_observation_structure_dictionary_contract(dictionary.as_meta())
    return dictionary


def load_observation_structure_dictionary_schema(path: str | Path | None = None) -> dict[str, Any]:
    schema_path = Path(path) if path is not None else DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_PATH
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)
    if not isinstance(schema, Mapping):
        raise ValueError("observation structure dictionary schema root must be an object")
    if _clean(schema.get("$id")) != "https://cocolon.local/schemas/emlis_observation_structure_dictionary.v1.json":
        raise ValueError("observation structure dictionary schema $id mismatch")
    return dict(schema)


def load_observation_structure_dictionary(path: str | Path | None = None) -> ObservationStructureDictionary:
    dictionary_path = Path(path) if path is not None else DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_PATH
    with dictionary_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, Mapping):
        raise ValueError("observation structure dictionary root must be an object")
    return validate_observation_structure_dictionary_payload(payload)


def select_observation_structure_entries(
    dictionary: ObservationStructureDictionary | Mapping[str, Any] | None = None,
    *,
    entry_type: str | None = None,
    relation_id: str | None = None,
    input_word: str | None = None,
) -> list[dict[str, Any]]:
    if dictionary is None:
        resolved = load_observation_structure_dictionary()
    elif isinstance(dictionary, ObservationStructureDictionary):
        resolved = dictionary
    elif isinstance(dictionary, Mapping):
        resolved = validate_observation_structure_dictionary_payload(dictionary)
    else:
        raise ValueError("dictionary must be ObservationStructureDictionary or payload mapping")

    selected_type = _clean(entry_type)
    selected_relation = _clean(relation_id)
    selected_word = _clean(input_word)

    out: list[dict[str, Any]] = []
    for entry in resolved.entries:
        if selected_type and entry.entry_type != selected_type:
            continue
        if selected_relation and selected_relation not in entry.relation_candidates:
            continue
        if selected_word and selected_word not in entry.input_words:
            continue
        out.append(entry.as_meta())
    return out


def select_observation_structure_relations(
    dictionary: ObservationStructureDictionary | Mapping[str, Any] | None = None,
    *,
    relation_id: str | None = None,
) -> list[dict[str, Any]]:
    if dictionary is None:
        resolved = load_observation_structure_dictionary()
    elif isinstance(dictionary, ObservationStructureDictionary):
        resolved = dictionary
    elif isinstance(dictionary, Mapping):
        resolved = validate_observation_structure_dictionary_payload(dictionary)
    else:
        raise ValueError("dictionary must be ObservationStructureDictionary or payload mapping")

    selected_relation = _clean(relation_id)
    out: list[dict[str, Any]] = []
    for relation in resolved.relations:
        if selected_relation and relation.relation_id != selected_relation:
            continue
        out.append(relation.as_meta())
    return out


def dump_observation_structure_dictionary_contract(
    value: ObservationStructureDictionary | Mapping[str, Any] | None = None,
) -> str:
    if value is None:
        value = load_observation_structure_dictionary()
    if isinstance(value, ObservationStructureDictionary):
        meta = value.as_meta()
    else:
        meta = dict(value)
        assert_observation_structure_dictionary_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


# Backward-friendly aliases for future integration code.
load_emlis_ai_observation_structure_dictionary = load_observation_structure_dictionary
load_emlis_ai_observation_structure_dictionary_schema = load_observation_structure_dictionary_schema
validate_emlis_ai_observation_structure_dictionary_payload = validate_observation_structure_dictionary_payload
assert_emlis_ai_observation_structure_dictionary_contract = assert_observation_structure_dictionary_contract
dump_emlis_ai_observation_structure_dictionary_contract = dump_observation_structure_dictionary_contract
select_emlis_ai_observation_structure_entries = select_observation_structure_entries
select_emlis_ai_observation_structure_relations = select_observation_structure_relations
