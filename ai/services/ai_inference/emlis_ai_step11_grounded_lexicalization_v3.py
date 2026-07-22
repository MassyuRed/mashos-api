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


# ---------------------------------------------------------------------------
# rc0028 runtime-disconnected successor projection (append-only)
# ---------------------------------------------------------------------------

STEP11_RC0028_EXPERIMENT_LEXICAL_ATOM_SPECS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0028_experiment_lexical_atom_specs.v1"
)
_STEP11_RC0028_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STEP11_RC0028_OWNER_ORDINAL_MAX = 24


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentOwnerBinding:
    source_owner_id: str
    source_owner_kind: str
    owner_ordinal: int
    owner_ordinal_token: str


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParticipationBinding:
    participation_id: str
    parent_nucleus_id: str
    construction_slot_id: str
    target_owner_kind: str
    target_owner_id: str
    target_owner_ordinal: int
    target_owner_ordinal_token: str
    owner_resolution: str
    source_span_id: str
    intersection_start_index: int
    intersection_end_index: int
    semantic_equivalence_authorized: bool


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentConstructionInstanceBinding:
    construction_instance_id: str
    parent_nucleus_id: str
    construction_code: str
    construction_atom_code: str
    construction_surface_token: str
    source_field: str
    source_field_role: str
    source_span_id: str
    evidence_alias_ids: tuple[str, ...]
    instance_start_index: int
    instance_end_index: int
    slot_ids: tuple[str, ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentConstructionIntervalBinding:
    left_construction_instance_id: str
    right_construction_instance_id: str
    range_relation: str


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentConstructionLexicalAtomSpec:
    lexical_atom_id: str
    facet_id: str
    construction_slot_id: str
    construction_instance_id: str
    parent_nucleus_id: str
    source_span_id: str
    source_field: str
    source_field_role: str
    evidence_alias_ids: tuple[str, ...]
    slot_start_index: int
    slot_end_index: int
    lexical_role_kind: str
    construction_code: str
    construction_position: str
    lexical_internal_link: str
    construction_atom_code: str
    construction_surface_token: str
    role_position_atom_code: str
    role_position_surface_token: str
    participation_ids: tuple[str, ...]
    target_owner_ordinals: tuple[int, ...]
    visible_authority: str
    required: bool
    semantic_coverage_authority: str = "none"


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec:
    lexical_atom_id: str
    experiment_relation_id: str
    source_relation_id: str
    refines_source_relation_id: str | None
    authority_basis: str
    source_relation_type: str
    effective_relation_type: str
    source_certainty: str
    source_from_nucleus_id: str
    source_to_nucleus_id: str
    source_relation_ids: tuple[str, ...]
    source_meaning_arc_keys: tuple[str, ...]
    from_source_owner_id: str
    to_source_owner_id: str
    relation_endpoint_role: str
    source_owner_id: str
    source_owner_ordinal: int
    source_owner_ordinal_token: str
    opposite_source_owner_id: str
    opposite_source_owner_ordinal: int
    relation_direction: str
    source_grounding_kind: str
    source_retention: str
    experiment_retention: str
    evidence_alias_ids: tuple[str, ...]
    marker_code: str | None
    marker_policy_version: str | None
    marker_policy_sha256: str | None
    marker_source_span_id: str | None
    marker_start_index: int | None
    marker_end_index: int | None
    relation_surface_key: str
    relation_surface_token: str
    atom_code: str
    required: bool
    semantic_coverage_authority: str = "none"


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec:
    lexical_atom_id: str
    source_semantic_link_id: str
    source_span_id: str
    connective_code: str
    relation_type: str
    direction: str
    from_semantic_unit_id: str
    from_owner_ordinal: int
    to_semantic_unit_id: str
    to_owner_ordinal: int
    semantic_link_surface_key: str
    semantic_link_surface_token: str
    atom_code: str
    required: bool
    semantic_coverage_authority: str = "none"


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec:
    lexical_atom_id: str
    source_unknown_id: str
    dimension: str
    source_span_id: str
    affected_source_owners: tuple[tuple[str, str, int], ...]
    lexical_role_kind: str
    unknown_surface_token: str
    atom_code: str
    required: bool
    semantic_coverage_authority: str = "none"


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentLexicalAtomSpecs:
    schema_version: str
    source_experiment_snapshot_sha256: str
    source_relation_construction_authority_sha256: str
    source_lexical_role_witness_sha256: str
    surface_catalog_sha256: str
    owner_bindings: tuple[Step11Rc0028ExperimentOwnerBinding, ...]
    construction_instances: tuple[
        Step11Rc0028ExperimentConstructionInstanceBinding, ...
    ]
    construction_interval_bindings: tuple[
        Step11Rc0028ExperimentConstructionIntervalBinding, ...
    ]
    participation_bindings: tuple[
        Step11Rc0028ExperimentParticipationBinding, ...
    ]
    construction_atoms: tuple[
        Step11Rc0028ExperimentConstructionLexicalAtomSpec, ...
    ]
    relation_endpoint_atoms: tuple[
        Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec, ...
    ]
    semantic_link_atoms: tuple[
        Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec, ...
    ]
    explicit_unknown_atoms: tuple[
        Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec, ...
    ]
    visible_lexical_atom_count: int
    total_matchable_atom_count: int
    max_visible_lexical_atoms: int
    max_total_matchable_atoms: int
    semantic_coverage_authority: str
    specs_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False


def _step11_rc0028_owner_binding_material(
    value: Step11Rc0028ExperimentOwnerBinding,
) -> dict[str, Any]:
    return {
        "source_owner_id": value.source_owner_id,
        "source_owner_kind": value.source_owner_kind,
        "owner_ordinal": value.owner_ordinal,
        "owner_ordinal_token": value.owner_ordinal_token,
    }


def _step11_rc0028_participation_material(
    value: Step11Rc0028ExperimentParticipationBinding,
) -> dict[str, Any]:
    return {
        "participation_id": value.participation_id,
        "parent_nucleus_id": value.parent_nucleus_id,
        "construction_slot_id": value.construction_slot_id,
        "target_owner_kind": value.target_owner_kind,
        "target_owner_id": value.target_owner_id,
        "target_owner_ordinal": value.target_owner_ordinal,
        "target_owner_ordinal_token": value.target_owner_ordinal_token,
        "owner_resolution": value.owner_resolution,
        "source_span_id": value.source_span_id,
        "intersection_start_index": value.intersection_start_index,
        "intersection_end_index": value.intersection_end_index,
        "semantic_equivalence_authorized": (
            value.semantic_equivalence_authorized
        ),
    }


def _step11_rc0028_instance_material(
    value: Step11Rc0028ExperimentConstructionInstanceBinding,
) -> dict[str, Any]:
    return {
        "construction_instance_id": value.construction_instance_id,
        "parent_nucleus_id": value.parent_nucleus_id,
        "construction_code": value.construction_code,
        "construction_atom_code": value.construction_atom_code,
        "construction_surface_token": value.construction_surface_token,
        "source_field": value.source_field,
        "source_field_role": value.source_field_role,
        "source_span_id": value.source_span_id,
        "evidence_alias_ids": list(value.evidence_alias_ids),
        "instance_start_index": value.instance_start_index,
        "instance_end_index": value.instance_end_index,
        "slot_ids": list(value.slot_ids),
        "participation_ids": list(value.participation_ids),
    }


def _step11_rc0028_interval_material(
    value: Step11Rc0028ExperimentConstructionIntervalBinding,
) -> dict[str, Any]:
    return {
        "left_construction_instance_id": (
            value.left_construction_instance_id
        ),
        "right_construction_instance_id": (
            value.right_construction_instance_id
        ),
        "range_relation": value.range_relation,
    }


def _step11_rc0028_construction_atom_material(
    value: Step11Rc0028ExperimentConstructionLexicalAtomSpec,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    material = {
        "facet_id": value.facet_id,
        "construction_slot_id": value.construction_slot_id,
        "construction_instance_id": value.construction_instance_id,
        "parent_nucleus_id": value.parent_nucleus_id,
        "source_span_id": value.source_span_id,
        "source_field": value.source_field,
        "source_field_role": value.source_field_role,
        "evidence_alias_ids": list(value.evidence_alias_ids),
        "slot_start_index": value.slot_start_index,
        "slot_end_index": value.slot_end_index,
        "lexical_role_kind": value.lexical_role_kind,
        "construction_code": value.construction_code,
        "construction_position": value.construction_position,
        "lexical_internal_link": value.lexical_internal_link,
        "construction_atom_code": value.construction_atom_code,
        "construction_surface_token": value.construction_surface_token,
        "role_position_atom_code": value.role_position_atom_code,
        "role_position_surface_token": value.role_position_surface_token,
        "participation_ids": list(value.participation_ids),
        "target_owner_ordinals": list(value.target_owner_ordinals),
        "visible_authority": value.visible_authority,
        "required": value.required,
        "semantic_coverage_authority": value.semantic_coverage_authority,
    }
    return (
        {"lexical_atom_id": value.lexical_atom_id, **material}
        if include_id
        else material
    )


def _step11_rc0028_relation_atom_material(
    value: Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    material = {
        "experiment_relation_id": value.experiment_relation_id,
        "source_relation_id": value.source_relation_id,
        "refines_source_relation_id": value.refines_source_relation_id,
        "authority_basis": value.authority_basis,
        "source_relation_type": value.source_relation_type,
        "effective_relation_type": value.effective_relation_type,
        "source_certainty": value.source_certainty,
        "source_from_nucleus_id": value.source_from_nucleus_id,
        "source_to_nucleus_id": value.source_to_nucleus_id,
        "source_relation_ids": list(value.source_relation_ids),
        "source_meaning_arc_keys": list(value.source_meaning_arc_keys),
        "from_source_owner_id": value.from_source_owner_id,
        "to_source_owner_id": value.to_source_owner_id,
        "relation_endpoint_role": value.relation_endpoint_role,
        "source_owner_id": value.source_owner_id,
        "source_owner_ordinal": value.source_owner_ordinal,
        "source_owner_ordinal_token": value.source_owner_ordinal_token,
        "opposite_source_owner_id": value.opposite_source_owner_id,
        "opposite_source_owner_ordinal": value.opposite_source_owner_ordinal,
        "relation_direction": value.relation_direction,
        "source_grounding_kind": value.source_grounding_kind,
        "source_retention": value.source_retention,
        "experiment_retention": value.experiment_retention,
        "evidence_alias_ids": list(value.evidence_alias_ids),
        "marker_code": value.marker_code,
        "marker_policy_version": value.marker_policy_version,
        "marker_policy_sha256": value.marker_policy_sha256,
        "marker_source_span_id": value.marker_source_span_id,
        "marker_start_index": value.marker_start_index,
        "marker_end_index": value.marker_end_index,
        "relation_surface_key": value.relation_surface_key,
        "relation_surface_token": value.relation_surface_token,
        "atom_code": value.atom_code,
        "required": value.required,
        "semantic_coverage_authority": value.semantic_coverage_authority,
    }
    return (
        {"lexical_atom_id": value.lexical_atom_id, **material}
        if include_id
        else material
    )


def _step11_rc0028_semantic_link_atom_material(
    value: Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    material = {
        "source_semantic_link_id": value.source_semantic_link_id,
        "source_span_id": value.source_span_id,
        "connective_code": value.connective_code,
        "relation_type": value.relation_type,
        "direction": value.direction,
        "from_semantic_unit_id": value.from_semantic_unit_id,
        "from_owner_ordinal": value.from_owner_ordinal,
        "to_semantic_unit_id": value.to_semantic_unit_id,
        "to_owner_ordinal": value.to_owner_ordinal,
        "semantic_link_surface_key": value.semantic_link_surface_key,
        "semantic_link_surface_token": value.semantic_link_surface_token,
        "atom_code": value.atom_code,
        "required": value.required,
        "semantic_coverage_authority": value.semantic_coverage_authority,
    }
    return (
        {"lexical_atom_id": value.lexical_atom_id, **material}
        if include_id
        else material
    )


def _step11_rc0028_unknown_atom_material(
    value: Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    material = {
        "source_unknown_id": value.source_unknown_id,
        "dimension": value.dimension,
        "source_span_id": value.source_span_id,
        "affected_source_owners": [
            [owner_kind, owner_id, ordinal]
            for owner_kind, owner_id, ordinal in value.affected_source_owners
        ],
        "lexical_role_kind": value.lexical_role_kind,
        "unknown_surface_token": value.unknown_surface_token,
        "atom_code": value.atom_code,
        "required": value.required,
        "semantic_coverage_authority": value.semantic_coverage_authority,
    }
    return (
        {"lexical_atom_id": value.lexical_atom_id, **material}
        if include_id
        else material
    )


def _step11_rc0028_lexical_specs_payload(
    value: Step11Rc0028ExperimentLexicalAtomSpecs,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "source_experiment_snapshot_sha256": (
            value.source_experiment_snapshot_sha256
        ),
        "source_relation_construction_authority_sha256": (
            value.source_relation_construction_authority_sha256
        ),
        "source_lexical_role_witness_sha256": (
            value.source_lexical_role_witness_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "owner_bindings": [
            _step11_rc0028_owner_binding_material(row)
            for row in value.owner_bindings
        ],
        "construction_instances": [
            _step11_rc0028_instance_material(row)
            for row in value.construction_instances
        ],
        "construction_interval_bindings": [
            _step11_rc0028_interval_material(row)
            for row in value.construction_interval_bindings
        ],
        "participation_bindings": [
            _step11_rc0028_participation_material(row)
            for row in value.participation_bindings
        ],
        "construction_atoms": [
            _step11_rc0028_construction_atom_material(row)
            for row in value.construction_atoms
        ],
        "relation_endpoint_atoms": [
            _step11_rc0028_relation_atom_material(row)
            for row in value.relation_endpoint_atoms
        ],
        "semantic_link_atoms": [
            _step11_rc0028_semantic_link_atom_material(row)
            for row in value.semantic_link_atoms
        ],
        "explicit_unknown_atoms": [
            _step11_rc0028_unknown_atom_material(row)
            for row in value.explicit_unknown_atoms
        ],
        "visible_lexical_atom_count": value.visible_lexical_atom_count,
        "total_matchable_atom_count": value.total_matchable_atom_count,
        "max_visible_lexical_atoms": value.max_visible_lexical_atoms,
        "max_total_matchable_atoms": value.max_total_matchable_atoms,
        "semantic_coverage_authority": value.semantic_coverage_authority,
        "experimental_only": value.experimental_only,
        "body_free": value.body_free,
        "runtime_connected": value.runtime_connected,
    }


def _step11_rc0028_atom_id(prefix: str, material: Mapping[str, Any]) -> str:
    return prefix + artifact_sha256(dict(material))[:24]


def _step11_rc0028_owner_bindings(
    snapshot: Any,
    catalog: Mapping[str, Any],
) -> tuple[Step11Rc0028ExperimentOwnerBinding, ...]:
    authority = snapshot.relation_construction_authority
    witness = snapshot.lexical_role_witness
    kind_by_id: dict[str, str] = {}

    def bind(owner_id: Any, owner_kind: str) -> None:
        if type(owner_id) is not str or not owner_id:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_SOURCE_OWNER_INVALID"
            )
        existing = kind_by_id.get(owner_id)
        if existing is not None and existing != owner_kind:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_SOURCE_OWNER_KIND_MISMATCH"
            )
        kind_by_id[owner_id] = owner_kind

    # Bind the successor's explicit owner kinds first.  A frozen inventory
    # nucleus can carry a semantic-unit ``actual_source_id``; treating every
    # such identity as kind ``nucleus`` would erase that upstream distinction.
    for row in authority.source_owner_participations:
        bind(row.parent_nucleus_id, "nucleus")
        bind(row.target_owner_id, row.target_owner_kind)
    for row in witness.relation_endpoint_bindings:
        bind(row.source_owner_id, "nucleus")
    for row in authority.semantic_link_bindings:
        bind(row.from_semantic_unit_id, "semantic_unit")
        bind(row.to_semantic_unit_id, "semantic_unit")
    for row in authority.explicit_unknown_authorities:
        for owner in row.affected_source_owners:
            bind(owner.owner_id, owner.owner_kind)

    nucleus_order: list[str] = []
    for row in snapshot.base_snapshot.nuclei:
        owner_id = str(row.actual_source_id)
        bind(owner_id, kind_by_id.get(owner_id, "nucleus"))
        if owner_id not in nucleus_order:
            nucleus_order.append(owner_id)

    semantic_unit_order = tuple(
        dict.fromkeys(
            row.target_owner_id
            for row in sorted(
                authority.source_owner_participations,
                key=lambda item: (
                    item.source_span_id,
                    item.intersection_start_index,
                    item.intersection_end_index,
                    item.target_owner_id,
                ),
            )
            if row.target_owner_kind == "semantic_unit"
        )
    )
    ordered = tuple(
        dict.fromkeys(
            (
                *nucleus_order,
                *semantic_unit_order,
                *sorted(kind_by_id),
            )
        )
    )
    if len(ordered) > _STEP11_RC0028_OWNER_ORDINAL_MAX:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED"
        )
    ordinal_tokens = catalog["owner_ordinal_tokens"]
    return tuple(
        Step11Rc0028ExperimentOwnerBinding(
            source_owner_id=owner_id,
            source_owner_kind=kind_by_id[owner_id],
            owner_ordinal=ordinal,
            owner_ordinal_token=str(ordinal_tokens[str(ordinal)]),
        )
        for ordinal, owner_id in enumerate(ordered, start=1)
    )


def _build_step11_rc0028_experiment_lexical_atom_specs(
    successor_snapshot: Any,
    *,
    validate_output: bool,
) -> Step11Rc0028ExperimentLexicalAtomSpecs:
    # Dynamic local load preserves both the rc0027 import graph and the
    # accepted E1b predecessor's frozen reverse-import audit.
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    GroundedLexicalRoleExperimentSnapshotSuccessor = (
        successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    )
    validate_grounded_lexical_role_experiment_snapshot_successor = (
        successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor
    )
    from emlis_ai_step11_rc0028_experiment_surface_catalog_v3 import (
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256,
        validate_step11_rc0028_experiment_surface_catalog,
    )

    if type(successor_snapshot) is not GroundedLexicalRoleExperimentSnapshotSuccessor:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_SUCCESSOR_SNAPSHOT_INVALID"
        )
    if validate_grounded_lexical_role_experiment_snapshot_successor(
        successor_snapshot
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_SUCCESSOR_SNAPSHOT_INVALID"
        )
    catalog_issues = validate_step11_rc0028_experiment_surface_catalog(
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
    )
    if catalog_issues:
        raise Step11GroundedLexicalizationError(catalog_issues[0])
    if (
        successor_snapshot.semantic_coverage_authorized is not False
        or successor_snapshot.lexical_role_witness.semantic_coverage_authority
        != "none"
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM"
        )

    catalog = STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    owner_bindings = _step11_rc0028_owner_bindings(
        successor_snapshot, catalog
    )
    owner_by_id = {row.source_owner_id: row for row in owner_bindings}
    instance_by_id = {
        row.construction_instance_id: row
        for row in authority.construction_instances
    }
    slot_by_id = {
        row.construction_slot_id: row for row in authority.construction_slots
    }
    participation_by_id = {
        row.participation_id: row
        for row in authority.source_owner_participations
    }
    relation_by_id = {
        row.experiment_relation_id: row for row in authority.relation_authorities
    }
    if (
        len(instance_by_id) != len(authority.construction_instances)
        or len(slot_by_id) != len(authority.construction_slots)
        or len(participation_by_id)
        != len(authority.source_owner_participations)
        or len(relation_by_id) != len(authority.relation_authorities)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_SOURCE_ID_DUPLICATE"
        )

    construction_instances = tuple(
        Step11Rc0028ExperimentConstructionInstanceBinding(
            construction_instance_id=row.construction_instance_id,
            parent_nucleus_id=row.parent_nucleus_id,
            construction_code=row.construction_code,
            construction_atom_code=catalog["construction_atom_codes"][
                row.construction_code
            ],
            construction_surface_token=catalog[
                "construction_surface_tokens"
            ][row.construction_code],
            source_field=row.source_field,
            source_field_role=row.source_field_role,
            source_span_id=row.source_span_id,
            evidence_alias_ids=tuple(row.evidence_alias_ids),
            instance_start_index=row.instance_start_index,
            instance_end_index=row.instance_end_index,
            slot_ids=tuple(row.slot_ids),
            participation_ids=tuple(row.participation_ids),
        )
        for row in authority.construction_instances
    )
    construction_interval_bindings = tuple(
        Step11Rc0028ExperimentConstructionIntervalBinding(
            left_construction_instance_id=(
                row.left_construction_instance_id
            ),
            right_construction_instance_id=(
                row.right_construction_instance_id
            ),
            range_relation=row.range_relation,
        )
        for row in authority.interval_edges
    )
    participation_bindings = tuple(
        Step11Rc0028ExperimentParticipationBinding(
            participation_id=row.participation_id,
            parent_nucleus_id=row.parent_nucleus_id,
            construction_slot_id=row.construction_slot_id,
            target_owner_kind=row.target_owner_kind,
            target_owner_id=row.target_owner_id,
            target_owner_ordinal=owner_by_id[row.target_owner_id].owner_ordinal,
            target_owner_ordinal_token=(
                owner_by_id[row.target_owner_id].owner_ordinal_token
            ),
            owner_resolution=row.owner_resolution,
            source_span_id=row.source_span_id,
            intersection_start_index=row.intersection_start_index,
            intersection_end_index=row.intersection_end_index,
            semantic_equivalence_authorized=(
                row.semantic_equivalence_authorized
            ),
        )
        for row in authority.source_owner_participations
    )

    construction_atoms: list[
        Step11Rc0028ExperimentConstructionLexicalAtomSpec
    ] = []
    for facet in witness.facets:
        instance = instance_by_id.get(facet.source_owner_id)
        slot = slot_by_id.get(facet.construction_slot_id)
        if (
            instance is None
            or slot is None
            or slot.construction_instance_id != instance.construction_instance_id
            or facet.parent_nucleus_id != instance.parent_nucleus_id
            or facet.construction_code != instance.construction_code
            or tuple(facet.participation_ids) != tuple(slot.participation_ids)
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_CONSTRUCTION_BINDING_MISMATCH"
            )
        role_key = (
            facet.lexical_role_kind + ":" + facet.construction_position
        )
        if role_key not in catalog["role_position_atom_codes"]:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_ROLE_POSITION_UNSUPPORTED"
            )
        target_ordinals = tuple(
            owner_by_id[participation_by_id[participation_id].target_owner_id]
            .owner_ordinal
            for participation_id in facet.participation_ids
        )
        provisional = Step11Rc0028ExperimentConstructionLexicalAtomSpec(
            lexical_atom_id="",
            facet_id=facet.facet_id,
            construction_slot_id=facet.construction_slot_id,
            construction_instance_id=facet.source_owner_id,
            parent_nucleus_id=facet.parent_nucleus_id,
            source_span_id=facet.source_span_id,
            source_field=slot.source_field,
            source_field_role=facet.source_field_role,
            evidence_alias_ids=tuple(slot.evidence_alias_ids),
            slot_start_index=slot.slot_start_index,
            slot_end_index=slot.slot_end_index,
            lexical_role_kind=facet.lexical_role_kind,
            construction_code=facet.construction_code,
            construction_position=facet.construction_position,
            lexical_internal_link=facet.lexical_internal_link,
            construction_atom_code=catalog["construction_atom_codes"][
                facet.construction_code
            ],
            construction_surface_token=catalog[
                "construction_surface_tokens"
            ][facet.construction_code],
            role_position_atom_code=catalog["role_position_atom_codes"][
                role_key
            ],
            role_position_surface_token=catalog[
                "role_position_surface_tokens"
            ][role_key],
            participation_ids=tuple(facet.participation_ids),
            target_owner_ordinals=target_ordinals,
            visible_authority=facet.visible_authority,
            required=facet.required,
        )
        construction_atoms.append(
            Step11Rc0028ExperimentConstructionLexicalAtomSpec(
                **{
                    **_step11_rc0028_construction_atom_material(
                        provisional, include_id=False
                    ),
                    "lexical_atom_id": _step11_rc0028_atom_id(
                        "rc0028lex:construction:",
                        _step11_rc0028_construction_atom_material(
                            provisional, include_id=False
                        ),
                    ),
                    "participation_ids": provisional.participation_ids,
                    "evidence_alias_ids": provisional.evidence_alias_ids,
                    "target_owner_ordinals": (
                        provisional.target_owner_ordinals
                    ),
                }
            )
        )

    relation_endpoint_atoms: list[
        Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec
    ] = []
    for endpoint in witness.relation_endpoint_bindings:
        relation = relation_by_id.get(endpoint.relation_id)
        if relation is None:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_RELATION_BINDING_MISMATCH"
            )
        expected_owner = (
            relation.from_source_owner_id
            if endpoint.relation_endpoint_role == "from"
            else relation.to_source_owner_id
        )
        opposite_owner = (
            relation.to_source_owner_id
            if endpoint.relation_endpoint_role == "from"
            else relation.from_source_owner_id
        )
        if (
            endpoint.source_owner_id != expected_owner
            or endpoint.source_relation_id != relation.source_relation_id
            or endpoint.relation_direction != relation.direction
            or endpoint.effective_relation_type
            != relation.effective_relation_type
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_RELATION_BINDING_MISMATCH"
            )
        surface_key = (
            relation.effective_relation_type + ":" + relation.direction
        )
        if surface_key not in catalog["relation_surface_tokens"]:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_RELATION_TYPE_UNSUPPORTED"
            )
        provisional = Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec(
            lexical_atom_id="",
            experiment_relation_id=relation.experiment_relation_id,
            source_relation_id=relation.source_relation_id,
            refines_source_relation_id=relation.refines_source_relation_id,
            authority_basis=relation.authority_basis,
            source_relation_type=relation.source_relation_type,
            effective_relation_type=relation.effective_relation_type,
            source_certainty=format(relation.source_certainty, ".17g"),
            source_from_nucleus_id=relation.source_from_nucleus_id,
            source_to_nucleus_id=relation.source_to_nucleus_id,
            source_relation_ids=tuple(relation.source_relation_ids),
            source_meaning_arc_keys=tuple(
                relation.source_meaning_arc_keys
            ),
            from_source_owner_id=relation.from_source_owner_id,
            to_source_owner_id=relation.to_source_owner_id,
            relation_endpoint_role=endpoint.relation_endpoint_role,
            source_owner_id=endpoint.source_owner_id,
            source_owner_ordinal=owner_by_id[
                endpoint.source_owner_id
            ].owner_ordinal,
            source_owner_ordinal_token=owner_by_id[
                endpoint.source_owner_id
            ].owner_ordinal_token,
            opposite_source_owner_id=opposite_owner,
            opposite_source_owner_ordinal=owner_by_id[
                opposite_owner
            ].owner_ordinal,
            relation_direction=relation.direction,
            source_grounding_kind=relation.source_grounding_kind,
            source_retention=relation.source_retention,
            experiment_retention=relation.experiment_retention,
            evidence_alias_ids=tuple(relation.evidence_alias_ids),
            marker_code=relation.marker_code,
            marker_policy_version=relation.marker_policy_version,
            marker_policy_sha256=relation.marker_policy_sha256,
            marker_source_span_id=relation.marker_source_span_id,
            marker_start_index=relation.marker_start_index,
            marker_end_index=relation.marker_end_index,
            relation_surface_key=surface_key,
            relation_surface_token=catalog["relation_surface_tokens"][
                surface_key
            ],
            atom_code=(
                "relation_"
                + relation.effective_relation_type
                + "_"
                + relation.direction
                + "_"
                + endpoint.relation_endpoint_role
            ),
            required=endpoint.required,
        )
        material = _step11_rc0028_relation_atom_material(
            provisional, include_id=False
        )
        relation_endpoint_atoms.append(
            Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec(
                **{
                    **material,
                    "lexical_atom_id": _step11_rc0028_atom_id(
                        "rc0028lex:relation:", material
                    ),
                    "evidence_alias_ids": provisional.evidence_alias_ids,
                    "source_relation_ids": provisional.source_relation_ids,
                    "source_meaning_arc_keys": (
                        provisional.source_meaning_arc_keys
                    ),
                }
            )
        )

    semantic_link_atoms: list[
        Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec
    ] = []
    for link in authority.semantic_link_bindings:
        surface_key = link.relation_type + ":" + link.direction
        if surface_key not in catalog["semantic_link_surface_tokens"]:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_SEMANTIC_LINK_TYPE_UNSUPPORTED"
            )
        provisional = Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec(
            lexical_atom_id="",
            source_semantic_link_id=link.source_semantic_link_id,
            source_span_id=link.source_span_id,
            connective_code=link.connective_code,
            relation_type=link.relation_type,
            direction=link.direction,
            from_semantic_unit_id=link.from_semantic_unit_id,
            from_owner_ordinal=owner_by_id[
                link.from_semantic_unit_id
            ].owner_ordinal,
            to_semantic_unit_id=link.to_semantic_unit_id,
            to_owner_ordinal=owner_by_id[
                link.to_semantic_unit_id
            ].owner_ordinal,
            semantic_link_surface_key=surface_key,
            semantic_link_surface_token=catalog[
                "semantic_link_surface_tokens"
            ][surface_key],
            atom_code=(
                "semantic_link_"
                + link.relation_type
                + "_"
                + link.direction
            ),
            required=link.required,
        )
        material = _step11_rc0028_semantic_link_atom_material(
            provisional, include_id=False
        )
        semantic_link_atoms.append(
            Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec(
                **{
                    **material,
                    "lexical_atom_id": _step11_rc0028_atom_id(
                        "rc0028lex:link:", material
                    ),
                }
            )
        )

    explicit_unknown_atoms: list[
        Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec
    ] = []
    for unknown in authority.explicit_unknown_authorities:
        if unknown.dimension not in catalog["unknown_surface_tokens"]:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_DIMENSION_UNSUPPORTED"
            )
        affected = tuple(
            (
                owner.owner_kind,
                owner.owner_id,
                owner_by_id[owner.owner_id].owner_ordinal,
            )
            for owner in unknown.affected_source_owners
        )
        provisional = Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec(
            lexical_atom_id="",
            source_unknown_id=unknown.source_unknown_id,
            dimension=unknown.dimension,
            source_span_id=unknown.source_span_id,
            affected_source_owners=affected,
            lexical_role_kind=unknown.lexical_role_kind,
            unknown_surface_token=catalog["unknown_surface_tokens"][
                unknown.dimension
            ],
            atom_code="unknown_" + unknown.dimension,
            required=unknown.required,
        )
        material = _step11_rc0028_unknown_atom_material(
            provisional, include_id=False
        )
        explicit_unknown_atoms.append(
            Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec(
                **{
                    **material,
                    "lexical_atom_id": _step11_rc0028_atom_id(
                        "rc0028lex:unknown:", material
                    ),
                    "affected_source_owners": (
                        provisional.affected_source_owners
                    ),
                }
            )
        )

    visible_count = len(construction_atoms)
    total_count = (
        visible_count
        + len(relation_endpoint_atoms)
        + len(semantic_link_atoms)
        + len(explicit_unknown_atoms)
    )
    max_visible = authority.resource_bounds.max_lexical_construction_slots
    max_total = (
        max_visible
        + 2 * authority.resource_bounds.exact_effective_relations
        + authority.resource_bounds.exact_semantic_links
        + authority.resource_bounds.exact_explicit_unknowns
    )
    if visible_count > max_visible or total_count > max_total:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED"
        )
    provisional_specs = Step11Rc0028ExperimentLexicalAtomSpecs(
        schema_version=STEP11_RC0028_EXPERIMENT_LEXICAL_ATOM_SPECS_SCHEMA,
        source_experiment_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        source_relation_construction_authority_sha256=(
            successor_snapshot.source_relation_construction_authority_sha256
        ),
        source_lexical_role_witness_sha256=(
            successor_snapshot.source_lexical_role_witness_sha256
        ),
        surface_catalog_sha256=(
            STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256
        ),
        owner_bindings=owner_bindings,
        construction_instances=construction_instances,
        construction_interval_bindings=construction_interval_bindings,
        participation_bindings=participation_bindings,
        construction_atoms=tuple(construction_atoms),
        relation_endpoint_atoms=tuple(relation_endpoint_atoms),
        semantic_link_atoms=tuple(semantic_link_atoms),
        explicit_unknown_atoms=tuple(explicit_unknown_atoms),
        visible_lexical_atom_count=visible_count,
        total_matchable_atom_count=total_count,
        max_visible_lexical_atoms=max_visible,
        max_total_matchable_atoms=max_total,
        semantic_coverage_authority="none",
        specs_sha256="0" * 64,
    )
    result = Step11Rc0028ExperimentLexicalAtomSpecs(
        **{
            **_step11_rc0028_lexical_specs_payload(provisional_specs),
            "owner_bindings": provisional_specs.owner_bindings,
            "construction_instances": provisional_specs.construction_instances,
            "construction_interval_bindings": (
                provisional_specs.construction_interval_bindings
            ),
            "participation_bindings": provisional_specs.participation_bindings,
            "construction_atoms": provisional_specs.construction_atoms,
            "relation_endpoint_atoms": provisional_specs.relation_endpoint_atoms,
            "semantic_link_atoms": provisional_specs.semantic_link_atoms,
            "explicit_unknown_atoms": provisional_specs.explicit_unknown_atoms,
            "specs_sha256": artifact_sha256(
                _step11_rc0028_lexical_specs_payload(provisional_specs)
            ),
        }
    )
    if validate_output:
        issues = validate_step11_rc0028_experiment_lexical_atom_specs(result)
        if issues:
            raise Step11GroundedLexicalizationError(issues[0])
    return result


def build_step11_rc0028_experiment_lexical_atom_specs(
    successor_snapshot: Any,
) -> Step11Rc0028ExperimentLexicalAtomSpecs:
    """Project the validated E1b successor into bounded lexical atoms."""

    return _build_step11_rc0028_experiment_lexical_atom_specs(
        successor_snapshot,
        validate_output=True,
    )


def validate_step11_rc0028_experiment_lexical_atom_specs(
    value: Any,
    *,
    successor_snapshot: Any | None = None,
) -> tuple[str, ...]:
    """Validate closed topology, catalog bindings, counts, and commitments."""

    if type(value) is not Step11Rc0028ExperimentLexicalAtomSpecs:
        return ("STEP11_RC0028_LEXICAL_ATOM_SPECS_TYPE_INVALID",)
    from emlis_ai_step11_rc0028_experiment_surface_catalog_v3 import (
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256,
        STEP11_RC0028_OWNER_ORDINAL_MAX,
        validate_step11_rc0028_experiment_surface_catalog,
    )

    issues: set[str] = set()
    catalog = STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
    if validate_step11_rc0028_experiment_surface_catalog(catalog):
        issues.add("STEP11_RC0028_CATALOG_INVALID")
    if (
        value.schema_version
        != STEP11_RC0028_EXPERIMENT_LEXICAL_ATOM_SPECS_SCHEMA
        or value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
        or value.semantic_coverage_authority != "none"
    ):
        issues.add("STEP11_RC0028_LEXICAL_ATOM_SPECS_CONTRACT_MISMATCH")
    hashes = (
        value.source_experiment_snapshot_sha256,
        value.source_relation_construction_authority_sha256,
        value.source_lexical_role_witness_sha256,
        value.surface_catalog_sha256,
        value.specs_sha256,
    )
    if any(
        type(item) is not str
        or _STEP11_RC0028_SHA256_RE.fullmatch(item) is None
        or item == "0" * 64
        for item in hashes
    ):
        issues.add("STEP11_RC0028_LEXICAL_ATOM_SPECS_HASH_INVALID")
    if value.surface_catalog_sha256 != (
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256
    ):
        issues.add("STEP11_RC0028_CATALOG_COMMITMENT_MISMATCH")

    owner_ids = tuple(row.source_owner_id for row in value.owner_bindings)
    owner_ordinals = tuple(row.owner_ordinal for row in value.owner_bindings)
    owner_by_id = {row.source_owner_id: row for row in value.owner_bindings}
    if (
        len(owner_by_id) != len(value.owner_bindings)
        or owner_ordinals != tuple(range(1, len(value.owner_bindings) + 1))
        or len(owner_ordinals) > STEP11_RC0028_OWNER_ORDINAL_MAX
        or any(
            row.source_owner_kind not in {"nucleus", "semantic_unit"}
            or row.owner_ordinal_token
            != catalog["owner_ordinal_tokens"].get(str(row.owner_ordinal))
            for row in value.owner_bindings
        )
    ):
        issues.add("STEP11_RC0028_OWNER_BINDING_MISMATCH")

    instance_by_id = {
        row.construction_instance_id: row
        for row in value.construction_instances
    }
    participation_by_id = {
        row.participation_id: row for row in value.participation_bindings
    }
    construction_by_slot = {
        row.construction_slot_id: row for row in value.construction_atoms
    }
    if (
        len(instance_by_id) != len(value.construction_instances)
        or len(participation_by_id) != len(value.participation_bindings)
        or len(construction_by_slot) != len(value.construction_atoms)
    ):
        issues.add("STEP11_RC0028_LEXICAL_ATOM_ID_DUPLICATE")
    all_instance_ids = set(instance_by_id)
    all_slot_ids = set(construction_by_slot)
    all_participation_ids = set(participation_by_id)
    if any(
        row.construction_atom_code
        != catalog["construction_atom_codes"].get(row.construction_code)
        or row.construction_surface_token
        != catalog["construction_surface_tokens"].get(row.construction_code)
        or not set(row.slot_ids) <= all_slot_ids
        or not set(row.participation_ids) <= all_participation_ids
        or row.instance_start_index < 0
        or row.instance_end_index <= row.instance_start_index
        for row in value.construction_instances
    ):
        issues.add("STEP11_RC0028_CONSTRUCTION_INSTANCE_BINDING_MISMATCH")
    if any(
        row.left_construction_instance_id not in all_instance_ids
        or row.right_construction_instance_id not in all_instance_ids
        or row.range_relation
        not in {
            "disjoint",
            "contains",
            "contained_by",
            "partial_overlap",
            "coextensive",
        }
        for row in value.construction_interval_bindings
    ):
        issues.add("STEP11_RC0028_CONSTRUCTION_OVERLAP_BINDING_MISMATCH")
    if any(
        row.construction_slot_id not in all_slot_ids
        or row.target_owner_id not in owner_by_id
        or owner_by_id[row.target_owner_id].source_owner_kind
        != row.target_owner_kind
        or owner_by_id[row.target_owner_id].owner_ordinal
        != row.target_owner_ordinal
        or owner_by_id[row.target_owner_id].owner_ordinal_token
        != row.target_owner_ordinal_token
        or row.intersection_start_index < 0
        or row.intersection_end_index <= row.intersection_start_index
        or row.semantic_equivalence_authorized is not False
        for row in value.participation_bindings
    ):
        issues.add("STEP11_RC0028_PARTICIPATION_BINDING_MISMATCH")
    if any(
        row.construction_instance_id not in all_instance_ids
        or row.parent_nucleus_id not in owner_by_id
        or row.slot_start_index < 0
        or row.slot_end_index <= row.slot_start_index
        or row.construction_atom_code
        != catalog["construction_atom_codes"].get(row.construction_code)
        or row.construction_surface_token
        != catalog["construction_surface_tokens"].get(row.construction_code)
        or row.role_position_atom_code
        != catalog["role_position_atom_codes"].get(
            row.lexical_role_kind + ":" + row.construction_position
        )
        or row.role_position_surface_token
        != catalog["role_position_surface_tokens"].get(
            row.lexical_role_kind + ":" + row.construction_position
        )
        or not set(row.participation_ids) <= all_participation_ids
        or row.semantic_coverage_authority != "none"
        or row.lexical_atom_id
        != _step11_rc0028_atom_id(
            "rc0028lex:construction:",
            _step11_rc0028_construction_atom_material(
                row, include_id=False
            ),
        )
        for row in value.construction_atoms
    ):
        issues.add("STEP11_RC0028_CONSTRUCTION_ATOM_BINDING_MISMATCH")

    relation_ids: dict[str, set[str]] = {}
    if any(
        row.source_owner_id not in owner_by_id
        or row.opposite_source_owner_id not in owner_by_id
        or row.source_owner_ordinal
        != owner_by_id[row.source_owner_id].owner_ordinal
        or row.source_owner_ordinal_token
        != owner_by_id[row.source_owner_id].owner_ordinal_token
        or row.opposite_source_owner_ordinal
        != owner_by_id[row.opposite_source_owner_id].owner_ordinal
        or row.relation_endpoint_role not in {"from", "to"}
        or row.relation_surface_key
        != row.effective_relation_type + ":" + row.relation_direction
        or row.relation_surface_token
        != catalog["relation_surface_tokens"].get(row.relation_surface_key)
        or row.semantic_coverage_authority != "none"
        or row.lexical_atom_id
        != _step11_rc0028_atom_id(
            "rc0028lex:relation:",
            _step11_rc0028_relation_atom_material(row, include_id=False),
        )
        for row in value.relation_endpoint_atoms
    ):
        issues.add("STEP11_RC0028_RELATION_ENDPOINT_BINDING_MISMATCH")
    for row in value.relation_endpoint_atoms:
        relation_ids.setdefault(row.experiment_relation_id, set()).add(
            row.relation_endpoint_role
        )
    if any(roles != {"from", "to"} for roles in relation_ids.values()):
        issues.add("STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH")

    if any(
        row.from_semantic_unit_id not in owner_by_id
        or row.to_semantic_unit_id not in owner_by_id
        or row.from_owner_ordinal
        != owner_by_id[row.from_semantic_unit_id].owner_ordinal
        or row.to_owner_ordinal
        != owner_by_id[row.to_semantic_unit_id].owner_ordinal
        or row.semantic_link_surface_key
        != row.relation_type + ":" + row.direction
        or row.semantic_link_surface_token
        != catalog["semantic_link_surface_tokens"].get(
            row.semantic_link_surface_key
        )
        or row.semantic_coverage_authority != "none"
        or row.lexical_atom_id
        != _step11_rc0028_atom_id(
            "rc0028lex:link:",
            _step11_rc0028_semantic_link_atom_material(
                row, include_id=False
            ),
        )
        for row in value.semantic_link_atoms
    ):
        issues.add("STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH")
    if any(
        not row.affected_source_owners
        or any(owner_id not in owner_by_id for _kind, owner_id, _ord in row.affected_source_owners)
        or any(
            owner_by_id[owner_id].source_owner_kind != owner_kind
            or owner_by_id[owner_id].owner_ordinal != ordinal
            for owner_kind, owner_id, ordinal in row.affected_source_owners
        )
        or row.unknown_surface_token
        != catalog["unknown_surface_tokens"].get(row.dimension)
        or row.semantic_coverage_authority != "none"
        or row.lexical_atom_id
        != _step11_rc0028_atom_id(
            "rc0028lex:unknown:",
            _step11_rc0028_unknown_atom_material(row, include_id=False),
        )
        for row in value.explicit_unknown_atoms
    ):
        issues.add("STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH")

    atom_ids = tuple(
        row.lexical_atom_id
        for rows in (
            value.construction_atoms,
            value.relation_endpoint_atoms,
            value.semantic_link_atoms,
            value.explicit_unknown_atoms,
        )
        for row in rows
    )
    expected_total = (
        len(value.construction_atoms)
        + len(value.relation_endpoint_atoms)
        + len(value.semantic_link_atoms)
        + len(value.explicit_unknown_atoms)
    )
    if len(set(atom_ids)) != len(atom_ids):
        issues.add("STEP11_RC0028_LEXICAL_ATOM_ID_DUPLICATE")
    if (
        value.visible_lexical_atom_count != len(value.construction_atoms)
        or value.total_matchable_atom_count != expected_total
        or value.visible_lexical_atom_count > value.max_visible_lexical_atoms
        or value.total_matchable_atom_count > value.max_total_matchable_atoms
        or value.max_total_matchable_atoms < value.max_visible_lexical_atoms
    ):
        issues.add("STEP11_RC0028_RESOURCE_BOUND_EXCEEDED")
    try:
        expected_hash = artifact_sha256(
            _step11_rc0028_lexical_specs_payload(value)
        )
    except (AttributeError, TypeError, ValueError):
        expected_hash = ""
    if value.specs_sha256 != expected_hash:
        issues.add("STEP11_RC0028_LEXICAL_ATOM_SPECS_HASH_MISMATCH")

    if successor_snapshot is not None:
        try:
            expected = _build_step11_rc0028_experiment_lexical_atom_specs(
                successor_snapshot,
                validate_output=False,
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            issues.add("STEP11_RC0028_SUCCESSOR_SNAPSHOT_INVALID")
        else:
            if value != expected:
                issues.add("STEP11_RC0028_SOURCE_BINDING_MISMATCH")
    return tuple(sorted(issues))


def step11_rc0028_experiment_lexical_atom_specs_material(
    value: Step11Rc0028ExperimentLexicalAtomSpecs,
) -> dict[str, Any]:
    issues = validate_step11_rc0028_experiment_lexical_atom_specs(value)
    if issues:
        raise Step11GroundedLexicalizationError(issues[0])
    return {
        **_step11_rc0028_lexical_specs_payload(value),
        "specs_sha256": value.specs_sha256,
    }


__all__ += [
    "STEP11_RC0028_EXPERIMENT_LEXICAL_ATOM_SPECS_SCHEMA",
    "Step11Rc0028ExperimentConstructionInstanceBinding",
    "Step11Rc0028ExperimentConstructionIntervalBinding",
    "Step11Rc0028ExperimentConstructionLexicalAtomSpec",
    "Step11Rc0028ExperimentExplicitUnknownLexicalAtomSpec",
    "Step11Rc0028ExperimentLexicalAtomSpecs",
    "Step11Rc0028ExperimentOwnerBinding",
    "Step11Rc0028ExperimentParticipationBinding",
    "Step11Rc0028ExperimentRelationEndpointLexicalAtomSpec",
    "Step11Rc0028ExperimentSemanticLinkLexicalAtomSpec",
    "build_step11_rc0028_experiment_lexical_atom_specs",
    "step11_rc0028_experiment_lexical_atom_specs_material",
    "validate_step11_rc0028_experiment_lexical_atom_specs",
]


# ---------------------------------------------------------------------------
# rc0029 experiment-only grounded natural handles (append-only)
# ---------------------------------------------------------------------------

STEP11_RC0029_NATURAL_HANDLE_SPECS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0029_natural_handle_specs.v1"
)


@dataclass(frozen=True, slots=True)
class Step11Rc0029NaturalHandleSpec:
    source_owner_id: str
    source_owner_kind: str
    source_owner_ordinal: int
    base_source_nucleus_id: str
    grounded_phrase_id: str
    grounded_phrase_text: str
    semantic_head_kind: str
    semantic_head_text: str
    role_qualifier_tokens: tuple[str, ...]
    handle_text: str
    handle_text_sha256: str


@dataclass(frozen=True, slots=True)
class Step11Rc0029NaturalHandleSpecs:
    schema_version: str
    source_base_candidate_id: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    surface_catalog_sha256: str
    required_source_owner_ids: tuple[str, ...]
    handles: tuple[Step11Rc0029NaturalHandleSpec, ...]
    semantic_coverage_authority: str
    specs_sha256: str
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False


def _step11_rc0029_handle_material(
    value: Step11Rc0029NaturalHandleSpec,
) -> dict[str, Any]:
    return {
        "source_owner_id": value.source_owner_id,
        "source_owner_kind": value.source_owner_kind,
        "source_owner_ordinal": value.source_owner_ordinal,
        "base_source_nucleus_id": value.base_source_nucleus_id,
        "grounded_phrase_id": value.grounded_phrase_id,
        "grounded_phrase_text": value.grounded_phrase_text,
        "semantic_head_kind": value.semantic_head_kind,
        "semantic_head_text": value.semantic_head_text,
        "role_qualifier_tokens": list(value.role_qualifier_tokens),
        "handle_text": value.handle_text,
        "handle_text_sha256": value.handle_text_sha256,
    }


def _step11_rc0029_handles_payload(
    value: Step11Rc0029NaturalHandleSpecs,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_successor_snapshot_sha256": (
            value.source_successor_snapshot_sha256
        ),
        "source_lexical_atom_specs_sha256": (
            value.source_lexical_atom_specs_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "required_source_owner_ids": list(value.required_source_owner_ids),
        "handles": [
            _step11_rc0029_handle_material(row) for row in value.handles
        ],
        "semantic_coverage_authority": value.semantic_coverage_authority,
        "experimental_only": value.experimental_only,
        "private_body_full": value.private_body_full,
        "shareable": value.shareable,
        "runtime_connected": value.runtime_connected,
    }


def _build_step11_rc0029_natural_handle_specs(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    validate_output: bool,
) -> Step11Rc0029NaturalHandleSpecs:
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    surface_owner = __import__(
        "emlis_ai_step11_natural_surface_v3",
        fromlist=("Step11NaturalSurfaceCandidate",),
    )
    catalog_owner = __import__(
        "emlis_ai_step11_rc0029_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "validate_step11_rc0029_experiment_surface_catalog",
        ),
    )
    expected_successor_type = (
        successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    )
    if type(base_candidate) is not surface_owner.Step11NaturalSurfaceCandidate:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_BASE_CANDIDATE_INVALID"
        )
    if (
        base_candidate.candidate_version_id != "nls_v3_rc_0027"
        or type(base_candidate.final_utf8_bytes) is not bytes
        or hashlib.sha256(base_candidate.final_utf8_bytes).hexdigest()
        != base_candidate.rendered_surface.sha256
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_BASE_CANDIDATE_INVALID"
        )
    if type(successor_snapshot) is not expected_successor_type:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_SUCCESSOR_SNAPSHOT_INVALID"
        )
    if successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
        successor_snapshot
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_SUCCESSOR_SNAPSHOT_INVALID"
        )
    lexical_issues = validate_step11_rc0028_experiment_lexical_atom_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    )
    if lexical_issues:
        raise Step11GroundedLexicalizationError(lexical_issues[0])
    catalog = catalog_owner.STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG
    if catalog_owner.validate_step11_rc0029_experiment_surface_catalog(catalog):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_CATALOG_INVALID"
        )

    owner_by_id = {
        row.source_owner_id: row for row in lexical_atom_specs.owner_bindings
    }
    owner_by_ordinal = {
        row.owner_ordinal: row for row in lexical_atom_specs.owner_bindings
    }
    if (
        len(owner_by_id) != len(lexical_atom_specs.owner_bindings)
        or len(owner_by_ordinal) != len(lexical_atom_specs.owner_bindings)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_SOURCE_OWNER_INVALID"
        )
    required: set[str] = set()
    qualifiers: dict[str, set[str]] = {}

    def add(owner_id: str, token: str | None = None) -> None:
        if owner_id not in owner_by_id:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_SOURCE_OWNER_INVALID"
            )
        required.add(owner_id)
        if token:
            qualifiers.setdefault(owner_id, set()).add(token)

    role_tokens = catalog["role_position_surface_tokens"]
    for atom in lexical_atom_specs.construction_atoms:
        token = role_tokens.get(
            atom.lexical_role_kind + ":" + atom.construction_position
        )
        if type(token) is not str or not token:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_CONSTRUCTION_ROLE_INVALID"
            )
        for ordinal in atom.target_owner_ordinals:
            owner = owner_by_ordinal.get(ordinal)
            if owner is None:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0029_SOURCE_OWNER_INVALID"
                )
            add(owner.source_owner_id, token)
    topology_tokens = catalog["owner_role_surface_tokens"]
    for atom in lexical_atom_specs.relation_endpoint_atoms:
        add(
            atom.source_owner_id,
            topology_tokens["relation_" + atom.relation_endpoint_role],
        )
    for atom in lexical_atom_specs.semantic_link_atoms:
        add(atom.from_semantic_unit_id, topology_tokens["semantic_link_from"])
        add(atom.to_semantic_unit_id, topology_tokens["semantic_link_to"])
    for atom in lexical_atom_specs.explicit_unknown_atoms:
        for _kind, owner_id, _ordinal in atom.affected_source_owners:
            add(owner_id, topology_tokens["explicit_unknown"])

    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    nucleus_by_actual = {str(row.actual_source_id): row for row in nuclei}
    nucleus_by_source = {str(row.source_id): row for row in nuclei}
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    if (
        len(nucleus_by_actual) != len(nuclei)
        or len(nucleus_by_source) != len(nuclei)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_BASE_NUCLEUS_INVALID"
        )
    mapped_reception_ids = {
        str(opportunity_id)
        for binding in base_candidate.surface_ast.reception_antecedent_bindings
        for opportunity_id in binding.source_reception_opportunity_ids
    }
    required_reception_opportunities = tuple(
        row
        for row in successor_snapshot.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    for opportunity in required_reception_opportunities:
        target_token = (
            topology_tokens["reception_antecedent"]
            if str(opportunity.source_id) in mapped_reception_ids
            else topology_tokens["reception_target"]
        )
        for source_id in opportunity.target_nucleus_ids:
            actual_id = actual_by_source.get(str(source_id))
            if actual_id is None:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0029_RECEPTION_TARGET_UNRESOLVED"
                )
            add(actual_id, target_token)
        for source_id in opportunity.support_nucleus_ids:
            actual_id = actual_by_source.get(str(source_id))
            if actual_id is None:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0029_RECEPTION_SUPPORT_UNRESOLVED"
                )
            add(actual_id, topology_tokens["reception_support"])
    if not required:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_REQUIRED_OWNER_SET_EMPTY"
        )
    parent_by_semantic: dict[str, set[str]] = {}
    for row in lexical_atom_specs.participation_bindings:
        if row.target_owner_kind == "semantic_unit":
            parent_by_semantic.setdefault(row.target_owner_id, set()).add(
                row.parent_nucleus_id
            )
    phrase_specs = tuple(base_candidate.surface_ast.grounded_phrase_specs)
    base_text = base_candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    prepared: list[
        tuple[Any, str, Any, str, str, str, tuple[str, ...]]
    ] = []
    qualifier_order = tuple(
        dict.fromkeys(
            (
                *catalog["role_position_surface_tokens"].values(),
                *catalog["owner_role_surface_tokens"].values(),
            )
        )
    )
    qualifier_rank = {
        token: index for index, token in enumerate(qualifier_order)
    }
    head_tokens = catalog["owner_kind_surface_tokens"]
    for owner in (
        row
        for row in lexical_atom_specs.owner_bindings
        if row.source_owner_id in required
    ):
        # Direct actual-nucleus ownership always wins.  A construction-only
        # semantic unit may use its one participation parent only when there
        # is no direct actual nucleus for that owner.
        nucleus = nucleus_by_actual.get(owner.source_owner_id)
        if nucleus is None:
            parents = parent_by_semantic.get(owner.source_owner_id, set())
            if len(parents) != 1:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0029_HANDLE_OWNER_AMBIGUOUS"
                )
            parent_id = next(iter(parents))
            nucleus = nucleus_by_actual.get(parent_id)
            if nucleus is None:
                nucleus = nucleus_by_source.get(parent_id)
        if nucleus is None:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_HANDLE_OWNER_UNRESOLVED"
            )
        source_nucleus_id = str(nucleus.source_id)
        semantic_head_kind = str(nucleus.kind)
        semantic_head_text = head_tokens.get(semantic_head_kind)
        if type(semantic_head_text) is not str or not semantic_head_text:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_HANDLE_SEMANTIC_HEAD_UNRESOLVED"
            )
        matching = tuple(
            row
            for row in phrase_specs
            if source_nucleus_id in row.owner_nucleus_ids
        )
        if len(matching) != 1:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_HANDLE_PHRASE_UNRESOLVED"
            )
        phrase = matching[0]
        phrase_text = str(phrase.phrase_text)
        role_qualifiers = tuple(
            sorted(
                qualifiers.get(owner.source_owner_id, ()),
                key=lambda token: (qualifier_rank.get(token, 10_000), token),
            )
        )
        if phrase_text not in base_text:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_HANDLE_TEXT_INVALID"
            )
        prepared.append(
            (
                owner,
                source_nucleus_id,
                phrase,
                phrase_text,
                semantic_head_kind,
                semantic_head_text,
                role_qualifiers,
            )
        )

    selected_qualifiers: dict[str, tuple[str, ...]] = {
        owner.source_owner_id: () for owner, *_rest in prepared
    }
    by_head: dict[
        str,
        list[tuple[Any, str, Any, str, str, str, tuple[str, ...]]],
    ] = {}
    for row in prepared:
        by_head.setdefault(row[5], []).append(row)
    for rows in by_head.values():
        if len(rows) == 1:
            continue
        authorized_by_token: dict[str, set[str]] = {}
        for row in rows:
            for token in row[6]:
                authorized_by_token.setdefault(token, set()).add(
                    row[0].source_owner_id
                )
        for row in rows:
            owner_id = row[0].source_owner_id
            unique_tokens = tuple(
                token
                for token in row[6]
                if authorized_by_token.get(token) == {owner_id}
            )
            if not unique_tokens:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0029_HANDLE_COLLISION"
                )
            selected_qualifiers[owner_id] = (unique_tokens[0],)

    handles: list[Step11Rc0029NaturalHandleSpec] = []
    for (
        owner,
        source_nucleus_id,
        phrase,
        phrase_text,
        semantic_head_kind,
        semantic_head_text,
        _available,
    ) in prepared:
        role_qualifiers = selected_qualifiers[owner.source_owner_id]
        handle_text = (
            semantic_head_text
            if not role_qualifiers
            else role_qualifiers[0] + semantic_head_text
        )
        if (
            not handle_text
            or len(handle_text) > 32
            or any(marker in handle_text for marker in ("\r", "\n", "「", "」"))
            or unicodedata.normalize("NFC", handle_text) != handle_text
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0029_HANDLE_TEXT_INVALID"
            )
        handles.append(
            Step11Rc0029NaturalHandleSpec(
                source_owner_id=owner.source_owner_id,
                source_owner_kind=owner.source_owner_kind,
                source_owner_ordinal=owner.owner_ordinal,
                base_source_nucleus_id=source_nucleus_id,
                grounded_phrase_id=str(phrase.grounded_phrase_id),
                grounded_phrase_text=phrase_text,
                semantic_head_kind=semantic_head_kind,
                semantic_head_text=semantic_head_text,
                role_qualifier_tokens=role_qualifiers,
                handle_text=handle_text,
                handle_text_sha256=hashlib.sha256(
                    handle_text.encode("utf-8")
                ).hexdigest(),
            )
        )
    handles.sort(
        key=lambda row: (
            row.semantic_head_text,
            row.role_qualifier_tokens,
            row.handle_text,
        )
    )
    if len({row.handle_text for row in handles}) != len(handles):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_HANDLE_COLLISION"
        )
    provisional = Step11Rc0029NaturalHandleSpecs(
        schema_version=STEP11_RC0029_NATURAL_HANDLE_SPECS_SCHEMA,
        source_base_candidate_id=base_candidate.candidate_id,
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        source_lexical_atom_specs_sha256=lexical_atom_specs.specs_sha256,
        surface_catalog_sha256=(
            catalog_owner.STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256
        ),
        required_source_owner_ids=tuple(sorted(required)),
        handles=tuple(handles),
        semantic_coverage_authority="none",
        specs_sha256="0" * 64,
    )
    value = Step11Rc0029NaturalHandleSpecs(
        **{
            **_step11_rc0029_handles_payload(provisional),
            "required_source_owner_ids": provisional.required_source_owner_ids,
            "handles": provisional.handles,
            "specs_sha256": artifact_sha256(
                _step11_rc0029_handles_payload(provisional)
            ),
        }
    )
    if validate_output:
        issues = validate_step11_rc0029_natural_handle_specs(
            value,
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        if issues:
            raise Step11GroundedLexicalizationError(issues[0])
    return value


def build_step11_rc0029_natural_handle_specs(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Step11Rc0029NaturalHandleSpecs:
    return _build_step11_rc0029_natural_handle_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        validate_output=True,
    )


def validate_step11_rc0029_natural_handle_specs(
    value: Any,
    *,
    base_candidate: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0029NaturalHandleSpecs:
        return ("STEP11_RC0029_HANDLE_SPECS_TYPE_INVALID",)
    issues: set[str] = set()
    try:
        expected = _build_step11_rc0029_natural_handle_specs(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            validate_output=False,
        )
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        return ("STEP11_RC0029_HANDLE_SPECS_REVALIDATION_FAILED",)
    if value != expected:
        issues.add("STEP11_RC0029_HANDLE_SPECS_SOURCE_MISMATCH")
    if value.semantic_coverage_authority != "none":
        issues.add("STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM")
    if (
        value.experimental_only is not True
        or value.private_body_full is not True
        or value.shareable is not False
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0029_RUNTIME_BOUNDARY_INVALID")
    if value.specs_sha256 != artifact_sha256(
        _step11_rc0029_handles_payload(value)
    ):
        issues.add("STEP11_RC0029_HANDLE_SPECS_HASH_MISMATCH")
    return tuple(sorted(issues))


def step11_rc0029_natural_handle_specs_material(
    value: Step11Rc0029NaturalHandleSpecs,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029NaturalHandleSpecs:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0029_HANDLE_SPECS_TYPE_INVALID"
        )
    return {
        **_step11_rc0029_handles_payload(value),
        "specs_sha256": value.specs_sha256,
    }


__all__ += [
    "STEP11_RC0029_NATURAL_HANDLE_SPECS_SCHEMA",
    "Step11Rc0029NaturalHandleSpec",
    "Step11Rc0029NaturalHandleSpecs",
    "build_step11_rc0029_natural_handle_specs",
    "step11_rc0029_natural_handle_specs_material",
    "validate_step11_rc0029_natural_handle_specs",
]


# ---------------------------------------------------------------------------
# rc0030 experiment-only clause-ready referent projection (append-only)
# ---------------------------------------------------------------------------

STEP11_RC0030_CLAUSE_READY_LEXICAL_SPECS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_clause_ready_lexical_specs.v1"
)
_STEP11_RC0030_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STEP11_RC0030_FORBIDDEN_REFERENT_MARKERS = (
    "見えたこと",
    "Emlisから",
    "構造を見ると",
    "そこには",
    "つ目",
    "owner",
    "relation record",
)


@dataclass(frozen=True, slots=True)
class Step11Rc0030ClauseReadyLexeme:
    """One source-grounded noun phrase ready for clause composition.

    ``referent_text`` is the already-authorized rc0027 grounded noun phrase,
    not an ordinal, schema label, raw quote, or completed sentence.  The
    ``handle_text`` compatibility view lets the disconnected forward owner
    migrate without reusing rc0029's generic semantic-head handles.
    """

    source_owner_id: str
    source_owner_kind: str
    source_owner_ordinal: int
    base_source_nucleus_id: str
    grounded_phrase_id: str
    grounded_phrase_text: str
    referent_text: str
    referent_text_sha256: str
    owner_obligation_ids: tuple[str, ...]
    base_observation_sentence_group_ids: tuple[str, ...]
    role_qualifier_tokens: tuple[str, ...] = ()

    @property
    def handle_text(self) -> str:
        return self.referent_text

    @property
    def handle_text_sha256(self) -> str:
        return self.referent_text_sha256


@dataclass(frozen=True, slots=True)
class Step11Rc0030ClauseReadyLexicalSpecs:
    schema_version: str
    source_base_candidate_id: str
    source_base_realization_plan_id: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    surface_catalog_sha256: str
    base_leading_observation_unit_id: str
    required_source_owner_ids: tuple[str, ...]
    lexemes: tuple[Step11Rc0030ClauseReadyLexeme, ...]
    semantic_coverage_authority: str
    specs_sha256: str
    max_source_owners: int
    max_referent_scalars: int
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False

    @property
    def handles(self) -> tuple[Step11Rc0030ClauseReadyLexeme, ...]:
        """Compatibility view for the disconnected forward experiment."""

        return self.lexemes


def _step11_rc0030_clause_ready_lexeme_material(
    value: Step11Rc0030ClauseReadyLexeme,
) -> dict[str, Any]:
    return {
        "source_owner_id": value.source_owner_id,
        "source_owner_kind": value.source_owner_kind,
        "source_owner_ordinal": value.source_owner_ordinal,
        "base_source_nucleus_id": value.base_source_nucleus_id,
        "grounded_phrase_id": value.grounded_phrase_id,
        "grounded_phrase_text": value.grounded_phrase_text,
        "referent_text": value.referent_text,
        "referent_text_sha256": value.referent_text_sha256,
        "owner_obligation_ids": list(value.owner_obligation_ids),
        "base_observation_sentence_group_ids": list(
            value.base_observation_sentence_group_ids
        ),
        "role_qualifier_tokens": list(value.role_qualifier_tokens),
    }


def _step11_rc0030_clause_ready_specs_payload(
    value: Step11Rc0030ClauseReadyLexicalSpecs,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_base_realization_plan_id": (
            value.source_base_realization_plan_id
        ),
        "source_successor_snapshot_sha256": (
            value.source_successor_snapshot_sha256
        ),
        "source_lexical_atom_specs_sha256": (
            value.source_lexical_atom_specs_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "base_leading_observation_unit_id": (
            value.base_leading_observation_unit_id
        ),
        "required_source_owner_ids": list(value.required_source_owner_ids),
        "lexemes": [
            _step11_rc0030_clause_ready_lexeme_material(row)
            for row in value.lexemes
        ],
        "semantic_coverage_authority": value.semantic_coverage_authority,
        "max_source_owners": value.max_source_owners,
        "max_referent_scalars": value.max_referent_scalars,
        "experimental_only": value.experimental_only,
        "private_body_full": value.private_body_full,
        "shareable": value.shareable,
        "runtime_connected": value.runtime_connected,
    }


def _step11_rc0030_referent_text_valid(
    value: Any,
    *,
    maximum: int,
) -> bool:
    return bool(
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= maximum
        and unicodedata.normalize("NFC", value) == value
        and not any(marker in value for marker in ("\r", "\n", "「", "」"))
        and not value.endswith(("。", "！", "？", "!", "?"))
        and not any(
            marker in value
            for marker in _STEP11_RC0030_FORBIDDEN_REFERENT_MARKERS
        )
        and not any(unicodedata.category(char).startswith("C") for char in value)
    )


def _build_step11_rc0030_clause_ready_lexical_specs(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    validate_output: bool,
) -> Step11Rc0030ClauseReadyLexicalSpecs:
    surface_owner = __import__(
        "emlis_ai_step11_natural_surface_v3",
        fromlist=(
            "STEP11_CANDIDATE_VERSION_ID",
            "STEP11_SURFACE_REALIZATION_PLAN_SCHEMA",
            "Step11NaturalSurfaceCandidate",
            "Step11SurfaceRealizationPlan",
            "step11_surface_realization_plan_material",
        ),
    )
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    catalog_owner = __import__(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "STEP11_RC0030_OWNER_MAX",
            "STEP11_RC0030_REFERENT_SCALAR_MAX",
            "validate_step11_rc0030_experiment_surface_catalog",
        ),
    )
    if type(base_candidate) is not surface_owner.Step11NaturalSurfaceCandidate:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_BASE_CANDIDATE_INVALID"
        )
    if (
        base_candidate.candidate_version_id
        != surface_owner.STEP11_CANDIDATE_VERSION_ID
        or type(base_candidate.final_utf8_bytes) is not bytes
        or not base_candidate.final_utf8_bytes
        or hashlib.sha256(base_candidate.final_utf8_bytes).hexdigest()
        != base_candidate.rendered_surface.sha256
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_BASE_CANDIDATE_INVALID"
        )
    expected_successor_type = (
        successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    )
    if (
        type(successor_snapshot) is not expected_successor_type
        or successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            successor_snapshot
        )
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_SUCCESSOR_SNAPSHOT_INVALID"
        )
    lexical_issues = validate_step11_rc0028_experiment_lexical_atom_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    )
    if lexical_issues:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_LEXICAL_ATOM_SPECS_INVALID"
        )
    catalog = catalog_owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    if catalog_owner.validate_step11_rc0030_experiment_surface_catalog(
        catalog
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_CATALOG_INVALID"
        )

    plan = base_candidate.surface_ast.surface_realization_plan
    if (
        type(plan) is not surface_owner.Step11SurfaceRealizationPlan
        or plan.schema_version
        != surface_owner.STEP11_SURFACE_REALIZATION_PLAN_SCHEMA
        or plan.candidate_version_id
        != surface_owner.STEP11_CANDIDATE_VERSION_ID
        or plan.body_free is not True
        or plan.realization_plan_id
        != "nls3s11real_"
        + artifact_sha256(
            surface_owner.step11_surface_realization_plan_material(
                plan,
                include_id=False,
            )
        )[:16]
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_BASE_CANDIDATE_INVALID"
        )
    observation_units = tuple(
        sorted(
            (row for row in plan.units if row.section_role == "observation"),
            key=lambda row: row.source_order,
        )
    )
    if (
        not observation_units
        or len({row.source_order for row in observation_units})
        != len(observation_units)
        or not observation_units[0].semantic_unit_id
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_BASE_LEADING_OBSERVATION_UNRESOLVED"
        )
    base_leading_observation_unit_id = observation_units[0].semantic_unit_id
    observation_group_rank = {
        group_id: index
        for index, group_id in enumerate(plan.observation_sentence_group_ids)
    }
    groups_by_nucleus: dict[str, set[str]] = {}
    for unit in observation_units:
        group_id = str(unit.assigned_sentence_group_id)
        if group_id not in observation_group_rank:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_OWNER_GROUP_UNRESOLVED"
            )
        for nucleus_id in unit.owner_nucleus_ids:
            groups_by_nucleus.setdefault(str(nucleus_id), set()).add(group_id)

    # Resolve the owners required by the immutable E1b authority directly
    # against the rc0027 AST.  In particular, do not delegate to rc0029's
    # semantic-head/qualifier collision policy: P2's clause-ready referent is
    # the already-grounded rc0027 phrase itself, and rc0029 is only frozen
    # predecessor evidence rather than an input authority for rc0030.
    owner_by_id = {
        row.source_owner_id: row for row in lexical_atom_specs.owner_bindings
    }
    owner_by_ordinal = {
        row.owner_ordinal: row for row in lexical_atom_specs.owner_bindings
    }
    if (
        len(owner_by_id) != len(lexical_atom_specs.owner_bindings)
        or len(owner_by_ordinal) != len(lexical_atom_specs.owner_bindings)
        or len(owner_by_id) > catalog_owner.STEP11_RC0030_OWNER_MAX
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_RESOURCE_BOUND_EXCEEDED"
        )

    required: set[str] = set()

    def require_owner(owner_id: str) -> None:
        if owner_id not in owner_by_id:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_SOURCE_OWNER_INVALID"
            )
        required.add(owner_id)

    for atom in lexical_atom_specs.construction_atoms:
        for ordinal in atom.target_owner_ordinals:
            owner = owner_by_ordinal.get(ordinal)
            if owner is None:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0030_SOURCE_OWNER_INVALID"
                )
            require_owner(owner.source_owner_id)
    for atom in lexical_atom_specs.relation_endpoint_atoms:
        require_owner(atom.source_owner_id)
    for atom in lexical_atom_specs.semantic_link_atoms:
        require_owner(atom.from_semantic_unit_id)
        require_owner(atom.to_semantic_unit_id)
    for atom in lexical_atom_specs.explicit_unknown_atoms:
        for _owner_kind, owner_id, _owner_ordinal in atom.affected_source_owners:
            require_owner(owner_id)

    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    nucleus_by_actual = {str(row.actual_source_id): row for row in nuclei}
    nucleus_by_source = {str(row.source_id): row for row in nuclei}
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    if (
        len(nucleus_by_actual) != len(nuclei)
        or len(nucleus_by_source) != len(nuclei)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_BASE_NUCLEUS_INVALID"
        )
    for opportunity in successor_snapshot.base_snapshot.reception_opportunities:
        if opportunity.retention != "required" and opportunity.safety_required is not True:
            continue
        for source_id in (
            *opportunity.target_nucleus_ids,
            *opportunity.support_nucleus_ids,
        ):
            actual_id = actual_by_source.get(str(source_id))
            if actual_id is None:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0030_RECEPTION_OWNER_UNRESOLVED"
                )
            require_owner(actual_id)
    if not required or len(required) > catalog_owner.STEP11_RC0030_OWNER_MAX:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_RESOURCE_BOUND_EXCEEDED"
        )

    parent_by_semantic: dict[str, set[str]] = {}
    for row in lexical_atom_specs.participation_bindings:
        if row.target_owner_kind == "semantic_unit":
            parent_by_semantic.setdefault(row.target_owner_id, set()).add(
                row.parent_nucleus_id
            )
    phrase_specs = tuple(base_candidate.surface_ast.grounded_phrase_specs)
    if len({str(row.grounded_phrase_id) for row in phrase_specs}) != len(
        phrase_specs
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_REFERENT_UNRESOLVED"
        )
    base_text = base_candidate.final_utf8_bytes.decode("utf-8", errors="strict")

    lexemes: list[Step11Rc0030ClauseReadyLexeme] = []
    for owner in sorted(
        (
            row
            for row in lexical_atom_specs.owner_bindings
            if row.source_owner_id in required
        ),
        key=lambda row: row.owner_ordinal,
    ):
        nucleus = nucleus_by_actual.get(owner.source_owner_id)
        if nucleus is None:
            parents = parent_by_semantic.get(owner.source_owner_id, set())
            if len(parents) != 1:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0030_OWNER_BASE_NUCLEUS_AMBIGUOUS"
                )
            parent_id = next(iter(parents))
            nucleus = nucleus_by_actual.get(parent_id)
            if nucleus is None:
                nucleus = nucleus_by_source.get(parent_id)
        if nucleus is None:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_OWNER_BASE_NUCLEUS_UNRESOLVED"
            )
        source_nucleus_id = str(nucleus.source_id)
        matching_phrases = tuple(
            row
            for row in phrase_specs
            if source_nucleus_id in row.owner_nucleus_ids
        )
        if len(matching_phrases) != 1:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_REFERENT_UNRESOLVED"
            )
        phrase = matching_phrases[0]
        referent_text = str(phrase.phrase_text)
        if (
            referent_text not in base_text
            or not _step11_rc0030_referent_text_valid(
                referent_text,
                maximum=catalog_owner.STEP11_RC0030_REFERENT_SCALAR_MAX,
            )
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_REFERENT_TEXT_INVALID"
            )
        group_ids = tuple(
            sorted(
                groups_by_nucleus.get(source_nucleus_id, ()),
                key=lambda group_id: observation_group_rank[group_id],
            )
        )
        if not group_ids:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0030_OWNER_GROUP_UNRESOLVED"
            )
        lexemes.append(
            Step11Rc0030ClauseReadyLexeme(
                source_owner_id=owner.source_owner_id,
                source_owner_kind=owner.source_owner_kind,
                source_owner_ordinal=owner.owner_ordinal,
                base_source_nucleus_id=source_nucleus_id,
                grounded_phrase_id=str(phrase.grounded_phrase_id),
                grounded_phrase_text=referent_text,
                referent_text=referent_text,
                referent_text_sha256=hashlib.sha256(
                    referent_text.encode("utf-8")
                ).hexdigest(),
                owner_obligation_ids=tuple(phrase.owner_obligation_ids),
                base_observation_sentence_group_ids=group_ids,
                role_qualifier_tokens=(),
            )
        )
    lexemes.sort(key=lambda row: row.source_owner_ordinal)
    if (
        not lexemes
        or len({row.source_owner_id for row in lexemes}) != len(lexemes)
        or len({row.source_owner_ordinal for row in lexemes}) != len(lexemes)
        or len({row.referent_text for row in lexemes}) != len(lexemes)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_REFERENT_COLLISION"
        )
    required_source_owner_ids = tuple(row.source_owner_id for row in lexemes)
    if set(required_source_owner_ids) != required:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_SOURCE_OWNER_INVALID"
        )

    provisional = Step11Rc0030ClauseReadyLexicalSpecs(
        schema_version=STEP11_RC0030_CLAUSE_READY_LEXICAL_SPECS_SCHEMA,
        source_base_candidate_id=base_candidate.candidate_id,
        source_base_realization_plan_id=plan.realization_plan_id,
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        source_lexical_atom_specs_sha256=lexical_atom_specs.specs_sha256,
        surface_catalog_sha256=(
            catalog_owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256
        ),
        base_leading_observation_unit_id=(
            base_leading_observation_unit_id
        ),
        required_source_owner_ids=required_source_owner_ids,
        lexemes=tuple(lexemes),
        semantic_coverage_authority="none",
        specs_sha256="0" * 64,
        max_source_owners=catalog_owner.STEP11_RC0030_OWNER_MAX,
        max_referent_scalars=catalog_owner.STEP11_RC0030_REFERENT_SCALAR_MAX,
    )
    value = Step11Rc0030ClauseReadyLexicalSpecs(
        **{
            **_step11_rc0030_clause_ready_specs_payload(provisional),
            "required_source_owner_ids": provisional.required_source_owner_ids,
            "lexemes": provisional.lexemes,
            "specs_sha256": artifact_sha256(
                _step11_rc0030_clause_ready_specs_payload(provisional)
            ),
        }
    )
    if validate_output:
        issues = validate_step11_rc0030_clause_ready_lexical_specs(
            value,
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        if issues:
            raise Step11GroundedLexicalizationError(issues[0])
    return value


def build_step11_rc0030_clause_ready_lexical_specs(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Step11Rc0030ClauseReadyLexicalSpecs:
    """Project immutable rc0027/E1b authority into natural clause referents."""

    return _build_step11_rc0030_clause_ready_lexical_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        validate_output=True,
    )


def _validate_step11_rc0030_clause_ready_lexical_specs_unsafe(
    value: Any,
    *,
    base_candidate: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0030ClauseReadyLexicalSpecs:
        return ("STEP11_RC0030_CLAUSE_READY_SPECS_TYPE_INVALID",)
    issues: set[str] = set()
    try:
        expected = _build_step11_rc0030_clause_ready_lexical_specs(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            validate_output=False,
        )
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        return ("STEP11_RC0030_CLAUSE_READY_SPECS_REVALIDATION_FAILED",)
    if value != expected:
        issues.add("STEP11_RC0030_CLAUSE_READY_SPECS_SOURCE_MISMATCH")
    if (
        value.schema_version
        != STEP11_RC0030_CLAUSE_READY_LEXICAL_SPECS_SCHEMA
        or value.semantic_coverage_authority != "none"
        or value.experimental_only is not True
        or value.private_body_full is not True
        or value.shareable is not False
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0030_CLAUSE_READY_SPECS_CONTRACT_MISMATCH")
    if (
        any(
            type(item) is not str
            or _STEP11_RC0030_SHA256_RE.fullmatch(item) is None
            or item == "0" * 64
            for item in (
                value.source_successor_snapshot_sha256,
                value.source_lexical_atom_specs_sha256,
                value.surface_catalog_sha256,
                value.specs_sha256,
            )
        )
        or value.specs_sha256
        != artifact_sha256(_step11_rc0030_clause_ready_specs_payload(value))
    ):
        issues.add("STEP11_RC0030_CLAUSE_READY_SPECS_HASH_MISMATCH")
    if (
        not value.lexemes
        or len(value.lexemes) > value.max_source_owners
        or value.max_source_owners != 24
        or value.max_referent_scalars != 32
        or value.required_source_owner_ids
        != tuple(row.source_owner_id for row in value.lexemes)
        or len(set(value.required_source_owner_ids)) != len(value.lexemes)
        or len({row.source_owner_ordinal for row in value.lexemes})
        != len(value.lexemes)
        or len({row.referent_text for row in value.lexemes})
        != len(value.lexemes)
        or any(
            type(row) is not Step11Rc0030ClauseReadyLexeme
            or row.source_owner_kind not in {"nucleus", "semantic_unit"}
            or type(row.source_owner_ordinal) is not int
            or not 1 <= row.source_owner_ordinal <= value.max_source_owners
            or not row.source_owner_id
            or not row.base_source_nucleus_id
            or not row.grounded_phrase_id
            or not row.owner_obligation_ids
            or len(set(row.owner_obligation_ids))
            != len(row.owner_obligation_ids)
            or not row.base_observation_sentence_group_ids
            or len(set(row.base_observation_sentence_group_ids))
            != len(row.base_observation_sentence_group_ids)
            or row.grounded_phrase_text != row.referent_text
            or not _step11_rc0030_referent_text_valid(
                row.referent_text,
                maximum=value.max_referent_scalars,
            )
            or hashlib.sha256(row.referent_text.encode("utf-8")).hexdigest()
            != row.referent_text_sha256
            or row.handle_text != row.referent_text
            or row.handle_text_sha256 != row.referent_text_sha256
            for row in value.lexemes
        )
    ):
        issues.add("STEP11_RC0030_CLAUSE_READY_SPECS_REFERENT_MISMATCH")
    return tuple(sorted(issues))


def validate_step11_rc0030_clause_ready_lexical_specs(
    value: Any,
    *,
    base_candidate: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    """Fail closed for malformed or adversarial projection containers."""

    try:
        return _validate_step11_rc0030_clause_ready_lexical_specs_unsafe(
            value,
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("STEP11_RC0030_CLAUSE_READY_SPECS_REVALIDATION_FAILED",)


def step11_rc0030_clause_ready_lexical_specs_material(
    value: Step11Rc0030ClauseReadyLexicalSpecs,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ClauseReadyLexicalSpecs:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0030_CLAUSE_READY_SPECS_TYPE_INVALID"
        )
    return {
        **_step11_rc0030_clause_ready_specs_payload(value),
        "specs_sha256": value.specs_sha256,
    }


# A projection is the same closed artifact viewed from the orchestration
# boundary.  Aliases avoid a second mutable shape or duplicate builder.
Step11Rc0030ClauseReadyLexicalProjection = (
    Step11Rc0030ClauseReadyLexicalSpecs
)
build_step11_rc0030_clause_ready_lexical_projection = (
    build_step11_rc0030_clause_ready_lexical_specs
)
validate_step11_rc0030_clause_ready_lexical_projection = (
    validate_step11_rc0030_clause_ready_lexical_specs
)
step11_rc0030_clause_ready_lexical_projection_material = (
    step11_rc0030_clause_ready_lexical_specs_material
)


__all__ += [
    "STEP11_RC0030_CLAUSE_READY_LEXICAL_SPECS_SCHEMA",
    "Step11Rc0030ClauseReadyLexeme",
    "Step11Rc0030ClauseReadyLexicalProjection",
    "Step11Rc0030ClauseReadyLexicalSpecs",
    "build_step11_rc0030_clause_ready_lexical_projection",
    "build_step11_rc0030_clause_ready_lexical_specs",
    "step11_rc0030_clause_ready_lexical_projection_material",
    "step11_rc0030_clause_ready_lexical_specs_material",
    "validate_step11_rc0030_clause_ready_lexical_projection",
    "validate_step11_rc0030_clause_ready_lexical_specs",
]


# rc0031 experiment-only Product owner projection (append-only B5 owner)

def _step11_rc0031_product_owner_expression_projection(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[tuple[str, str, str, str, str], ...]:
    try:
        projection = build_step11_rc0030_clause_ready_lexical_specs(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        issues = validate_step11_rc0030_clause_ready_lexical_specs(
            projection,
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    except Exception:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        ) from None
    if issues:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        )
    fragments = tuple(base_candidate.surface_ast.source_fragments)
    rows: list[tuple[str, str, str, str, str]] = []
    seen_owners: set[str] = set()
    seen_expressions: set[str] = set()
    for lexeme in projection.lexemes:
        matches = tuple(
            fragment
            for fragment in fragments
            if lexeme.base_source_nucleus_id in fragment.source_nucleus_ids
            and fragment.evidence_grade == "exact_source_span"
        )
        if not matches:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_SOURCE_FRAGMENT_UNRESOLVED"
            )
        if len(matches) != 1:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_SOURCE_FRAGMENT_AMBIGUOUS"
            )
        fragment = matches[0]
        source_expression = unicodedata.normalize(
            "NFC", str(fragment.text).strip(" \t\r\n。！？!?")
        )
        if len(source_expression) > 27:
            source_expression = (
                source_expression[:13]
                + "…"
                + source_expression[-13:]
            )
        expression = source_expression + "ということ"
        if (
            type(lexeme.source_owner_id) is not str
            or not lexeme.source_owner_id
            or type(lexeme.base_source_nucleus_id) is not str
            or not lexeme.base_source_nucleus_id
            or type(fragment.source_anchor_id) is not str
            or not fragment.source_anchor_id
            or not source_expression
            or expression != expression.strip()
            or unicodedata.normalize("NFC", expression) != expression
            or not 1 <= len(expression) <= 32
            or "\r" in expression
            or "\n" in expression
            or lexeme.source_owner_id in seen_owners
            or expression in seen_expressions
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
            )
        seen_owners.add(lexeme.source_owner_id)
        seen_expressions.add(expression)
        rows.append(
            (
                lexeme.source_owner_id,
                lexeme.base_source_nucleus_id,
                fragment.source_anchor_id,
                expression,
                hashlib.sha256(expression.encode("utf-8")).hexdigest(),
            )
        )
    if len(rows) != len(projection.lexemes):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
        )
    return tuple(rows)
# rc0031 experiment-only Product owner grammatical-head range authority (append-only B6 owner)

_STEP11_RC0031_OWNER_HEAD_RANGE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_product_owner_head_range.v1"
)
_STEP11_RC0031_OWNER_HEAD_RANGE_MAX = 32
_STEP11_RC0031_OWNER_HEAD_TERMINAL_POSITIONS = frozenset(
    {"consequent", "predicate", "quality", "limit"}
)
_STEP11_RC0031_OWNER_HEAD_FINAL_CONSTRUCTIONS = frozenset(
    {"explicit_coexistence", "balanced_consideration"}
)


@dataclass(frozen=True, slots=True)
class Step11Rc0031ProductOwnerGrammaticalHeadRangeBinding:
    source_owner_id: str
    base_source_nucleus_id: str
    source_fragment_anchor_id: str
    source_slot: str
    source_fragment_start: int
    source_fragment_end: int
    grammatical_head_start: int
    grammatical_head_end: int
    grammatical_head_scalar_count: int
    selection_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority:
    schema_version: str
    source_base_candidate_id: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    bindings: tuple[
        Step11Rc0031ProductOwnerGrammaticalHeadRangeBinding, ...
    ]
    binding_count: int
    authority_sha256: str
    semantic_coverage_authorized: bool = False
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False


def _step11_rc0031_owner_head_binding_material(
    value: Step11Rc0031ProductOwnerGrammaticalHeadRangeBinding,
) -> dict[str, Any]:
    return {
        "source_owner_id": value.source_owner_id,
        "base_source_nucleus_id": value.base_source_nucleus_id,
        "source_fragment_anchor_id": value.source_fragment_anchor_id,
        "source_slot": value.source_slot,
        "source_fragment_start": value.source_fragment_start,
        "source_fragment_end": value.source_fragment_end,
        "grammatical_head_start": value.grammatical_head_start,
        "grammatical_head_end": value.grammatical_head_end,
        "grammatical_head_scalar_count": value.grammatical_head_scalar_count,
        "selection_basis": value.selection_basis,
    }


def _step11_rc0031_owner_head_authority_material(
    value: Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority,
    *,
    include_sha256: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_successor_snapshot_sha256": (
            value.source_successor_snapshot_sha256
        ),
        "source_lexical_atom_specs_sha256": (
            value.source_lexical_atom_specs_sha256
        ),
        "bindings": [
            _step11_rc0031_owner_head_binding_material(row)
            for row in value.bindings
        ],
        "binding_count": value.binding_count,
        "semantic_coverage_authorized": (
            value.semantic_coverage_authorized
        ),
        "experimental_only": value.experimental_only,
        "body_free": value.body_free,
        "runtime_connected": value.runtime_connected,
        "authority_sha256": value.authority_sha256,
    }
    if not include_sha256:
        result.pop("authority_sha256")
    return result


def _step11_rc0031_owner_head_validated_projection(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Any:
    projection = build_step11_rc0030_clause_ready_lexical_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    if validate_step11_rc0030_clause_ready_lexical_specs(
        projection,
        base_candidate=base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    ) or validate_step11_rc0028_experiment_lexical_atom_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        )
    if (
        lexical_atom_specs.source_experiment_snapshot_sha256
        != successor_snapshot.experiment_snapshot_sha256
        or lexical_atom_specs.source_relation_construction_authority_sha256
        != successor_snapshot.relation_construction_authority.authority_sha256
        or lexical_atom_specs.source_lexical_role_witness_sha256
        != successor_snapshot.lexical_role_witness.witness_sha256
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        )
    return projection


def _step11_rc0031_owner_head_trimmed_range(fragment: Any) -> tuple[int, int]:
    text = str(fragment.text)
    if (
        not text
        or unicodedata.normalize("NFC", text) != text
        or fragment.source_end - fragment.source_start != len(text)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        )
    trim = " \t\r\n。！？!?"
    local_start = 0
    local_end = len(text)
    while local_start < local_end and text[local_start] in trim:
        local_start += 1
    while local_end > local_start and text[local_end - 1] in trim:
        local_end -= 1
    if local_start >= local_end:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
        )
    return (
        int(fragment.source_start) + local_start,
        int(fragment.source_start) + local_end,
    )


def _step11_rc0031_owner_head_syntactic_range(
    lexeme: Any,
    fragment: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[int, int]:
    base_snapshot = successor_snapshot.base_snapshot
    nuclei = tuple(
        row
        for row in base_snapshot.nuclei
        if str(row.source_id) == str(lexeme.base_source_nucleus_id)
    )
    if (
        len(nuclei) != 1
        or str(nuclei[0].actual_source_id) != str(lexeme.source_owner_id)
    ):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
        )
    nucleus = nuclei[0]
    evidence_span_ids = {
        str(row.actual_source_id)
        for row in base_snapshot.source_id_alias_bindings
        if str(row.source_kind) == "evidence"
        and str(row.alias_source_id)
        in {str(value) for value in nucleus.evidence_ids}
    }
    participations = tuple(
        row
        for row in lexical_atom_specs.participation_bindings
        if str(row.target_owner_id) == str(lexeme.source_owner_id)
        and int(row.target_owner_ordinal)
        == int(lexeme.source_owner_ordinal)
        and str(row.parent_nucleus_id) == str(nucleus.actual_source_id)
        and row.owner_resolution
        in {"exact_semantic_unit", "parent_nucleus_fallback"}
        and row.semantic_equivalence_authorized is False
    )
    atom_by_slot: dict[str, list[Any]] = {}
    for atom in lexical_atom_specs.construction_atoms:
        atom_by_slot.setdefault(str(atom.construction_slot_id), []).append(atom)
    instance_by_id = {
        str(row.construction_instance_id): row
        for row in lexical_atom_specs.construction_instances
    }
    text = str(fragment.text)
    candidates: list[tuple[str, str, int, int]] = []
    for participation in participations:
        atoms = tuple(
            atom_by_slot.get(str(participation.construction_slot_id), ())
        )
        if len(atoms) != 1:
            continue
        atom = atoms[0]
        instance = instance_by_id.get(str(atom.construction_instance_id))
        if instance is None:
            continue
        lineage_exact = bool(
            str(instance.parent_nucleus_id) == str(nucleus.actual_source_id)
            and str(atom.parent_nucleus_id) == str(nucleus.actual_source_id)
            and str(instance.source_span_id) in evidence_span_ids
            and str(atom.source_span_id) == str(instance.source_span_id)
            and str(participation.source_span_id)
            == str(instance.source_span_id)
            and str(instance.source_field) == str(fragment.source_field)
            and str(atom.source_field) == str(fragment.source_field)
            and str(instance.source_field_role) == str(fragment.source_slot)
            and str(atom.source_field_role) == str(fragment.source_slot)
            and str(atom.construction_slot_id)
            == str(participation.construction_slot_id)
            and str(participation.participation_id)
            in {str(value) for value in atom.participation_ids}
            and str(participation.participation_id)
            in {str(value) for value in instance.participation_ids}
            and str(atom.construction_slot_id)
            in {str(value) for value in instance.slot_ids}
            and int(lexeme.source_owner_ordinal)
            in {int(value) for value in atom.target_owner_ordinals}
            and int(participation.intersection_start_index)
            == int(atom.slot_start_index)
            and int(participation.intersection_end_index)
            == int(atom.slot_end_index)
            and str(atom.construction_code)
            == str(instance.construction_code)
            and atom.visible_authority == "feature_only"
            and atom.semantic_coverage_authority == "none"
            and atom.required is True
            and int(instance.instance_start_index) == 0
            and int(instance.instance_end_index) == len(text)
            and len(text)
            == int(fragment.source_end) - int(fragment.source_start)
            and text == text.strip()
            and unicodedata.normalize("NFC", text) == text
        )
        if not lineage_exact:
            continue
        if (
            atom.construction_position
            in _STEP11_RC0031_OWNER_HEAD_TERMINAL_POSITIONS
            and int(atom.slot_end_index) == int(instance.instance_end_index)
        ):
            local_start = int(atom.slot_start_index)
            local_end = int(atom.slot_end_index)
        elif (
            atom.construction_code
            in _STEP11_RC0031_OWNER_HEAD_FINAL_CONSTRUCTIONS
            and atom.construction_position == "secondary"
            and int(atom.slot_start_index) < int(instance.instance_end_index)
        ):
            local_start = int(atom.slot_start_index)
            local_end = int(instance.instance_end_index)
        else:
            continue
        if (
            not 0 <= local_start < local_end <= len(text)
            or local_end - local_start
            > _STEP11_RC0031_OWNER_HEAD_RANGE_MAX
        ):
            continue
        candidates.append(
            (
                str(instance.construction_instance_id),
                str(atom.construction_slot_id),
                int(fragment.source_start) + local_start,
                int(fragment.source_start) + local_end,
            )
        )
    if len(candidates) != 1:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
        )
    return candidates[0][2], candidates[0][3]


def _build_step11_rc0031_product_owner_grammatical_head_range_authority(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority:
    try:
        projection = _step11_rc0031_owner_head_validated_projection(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        fragments = tuple(base_candidate.surface_ast.source_fragments)
        bindings: list[
            Step11Rc0031ProductOwnerGrammaticalHeadRangeBinding
        ] = []
        seen_owner_ids: set[str] = set()
        for lexeme in projection.lexemes:
            matches = tuple(
                fragment
                for fragment in fragments
                if lexeme.base_source_nucleus_id
                in fragment.source_nucleus_ids
                and fragment.evidence_grade == "exact_source_span"
            )
            if len(matches) != 1:
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
                )
            fragment = matches[0]
            whole_start, whole_end = _step11_rc0031_owner_head_trimmed_range(
                fragment
            )
            if whole_end - whole_start <= _STEP11_RC0031_OWNER_HEAD_RANGE_MAX:
                head_start, head_end = whole_start, whole_end
                selection_basis = "whole_exact_source_fragment"
            else:
                head_start, head_end = _step11_rc0031_owner_head_syntactic_range(
                    lexeme,
                    fragment,
                    successor_snapshot=successor_snapshot,
                    lexical_atom_specs=lexical_atom_specs,
                )
                selection_basis = (
                    "grounded_syntactic_head_exact_source_range"
                )
            if (
                type(lexeme.source_owner_id) is not str
                or not lexeme.source_owner_id
                or lexeme.source_owner_id in seen_owner_ids
                or not int(fragment.source_start)
                <= head_start
                < head_end
                <= int(fragment.source_end)
                or not 1
                <= head_end - head_start
                <= _STEP11_RC0031_OWNER_HEAD_RANGE_MAX
            ):
                raise Step11GroundedLexicalizationError(
                    "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
                )
            seen_owner_ids.add(lexeme.source_owner_id)
            bindings.append(
                Step11Rc0031ProductOwnerGrammaticalHeadRangeBinding(
                    source_owner_id=lexeme.source_owner_id,
                    base_source_nucleus_id=lexeme.base_source_nucleus_id,
                    source_fragment_anchor_id=fragment.source_anchor_id,
                    source_slot=fragment.source_slot,
                    source_fragment_start=int(fragment.source_start),
                    source_fragment_end=int(fragment.source_end),
                    grammatical_head_start=head_start,
                    grammatical_head_end=head_end,
                    grammatical_head_scalar_count=head_end - head_start,
                    selection_basis=selection_basis,
                )
            )
        if not bindings or len(bindings) != len(projection.lexemes):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
            )
        provisional = (
            Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority(
                schema_version=_STEP11_RC0031_OWNER_HEAD_RANGE_SCHEMA,
                source_base_candidate_id=base_candidate.candidate_id,
                source_successor_snapshot_sha256=(
                    successor_snapshot.experiment_snapshot_sha256
                ),
                source_lexical_atom_specs_sha256=(
                    lexical_atom_specs.specs_sha256
                ),
                bindings=tuple(bindings),
                binding_count=len(bindings),
                authority_sha256="0" * 64,
            )
        )
        return Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority(
            **{
                **_step11_rc0031_owner_head_authority_material(
                    provisional, include_sha256=False
                ),
                "bindings": provisional.bindings,
                "authority_sha256": artifact_sha256(
                    _step11_rc0031_owner_head_authority_material(
                        provisional, include_sha256=False
                    )
                ),
            }
        )
    except Step11GroundedLexicalizationError:
        raise
    except Exception:
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID"
        ) from None


def _validate_step11_rc0031_product_owner_grammatical_head_range_authority(
    value: Any,
    *,
    base_candidate: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0031ProductOwnerGrammaticalHeadRangeAuthority:
        return ("STEP11_RC0031_PRODUCT_OWNER_HEAD_RANGE_TYPE_INVALID",)
    try:
        expected = (
            _build_step11_rc0031_product_owner_grammatical_head_range_authority(
                base_candidate,
                successor_snapshot=successor_snapshot,
                lexical_atom_specs=lexical_atom_specs,
            )
        )
    except Exception:
        return ("STEP11_RC0031_PRODUCT_OWNER_HEAD_RANGE_REVALIDATION_FAILED",)
    issues: set[str] = set()
    if value != expected:
        issues.add("STEP11_RC0031_PRODUCT_OWNER_HEAD_RANGE_SOURCE_MISMATCH")
    if (
        value.schema_version != _STEP11_RC0031_OWNER_HEAD_RANGE_SCHEMA
        or value.binding_count != len(value.bindings)
        or value.semantic_coverage_authorized is not False
        or value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
        or value.authority_sha256
        != artifact_sha256(
            _step11_rc0031_owner_head_authority_material(
                value, include_sha256=False
            )
        )
    ):
        issues.add("STEP11_RC0031_PRODUCT_OWNER_HEAD_RANGE_CONTRACT_MISMATCH")
    return tuple(sorted(issues))


def _step11_rc0031_product_owner_expression_projection_with_grammatical_head_range_authority(
    base_candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[tuple[str, str, str, str, str], ...]:
    authority = (
        _build_step11_rc0031_product_owner_grammatical_head_range_authority(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    )
    projection = _step11_rc0031_owner_head_validated_projection(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    fragments_by_anchor = {
        str(row.source_anchor_id): row
        for row in base_candidate.surface_ast.source_fragments
    }
    bindings_by_owner = {
        str(row.source_owner_id): row for row in authority.bindings
    }
    rows: list[tuple[str, str, str, str, str]] = []
    seen_expressions: set[str] = set()
    for lexeme in projection.lexemes:
        binding = bindings_by_owner.get(str(lexeme.source_owner_id))
        if binding is None:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
            )
        fragment = fragments_by_anchor.get(binding.source_fragment_anchor_id)
        if fragment is None:
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_SOURCE_FRAGMENT_UNRESOLVED"
            )
        relative_start = (
            binding.grammatical_head_start - int(fragment.source_start)
        )
        relative_end = (
            binding.grammatical_head_end - int(fragment.source_start)
        )
        expression = unicodedata.normalize(
            "NFC", str(fragment.text)[relative_start:relative_end]
        )
        if (
            not expression
            or expression != expression.strip()
            or len(expression) != binding.grammatical_head_scalar_count
            or len(expression) > _STEP11_RC0031_OWNER_HEAD_RANGE_MAX
            or "\r" in expression
            or "\n" in expression
            or expression in seen_expressions
        ):
            raise Step11GroundedLexicalizationError(
                "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
            )
        seen_expressions.add(expression)
        rows.append(
            (
                binding.source_owner_id,
                binding.base_source_nucleus_id,
                binding.source_fragment_anchor_id,
                expression,
                hashlib.sha256(expression.encode("utf-8")).hexdigest(),
            )
        )
    if len(rows) != len(authority.bindings):
        raise Step11GroundedLexicalizationError(
            "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID"
        )
    return tuple(rows)


_step11_rc0031_product_owner_expression_projection = (
    _step11_rc0031_product_owner_expression_projection_with_grammatical_head_range_authority
)
