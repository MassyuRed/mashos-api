# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free upstream lexical-role witness for the rc0028 experiment.

The adapter observes only a validated Grounded plan and its request-local
Evidence resolver.  It records source owner, exact local range, grammatical
role and a commitment; source fragments never enter the returned artifact.
The module is intentionally not connected to the Step 11 renderer or matcher.
"""

from dataclasses import dataclass
import re
from typing import Any, Final, Literal, Sequence

from emlis_ai_evidence_ledger_service import (
    EvidenceLedgerResolutionError,
    EvidenceSpanResolver,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    GroundedSemanticNucleus,
    validate_grounded_observation_plan,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_witness.rc0028.experiment.v1"
)
GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_adapter.20260719.v1"
)
MAX_LEXICAL_ROLES_PER_NUCLEUS: Final = 6

LexicalRoleKind = Literal[
    "referent_primary",
    "referent_secondary",
    "antecedent_predication",
    "consequent_predication",
    "predicate_or_event",
    "state_or_quality",
    "transition_or_relation",
    "action_lifecycle",
    "unknown_or_limit",
]
LexicalConstructionCode = Literal[
    "comparative_assessment",
    "particle_object",
    "choice_uncertainty",
    "decision_timing",
    "purpose_action",
    "explicit_contrast",
    "ordered_sequence",
    "reported_self_assessment",
    "explicit_coexistence",
    "parallel_addition",
    "nonreduction_boundary",
    "withheld_action",
    "balanced_consideration",
]
ConstructionPosition = Literal[
    "primary",
    "secondary",
    "antecedent",
    "consequent",
    "predicate",
    "quality",
    "connector",
    "limit",
    "lifecycle",
]
InternalLinkCode = Literal[
    "none",
    "qualifies",
    "contrast",
    "coexistence",
    "precedes",
    "limits",
]
UnresolvedReasonCode = Literal[
    "LEXICAL_ROLE_MULTI_SOURCE_OWNER",
    "LEXICAL_ROLE_SOURCE_UNRESOLVED",
    "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP",
    "LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED",
    "LEXICAL_ROLE_NO_CLOSED_CONSTRUCTION",
]

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_ROLE_KINDS: Final = frozenset(
    {
        "referent_primary",
        "referent_secondary",
        "antecedent_predication",
        "consequent_predication",
        "predicate_or_event",
        "state_or_quality",
        "transition_or_relation",
        "action_lifecycle",
        "unknown_or_limit",
    }
)
_CONSTRUCTIONS: Final = frozenset(
    {
        "comparative_assessment",
        "particle_object",
        "choice_uncertainty",
        "decision_timing",
        "purpose_action",
        "explicit_contrast",
        "ordered_sequence",
        "reported_self_assessment",
        "explicit_coexistence",
        "parallel_addition",
        "nonreduction_boundary",
        "withheld_action",
        "balanced_consideration",
    }
)
_POSITIONS: Final = frozenset(
    {
        "primary",
        "secondary",
        "antecedent",
        "consequent",
        "predicate",
        "quality",
        "connector",
        "limit",
        "lifecycle",
    }
)
_LINKS: Final = frozenset(
    {"none", "qualifies", "contrast", "coexistence", "precedes", "limits"}
)
_UNRESOLVED_REASON_CODES: Final = frozenset(
    {
        "LEXICAL_ROLE_MULTI_SOURCE_OWNER",
        "LEXICAL_ROLE_SOURCE_UNRESOLVED",
        "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP",
        "LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED",
        "LEXICAL_ROLE_NO_CLOSED_CONSTRUCTION",
    }
)
GROUNDED_LEXICAL_ROLE_KINDS: Final = _ROLE_KINDS
GROUNDED_LEXICAL_ROLE_CONSTRUCTION_CODES: Final = _CONSTRUCTIONS
GROUNDED_LEXICAL_ROLE_CONSTRUCTION_POSITIONS: Final = _POSITIONS
GROUNDED_LEXICAL_ROLE_INTERNAL_LINK_CODES: Final = _LINKS
GROUNDED_LEXICAL_ROLE_UNRESOLVED_REASON_CODES: Final = (
    _UNRESOLVED_REASON_CODES
)

# These expressions identify reusable grammatical constructions.  They do not
# contain input topics, expected prose, evaluation identity or completed
# response phrases.
_COMPARATIVE_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?:の方|のほう)が[、,]?(?P<quality>.+)$"
)
_PARTICLE_OBJECT_RE: Final = re.compile(
    r"^(?:.{1,32}?(?:は|が)[、,]?)?"
    r"(?P<primary>[^、,。．.!！?？を]{1,32})を"
    r"(?P<predicate>[^、,。．.!！?？]{2,})$"
)
_AMBIGUOUS_PARTICLE_OBJECT_SCOPE_RE: Final = re.compile(r"(?:で|に|へ).+")
_CHOICE_UNCERTAINTY_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?:かどうか|か)"
    r"(?P<limit>(?:迷|決めかね|判断でき|選べ).+)$"
)
_DECISION_TIMING_RE: Final = re.compile(
    r"^(?P<primary>.+?時期)(?:も|は|を)?"
    r"(?P<limit>(?:決め|判断|選)[^、,。]*ない)$"
)
_PURPOSE_ACTION_RE: Final = re.compile(
    r"^(?P<connector>.{2,}?よう)[、,](?P<predicate>.{2,})$"
)
_EXPLICIT_CONTRAST_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?)"
    r"(?P<connector>けれども|けれど|だけど|けど|のに|とはいえ)"
    r"[、,]?(?P<consequent>.{2,})$"
)
_ORDERED_SEQUENCE_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?)(?P<connector>(?:て|で)から|後で|あとで)"
    r"[、,]?(?P<consequent>.{2,})$"
)
_SELF_ASSESSMENT_RE: Final = re.compile(
    r"^(?P<primary>.*?(?:自分|私)(?:に|には|は)?)"
    r"(?P<quality>.{0,}?(?:"
    r"向いて(?:い)?ない|"
    r"(?:価値|資格|適性)(?:が|は)?ない|"
    r"(?:苦手|だめ|駄目|無理)(?:だ|だと|だと思|かもしれ|だろう|なの)"
    r").*)$"
)
_COEXISTENCE_RE: Final = re.compile(
    r"^(?P<primary>.+?)と[、,](?P<secondary>.+?)(?P<connector>両方).+$"
)
_PARALLEL_ADDITION_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?[いきくすつぬぶむるただ])"
    r"(?P<connector>し)[、,](?P<consequent>.{2,})$"
)
_NONREDUCTION_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?P<connector>だけで)[、,]"
    r"(?P<limit>.+?まで.*?(?:決め|判断|断定|みな|扱|とは限|わけでは).*)$"
)
_WITHHELD_ACTION_RE: Final = re.compile(
    r"^(?P<lifecycle>.{2,}?(?:ず|ないで))[、,](?P<remainder>.{2,})$"
)
_BALANCED_RE: Final = re.compile(
    r"^(?P<primary>.+?)も(?P<secondary>.+?)も[、,]"
    r"(?P<connector>どちらか一方).+$"
)


class GroundedLexicalRoleError(ValueError):
    """Fail-closed error whose message is always a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class GroundedLexicalRoleFacet:
    """One source facet using half-open, Evidence-span-local offsets."""

    facet_id: str
    owner_nucleus_id: str
    source_span_id: str
    source_field_role: Literal["thought", "action"]
    start_index: int
    end_index: int
    source_fragment_sha256: str
    lexical_role_kind: LexicalRoleKind
    construction_code: LexicalConstructionCode
    construction_position: ConstructionPosition
    internal_link: InternalLinkCode
    visible_authority: Literal["feature_only"] = "feature_only"
    required: bool = True
    forbidden_claim_codes: tuple[str, ...] = (
        "NO_RAW_FRAGMENT_REPLAY",
        "NO_GENERIC_ONLY_COVERAGE",
        "NO_OWNER_REBINDING",
    )


@dataclass(frozen=True)
class GroundedLexicalRoleWitness:
    """Facet-presence diagnostic; covered does not mean semantic coverage."""

    schema_version: str
    adapter_version: str
    plan_binding_sha256: str
    facets: tuple[GroundedLexicalRoleFacet, ...]
    covered_required_nucleus_ids: tuple[str, ...]
    unresolved_required_nucleus_ids: tuple[str, ...]
    unresolved_owner_reasons: tuple[tuple[str, UnresolvedReasonCode], ...]
    resource_bound: int
    witness_sha256: str
    body_free: bool = True


def _source_field_role(value: str) -> Literal["thought", "action"]:
    if value == "memo":
        return "thought"
    if value == "memo_action":
        return "action"
    raise GroundedLexicalRoleError("LEXICAL_ROLE_SOURCE_FIELD_INVALID")


def _required_text_nuclei(
    plan: GroundedObservationPlan,
) -> tuple[GroundedSemanticNucleus, ...]:
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    return tuple(
        row
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= _TEXT_SOURCE_FIELDS
    )


def _validated_plan_and_spans(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[Any, ...]:
    if type(plan) is not GroundedObservationPlan:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_PLAN_INVALID")
    if type(resolver) is not EvidenceSpanResolver:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_RESOLVER_INVALID")
    try:
        issues = validate_grounded_observation_plan(plan, resolver)
        spans = tuple(resolver.resolve(span_id) for span_id in resolver.span_ids)
    except (AttributeError, EvidenceLedgerResolutionError, TypeError, ValueError) as exc:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_PLAN_INVALID") from exc
    if issues:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_PLAN_INVALID")
    return spans


def _plan_binding_sha256(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
) -> str:
    commitments = [
        {
            "span_id": str(getattr(span, "span_id", "")),
            "source_field": str(getattr(span, "source_field", "")),
            "start_index": int(getattr(span, "start_index", -1)),
            "end_index": int(getattr(span, "end_index", -1)),
            "detected_type": str(getattr(span, "detected_type", "")),
            "source_body_sha256": artifact_sha256(
                {"source_body": str(getattr(span, "raw_text", ""))}
            ),
        }
        for span in spans
    ]
    return artifact_sha256(
        {
            "schema_version": GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA,
            "adapter_version": GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION,
            "grounded_plan_body_free_meta": _canonical_body_free(
                plan.as_body_free_meta()
            ),
            "evidence_commitments": commitments,
        }
    )


def _canonical_body_free(value: Any) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return format(value, ".17g")
    if isinstance(value, (tuple, list)):
        return [_canonical_body_free(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _canonical_body_free(item)
            for key, item in value.items()
        }
    raise GroundedLexicalRoleError("LEXICAL_ROLE_PLAN_PROJECTION_INVALID")


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    trim = " \t\r\n\u3000、,。．.!！?？"
    while start < end and text[start] in trim:
        start += 1
    while end > start and text[end - 1] in trim:
        end -= 1
    return start, end


def _facet(
    *,
    nucleus: GroundedSemanticNucleus,
    span: Any,
    raw_text: str,
    start: int,
    end: int,
    lexical_role_kind: str,
    construction_code: str,
    construction_position: str,
    internal_link: str,
) -> GroundedLexicalRoleFacet:
    start, end = _trim_range(raw_text, start, end)
    if not (0 <= start < end <= len(raw_text)):
        raise GroundedLexicalRoleError("LEXICAL_ROLE_SOURCE_RANGE_INVALID")
    if lexical_role_kind not in _ROLE_KINDS:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_KIND_INVALID")
    if construction_code not in _CONSTRUCTIONS:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_CONSTRUCTION_INVALID")
    if construction_position not in _POSITIONS:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_POSITION_INVALID")
    if internal_link not in _LINKS:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_INTERNAL_LINK_INVALID")
    fragment_sha256 = artifact_sha256(
        {"source_fragment": raw_text[start:end]}
    )
    identity = {
        "adapter_version": GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION,
        "owner_nucleus_id": nucleus.nucleus_id,
        "source_span_id": str(getattr(span, "span_id", "")),
        "start_index": start,
        "end_index": end,
        "source_fragment_sha256": fragment_sha256,
        "lexical_role_kind": lexical_role_kind,
        "construction_code": construction_code,
        "construction_position": construction_position,
        "internal_link": internal_link,
    }
    return GroundedLexicalRoleFacet(
        facet_id="lexical_role:f" + artifact_sha256(identity)[:24],
        owner_nucleus_id=nucleus.nucleus_id,
        source_span_id=str(getattr(span, "span_id", "")),
        source_field_role=_source_field_role(
            str(getattr(span, "source_field", ""))
        ),
        start_index=start,
        end_index=end,
        source_fragment_sha256=fragment_sha256,
        lexical_role_kind=lexical_role_kind,  # type: ignore[arg-type]
        construction_code=construction_code,  # type: ignore[arg-type]
        construction_position=construction_position,  # type: ignore[arg-type]
        internal_link=internal_link,  # type: ignore[arg-type]
    )


def _append_group(
    out: list[GroundedLexicalRoleFacet],
    *,
    nucleus: GroundedSemanticNucleus,
    span: Any,
    raw_text: str,
    match: re.Match[str],
    construction_code: str,
    internal_link: str,
    groups: Sequence[tuple[str, str, str]],
) -> None:
    existing = {row.lexical_role_kind for row in out}
    for group_name, role_kind, position in groups:
        if role_kind in existing:
            raise GroundedLexicalRoleError(
                "LEXICAL_ROLE_DUPLICATE_KIND_FOR_OWNER"
            )
        start, end = match.span(group_name)
        out.append(
            _facet(
                nucleus=nucleus,
                span=span,
                raw_text=raw_text,
                start=start,
                end=end,
                lexical_role_kind=role_kind,
                construction_code=construction_code,
                construction_position=position,
                internal_link=internal_link,
            )
        )
        existing.add(role_kind)


def _facets_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    span: Any,
) -> tuple[GroundedLexicalRoleFacet, ...]:
    raw_text = str(getattr(span, "raw_text", ""))
    out: list[GroundedLexicalRoleFacet] = []

    match = _EXPLICIT_CONTRAST_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="explicit_contrast",
            internal_link="contrast",
            groups=(
                ("antecedent", "antecedent_predication", "antecedent"),
                ("connector", "transition_or_relation", "connector"),
                ("consequent", "consequent_predication", "consequent"),
            ),
        )

    match = _ORDERED_SEQUENCE_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="ordered_sequence",
            internal_link="precedes",
            groups=(
                ("antecedent", "antecedent_predication", "antecedent"),
                ("connector", "transition_or_relation", "connector"),
                ("consequent", "consequent_predication", "consequent"),
            ),
        )

    match = (
        _WITHHELD_ACTION_RE.fullmatch(raw_text)
        if str(getattr(span, "source_field", "")) == "memo_action"
        and nucleus.kind == "action"
        else None
    )
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="withheld_action",
            internal_link="precedes",
            groups=(("lifecycle", "action_lifecycle", "lifecycle"),),
        )

    match = _COEXISTENCE_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="explicit_coexistence",
            internal_link="coexistence",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("secondary", "referent_secondary", "secondary"),
                ("connector", "transition_or_relation", "connector"),
            ),
        )

    match = _BALANCED_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="balanced_consideration",
            internal_link="coexistence",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("secondary", "referent_secondary", "secondary"),
                ("connector", "transition_or_relation", "connector"),
            ),
        )

    match = _PARALLEL_ADDITION_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="parallel_addition",
            internal_link="coexistence",
            groups=(
                ("antecedent", "antecedent_predication", "antecedent"),
                ("connector", "transition_or_relation", "connector"),
                ("consequent", "consequent_predication", "consequent"),
            ),
        )

    match = _NONREDUCTION_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="nonreduction_boundary",
            internal_link="limits",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("connector", "transition_or_relation", "connector"),
                ("limit", "unknown_or_limit", "limit"),
            ),
        )

    match = _COMPARATIVE_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="comparative_assessment",
            internal_link="qualifies",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("quality", "state_or_quality", "quality"),
            ),
        )

    match = _CHOICE_UNCERTAINTY_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="choice_uncertainty",
            internal_link="limits",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("limit", "unknown_or_limit", "limit"),
            ),
        )

    match = _DECISION_TIMING_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="decision_timing",
            internal_link="limits",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("limit", "unknown_or_limit", "limit"),
            ),
        )

    match = _PURPOSE_ACTION_RE.fullmatch(raw_text)
    if match is not None:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="purpose_action",
            internal_link="qualifies",
            groups=(
                ("connector", "transition_or_relation", "connector"),
                ("predicate", "predicate_or_event", "predicate"),
            ),
        )

    match = _SELF_ASSESSMENT_RE.fullmatch(raw_text)
    if match is not None and not out:
        _append_group(
            out,
            nucleus=nucleus,
            span=span,
            raw_text=raw_text,
            match=match,
            construction_code="reported_self_assessment",
            internal_link="qualifies",
            groups=(
                ("primary", "referent_primary", "primary"),
                ("quality", "state_or_quality", "quality"),
            ),
        )

    if not out:
        match = _PARTICLE_OBJECT_RE.fullmatch(raw_text)
        if match is not None and _AMBIGUOUS_PARTICLE_OBJECT_SCOPE_RE.search(
            match.group("primary")
        ):
            match = None
        if match is not None:
            _append_group(
                out,
                nucleus=nucleus,
                span=span,
                raw_text=raw_text,
                match=match,
                construction_code="particle_object",
                internal_link="qualifies",
                groups=(
                    ("primary", "referent_primary", "primary"),
                    ("predicate", "predicate_or_event", "predicate"),
                ),
            )

    if len(out) > MAX_LEXICAL_ROLES_PER_NUCLEUS:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED")
    return tuple(out)


def _facet_material(row: GroundedLexicalRoleFacet) -> dict[str, Any]:
    return {
        "facet_id": row.facet_id,
        "owner_nucleus_id": row.owner_nucleus_id,
        "source_span_id": row.source_span_id,
        "source_field_role": row.source_field_role,
        "start_index": row.start_index,
        "end_index": row.end_index,
        "source_fragment_sha256": row.source_fragment_sha256,
        "lexical_role_kind": row.lexical_role_kind,
        "construction_code": row.construction_code,
        "construction_position": row.construction_position,
        "internal_link": row.internal_link,
        "visible_authority": row.visible_authority,
        "required": row.required,
        "forbidden_claim_codes": list(row.forbidden_claim_codes),
    }


def _witness_payload(
    *,
    schema_version: str,
    adapter_version: str,
    plan_binding_sha256: str,
    facets: Sequence[GroundedLexicalRoleFacet],
    covered_required_nucleus_ids: Sequence[str],
    unresolved_required_nucleus_ids: Sequence[str],
    unresolved_owner_reasons: Sequence[tuple[str, str]],
    resource_bound: int,
    body_free: bool,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "plan_binding_sha256": plan_binding_sha256,
        "facets": [_facet_material(row) for row in facets],
        "covered_required_nucleus_ids": list(covered_required_nucleus_ids),
        "unresolved_required_nucleus_ids": list(
            unresolved_required_nucleus_ids
        ),
        "unresolved_owner_reasons": [
            [owner_id, reason_code]
            for owner_id, reason_code in unresolved_owner_reasons
        ],
        "resource_bound": resource_bound,
        "body_free": body_free,
    }


def grounded_lexical_role_witness_material(
    witness: GroundedLexicalRoleWitness,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> dict[str, Any]:
    """Validate then return the closed projection without source fragments."""

    issues = validate_grounded_lexical_role_witness(
        witness,
        plan=plan,
        resolver=resolver,
    )
    if issues:
        raise GroundedLexicalRoleError(issues[0])

    payload = _witness_payload(
        schema_version=witness.schema_version,
        adapter_version=witness.adapter_version,
        plan_binding_sha256=witness.plan_binding_sha256,
        facets=witness.facets,
        covered_required_nucleus_ids=witness.covered_required_nucleus_ids,
        unresolved_required_nucleus_ids=(
            witness.unresolved_required_nucleus_ids
        ),
        unresolved_owner_reasons=witness.unresolved_owner_reasons,
        resource_bound=witness.resource_bound,
        body_free=witness.body_free,
    )
    return {**payload, "witness_sha256": witness.witness_sha256}


def build_grounded_lexical_role_witness(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> GroundedLexicalRoleWitness:
    """Build a deterministic experiment witness from current source only."""

    spans = _validated_plan_and_spans(plan, resolver)
    span_by_id = {str(getattr(row, "span_id", "")): row for row in spans}
    required_text = _required_text_nuclei(plan)
    facets: list[GroundedLexicalRoleFacet] = []
    covered: list[str] = []
    unresolved: list[str] = []
    unresolved_reasons: list[tuple[str, UnresolvedReasonCode]] = []
    for nucleus in required_text:
        if len(nucleus.source_span_ids) != 1:
            unresolved.append(nucleus.nucleus_id)
            unresolved_reasons.append(
                (nucleus.nucleus_id, "LEXICAL_ROLE_MULTI_SOURCE_OWNER")
            )
            continue
        span = span_by_id.get(nucleus.source_span_ids[0])
        if span is None or str(getattr(span, "source_field", "")) not in (
            _TEXT_SOURCE_FIELDS
        ):
            unresolved.append(nucleus.nucleus_id)
            unresolved_reasons.append(
                (nucleus.nucleus_id, "LEXICAL_ROLE_SOURCE_UNRESOLVED")
            )
            continue
        try:
            rows = _facets_for_nucleus(nucleus, span)
        except GroundedLexicalRoleError as exc:
            if exc.code not in {
                "LEXICAL_ROLE_DUPLICATE_KIND_FOR_OWNER",
                "LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED",
            }:
                raise
            rows = ()
            unresolved_reason = (
                "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP"
                if exc.code == "LEXICAL_ROLE_DUPLICATE_KIND_FOR_OWNER"
                else "LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED"
            )
        else:
            unresolved_reason = "LEXICAL_ROLE_NO_CLOSED_CONSTRUCTION"
        if rows:
            facets.extend(rows)
            covered.append(nucleus.nucleus_id)
        else:
            unresolved.append(nucleus.nucleus_id)
            unresolved_reasons.append(
                (nucleus.nucleus_id, unresolved_reason)
            )
    resource_bound = (
        MAX_LEXICAL_ROLES_PER_NUCLEUS * len(required_text)
        + 2 * len(plan.relations)
        + len(plan.unknown_boundaries)
    )
    if len(facets) > resource_bound:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_RESOURCE_BOUND_EXCEEDED")
    binding = _plan_binding_sha256(plan, spans)
    payload = _witness_payload(
        schema_version=GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA,
        adapter_version=GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION,
        plan_binding_sha256=binding,
        facets=facets,
        covered_required_nucleus_ids=covered,
        unresolved_required_nucleus_ids=unresolved,
        unresolved_owner_reasons=unresolved_reasons,
        resource_bound=resource_bound,
        body_free=True,
    )
    return GroundedLexicalRoleWitness(
        schema_version=GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA,
        adapter_version=GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION,
        plan_binding_sha256=binding,
        facets=tuple(facets),
        covered_required_nucleus_ids=tuple(covered),
        unresolved_required_nucleus_ids=tuple(unresolved),
        unresolved_owner_reasons=tuple(unresolved_reasons),
        resource_bound=resource_bound,
        witness_sha256=artifact_sha256(payload),
        body_free=True,
    )


def resolve_grounded_lexical_role_source_text(
    facet: GroundedLexicalRoleFacet,
    *,
    resolver: EvidenceSpanResolver,
) -> str:
    """Resolve one facet only inside the live request and verify its digest."""

    if type(facet) is not GroundedLexicalRoleFacet:
        raise GroundedLexicalRoleError("LEXICAL_ROLE_FACET_TYPE_INVALID")
    try:
        span = resolver.resolve(facet.source_span_id)
    except (AttributeError, EvidenceLedgerResolutionError, TypeError) as exc:
        raise GroundedLexicalRoleError(
            "LEXICAL_ROLE_SOURCE_UNRESOLVED"
        ) from exc
    if _source_field_role(str(getattr(span, "source_field", ""))) != (
        facet.source_field_role
    ):
        raise GroundedLexicalRoleError("LEXICAL_ROLE_SOURCE_FIELD_MISMATCH")
    source = str(getattr(span, "raw_text", ""))
    if not (0 <= facet.start_index < facet.end_index <= len(source)):
        raise GroundedLexicalRoleError("LEXICAL_ROLE_SOURCE_RANGE_INVALID")
    fragment = source[facet.start_index : facet.end_index]
    if artifact_sha256({"source_fragment": fragment}) != (
        facet.source_fragment_sha256
    ):
        raise GroundedLexicalRoleError("LEXICAL_ROLE_SOURCE_HASH_MISMATCH")
    return fragment


def validate_grounded_lexical_role_witness(
    value: Any,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Independently rebuild and compare the complete witness contract."""

    try:
        expected = build_grounded_lexical_role_witness(plan, resolver)
    except GroundedLexicalRoleError as exc:
        return (exc.code,)
    if type(value) is not GroundedLexicalRoleWitness:
        return ("LEXICAL_ROLE_WITNESS_TYPE_INVALID",)
    issues: list[str] = []
    if value.schema_version != GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA:
        issues.append("LEXICAL_ROLE_WITNESS_SCHEMA_MISMATCH")
    if value.adapter_version != GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION:
        issues.append("LEXICAL_ROLE_WITNESS_ADAPTER_MISMATCH")
    if value.plan_binding_sha256 != expected.plan_binding_sha256:
        issues.append("LEXICAL_ROLE_PLAN_BINDING_MISMATCH")
    if type(value.facets) is not tuple or value.facets != expected.facets:
        issues.append("LEXICAL_ROLE_FACETS_MISMATCH")
    if (
        type(value.covered_required_nucleus_ids) is not tuple
        or value.covered_required_nucleus_ids
        != expected.covered_required_nucleus_ids
    ):
        issues.append("LEXICAL_ROLE_COVERED_OWNERS_MISMATCH")
    if (
        type(value.unresolved_required_nucleus_ids) is not tuple
        or value.unresolved_required_nucleus_ids
        != expected.unresolved_required_nucleus_ids
    ):
        issues.append("LEXICAL_ROLE_UNRESOLVED_OWNERS_MISMATCH")
    if (
        type(value.unresolved_owner_reasons) is not tuple
        or value.unresolved_owner_reasons != expected.unresolved_owner_reasons
    ):
        issues.append("LEXICAL_ROLE_UNRESOLVED_REASONS_MISMATCH")
    if type(value.unresolved_owner_reasons) is tuple and any(
        type(item) is not tuple
        or len(item) != 2
        or type(item[0]) is not str
        or item[1] not in _UNRESOLVED_REASON_CODES
        for item in value.unresolved_owner_reasons
    ):
        issues.append("LEXICAL_ROLE_UNRESOLVED_REASONS_INVALID")
    if value.resource_bound != expected.resource_bound:
        issues.append("LEXICAL_ROLE_RESOURCE_BOUND_MISMATCH")
    if value.body_free is not True:
        issues.append("LEXICAL_ROLE_BODY_FREE_REQUIRED")
    try:
        presented_payload = _witness_payload(
            schema_version=value.schema_version,
            adapter_version=value.adapter_version,
            plan_binding_sha256=value.plan_binding_sha256,
            facets=value.facets,
            covered_required_nucleus_ids=(
                value.covered_required_nucleus_ids
            ),
            unresolved_required_nucleus_ids=(
                value.unresolved_required_nucleus_ids
            ),
            unresolved_owner_reasons=value.unresolved_owner_reasons,
            resource_bound=value.resource_bound,
            body_free=value.body_free,
        )
        presented_hash = artifact_sha256(presented_payload)
    except (AttributeError, TypeError, ValueError):
        presented_hash = ""
    if (
        value.witness_sha256 != expected.witness_sha256
        or value.witness_sha256 != presented_hash
    ):
        issues.append("LEXICAL_ROLE_WITNESS_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


__all__ = [
    "GROUNDED_LEXICAL_ROLE_ADAPTER_VERSION",
    "GROUNDED_LEXICAL_ROLE_CONSTRUCTION_CODES",
    "GROUNDED_LEXICAL_ROLE_CONSTRUCTION_POSITIONS",
    "GROUNDED_LEXICAL_ROLE_INTERNAL_LINK_CODES",
    "GROUNDED_LEXICAL_ROLE_KINDS",
    "GROUNDED_LEXICAL_ROLE_UNRESOLVED_REASON_CODES",
    "GROUNDED_LEXICAL_ROLE_WITNESS_SCHEMA",
    "MAX_LEXICAL_ROLES_PER_NUCLEUS",
    "GroundedLexicalRoleError",
    "GroundedLexicalRoleFacet",
    "GroundedLexicalRoleWitness",
    "build_grounded_lexical_role_witness",
    "grounded_lexical_role_witness_material",
    "resolve_grounded_lexical_role_source_text",
    "validate_grounded_lexical_role_witness",
]
