# -*- coding: utf-8 -*-
from __future__ import annotations

"""Grounded, body-free lexicalization authority for Step 11.

This module projects only validated ``GroundedSourceSnapshot`` attributes into
a closed sequence of short Japanese feature atoms.  It never reads corpus or
case identity, never stores a completed sentence, and never treats a visible
source quotation as semantic coverage.  A bounded source anchor is available
only as a candidate-wide disambiguator when the feature phrase alone cannot
bind two otherwise identical nuclei.
"""

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


STEP11_GROUNDED_LEXICALIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_grounded_lexicalization.rc0027.v2"
)
STEP11_VISIBLE_SOURCE_ANCHOR_REASON = "INPUT_SPECIFIC_BINDING_REQUIRED"

_FEATURE_ORDER = (
    "semantic_role",
    "temporal_scope",
    "modality",
    "source_field",
    "referent_scope",
    "label_strength",
    "polarity",
    "semantic_qualifier",
    "action_lifecycle",
    "nucleus_kind",
)
_BASE_FEATURES = frozenset({"nucleus_kind"})
_COLLISION_FEATURES = (
    "label_strength",
    "semantic_qualifier",
    "source_field",
    "referent_scope",
)
_FORBIDDEN_ANCHOR_RE = re.compile(
    r"[\r\n\x00-\x1f\x7f\u2028\u2029"
    r"。、，．！？!?;；:：,.'\"`"
    r"\(\)\[\]\{\}（）［］｛｝〈〉《》【】〔〕"
    r"\u300c\u300d\u300e\u300f]"
)
_FORBIDDEN_ANCHOR_LABELS = ("見えたこと", "Emlisから", "Emlis")


class Step11GroundedLexicalizationError(ValueError):
    """Fail-closed error carrying no request text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11GroundedPhraseSpec:
    grounded_phrase_id: str
    owner_nucleus_ids: tuple[str, ...]
    owner_obligation_ids: tuple[str, ...]
    visible_feature_fields: tuple[tuple[str, str], ...]
    visible_feature_fingerprint_sha256: str
    phrase_profile_id: str
    anchor_risk_rank: int
    phrase_text: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11VisibleSourceAnchorUse:
    anchor_use_id: str
    source_fragment_anchor_id: str
    owner_nucleus_id: str
    owner_obligation_id: str
    source_slot: str
    source_start: int
    source_end: int
    scalar_count: int
    anchor_text: str
    anchor_text_sha256: str
    binding_family: str
    reason_code: str


def step11_grounded_phrase_spec_material(
    value: Step11GroundedPhraseSpec,
) -> dict[str, Any]:
    return {
        "grounded_phrase_id": value.grounded_phrase_id,
        "owner_nucleus_ids": list(value.owner_nucleus_ids),
        "owner_obligation_ids": list(value.owner_obligation_ids),
        "visible_feature_fields": [
            [name, feature_value]
            for name, feature_value in value.visible_feature_fields
        ],
        "visible_feature_fingerprint_sha256": (
            value.visible_feature_fingerprint_sha256
        ),
        "phrase_profile_id": value.phrase_profile_id,
        "anchor_risk_rank": value.anchor_risk_rank,
        "phrase_text": value.phrase_text,
    }


def step11_visible_source_anchor_use_material(
    value: Step11VisibleSourceAnchorUse,
) -> dict[str, Any]:
    return {
        "anchor_use_id": value.anchor_use_id,
        "source_fragment_anchor_id": value.source_fragment_anchor_id,
        "owner_nucleus_id": value.owner_nucleus_id,
        "owner_obligation_id": value.owner_obligation_id,
        "source_slot": value.source_slot,
        "source_start": value.source_start,
        "source_end": value.source_end,
        "scalar_count": value.scalar_count,
        "anchor_text": value.anchor_text,
        "anchor_text_sha256": value.anchor_text_sha256,
        "binding_family": value.binding_family,
        "reason_code": value.reason_code,
    }


def _source_field(source: Any) -> str:
    token_map = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "feature_tokens"
    ]["source_field"]
    values = tuple(str(value) for value in source.source_fields)
    if len(values) == 1 and values[0] in token_map:
        return values[0]
    return "mixed"


def _semantic_role(source: Any) -> str:
    result = "none"
    for code in source.source_attribute_codes:
        if code == "unit_role:antecedent":
            result = "antecedent"
        elif code == "unit_role:consequent":
            result = "consequent"
    return result


def _semantic_qualifier(source: Any) -> str:
    attribute_codes = frozenset(str(code) for code in source.source_attribute_codes)
    for key in (
        "concrete_action_evidence",
        "concrete_action",
        "contrast_before",
        "contrast_after",
        "embedded_turn",
        "initial_condition",
        "retained_intention",
    ):
        if f"semantic_role:{key}" in attribute_codes:
            return f"source_semantic_role:{key}"
    for key in ("constraint", "continuation", "shift", "action", "wish"):
        if f"operator:{key}" in attribute_codes:
            return f"source_operator:{key}"
    allowed_blocks = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "feature_tokens"
    ]["semantic_qualifier"]
    for block_key in source.source_meaning_block_keys:
        key = str(block_key).rsplit(":", 1)[-1]
        value = f"meaning_block_kind:{key}"
        if value in allowed_blocks:
            return value
    return "none"


def _raw_feature_values(
    source: Any,
    additional_values: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    additional = {
        str(name): str(value)
        for name, value in (additional_values or {}).items()
    }
    unsupported = set(additional) - {
        "label_strength",
        "realization_lifecycle",
    }
    if unsupported:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_ADDITIONAL_FEATURE_UNSUPPORTED"
        )
    lifecycle = additional.get("realization_lifecycle", "not_applicable")
    modality = str(source.modality)
    temporal_scope = str(source.temporal_scope)
    if str(source.kind) == "action":
        lifecycle_policy = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
            "lifecycle_authority_policy"
        ]
        projection = lifecycle_policy["action_projection"].get(lifecycle)
        if projection is not None:
            modality = str(projection["modality"])
            temporal_scope = str(projection["temporal_scope"])
        elif lifecycle != "not_applicable":
            raise Step11GroundedLexicalizationError(
                "STEP11_GROUNDED_ACTION_LIFECYCLE_UNSUPPORTED"
            )
    result = {
        "temporal_scope": temporal_scope,
        "source_field": _source_field(source),
        "semantic_role": _semantic_role(source),
        "polarity": str(source.polarity),
        "semantic_qualifier": _semantic_qualifier(source),
        "modality": modality,
        "referent_scope": str(source.referent_scope),
        "label_strength": additional.get("label_strength", "none"),
        "action_lifecycle": (
            lifecycle if str(source.kind) == "action" else "not_applicable"
        ),
        "nucleus_kind": str(source.kind),
        "realization_lifecycle": lifecycle,
        "source_attribute_codes": tuple(
            sorted(str(code) for code in source.source_attribute_codes)
        ),
        "source_predicate_kind": str(source.source_predicate_kind),
        "required": bool(source.required),
    }
    return result


def _feature_values(
    raw: Mapping[str, str],
    selected_names: frozenset[str],
) -> tuple[tuple[str, str], ...]:
    token_maps = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "feature_tokens"
    ]
    fields: list[tuple[str, str]] = []
    for name in _FEATURE_ORDER:
        if name not in selected_names:
            continue
        value = raw[name]
        tokens = token_maps.get(name)
        if type(tokens) is not dict or value not in tokens:
            raise Step11GroundedLexicalizationError(
                "STEP11_GROUNDED_FEATURE_VALUE_UNSUPPORTED"
            )
        if tokens[value]:
            fields.append((name, value))
    if not fields or fields[-1][0] != "nucleus_kind":
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_FEATURE_HEAD_UNRESOLVED"
        )
    return tuple(fields)


def _profile_matches(
    profile: Mapping[str, Any], raw: Mapping[str, Any]
) -> bool:
    match = profile.get("match")
    if type(match) is not dict:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_MATCH_INVALID"
        )
    allowed = {
        "nucleus_kinds": "nucleus_kind",
        "modalities": "modality",
        "polarities": "polarity",
        "label_strengths": "label_strength",
        "lifecycles": "realization_lifecycle",
    }
    for condition_name, raw_name in allowed.items():
        values = match.get(condition_name)
        if values is None:
            continue
        if type(values) is not list or not values or raw[raw_name] not in values:
            return False
    attribute_codes = frozenset(raw["source_attribute_codes"])
    all_codes = match.get("all_attribute_codes", [])
    any_codes = match.get("any_attribute_codes", [])
    if type(all_codes) is not list or type(any_codes) is not list:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_MATCH_INVALID"
        )
    if not set(str(value) for value in all_codes) <= attribute_codes:
        return False
    if any_codes and not attribute_codes & {
        str(value) for value in any_codes
    }:
        return False
    known_keys = {*allowed, "all_attribute_codes", "any_attribute_codes"}
    if set(match) - known_keys:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_MATCH_INVALID"
        )
    return True


def _select_phrase_profile(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    registry = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "phrase_profile_registry"
    ]
    profiles = registry.get("profiles") if type(registry) is dict else None
    if type(profiles) is not list or not profiles:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_REGISTRY_INVALID"
        )
    matches = tuple(
        profile
        for profile in profiles
        if type(profile) is dict and _profile_matches(profile, raw)
    )
    if not matches:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_UNRESOLVED"
        )
    profile = matches[0]
    if (
        type(profile.get("profile_id")) is not str
        or type(profile.get("noun_phrase")) is not str
        or not profile["noun_phrase"]
        or type(profile.get("anchor_risk_rank")) is not int
        or type(profile.get("visible_feature_names")) is not list
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_INVALID"
        )
    return profile


def _phrase_text(
    raw: Mapping[str, Any], selected_names: frozenset[str]
) -> tuple[str, Mapping[str, Any]]:
    token_maps = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "feature_tokens"
    ]
    profile = _select_phrase_profile(raw)
    profile_visible_names = frozenset(
        str(value) for value in profile["visible_feature_names"]
    )
    if not profile_visible_names <= frozenset(_FEATURE_ORDER):
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PROFILE_VISIBLE_FEATURE_INVALID"
        )
    atoms = tuple(
        token_maps[name][raw[name]]
        for name in _COLLISION_FEATURES
        if name in selected_names
        and name not in profile_visible_names
        and token_maps[name][raw[name]]
    ) + (str(profile["noun_phrase"]),)
    if len(atoms) != len(set(atoms)):
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PHRASE_ATOM_REPEATED"
        )
    text = "".join(atoms)
    text = unicodedata.normalize("NFC", text)
    if not text or "\r" in text or "\n" in text:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PHRASE_TEXT_INVALID"
        )
    return text, profile


def build_step11_grounded_phrase_specs(
    source_snapshot: Any,
    clauses: Sequence[Any],
    *,
    additional_owner_obligation_ids: Mapping[str, Sequence[str]] | None = None,
    additional_visible_feature_values: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> tuple[Step11GroundedPhraseSpec, ...]:
    """Build one deterministic semantic-feature phrase per active nucleus."""

    owners: dict[str, list[str]] = {}
    for clause in clauses:
        obligation_id = str(clause.obligation_id)
        for nucleus_id in clause.source_nucleus_ids:
            owners.setdefault(str(nucleus_id), []).append(obligation_id)
    for nucleus_id, obligation_ids in (
        additional_owner_obligation_ids or {}
    ).items():
        for obligation_id in obligation_ids:
            owners.setdefault(str(nucleus_id), []).append(str(obligation_id))
    if not owners:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PHRASE_OWNER_MISSING"
        )
    source_by_id = {
        str(source.source_id): source for source in source_snapshot.nuclei
    }
    ordered_nucleus_ids = tuple(
        str(source.source_id)
        for source in source_snapshot.nuclei
        if str(source.source_id) in owners
    )
    raw_by_id = {
        nucleus_id: _raw_feature_values(
            source_by_id[nucleus_id],
            (additional_visible_feature_values or {}).get(nucleus_id),
        )
        for nucleus_id in ordered_nucleus_ids
    }
    profile_by_id = {
        nucleus_id: _select_phrase_profile(raw_by_id[nucleus_id])
        for nucleus_id in ordered_nucleus_ids
    }
    selected_by_id = {
        nucleus_id: set(_BASE_FEATURES)
        | {
            str(name)
            for name in profile_by_id[nucleus_id]["visible_feature_names"]
        }
        for nucleus_id in ordered_nucleus_ids
    }
    for optional_name in _COLLISION_FEATURES:
        phrase_groups: dict[str, list[str]] = {}
        for nucleus_id in ordered_nucleus_ids:
            _fields = _feature_values(
                raw_by_id[nucleus_id],
                frozenset(selected_by_id[nucleus_id]),
            )
            phrase_text, _profile = _phrase_text(
                raw_by_id[nucleus_id],
                frozenset(selected_by_id[nucleus_id]),
            )
            phrase_groups.setdefault(phrase_text, []).append(nucleus_id)
        token_map = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
            "feature_tokens"
        ][optional_name]
        for rows in phrase_groups.values():
            if len(rows) <= 1:
                continue
            visible_values = {
                token_map[raw_by_id[nucleus_id][optional_name]]
                for nucleus_id in rows
            }
            if len(visible_values) <= 1:
                continue
            for nucleus_id in rows:
                selected_by_id[nucleus_id].add(optional_name)

    result: list[Step11GroundedPhraseSpec] = []
    for nucleus_id in ordered_nucleus_ids:
        source = source_by_id[nucleus_id]
        fields = _feature_values(
            raw_by_id[nucleus_id],
            frozenset(selected_by_id[nucleus_id]),
        )
        phrase_text, profile = _phrase_text(
            raw_by_id[nucleus_id],
            frozenset(selected_by_id[nucleus_id]),
        )
        fingerprint = artifact_sha256(
            {
                "visible_feature_fields": [list(row) for row in fields],
                "phrase_profile_id": str(profile["profile_id"]),
            }
        )
        source_semantics = {
            "owner_nucleus_ids": [nucleus_id],
            "owner_obligation_ids": list(dict.fromkeys(owners[nucleus_id])),
            "visible_feature_fields": [list(row) for row in fields],
            "source_predicate_kind": str(source.source_predicate_kind),
            "source_actor": str(source.source_actor),
            "source_degree": str(source.source_degree),
            "source_attribute_codes": sorted(
                str(value) for value in source.source_attribute_codes
            ),
            "realization_lifecycle": raw_by_id[nucleus_id][
                "realization_lifecycle"
            ],
            "phrase_profile_id": str(profile["profile_id"]),
            "anchor_risk_rank": int(profile["anchor_risk_rank"]),
        }
        result.append(
            Step11GroundedPhraseSpec(
                grounded_phrase_id=(
                    "nls3s11gp_" + artifact_sha256(source_semantics)[:16]
                ),
                owner_nucleus_ids=(nucleus_id,),
                owner_obligation_ids=tuple(dict.fromkeys(owners[nucleus_id])),
                visible_feature_fields=fields,
                visible_feature_fingerprint_sha256=fingerprint,
                phrase_profile_id=str(profile["profile_id"]),
                anchor_risk_rank=int(profile["anchor_risk_rank"]),
                phrase_text=phrase_text,
            )
        )
    if set(owners) != {
        nucleus_id
        for spec in result
        for nucleus_id in spec.owner_nucleus_ids
    }:
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PHRASE_SOURCE_UNRESOLVED"
        )
    return tuple(result)


def _anchor_scalar_is_unsafe(character: str) -> bool:
    return bool(
        character.isspace()
        or unicodedata.category(character).startswith("C")
        or _FORBIDDEN_ANCHOR_RE.search(character) is not None
    )


def _anchor_candidate_is_complete(value: str) -> bool:
    policy = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "anchor_segment_policy"
    ]
    minimum = int(policy["minimum_scalars"])
    maximum = int(policy["maximum_scalars"])
    prefixes = tuple(str(row) for row in policy["dangling_prefixes"])
    suffixes = tuple(str(row) for row in policy["dangling_suffixes"])
    return bool(
        minimum <= len(value) <= maximum
        and unicodedata.normalize("NFC", value) == value
        and value == value.strip()
        and not any(_anchor_scalar_is_unsafe(char) for char in value)
        and not any(label in value for label in _FORBIDDEN_ANCHOR_LABELS)
        and not value.startswith(prefixes)
        and not value.endswith(suffixes)
    )


def step11_safe_anchor_segments(
    fragment: Any,
) -> tuple[tuple[str, int, int], ...]:
    """Return only exact whole fragments or punctuation-delimited runs.

    Long runs are never shortened.  In particular, particles and connective
    stems are not treated as trusted boundaries: an overlong run simply has
    no visible-anchor authority and the caller must fail closed or choose a
    different owner.
    """

    value = str(fragment.text)
    if (
        unicodedata.normalize("NFC", value) != value
        or any(
            character.isspace()
            or unicodedata.category(character).startswith("C")
            for character in value
        )
    ):
        return ()
    policy = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "anchor_segment_policy"
    ]
    maximum = int(policy["maximum_scalars"])
    source_start = int(fragment.source_start)
    source_end = int(fragment.source_end)
    candidates: set[tuple[str, int, int]] = set()
    run_start: int | None = None
    runs: list[tuple[int, int]] = []
    for index, character in enumerate(value):
        punctuation = _FORBIDDEN_ANCHOR_RE.search(character) is not None
        if not punctuation and run_start is None:
            run_start = index
        if punctuation and run_start is not None:
            runs.append((run_start, index))
            run_start = None
    if run_start is not None:
        runs.append((run_start, len(value)))
    for relative_start, relative_end in runs:
        run = value[relative_start:relative_end]
        if len(run) <= maximum and _anchor_candidate_is_complete(run):
            candidates.add((run, relative_start, relative_end))
    exact: list[tuple[str, int, int]] = []
    for text, relative_start, relative_end in candidates:
        absolute_start = source_start + relative_start
        absolute_end = source_start + relative_end
        if (
            absolute_start < source_start
            or absolute_end > source_end
            or absolute_end - absolute_start != len(text)
            or value[relative_start:relative_end] != text
        ):
            continue
        exact.append((text, absolute_start, absolute_end))
    return tuple(
        (text, start, end)
        for text, start, end in sorted(
            exact,
            key=lambda row: (-len(row[0]), row[1], row[2], row[0]),
        )
    )


def select_step11_visible_source_anchor_use(
    grounded_phrase_specs: Sequence[Step11GroundedPhraseSpec],
    source_fragments: Sequence[Any],
    *,
    preferred_owner_nucleus_ids: Sequence[str] = (),
    binding_family_by_nucleus: Mapping[str, str] | None = None,
    require_input_specific_binding: bool = False,
) -> Step11VisibleSourceAnchorUse | None:
    """Select zero or one strictly necessary candidate-wide source anchor."""

    collision_groups: dict[str, list[Step11GroundedPhraseSpec]] = {}
    for spec in grounded_phrase_specs:
        collision_groups.setdefault(spec.phrase_text, []).append(spec)
    collisions = tuple(
        tuple(rows)
        for _text, rows in sorted(collision_groups.items())
        if len(rows) > 1
    )
    if collisions and (len(collisions) != 1 or len(collisions[0]) != 2):
        raise Step11GroundedLexicalizationError(
            "STEP11_GROUNDED_PHRASE_AMBIGUOUS"
        )
    if not collisions and not require_input_specific_binding:
        return None
    eligible_specs = (
        collisions[0] if collisions else tuple(grounded_phrase_specs)
    )
    eligible_ids = tuple(
        spec.owner_nucleus_ids[0] for spec in eligible_specs
    )
    fragments_by_nucleus: dict[str, list[Any]] = {
        nucleus_id: [] for nucleus_id in eligible_ids
    }
    for fragment in source_fragments:
        for nucleus_id in fragments_by_nucleus:
            if (
                nucleus_id in fragment.source_nucleus_ids
            ):
                fragments_by_nucleus[nucleus_id].append(fragment)
    visible_by_nucleus = {
        nucleus_id: tuple(
            (fragment, anchor_text, source_start, source_end)
            for fragment in sorted(
                fragments,
                key=lambda row: (
                    str(row.source_slot),
                    int(row.source_start),
                    int(row.source_end),
                    str(row.source_anchor_id),
                ),
            )
            for anchor_text, source_start, source_end
            in step11_safe_anchor_segments(fragment)
        )
        for nucleus_id, fragments in fragments_by_nucleus.items()
    }
    preferred = tuple(
        dict.fromkeys(
            (
                *(str(value) for value in preferred_owner_nucleus_ids),
                *eligible_ids,
            )
        )
    )
    spec_by_nucleus = {
        spec.owner_nucleus_ids[0]: spec for spec in eligible_specs
    }
    lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    binding_families = lexical["source_anchor_binding_families"]
    profiles = lexical["phrase_profile_registry"]["profiles"]
    profile_binding_family = {
        str(profile["profile_id"]): str(profile["binding_family"])
        for profile in profiles
    }
    for nucleus_id in preferred:
        spec = spec_by_nucleus.get(nucleus_id)
        if spec is None:
            continue
        nucleus_id = spec.owner_nucleus_ids[0]
        binding_family = str(
            (binding_family_by_nucleus or {}).get(
                nucleus_id,
                profile_binding_family.get(spec.phrase_profile_id, ""),
            )
        )
        if binding_family not in binding_families:
            raise Step11GroundedLexicalizationError(
                "STEP11_VISIBLE_SOURCE_ANCHOR_BINDING_FAMILY_INVALID"
            )
        other_anchors = {
            anchor_text
            for other_id in eligible_ids
            if other_id != nucleus_id
            for _fragment, anchor_text, _start, _end
            in visible_by_nucleus[other_id]
        }
        anchor_options = visible_by_nucleus[nucleus_id]
        if binding_family == "action_lifecycle":
            # Japanese action clauses normally resolve their tense and
            # ordering at the final predicate.  Prefer the exact safe range
            # nearest the fragment's right edge instead of an earlier
            # subordinate run.
            anchor_options = tuple(
                sorted(
                    anchor_options,
                    key=lambda row: (
                        int(row[0].source_end) - row[3],
                        -len(row[1]),
                        row[2],
                        row[3],
                        row[1],
                    ),
                )
            )
        for fragment, anchor_text, source_start, source_end in anchor_options:
            if anchor_text in other_anchors:
                continue
            owner_obligation_id = spec.owner_obligation_ids[0]
            material: Mapping[str, str] = {
                "source_fragment_anchor_id": str(fragment.source_anchor_id),
                "owner_nucleus_id": nucleus_id,
                "owner_obligation_id": owner_obligation_id,
                "source_slot": str(fragment.source_slot),
                "source_start": str(source_start),
                "source_end": str(source_end),
                "scalar_count": str(len(anchor_text)),
                "anchor_text_sha256": hashlib.sha256(
                    anchor_text.encode("utf-8")
                ).hexdigest(),
                "binding_family": binding_family,
                "reason_code": STEP11_VISIBLE_SOURCE_ANCHOR_REASON,
            }
            return Step11VisibleSourceAnchorUse(
                anchor_use_id="nls3s11anchor_" + artifact_sha256(material)[:16],
                source_fragment_anchor_id=str(fragment.source_anchor_id),
                owner_nucleus_id=nucleus_id,
                owner_obligation_id=owner_obligation_id,
                source_slot=str(fragment.source_slot),
                source_start=source_start,
                source_end=source_end,
                scalar_count=len(anchor_text),
                anchor_text=anchor_text,
                anchor_text_sha256=material["anchor_text_sha256"],
                binding_family=binding_family,
                reason_code=STEP11_VISIBLE_SOURCE_ANCHOR_REASON,
            )
    raise Step11GroundedLexicalizationError(
        "STEP11_GROUNDED_PHRASE_AMBIGUOUS"
        if collisions
        else "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED"
    )


def render_step11_grounded_phrase(
    spec: Step11GroundedPhraseSpec,
    visible_source_anchor_use: Step11VisibleSourceAnchorUse | None = None,
) -> str:
    """Render a natural noun phrase, optionally with the sole source anchor."""

    if visible_source_anchor_use is None:
        return spec.phrase_text
    anchor = visible_source_anchor_use
    grammar = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    binding_families = grammar["source_anchor_binding_families"]
    if (
        anchor.owner_nucleus_id not in spec.owner_nucleus_ids
        or anchor.owner_obligation_id not in spec.owner_obligation_ids
        or anchor.reason_code != STEP11_VISIBLE_SOURCE_ANCHOR_REASON
        or anchor.scalar_count != len(anchor.anchor_text)
        or not 2 <= anchor.scalar_count <= 16
        or anchor.source_end - anchor.source_start != anchor.scalar_count
        or anchor.source_start < 0
        or anchor.source_end <= anchor.source_start
        or unicodedata.normalize("NFC", anchor.anchor_text)
        != anchor.anchor_text
        or anchor.anchor_text != anchor.anchor_text.strip()
        or _FORBIDDEN_ANCHOR_RE.search(anchor.anchor_text)
        or any(
            unicodedata.category(char).startswith("C")
            for char in anchor.anchor_text
        )
        or not _anchor_candidate_is_complete(anchor.anchor_text)
        or any(label in anchor.anchor_text for label in _FORBIDDEN_ANCHOR_LABELS)
        or anchor.binding_family not in binding_families
        or hashlib.sha256(anchor.anchor_text.encode("utf-8")).hexdigest()
        != anchor.anchor_text_sha256
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_VISIBLE_SOURCE_ANCHOR_INVALID"
        )
    return (
        grammar["source_anchor_open"]
        + anchor.anchor_text
        + grammar["source_anchor_close"]
        + binding_families[anchor.binding_family]
        + spec.phrase_text
    )


__all__ = [
    "STEP11_GROUNDED_LEXICALIZATION_SCHEMA",
    "STEP11_VISIBLE_SOURCE_ANCHOR_REASON",
    "Step11GroundedLexicalizationError",
    "Step11GroundedPhraseSpec",
    "Step11VisibleSourceAnchorUse",
    "build_step11_grounded_phrase_specs",
    "render_step11_grounded_phrase",
    "select_step11_visible_source_anchor_use",
    "step11_safe_anchor_segments",
    "step11_grounded_phrase_spec_material",
    "step11_visible_source_anchor_use_material",
]
