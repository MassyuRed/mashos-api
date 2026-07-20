# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent inverse parser and semantic matcher for rc0027.

The inverse path intentionally does not import the rc0020 forward AST,
renderer, or candidate module.  It observes canonical body bytes, the shared
declarative catalog, the actual four-field app input, and independently
revalidated Step 4--6 parents only.

Compatibility wrappers at the end delegate hard-gate and selector calls to
the separate forward-aware owner without introducing an import-time forward
dependency into this inverse path.
"""

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Mapping, NamedTuple, Sequence

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    validate_evidence_ledger,
)
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
)
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)
from emlis_ai_step11_surface_catalog_v3 import (
    STEP11_SURFACE_CATALOG,
    STEP11_SURFACE_CATALOG_SHA256,
    validate_step11_surface_catalog,
)
from emlis_ai_step11_planning_frontier_v3 import (
    build_step11_planning_frontier,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    Step11SuppressedUnknown,
    build_step11_semantic_overlay,
    validate_step11_semantic_overlay,
)


STEP11_PARSED_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_parsed_surface_witness.v10"
)
STEP11_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_verified_surface_binding.v10"
)
STEP11_SOURCE_UNKNOWN_ORACLE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_source_unknown_oracle.rc0027.v1"
)
STEP11_HARD_GATE_SCHEMA = "cocolon.emlis.nls_v3.step11_hard_gate_result.v6"
STEP11_SELECTION_SCHEMA = "cocolon.emlis.nls_v3.step11_selection_result.v6"
STEP11_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"

_SLOT_ORDER = {"thought": 0, "action": 1, "emotion": 2, "category": 3}
_SOURCE_FIELD_TO_SLOT = {
    "memo": "thought",
    "memo_action": "action",
    "emotion_details": "emotion",
    "emotions": "emotion",
    "category": "category",
}
_BASE_NUCLEUS_SPAN_RE = re.compile(r"^nucleus:(s[1-9][0-9]*)$")
_MATCH_GENERIC_TRANSITION_SOURCE_REF = (
    "source_field_transition:memo_to_memo_action"
)
_MATCH_GENERIC_TRANSITION_ALLOWED_SOURCE_REFS = frozenset(
    {_MATCH_GENERIC_TRANSITION_SOURCE_REF, "whole_input_source_order"}
)
_MATCH_LEADING_DEPENDENT_RELATION_RESIDUE_RE = re.compile(
    r"^(?:(?:で|では|に|へ|を|が|は|と|も|から|まで|より))[、，,]\s*"
)
_MATCH_ACTIVE_DECISION_STATUSES = frozenset({"selected", "integrated_into"})
_MATCH_BOUNDARY_TEXT_FIELDS = ("memo", "memo_action")
_MATCH_BOUNDARY_FIELD_ORDER = {
    field: index for index, field in enumerate(_MATCH_BOUNDARY_TEXT_FIELDS)
}
_MATCH_BOUNDARY_COMPANION_REASON = (
    "source_boundary_clause_companion_integration"
)
_MATCH_BOUNDARY_COMPANION_MAXIMUM = 4
_MATCH_BOUNDARY_TARGET_KIND_PRIORITY = {
    "grounded_nucleus_notice": 0,
    "intention_or_next_action": 1,
    "grounded_relation_preservation": 2,
}
_TWO_PREDICATE_CONNECTIVE_RE = re.compile(
    r"^(?P<left>.{4,}?(?P<connector>後になると|けれど|だけど|のに|けど|て|で))、"
    r"(?P<right>.{4,})$"
)
_RELATIVE_TEMPORAL_DEICTIC_RE = re.compile(
    r"(?:帰ってから|戻ってから|その後|あの後|そのとき|あのとき)"
)
_CONTEXTUAL_PRECEDING_EVENT_RE = re.compile(
    r"(?:て|で)みたら|(?:て|で)もらえた|"
    r"(?:会|話|相談|訪問|外出|参加|面談|作業|用事)"
    r"[^、。！？!?\n]{0,20}(?:した|して|終えた|終わった)"
)
_MATCH_EVENT_SPLIT_RE = re.compile(
    r"(?:から|まで|だけ|は|が|を|に|へ|で|と|も|の|"
    r"[、。！？!?\s]+)"
)
_MATCH_EVENT_GENERIC_LEXEMES = frozenset(
    {"これ", "それ", "あれ", "こと", "もの", "ため", "よう"}
)
_RELATION_TYPE_PRIORITY = {
    "precedes": 0,
    "contrasts_with": 1,
    "coexists_with": 2,
    "supports_without_guarantee": 3,
    "qualifies": 4,
}
_RELATION_ENDPOINT_ROLES = frozenset({"action", "affect", "proposition"})
_EMOTION_VALENCE = {
    "positive": frozenset({"喜び", "平穏"}),
    "negative": frozenset({"悲しみ", "怒り", "不安"}),
}
_MATCH_OPEN_DECISION_RE = re.compile(
    r"(?:"
    r"決められ(?:ない|なく|ず|ません|ていない|ていません)|"
    r"決めきれ(?:ない|なく|ず|ません|ていない|ていません)|"
    r"決まら(?:ない|なく|ず|ないです|ません)|"
    r"決まってい(?:ない|ません)|決めてい(?:ない|ません)|"
    r"選べ(?:ない|なく|ず|ません|ていない|ていません)|"
    r"選びきれ(?:ない|なく|ず|ません|ていない|ていません)|"
    r"判断でき(?:ない|なく|ず|ません|ていない|ていません)|"
    r"(?:答え|結論)が出(?:ない|なく|ず|ません|ていない|ていません)|"
    r"未決定|保留|"
    r"迷(?:う(?=[。！？!?]|$)|って(?:いる|います|いて|おり)|"
    r"い(?:が|を)?(?:続け|中))"
    r")"
)
_MATCH_COMPLETED_DECISION_RE = re.compile(
    r"(?:決めた|選んだ|決定した|確定した|ことにした)"
)
_MATCH_POST_DECISION_COMPARATIVE_RE = re.compile(
    r"(?:別|ほか|他)の(?:選択|選択肢|案|ほう|方)"
    r"[^。！？!?\n]{0,36}(?:よかった|良かった|まし|"
    r"正しかった|正解だった)"
)
_MATCH_PURPOSE_NEGATION_PREFIX_RE = re.compile(
    r"(?:ないよう|ぬよう|なく(?:て|、)|ないため|ないまま)[^。！？!?]{0,72}[、,]"
)
_MATCH_MAIN_ACTION_PROGRESSIVE_RE = re.compile(
    r"(?:て|で)(?:いる|います|おり|いますね)(?:[。！？!?]|$)"
)
_MATCH_ACTION_INTENTION_RE = re.compile(
    r"(?:たい|つもり|予定|ようと思|ことにした|ことにする|"
    r"してみる|試してみる|しよう|するつもり|する予定|"
    r"決めておく|しておく|伝えるつもり|確認するつもり)"
    r"(?:[。！？!?]|$)|(?:よう|おう)(?:かな)?(?:[。！？!?]|$)"
)
_MATCH_ACTION_COMPLETED_RE = re.compile(
    r"(?:ました|でした|た|だ)(?=[、,。！？!?]|$)"
)
_MATCH_ACTION_ONGOING_RE = re.compile(
    r"(?:て|で)(?:いる|います|おる|おります)"
    r"(?:[。！？!?]|$)|"
    r"(?:最中|進行中|作業中|検討中)(?:だ|です)?(?:[。！？!?]|$)"
)
_MATCH_ACTION_NOT_COMPLETED_RE = re.compile(
    r"(?:まだ[^ 。！？!?]{0,32}(?:ていない|でいない|"
    r"していない|できていない|終わっていない))|"
    r"(?:[^ 。！？!?]{1,24}(?:は|が)まだ)(?:[。！？!?]|$)|"
    r"(?:[^ 。！？!?]{1,32}(?:て|で)いない)(?:[。！？!?]|$)|"
    r"(?:未送信|未提出|未完了|未実施|未着手|未決定)"
)


def _independent_action_lifecycle_for_nuclei(
    nucleus_ids: Sequence[str],
    *,
    nucleus_by_id: Mapping[str, Any],
    action_text: str,
) -> str:
    """Rebuild one exact-owned action lifecycle from source authority.

    The visible Reception and the forward semantic overlay are not authority
    here.  The app-reachable action field may classify only nuclei whose exact
    source owner is ``memo_action``; a semantic action extracted from ``memo``
    remains thought-slot content and must not borrow lifecycle grammar from an
    unrelated action field.  Only when exact action-field grammar is silent
    may the independently revalidated source nucleus modality carry a plain
    dictionary-form intention.  Distinct exact-owned nuclei must agree or the
    matcher keeps the lifecycle undetermined.
    """

    def classify(nucleus: Any) -> str:
        if _MATCH_ACTION_NOT_COMPLETED_RE.search(action_text) is not None:
            return "reported_not_completed"
        if _MATCH_ACTION_ONGOING_RE.search(action_text) is not None:
            return "reported_ongoing"
        if _MATCH_ACTION_INTENTION_RE.search(action_text) is not None:
            return "intended"
        if _MATCH_ACTION_COMPLETED_RE.search(action_text) is not None:
            return "reported_completed"
        return (
            "intended"
            if getattr(nucleus, "modality", None) == "intended"
            else "undetermined"
        )

    statuses = {
        classify(nucleus_by_id[nucleus_id])
        for nucleus_id in nucleus_ids
        if nucleus_id in nucleus_by_id
        and getattr(nucleus_by_id[nucleus_id], "kind", None) == "action"
        and "memo_action"
        in getattr(nucleus_by_id[nucleus_id], "source_fields", ())
    }
    if not statuses:
        return "not_applicable"
    return next(iter(statuses)) if len(statuses) == 1 else "undetermined"


_MATCH_RECEPTION_OWNER_KIND_RANK = {
    "grounded_nucleus_notice": 0,
    "intention_or_next_action": 1,
    "grounded_relation_preservation": 2,
    "unknown_boundary_preservation": 3,
}
_MATCH_RECEPTION_ACT_KIND_RANK = {
    "honor_concrete_action": {
        "intention_or_next_action": 0,
        "grounded_nucleus_notice": 1,
    },
    "receive_without_deciding": {
        "unknown_boundary_preservation": 0,
        "grounded_nucleus_notice": 1,
    },
    "stay_with_mixed_meaning": {
        "grounded_relation_preservation": 0,
        "grounded_nucleus_notice": 1,
    },
    "do_not_dismiss": {
        "self_denial_boundary": 0,
        "bounded_counterposition": 1,
        "grounded_nucleus_notice": 2,
    },
}
_MATCH_UNCERTAINTY_RE = re.compile(
    r"(?:分から|わから|判ら|不明|未定|"
    r"迷(?:う|って(?:いる|いて|おり)|い(?:が|を|続け|中))|"
    r"言葉にでき|定まっていな|まとまっていな|見えていな|"
    r"ぼんやり|思われそう|見られそう|言われそう|"
    r"だろう(?:か)?|かな(?:[。！？!?]|$)|…|\.\.\.)"
)
_MATCH_STANDALONE_DEICTIC_RE = re.compile(
    r"(?:これ|それ|あれ|どれ)(?:[、,]?(?:ね|な))?[。！？!?]?"
)
_MATCH_CONTENT_REFERENT_OPEN_RE = re.compile(
    r"(?P<focus>(?:出来事|内容|話題|対象|どのこと|どの件|"
    r"何を書く|何を(?:書く|話す|伝える))"
    r"[^、。！？!?\n]{0,24}"
    r"(?:決められない|決まらない|まとまらない|"
    r"分からない|わからない|選べない))"
)
_MATCH_ANTICIPATED_PASSIVE_OUTCOME_RE = re.compile(
    r"(?P<focus>[^、。！？!?\n]{1,48}"
    r"(?:される|られる|れる)のでは(?:ないか)?)"
)
_MATCH_PROJECTED_JUDGMENT_RE = re.compile(
    r"(?:思われ|見られ|言われ)(?:そう|るかもしれ|るのでは)"
)
_MATCH_OTHER_PERSON_AWARENESS_RE = re.compile(
    r"(?P<focus>(?:(?:相手|先方|周り|こちら|私たち|自分たち)"
    r"(?:に|には|の))[^、。！？!?\n]{1,40}"
    r"(?:見えて|伝わって|分かって|わかって|理解されて)"
    r"(?:いない|いる)(?:のか|かもしれない|のだろうか))"
)


class Step11InverseSurfaceError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11EndpointReference:
    reference_ordinal: int
    endpoint_role: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11ParsedGroundedPhrase:
    """One visible natural feature phrase recovered from body bytes only."""

    phrase_text: str
    visible_feature_fields: tuple[tuple[str, str], ...]
    visible_feature_fingerprint_sha256: str
    phrase_profile_id: str
    anchor_risk_rank: int
    action_lifecycle: str
    binding_family: str | None
    anchor_text: str | None
    byte_start: int
    byte_end: int
    anchor_byte_start: int | None = None
    anchor_byte_end: int | None = None


@dataclass(frozen=True, slots=True, repr=False)
class _Step11FusedObservationParse:
    form_id: str
    claim_kinds: tuple[str, ...]
    source_slot_hints: tuple[str, ...]
    source_fragments: tuple[str, ...]
    predicate_role: str
    realization_status: str
    relation_type: str | None = None
    relation_direction: str | None = None
    relation_endpoint_roles: tuple[str, ...] = ()
    unknown_dimension_class: str | None = None
    self_denial_not_fact: bool = False
    grounded_phrases: tuple[Step11ParsedGroundedPhrase, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class Step11ParsedAtom:
    atom_id: str
    section_role: str
    form_id: str
    claim_kinds: tuple[str, ...]
    source_slot_hints: tuple[str, ...]
    source_fragments: tuple[str, ...]
    predicate_role: str
    realization_status: str
    relation_type: str | None
    relation_direction: str | None
    relation_endpoint_roles: tuple[str, ...]
    unknown_dimension_class: str | None
    self_denial_not_fact: bool
    reception_act: str | None
    reception_scope: str | None
    byte_start: int
    byte_end: int
    introduced_reference: Step11EndpointReference | None = None
    relation_endpoint_references: tuple[Step11EndpointReference, ...] = ()
    unknown_target_references: tuple[Step11EndpointReference, ...] = ()
    compound_label_references: tuple[Step11EndpointReference, ...] = ()
    reception_antecedent_references: tuple[
        Step11EndpointReference, ...
    ] = ()
    grammatical_chunk_ordinal: int = 0
    sentence_ordinal: int = 0
    clause_ordinal: int = 0
    grounded_phrases: tuple[Step11ParsedGroundedPhrase, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class Step11ParsedSentence:
    sentence_ordinal: int
    section_role: str
    clause_atom_ids: tuple[str, ...]
    byte_start: int
    byte_end: int
    grammatical_chunk_clause_counts: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class Step11ParsedSurfaceWitness:
    schema_version: str
    surface_catalog_sha256: str
    body_sha256: str
    atoms: tuple[Step11ParsedAtom, ...]
    observation_atom_count: int
    reception_atom_count: int
    body_free_export_allowed: bool
    sentences: tuple[Step11ParsedSentence, ...] = ()


@dataclass(frozen=True, slots=True)
class Step11BindingRow:
    obligation_id: str
    obligation_kind: str
    atom_ids: tuple[str, ...]
    match_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11GroundedPhraseBinding:
    """Independent phrase-to-source binding; never forward-declared."""

    binding_id: str
    atom_id: str
    visible_feature_fingerprint_sha256: str
    phrase_profile_id: str
    anchor_risk_rank: int
    action_lifecycle: str
    binding_family: str | None
    owner_nucleus_ids: tuple[str, ...]
    owner_obligation_ids: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    source_anchor_slot: str | None
    source_anchor_start: int | None
    source_anchor_end: int | None
    source_anchor_text_sha256: str | None
    source_anchor_use_reason_code: str | None
    match_candidate_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11VerifiedSurfaceBinding:
    schema_version: str
    parsed_witness_sha256: str
    obligation_ledger_sha256: str
    content_plan_sha256: str
    discourse_plan_sha256: str
    binding_rows: tuple[Step11BindingRow, ...]
    required_obligation_ids: tuple[str, ...]
    integrated_relation_ids: tuple[str, ...]
    integrated_unknown_ids: tuple[str, ...]
    source_unknown_oracle_sha256: str
    integrated_mixed_emotion_requirement_ids: tuple[str, ...]
    integrated_reception_binding_ids: tuple[str, ...]
    source_fragment_count: int
    issue_codes: tuple[str, ...]
    verified: bool
    grounded_phrase_bindings: tuple[
        Step11GroundedPhraseBinding, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class Step11GateOutcome:
    ordinal: int
    gate_id: str
    passed: bool
    failure_code: str | None


class Step11SelectorAttributes(NamedTuple):
    """Canonical named lexicographic attributes from design section 14.1.

    ``NamedTuple`` keeps the append-only list representation used by the
    existing evidence tools while removing the positional ambiguity of the
    previous density tuple.  Values are stored in their natural direction;
    only the selector transforms the three ``max`` fields into a sort key.
    """

    required_binding_count: int
    required_distinctness_group_count: int
    bound_reception_target_count: int
    section_semantic_replay_count: int
    generic_referent_count: int
    unnecessary_source_anchor_count: int
    redundant_atom_count: int
    depth_deviation: int
    anaphora_distance: int
    candidate_id: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11HardGateResult:
    schema_version: str
    candidate_id: str
    candidate_version_id: str
    parsed_witness_sha256: str | None
    verified_binding_sha256: str | None
    outcomes: tuple[Step11GateOutcome, ...]
    failure_codes: tuple[str, ...]
    hard_pass: bool
    selector_attributes: Step11SelectorAttributes


@dataclass(frozen=True, slots=True, repr=False)
class Step11SelectionResult:
    schema_version: str
    candidate_version_id: str
    evaluated_candidate_ids: tuple[str, ...]
    gate_results: tuple[Step11HardGateResult, ...]
    selected_candidate_id: str | None
    selected_candidate: Any | None
    status: str
    bounded_candidate_limit: int
    recovery_attempted: bool
    v1_fallback_used: bool


def _normalise_text(value: str) -> str:
    return " ".join(
        unicodedata.normalize(
            "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
        ).split()
    )


def _unique_grounded_phrase_assignment(
    candidates_by_phrase: Mapping[str, Sequence[str]],
) -> tuple[dict[str, str] | None, str | None]:
    """Solve the complete phrase/nucleus assignment and require uniqueness.

    Local candidate cardinality is not treated as proof: two locally
    ambiguous phrases can still have one globally injective solution.  Search
    stops after the second solution because both two and larger cardinalities
    are the same fail-closed outcome.
    """

    if type(candidates_by_phrase) is not dict or not candidates_by_phrase:
        return None, "S11_MATCH_GROUNDED_PHRASE_ASSIGNMENT_INVALID"
    normalised: dict[str, tuple[str, ...]] = {}
    for phrase_key, candidate_ids in candidates_by_phrase.items():
        if (
            type(phrase_key) is not str
            or not phrase_key
            or type(candidate_ids) not in {list, tuple}
            or any(type(value) is not str or not value for value in candidate_ids)
        ):
            return None, "S11_MATCH_GROUNDED_PHRASE_ASSIGNMENT_INVALID"
        unique = tuple(sorted(set(candidate_ids)))
        if not unique:
            return None, "S11_MATCH_GROUNDED_PHRASE_UNRESOLVED"
        normalised[phrase_key] = unique
    ordered_keys = tuple(
        sorted(normalised, key=lambda key: (len(normalised[key]), key))
    )
    solutions: list[dict[str, str]] = []

    def visit(
        ordinal: int,
        used_nucleus_ids: frozenset[str],
        assignment: dict[str, str],
    ) -> None:
        if len(solutions) >= 2:
            return
        if ordinal == len(ordered_keys):
            solutions.append(dict(assignment))
            return
        phrase_key = ordered_keys[ordinal]
        for nucleus_id in normalised[phrase_key]:
            if nucleus_id in used_nucleus_ids:
                continue
            assignment[phrase_key] = nucleus_id
            visit(
                ordinal + 1,
                frozenset((*used_nucleus_ids, nucleus_id)),
                assignment,
            )
            assignment.pop(phrase_key, None)

    visit(0, frozenset(), {})
    if not solutions:
        return None, "S11_MATCH_GROUNDED_PHRASE_UNRESOLVED"
    if len(solutions) != 1:
        return None, "S11_MATCH_GROUNDED_PHRASE_ASSIGNMENT_AMBIGUOUS"
    return solutions[0], None


_GROUNDED_BASE_FEATURES = frozenset({"nucleus_kind"})
_GROUNDED_COLLISION_FEATURES = (
    "label_strength",
    "semantic_qualifier",
    "source_field",
    "referent_scope",
)
_GROUNDED_ANCHOR_FORBIDDEN_RE = re.compile(
    r"[\r\n\x00-\x1f\x7f\u2028\u2029"
    r"。、，．！？!?;；:：,.'\"`"
    r"\(\)\[\]\{\}（）［］｛｝〈〉《》【】〔〕"
    r"\u300c\u300d\u300e\u300f]"
)
_GROUNDED_ANCHOR_SEGMENT_AUTHORITIES = (
    "trusted_fragment_entire_text",
    "complete_punctuation_delimited_run",
)
_GROUNDED_KIND_ONLY_GENERIC_PROFILE_IDS = (
    "self_evaluation_neutral",
    "constraint_generic",
    "event_generic",
    "state_generic",
    "other_explicit_generic",
    "wish_generic",
    "value_generic",
    "change_generic",
    "uncertainty_generic",
    "conclusion_generic",
    "action_fallback",
    "reaction_fallback",
)
_GROUNDED_RESIDUAL_SEMANTIC_PREFIXES = (
    "operator:",
    "semantic_role:",
    "unit_role:",
)
_GROUNDED_RESIDUAL_HIGH_SIGNAL_CODES = (
    "operator:action",
    "operator:negation",
    "operator:shift",
    "operator:continuation",
    "operator:contrast",
    "operator:coexistence",
    "semantic_role:embedded_turn",
    "semantic_role:retained_intention",
    "unit_role:antecedent",
    "unit_role:consequent",
)
_GROUNDED_RESIDUAL_ORDERED_FACTORS = (
    "required_kind_only_generic",
    "required_relation_or_unknown_owner",
    "required_owner",
    "uncaptured_high_signal_attribute_count",
    "qualified_concrete_action_evidence",
    "uncaptured_semantic_attribute_count",
    "kind_only_generic",
    "static_anchor_risk_rank",
    "source_snapshot_order",
    "nucleus_id",
)
_GROUNDED_ANCHOR_DANGLING_PREFIXES = (
    "そして",
    "また",
    "ただ",
    "それでも",
    "けれど",
    "けど",
    "だけ",
    "は",
    "が",
    "を",
    "に",
    "へ",
    "と",
    "の",
    "も",
    "や",
    "で",
    "から",
    "ので",
)
_GROUNDED_ANCHOR_DANGLING_SUFFIXES = (
    "は",
    "が",
    "を",
    "に",
    "へ",
    "と",
    "の",
    "も",
    "や",
    "て",
    "で",
    "し",
    "から",
    "ので",
    "けれど",
    "けど",
    "ながら",
    "つつ",
    "たり",
    "なら",
    "れば",
    "たら",
)


@dataclass(frozen=True, slots=True)
class _Step11GroundedProfileContract:
    profile_id: str
    noun_phrase: str
    visible_feature_names: tuple[str, ...]
    anchor_risk_rank: int
    binding_family: str
    match: Mapping[str, tuple[str, ...]]
    visible_feature_values: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class _Step11ExpectedGroundedPhrase:
    visible_feature_fields: tuple[tuple[str, str], ...]
    phrase_text: str
    visible_feature_fingerprint_sha256: str
    phrase_profile_id: str
    anchor_risk_rank: int
    action_lifecycle: str
    profile_binding_family: str


def _step11_inverse_visible_anchor_text_safe(
    value: Any, maximum_scalars: int = 16
) -> bool:
    """Validate anchor scalars independently of the forward lexicalizer."""

    return bool(
        type(value) is str
        and type(maximum_scalars) is int
        and type(maximum_scalars) is not bool
        and maximum_scalars >= 2
        and unicodedata.normalize("NFC", value) == value
        and value == value.strip()
        and 2 <= len(value) <= maximum_scalars
        and _GROUNDED_ANCHOR_FORBIDDEN_RE.search(value) is None
        and not any(scalar.isspace() for scalar in value)
        and not any(
            unicodedata.category(scalar).startswith("C")
            for scalar in value
        )
        and not any(
            label in value
            for label in ("見えたこと", "Emlisから", "Emlis")
        )
    )


def _step11_inverse_anchor_candidate_complete(
    value: Any, maximum_scalars: int = 16
) -> bool:
    """Apply the inverse-owned Japanese fragment completion policy."""

    return bool(
        _step11_inverse_visible_anchor_text_safe(value, maximum_scalars)
        and not str(value).startswith(_GROUNDED_ANCHOR_DANGLING_PREFIXES)
        and not str(value).endswith(_GROUNDED_ANCHOR_DANGLING_SUFFIXES)
    )


def _step11_inverse_safe_anchor_segments(
    source_text: Any, maximum_scalars: int = 16
) -> tuple[tuple[str, int, int], ...]:
    """Rebuild whole trusted/punctuation-delimited runs independently.

    Whitespace/control-bearing fragments and every long run fail closed;
    particles and connectives never authorise an internal cut.
    """

    if (
        type(source_text) is not str
        or unicodedata.normalize("NFC", source_text) != source_text
        or type(maximum_scalars) is not int
        or type(maximum_scalars) is bool
        or maximum_scalars < 2
        or any(
            scalar.isspace()
            or unicodedata.category(scalar).startswith("C")
            for scalar in source_text
        )
    ):
        return ()

    runs: list[tuple[int, int]] = []
    run_start: int | None = None
    for index, scalar in enumerate(source_text):
        punctuation = _GROUNDED_ANCHOR_FORBIDDEN_RE.search(scalar) is not None
        if not punctuation and run_start is None:
            run_start = index
        if punctuation and run_start is not None:
            runs.append((run_start, index))
            run_start = None
    if run_start is not None:
        runs.append((run_start, len(source_text)))

    candidates: set[tuple[str, int, int]] = set()
    for run_start, run_end in runs:
        run = source_text[run_start:run_end]
        if len(run) <= maximum_scalars and (
            _step11_inverse_anchor_candidate_complete(run, maximum_scalars)
        ):
            candidates.add((run, run_start, run_end))
    return tuple(
        (text, start, end) for text, start, end in sorted(
            candidates,
            key=lambda row: (-len(row[0]), row[1], row[2], row[0]),
        )
    )


def _independent_grounded_raw_features(
    source: Any,
    *,
    label_strength: str = "none",
    action_lifecycle: str = "not_applicable",
) -> dict[str, Any]:
    """Project snapshot codes without importing the forward lexicalizer."""

    contract = _grounded_lexicalization_contract()
    feature_tokens = contract["feature_tokens"]
    source_fields = tuple(str(value) for value in source.source_fields)
    source_field = (
        source_fields[0]
        if len(source_fields) == 1
        and source_fields[0] in feature_tokens["source_field"]
        else "mixed"
    )
    roles = {
        code.removeprefix("unit_role:")
        for code in source.source_attribute_codes
        if code in {"unit_role:antecedent", "unit_role:consequent"}
    }
    if len(roles) > 1:
        raise Step11InverseSurfaceError(
            "S11_MATCH_GROUNDED_SEMANTIC_ROLE_AMBIGUOUS"
        )
    semantic_role = next(iter(roles), "none")
    attribute_codes = frozenset(
        str(code) for code in source.source_attribute_codes
    )
    qualifier = "none"
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
            qualifier = f"source_semantic_role:{key}"
            break
    if qualifier == "none":
        for key in ("constraint", "continuation", "shift", "action", "wish"):
            if f"operator:{key}" in attribute_codes:
                qualifier = f"source_operator:{key}"
                break
    if qualifier == "none":
        allowed_qualifiers = feature_tokens["semantic_qualifier"]
        for block_key in source.source_meaning_block_keys:
            value = (
                "meaning_block_kind:"
                + str(block_key).rsplit(":", 1)[-1]
            )
            if value in allowed_qualifiers:
                qualifier = value
                break
    modality = str(source.modality)
    temporal_scope = str(source.temporal_scope)
    if str(source.kind) == "action":
        projection = contract["action_projection"].get(action_lifecycle)
        if projection is not None:
            modality = projection["modality"]
            temporal_scope = projection["temporal_scope"]
        elif action_lifecycle != "not_applicable":
            raise Step11InverseSurfaceError(
                "S11_MATCH_GROUNDED_ACTION_LIFECYCLE_UNSUPPORTED"
            )
    elif action_lifecycle != "not_applicable":
        raise Step11InverseSurfaceError(
            "S11_MATCH_GROUNDED_ACTION_LIFECYCLE_OWNER_INVALID"
        )
    result: dict[str, Any] = {
        "semantic_role": semantic_role,
        "temporal_scope": temporal_scope,
        "modality": modality,
        "source_field": source_field,
        "referent_scope": str(source.referent_scope),
        "label_strength": label_strength,
        "polarity": str(source.polarity),
        "semantic_qualifier": qualifier,
        "action_lifecycle": (
            action_lifecycle
            if str(source.kind) == "action"
            else "not_applicable"
        ),
        "nucleus_kind": str(source.kind),
        "realization_lifecycle": action_lifecycle,
        "source_attribute_codes": tuple(sorted(attribute_codes)),
    }
    if any(
        value not in feature_tokens[field_name]
        for field_name, value in result.items()
        if field_name in _GROUNDED_FEATURE_ORDER
    ):
        raise Step11InverseSurfaceError(
            "S11_MATCH_GROUNDED_FEATURE_VALUE_UNSUPPORTED"
        )
    return result


def _independent_grounded_profile_matches(
    profile: _Step11GroundedProfileContract,
    raw: Mapping[str, Any],
) -> bool:
    """Evaluate one profile from nucleus-local facts only."""

    simple_conditions = {
        "semantic_roles": "semantic_role",
        "temporal_scopes": "temporal_scope",
        "nucleus_kinds": "nucleus_kind",
        "modalities": "modality",
        "source_fields": "source_field",
        "referent_scopes": "referent_scope",
        "polarities": "polarity",
        "label_strengths": "label_strength",
        "semantic_qualifiers": "semantic_qualifier",
        "lifecycles": "realization_lifecycle",
    }
    for condition_name, raw_name in simple_conditions.items():
        values = profile.match.get(condition_name)
        if values is not None and raw.get(raw_name) not in values:
            return False
    attribute_codes = frozenset(raw.get("source_attribute_codes", ()))
    if not set(profile.match.get("all_attribute_codes", ())) <= attribute_codes:
        return False
    any_codes = set(profile.match.get("any_attribute_codes", ()))
    return not any_codes or bool(attribute_codes & any_codes)


def _independent_grounded_phrase_contract(
    *,
    snapshot: Any,
    active_nucleus_ids: frozenset[str],
    semantic_overlay: Any | None = None,
    projection: Mapping[str, Any] | None = None,
) -> dict[str, _Step11ExpectedGroundedPhrase]:
    """Recompute profile-backed phrases from exact nucleus-local authority."""

    contract = _grounded_lexicalization_contract()
    feature_tokens = contract["feature_tokens"]
    profiles = contract["profiles"]
    ordered_ids = tuple(
        str(source.source_id)
        for source in snapshot.nuclei
        if str(source.source_id) in active_nucleus_ids
    )
    if set(ordered_ids) != set(active_nucleus_ids):
        raise Step11InverseSurfaceError(
            "S11_MATCH_GROUNDED_SOURCE_NUCLEUS_UNRESOLVED"
        )
    source_by_id = {
        str(source.source_id): source for source in snapshot.nuclei
    }
    action_text = str((projection or {}).get("action", ""))
    label_strength_by_nucleus: dict[str, str] = {}
    if semantic_overlay is not None:
        label_by_id = {
            str(row.label_anchor_id): row
            for row in semantic_overlay.label_anchors
        }
        for binding in semantic_overlay.nucleus_anchor_bindings:
            strengths = {
                str(label_by_id[anchor_id].strength)
                for anchor_id in binding.source_label_anchor_ids
                if anchor_id in label_by_id
                and label_by_id[anchor_id].strength is not None
            }
            if len(strengths) > 1:
                raise Step11InverseSurfaceError(
                    "S11_MATCH_GROUNDED_LABEL_STRENGTH_AMBIGUOUS"
                )
            if strengths:
                label_strength_by_nucleus[str(binding.nucleus_id)] = next(
                    iter(strengths)
                )
    raw_by_id = {
        nucleus_id: _independent_grounded_raw_features(
            source_by_id[nucleus_id],
            label_strength=label_strength_by_nucleus.get(
                nucleus_id, "none"
            ),
            action_lifecycle=_independent_action_lifecycle_for_nuclei(
                (nucleus_id,),
                nucleus_by_id=source_by_id,
                action_text=action_text,
            ),
        )
        for nucleus_id in ordered_ids
    }
    profile_by_id: dict[str, _Step11GroundedProfileContract] = {}
    for nucleus_id in ordered_ids:
        matching = tuple(
            profile
            for profile in profiles
            if _independent_grounded_profile_matches(
                profile, raw_by_id[nucleus_id]
            )
        )
        if not matching:
            raise Step11InverseSurfaceError(
                "S11_MATCH_GROUNDED_PROFILE_UNRESOLVED"
            )
        # Registry order is semantic priority.  Later matches are permitted
        # only as explicit fallbacks; the chosen first profile is still
        # independently re-evaluated rather than accepted from forward AST.
        profile_by_id[nucleus_id] = matching[0]
    selected_by_id = {
        nucleus_id: set(_GROUNDED_BASE_FEATURES)
        | set(profile_by_id[nucleus_id].visible_feature_names)
        for nucleus_id in ordered_ids
    }

    def fields_for(nucleus_id: str) -> tuple[tuple[str, str], ...]:
        raw = raw_by_id[nucleus_id]
        return tuple(
            (field_name, raw[field_name])
            for field_name in _GROUNDED_FEATURE_ORDER
            if field_name in selected_by_id[nucleus_id]
            and feature_tokens[field_name][raw[field_name]]
        )

    def phrase_text(nucleus_id: str) -> str:
        raw = raw_by_id[nucleus_id]
        profile = profile_by_id[nucleus_id]
        atoms = tuple(
            feature_tokens[field_name][raw[field_name]]
            for field_name in _GROUNDED_COLLISION_FEATURES
            if field_name in selected_by_id[nucleus_id]
            and field_name not in profile.visible_feature_names
            and feature_tokens[field_name][raw[field_name]]
        ) + (profile.noun_phrase,)
        if len(atoms) != len(set(atoms)):
            raise Step11InverseSurfaceError(
                "S11_MATCH_GROUNDED_PHRASE_ATOM_REPEATED"
            )
        return "".join(atoms)

    for optional_name in _GROUNDED_COLLISION_FEATURES:
        groups: dict[str, list[str]] = {}
        for nucleus_id in ordered_ids:
            groups.setdefault(phrase_text(nucleus_id), []).append(nucleus_id)
        for rows in groups.values():
            if len(rows) <= 1:
                continue
            visible_values = {
                feature_tokens[optional_name][
                    raw_by_id[nucleus_id][optional_name]
                ]
                for nucleus_id in rows
            }
            if len(visible_values) <= 1:
                continue
            for nucleus_id in rows:
                selected_by_id[nucleus_id].add(optional_name)
    result: dict[str, _Step11ExpectedGroundedPhrase] = {}
    for nucleus_id in ordered_ids:
        fields = fields_for(nucleus_id)
        if not fields or fields[-1][0] != "nucleus_kind":
            raise Step11InverseSurfaceError(
                "S11_MATCH_GROUNDED_FEATURE_HEAD_UNRESOLVED"
            )
        text = phrase_text(nucleus_id)
        profile = profile_by_id[nucleus_id]
        result[nucleus_id] = _Step11ExpectedGroundedPhrase(
            visible_feature_fields=fields,
            phrase_text=text,
            visible_feature_fingerprint_sha256=artifact_sha256(
                {
                    "visible_feature_fields": [
                        list(row) for row in fields
                    ],
                    "phrase_profile_id": profile.profile_id,
                }
            ),
            phrase_profile_id=profile.profile_id,
            anchor_risk_rank=profile.anchor_risk_rank,
            action_lifecycle=str(
                raw_by_id[nucleus_id]["action_lifecycle"]
            ),
            profile_binding_family=profile.binding_family,
        )
    return result


def _independent_grounded_phrase_bindings(
    *,
    witness: Step11ParsedSurfaceWitness,
    snapshot: Any,
    active_nucleus_ids: frozenset[str],
    by_id: Mapping[str, Mapping[str, Any]],
    discourse_plan: Mapping[str, Any],
    semantic_overlay: Any,
    projection: Mapping[str, Any],
) -> tuple[
    tuple[Step11GroundedPhraseBinding, ...],
    dict[str, frozenset[str]],
    tuple[str, ...],
]:
    """Bind all public feature-phrase occurrences without forward metadata."""

    issues: set[str] = set()
    observation_atoms = tuple(
        atom
        for atom in witness.atoms
        if atom.section_role == "observation"
    )
    occurrences: list[
        tuple[str, Step11ParsedAtom, int, Step11ParsedGroundedPhrase]
    ] = []
    for atom in observation_atoms:
        for ordinal, phrase in enumerate(atom.grounded_phrases, start=1):
            occurrence_id = (
                f"{atom.atom_id}:{ordinal}:{phrase.byte_start}:"
                f"{phrase.byte_end}:"
                f"{'anchor' if phrase.anchor_text is not None else 'plain'}"
            )
            occurrences.append((occurrence_id, atom, ordinal, phrase))
    if not occurrences:
        return (
            (),
            {atom.atom_id: frozenset() for atom in observation_atoms},
            ("S11_MATCH_GROUNDED_PHRASE_MISSING",),
        )

    try:
        expected = _independent_grounded_phrase_contract(
            snapshot=snapshot,
            active_nucleus_ids=active_nucleus_ids,
            semantic_overlay=semantic_overlay,
            projection=projection,
        )
    except Step11InverseSurfaceError as exc:
        return (
            (),
            {atom.atom_id: frozenset() for atom in observation_atoms},
            (exc.code,),
        )

    base_candidates: dict[str, tuple[str, ...]] = {}
    effective_candidates: dict[str, tuple[str, ...]] = {}
    anchor_ids_by_occurrence: dict[str, tuple[str, ...]] = {}
    anchor_evidence_by_occurrence: dict[
        str, tuple[str, int, int, str] | None
    ] = {}
    anchored_occurrences = tuple(
        row for row in occurrences if row[3].anchor_text is not None
    )
    if len(anchored_occurrences) > 1:
        issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_COUNT_INVALID")
    elif not anchored_occurrences:
        issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_REQUIRED")

    overlay_anchor_by_id = {
        str(row.anchor_id): row for row in semantic_overlay.anchors
    }
    nucleus_binding_by_id = {
        str(row.nucleus_id): row
        for row in semantic_overlay.nucleus_anchor_bindings
    }
    raw_input_values = {
        str(projection.get(slot, ""))
        for slot in ("thought", "action")
        if str(projection.get(slot, ""))
    }

    for occurrence_id, _atom, _ordinal, phrase in occurrences:
        if any(
            row.phrase_text == phrase.phrase_text
            and row.phrase_profile_id == phrase.phrase_profile_id
            and row.action_lifecycle != phrase.action_lifecycle
            for row in expected.values()
        ):
            issues.add("S11_MATCH_GROUNDED_ACTION_LIFECYCLE_MISMATCH")
        candidates = tuple(
            nucleus_id
            for nucleus_id in sorted(active_nucleus_ids)
            if (
                expected[nucleus_id].visible_feature_fields
                == phrase.visible_feature_fields
                and expected[nucleus_id].phrase_text == phrase.phrase_text
                and expected[nucleus_id].visible_feature_fingerprint_sha256
                == phrase.visible_feature_fingerprint_sha256
                and expected[nucleus_id].phrase_profile_id
                == phrase.phrase_profile_id
                and expected[nucleus_id].anchor_risk_rank
                == phrase.anchor_risk_rank
                and expected[nucleus_id].action_lifecycle
                == phrase.action_lifecycle
            )
        )
        base_candidates[occurrence_id] = candidates
        if not candidates:
            issues.add("S11_MATCH_GROUNDED_PHRASE_UNRESOLVED")
        if phrase.anchor_text is None:
            effective_candidates[occurrence_id] = candidates
            anchor_ids_by_occurrence[occurrence_id] = ()
            anchor_evidence_by_occurrence[occurrence_id] = None
            if phrase.binding_family is not None:
                issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_INVALID")
            continue

        anchor_text = phrase.anchor_text
        anchor_shape_green = bool(
            _step11_inverse_visible_anchor_text_safe(anchor_text, 16)
            and phrase.anchor_byte_start is not None
            and phrase.anchor_byte_end is not None
            and phrase.anchor_byte_end > phrase.anchor_byte_start
        )
        if not anchor_shape_green:
            issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_RANGE_INVALID")
        if (
            anchor_text in raw_input_values
            and len(anchor_text) > 16
        ):
            issues.add("S11_MATCH_RAW_INPUT_REPLAY_FORBIDDEN")

        exact_anchor_owners: list[
            tuple[str, str, str, int, int]
        ] = []
        unsafe_boundary_observed = False
        for nucleus_id in candidates:
            binding = nucleus_binding_by_id.get(nucleus_id)
            if binding is None:
                continue
            for anchor_id in binding.source_anchor_ids:
                anchor = overlay_anchor_by_id.get(str(anchor_id))
                if anchor is None:
                    continue
                slot = str(anchor.source_slot)
                relative_occurrences: list[int] = []
                cursor = 0
                while True:
                    relative_start = str(anchor.text).find(
                        anchor_text, cursor
                    )
                    if relative_start < 0:
                        break
                    relative_occurrences.append(relative_start)
                    cursor = relative_start + 1
                if len(relative_occurrences) != 1:
                    continue
                start = int(anchor.start) + relative_occurrences[0]
                end = start + len(anchor_text)
                if (
                    start < 0
                    or end > int(anchor.end)
                    or str(anchor.text)[
                        relative_occurrences[0] :
                        relative_occurrences[0] + len(anchor_text)
                    ]
                    != anchor_text
                ):
                    continue
                safe_segments = _step11_inverse_safe_anchor_segments(
                    str(anchor.text), 16
                )
                safe_relative_range = (
                    anchor_text,
                    relative_occurrences[0],
                    relative_occurrences[0] + len(anchor_text),
                )
                if safe_relative_range not in safe_segments:
                    unsafe_boundary_observed = True
                    continue
                if slot in {"thought", "action"}:
                    source_text = str(projection.get(slot, ""))
                    if (
                        end > len(source_text)
                        or source_text[start:end] != anchor_text
                    ):
                        continue
                exact_anchor_owners.append(
                    (nucleus_id, str(anchor_id), slot, start, end)
                )
        exact_anchor_owners = list(dict.fromkeys(exact_anchor_owners))
        if unsafe_boundary_observed and not exact_anchor_owners:
            issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_BOUNDARY_INVALID")
        narrowed = tuple(
            sorted({row[0] for row in exact_anchor_owners})
        )
        effective_candidates[occurrence_id] = narrowed
        owner_anchor_ids = tuple(
            row[1]
            for row in exact_anchor_owners
            for nucleus_id in (row[0],)
            if nucleus_id in narrowed
        )
        anchor_ids_by_occurrence[occurrence_id] = tuple(
            dict.fromkeys(owner_anchor_ids)
        )
        if len(narrowed) != 1 or len(anchor_ids_by_occurrence[occurrence_id]) != 1:
            issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_OWNER_INVALID")
            anchor_evidence_by_occurrence[occurrence_id] = None
        else:
            evidence_rows = tuple(
                row for row in exact_anchor_owners if row[0] == narrowed[0]
            )
            if len(evidence_rows) != 1:
                issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_RANGE_INVALID")
                anchor_evidence_by_occurrence[occurrence_id] = None
            else:
                anchor_evidence_by_occurrence[occurrence_id] = (
                    evidence_rows[0][2],
                    evidence_rows[0][3],
                    evidence_rows[0][4],
                    hashlib.sha256(anchor_text.encode("utf-8")).hexdigest(),
                )

    assignment, assignment_issue = _unique_grounded_phrase_assignment(
        effective_candidates
    )
    if assignment_issue is not None:
        issues.add(assignment_issue)
    if anchored_occurrences:
        # Feature-only noun phrases intentionally remain generic.  The one
        # exact primary anchor supplies the candidate-wide input-specific
        # referent even when feature tuples happen to be locally unique.
        pass

    if assignment is None:
        return (
            (),
            {atom.atom_id: frozenset() for atom in observation_atoms},
            tuple(sorted(issues)),
        )
    if set(assignment.values()) != set(active_nucleus_ids):
        issues.add("S11_MATCH_GROUNDED_PHRASE_COVERAGE_MISMATCH")

    active_obligation_ids = tuple(
        str(node.get("obligation_id"))
        for node in discourse_plan.get("nodes", [])
        if type(node) is dict
        and type(node.get("obligation_id")) is str
        and node.get("obligation_id") in by_id
    )
    owner_obligations_by_nucleus = {
        nucleus_id: (
            active_owners
            if (
                active_owners := tuple(
                    dict.fromkeys(
                        obligation_id
                        for obligation_id in active_obligation_ids
                        if nucleus_id
                        in tuple(
                            by_id[obligation_id].get("nucleus_ids", ())
                        )
                    )
                )
            )
            else tuple(
                obligation_id
                for obligation_id, obligation in by_id.items()
                if nucleus_id
                in tuple(obligation.get("nucleus_ids", ()))
            )
        )
        for nucleus_id in active_nucleus_ids
    }
    if any(
        not owner_obligations_by_nucleus[nucleus_id]
        for nucleus_id in active_nucleus_ids
    ):
        issues.add("S11_MATCH_GROUNDED_PHRASE_OBLIGATION_OWNER_UNRESOLVED")

    bindings: list[Step11GroundedPhraseBinding] = []
    nuclei_by_atom: dict[str, set[str]] = {
        atom.atom_id: set() for atom in observation_atoms
    }
    def expected_binding_family(nucleus_id: str) -> str:
        # The binding family is owned by the exact independently selected
        # registry profile.  In particular, relation presence or an embedded
        # turn cannot widen `relation_shift`; only the exact shift profile can
        # select that family.
        return expected[nucleus_id].profile_binding_family

    for occurrence_id, atom, ordinal, phrase in occurrences:
        nucleus_id = assignment[occurrence_id]
        nuclei_by_atom[atom.atom_id].add(nucleus_id)
        source_anchor_ids = anchor_ids_by_occurrence[occurrence_id]
        anchor_evidence = anchor_evidence_by_occurrence.get(occurrence_id)
        expected_family = expected_binding_family(nucleus_id)
        if source_anchor_ids:
            if phrase.binding_family != expected_family:
                issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_MISMATCH")
        elif phrase.binding_family is not None:
            issues.add("S11_MATCH_VISIBLE_SOURCE_ANCHOR_FAMILY_INVALID")
        owner_obligation_ids = owner_obligations_by_nucleus[nucleus_id]
        material = {
            "atom_id": atom.atom_id,
            "phrase_ordinal": ordinal,
            "phrase_byte_start": phrase.byte_start,
            "phrase_byte_end": phrase.byte_end,
            "visible_feature_fingerprint_sha256": (
                phrase.visible_feature_fingerprint_sha256
            ),
            "phrase_profile_id": phrase.phrase_profile_id,
            "anchor_risk_rank": phrase.anchor_risk_rank,
            "action_lifecycle": phrase.action_lifecycle,
            "binding_family": phrase.binding_family,
            "owner_nucleus_ids": [nucleus_id],
            "owner_obligation_ids": list(owner_obligation_ids),
            "source_anchor_ids": list(source_anchor_ids),
        }
        bindings.append(
            Step11GroundedPhraseBinding(
                binding_id=(
                    "nls3s11gpb_" + artifact_sha256(material)[:16]
                ),
                atom_id=atom.atom_id,
                visible_feature_fingerprint_sha256=(
                    phrase.visible_feature_fingerprint_sha256
                ),
                phrase_profile_id=phrase.phrase_profile_id,
                anchor_risk_rank=phrase.anchor_risk_rank,
                action_lifecycle=phrase.action_lifecycle,
                binding_family=phrase.binding_family,
                owner_nucleus_ids=(nucleus_id,),
                owner_obligation_ids=owner_obligation_ids,
                source_anchor_ids=source_anchor_ids,
                source_anchor_slot=(
                    anchor_evidence[0]
                    if anchor_evidence is not None
                    else None
                ),
                source_anchor_start=(
                    anchor_evidence[1]
                    if anchor_evidence is not None
                    else None
                ),
                source_anchor_end=(
                    anchor_evidence[2]
                    if anchor_evidence is not None
                    else None
                ),
                source_anchor_text_sha256=(
                    anchor_evidence[3]
                    if anchor_evidence is not None
                    else None
                ),
                source_anchor_use_reason_code=(
                    "INPUT_SPECIFIC_BINDING_REQUIRED"
                    if source_anchor_ids
                    else None
                ),
                match_candidate_count=1,
            )
        )
    return (
        tuple(bindings),
        {
            atom_id: frozenset(nucleus_ids)
            for atom_id, nucleus_ids in nuclei_by_atom.items()
        },
        tuple(sorted(issues)),
    )


def _independent_same_event_restatement(left: str, right: str) -> bool:
    """Recompute the narrow optional restatement exception inverse-side."""

    def event_lexemes(value: str) -> tuple[str, ...]:
        return tuple(
            token
            for token in _MATCH_EVENT_SPLIT_RE.split(_normalise_text(value))
            if token and token not in _MATCH_EVENT_GENERIC_LEXEMES
        )

    left_lexemes = event_lexemes(left)
    right_lexemes = event_lexemes(right)
    if len(left_lexemes) < 2 or len(right_lexemes) < 2:
        return False
    if left_lexemes[-1] != right_lexemes[-1]:
        return False
    return bool(set(left_lexemes[:-1]) & set(right_lexemes[:-1]))


def _semantic_core_text(value: str) -> str:
    """Return the proposition core used only by the self-denial contract.

    A self-evaluation anchor is sometimes the complete source sentence while
    the active nucleus is the same source span without its terminal sentence
    mark.  Treating those byte strings as unrelated loses the required
    denial; applying this relaxation globally would, however, weaken exact
    relation and unknown endpoint ownership.  Callers therefore opt in only
    for self-denial/nucleus reconciliation.
    """

    return re.sub(r"[。！？!?]+$", "", _normalise_text(value)).rstrip()


def _canonical_status(value: str | None) -> str:
    status = (value or "").strip().casefold()
    if status in {"reported_content"}:
        return "reported_content"
    if status in {"intended", "future_intent", "decision_to_act"}:
        return "intended"
    if status in {"reported_ongoing", "ongoing"}:
        return "reported_ongoing"
    if status in {"reported_not_completed", "not_completed"}:
        return "reported_not_completed"
    if status in {"reported_completed", "completed"}:
        return "reported_completed"
    if status in {"undetermined", "neutral", "status_neutral", ""}:
        return "undetermined"
    return status


def _project_input(current_input: Mapping[str, Any]) -> dict[str, Any]:
    if type(current_input) is not dict:
        raise Step11InverseSurfaceError("S11_MATCH_INPUT_MAPPING_REQUIRED")
    thought = current_input.get("thought_text")
    action = current_input.get("action_text")
    emotions = current_input.get("emotions")
    categories = current_input.get("categories")
    if type(thought) is not str or type(action) is not str:
        raise Step11InverseSurfaceError("S11_MATCH_TEXT_FIELDS_INVALID")
    if type(emotions) is not list or type(categories) is not list:
        raise Step11InverseSurfaceError("S11_MATCH_LABEL_ARRAYS_REQUIRED")

    def labels(rows: list[Any]) -> tuple[str, ...]:
        result: list[str] = []
        for row in rows:
            value = row if type(row) is str else row.get("type") if type(row) is dict else None
            if type(value) is not str or not _normalise_text(value):
                raise Step11InverseSurfaceError("S11_MATCH_LABEL_INVALID")
            result.append(_normalise_text(value))
        if len(result) != len(set(result)):
            raise Step11InverseSurfaceError("S11_MATCH_LABEL_DUPLICATE")
        return tuple(result)

    emotion_details: list[tuple[str, str]] = []
    for row in emotions:
        if type(row) is not dict:
            raise Step11InverseSurfaceError("S11_MATCH_EMOTION_ENTRY_INVALID")
        emotion_type = row.get("type")
        strength = row.get("strength")
        if (
            type(emotion_type) is not str
            or type(strength) is not str
            or not _normalise_text(emotion_type)
            or not _normalise_text(strength)
        ):
            raise Step11InverseSurfaceError("S11_MATCH_EMOTION_ENTRY_INVALID")
        emotion_details.append(
            (_normalise_text(emotion_type), _normalise_text(strength))
        )

    result = {
        "thought": _normalise_text(thought),
        "action": _normalise_text(action),
        "emotion": labels(emotions),
        "category": labels(categories),
        "emotion_details": tuple(emotion_details),
    }
    if not result["thought"] and not result["action"]:
        raise Step11InverseSurfaceError("S11_MATCH_TEXT_REQUIRED")
    return result


def _exact_raw_line_units(
    current_input: Mapping[str, Any],
) -> dict[str, frozenset[str]]:
    """Recover canonical units whose boundary is an actual source newline."""

    result: dict[str, frozenset[str]] = {}
    for source_field, slot in (
        ("thought_text", "thought"),
        ("action_text", "action"),
    ):
        value = current_input.get(source_field)
        if type(value) is not str:
            raise Step11InverseSurfaceError("S11_MATCH_TEXT_FIELDS_INVALID")
        raw = unicodedata.normalize(
            "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
        )
        result[slot] = frozenset(
            unit
            for line in raw.split("\n")
            if (unit := _normalise_text(line))
        )
    return result


def _meaningful_char_count(value: str) -> int:
    return sum(1 for char in value if not char.isspace() and char not in "。！？!?、，,.;；:：")


def _bounded_piece(value: str, maximum: int, *, from_end: bool) -> str:
    if len(value) <= maximum:
        return value
    piece = value[-maximum:] if from_end else value[:maximum]
    if from_end and piece and piece[0].isascii() and piece[0].isalnum():
        boundary = piece.find(" ")
        if 0 <= boundary < maximum // 2:
            piece = piece[boundary + 1 :]
    elif not from_end and piece and piece[-1].isascii() and piece[-1].isalnum():
        boundary = piece.rfind(" ")
        if boundary >= maximum // 2:
            piece = piece[:boundary]
    return piece.strip()


def _allowed_text_fragments(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    policy = STEP11_SURFACE_CATALOG["fragment_policy"]
    matches = tuple(re.finditer(r"[^。！？!?]+(?:[。！？!?]+|$)", value))
    meaningful = tuple(
        row
        for row in matches
        if _meaningful_char_count(row.group(0).strip())
        >= int(policy["minimum_meaningful_chars"])
    )
    if (
        len(value) <= int(policy["whole_text_max_chars"])
        and len(meaningful) <= 1
    ):
        return (value,)
    if not meaningful:
        meaningful = matches
    if not meaningful:
        return ()
    # The successor never truncates a semantic nucleus to satisfy a budget.
    # Each admissible fragment is one complete canonical source clause.
    first = meaningful[0].group(0).strip()
    last = meaningful[-1].group(0).strip()
    return tuple(dict.fromkeys((first, last)))


def _unknown_class(value: str) -> str:
    code = unicodedata.normalize("NFC", value).casefold()
    # The overlay owns the source-side semantic name while the declarative
    # surface catalog owns the inverse grammar key.  Keep this one explicit
    # cross-contract mapping ahead of the broader referent family: an exact
    # other-person awareness boundary must not collapse into an ordinary
    # omitted-referent boundary.
    if code == "other_person":
        return "other_person_awareness"
    if code == "decision_state":
        return "decision_state"
    if code == "post_decision_comparative_merit":
        return "post_decision_comparative_merit"
    for result, tokens in (
        ("cause", ("cause", "reason", "background")),
        (
            "referent",
            ("referent", "target", "subject", "other_person"),
        ),
        ("unresolved_intention", ("unresolved_intention", "choice")),
        ("future", ("future", "next", "later")),
        ("outcome", ("outcome", "result", "effect")),
        ("relation", ("relation", "connection", "link")),
    ):
        if any(token in code for token in tokens):
            return result
    return "generic"


def _independent_explicit_unknown_type(value: str) -> str | None:
    """Classify explicit open grammar without using the overlay classifier."""

    text = _normalise_text(value)
    if _MATCH_STANDALONE_DEICTIC_RE.fullmatch(text) is not None:
        return "omitted_referent"
    open_decision = _MATCH_OPEN_DECISION_RE.search(text) is not None
    uncertain = _MATCH_UNCERTAINTY_RE.search(text) is not None or open_decision
    if re.search(r"(?:なぜ|どうして|なんで|理由|原因|わけ)", text) and re.search(
        r"(?:分から|わから|判ら|不明|言葉にでき|説明でき|特定でき|"
        r"だろう|かな(?:[。！？!?]|$))",
        text,
    ):
        return "cause"
    if _MATCH_ANTICIPATED_PASSIVE_OUTCOME_RE.search(text) is not None:
        return "future_outcome"
    if _MATCH_PROJECTED_JUDGMENT_RE.search(text) is not None:
        return "other_person"
    if _MATCH_OTHER_PERSON_AWARENESS_RE.search(text) is not None:
        return "other_person"
    if _MATCH_CONTENT_REFERENT_OPEN_RE.search(text) is not None:
        return "omitted_referent"
    if _MATCH_POST_DECISION_COMPARATIVE_RE.search(text) is not None:
        return "post_decision_comparative_merit"
    if open_decision:
        return "decision_state"
    if (
        re.search(
            r"(?:あの件|この件|その件|あのこと|このこと|そのこと)",
            text,
        )
        or re.fullmatch(
            r"(?:まだ)?(?:よく)?分からない[。！？!?]?",
            text,
        )
        is not None
        or uncertain
        and re.search(
            r"(?:何について|何のこと|どの部分|どのこと|どれ|"
            r"どこ|何が|何を|何から|見落としていな|抜けていな|"
            r"欠けていな)",
            text,
        ) is not None
    ):
        return "omitted_referent"
    if uncertain and re.search(
        r"(?:決め|選(?:ぶ|べ)|選択|どちら|どうする|"
        r"続けるか|意図|つもり|したいのか|"
        r"ほうがよかった|方がよかった)",
        text,
    ) is not None:
        return "decision_state"
    if uncertain and re.search(
        r"(?:思われ|見られ|言われ|相手|周り|みんな|他の人)",
        text,
    ) is not None:
        return "other_person"
    if uncertain and re.search(
        r"(?:関係|つながり|距離|バランス|折り合い|両立)",
        text,
    ) is not None:
        return "relation"
    if uncertain and re.search(
        r"(?:これから|今後|次(?:回|は|に)|明日|来週|将来|この先|先の)",
        text,
    ) is not None:
        return "future_outcome"
    return "unspecified" if uncertain else None


def _independent_source_unknown_type(
    dimension_code: str,
    source_text: str,
    *,
    contextual_text: str,
) -> str | None:
    """Recompute one required frozen unknown from source bytes and code."""

    code = unicodedata.normalize("NFC", dimension_code).upper()
    normal = _normalise_text(source_text)
    classified = _independent_explicit_unknown_type(normal)
    if any(token in code for token in ("CHOICE", "DECISION", "INTENTION")):
        open_decision = _MATCH_OPEN_DECISION_RE.search(source_text) is not None
        completed_decision = (
            _MATCH_COMPLETED_DECISION_RE.search(source_text) is not None
        )
        post_decision_comparative = (
            _MATCH_POST_DECISION_COMPARATIVE_RE.search(source_text) is not None
        )
        # Reconstruct the frozen lifecycle independently, but keep the same
        # fail-close boundary as the forward overlay.  A single owned span
        # cannot simultaneously prove that a decision is completed and open.
        if open_decision and (
            completed_decision or post_decision_comparative
        ):
            return None
        if post_decision_comparative:
            return "post_decision_comparative_merit"
        if open_decision:
            return "decision_state"
        code_tokens = frozenset(code.split("_"))
        if (
            code.startswith("EXPLICIT_")
            and {"CHOICE", "DECISION", "UNKNOWN"} <= code_tokens
            and _MATCH_UNCERTAINTY_RE.search(source_text) is not None
            and not completed_decision
        ):
            return "decision_state"
        if classified == "omitted_referent":
            return classified
        return None
    if any(token in code for token in ("CAUSE", "REASON", "MOTIVE")):
        return (
            "cause"
            if code.startswith("EXPLICIT_")
            or classified == "cause"
            or re.search(
                r"(?:なんとなく|理由もなく|わけもなく)", source_text
            )
            else None
        )
    if any(token in code for token in ("OTHER_PERSON", "OTHER_REACTION")):
        return (
            "other_person"
            if code.startswith("EXPLICIT_") or classified == "other_person"
            else None
        )
    if any(token in code for token in ("FUTURE", "OUTCOME", "LATER", "NEXT_")):
        return (
            "future_outcome"
            if code.startswith("EXPLICIT_")
            or re.search(
                r"(?:これから|今後|次(?:回|は|に)|明日|来週|将来|この先)",
                source_text,
            )
            and _MATCH_UNCERTAINTY_RE.search(source_text) is not None
            else None
        )
    if any(token in code for token in ("RELATION", "CONNECTION")):
        return (
            "relation"
            if code.startswith("EXPLICIT_") or classified == "relation"
            else None
        )
    if "TEMPORAL_REFERENT" in code:
        marker = _RELATIVE_TEMPORAL_DEICTIC_RE.search(source_text)
        if marker is None:
            return None
        locally_resolved = (
            _CONTEXTUAL_PRECEDING_EVENT_RE.search(
                source_text[: marker.start()]
            )
            is not None
        )
        surrounding = contextual_text.replace(source_text, "", 1)
        externally_resolved = (
            _CONTEXTUAL_PRECEDING_EVENT_RE.search(surrounding) is not None
        )
        return (
            None
            if locally_resolved or externally_resolved
            else "omitted_referent"
        )
    if any(
        token in code
        for token in ("REFERENT", "OBJECT", "TARGET", "SUBJECT")
    ):
        if classified == "omitted_referent":
            return classified
        return "unspecified" if code.startswith("EXPLICIT_") else None
    if classified is not None:
        return classified
    return "unspecified" if code.startswith("EXPLICIT_") else None


def _witness_material(value: Step11ParsedSurfaceWitness) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "body_sha256": value.body_sha256,
        "atoms": [
            {
                "atom_id": row.atom_id,
                "section_role": row.section_role,
                "form_id": row.form_id,
                "claim_kinds": list(row.claim_kinds),
                "source_slot_hints": list(row.source_slot_hints),
                "source_fragment_sha256": [
                    hashlib.sha256(item.encode("utf-8")).hexdigest()
                    for item in row.source_fragments
                ],
                "predicate_role": row.predicate_role,
                "realization_status": row.realization_status,
                "relation_type": row.relation_type,
                "relation_direction": row.relation_direction,
                "relation_endpoint_roles": list(row.relation_endpoint_roles),
                "unknown_dimension_class": row.unknown_dimension_class,
                "self_denial_not_fact": row.self_denial_not_fact,
                "reception_act": row.reception_act,
                "reception_scope": row.reception_scope,
                "byte_start": row.byte_start,
                "byte_end": row.byte_end,
                "introduced_reference": (
                    {
                        "reference_ordinal": (
                            row.introduced_reference.reference_ordinal
                        ),
                        "endpoint_role": (
                            row.introduced_reference.endpoint_role
                        ),
                    }
                    if row.introduced_reference is not None
                    else None
                ),
                "relation_endpoint_references": [
                    {
                        "reference_ordinal": item.reference_ordinal,
                        "endpoint_role": item.endpoint_role,
                    }
                    for item in row.relation_endpoint_references
                ],
                "unknown_target_references": [
                    {
                        "reference_ordinal": item.reference_ordinal,
                        "endpoint_role": item.endpoint_role,
                    }
                    for item in row.unknown_target_references
                ],
                "compound_label_references": [
                    {
                        "reference_ordinal": item.reference_ordinal,
                        "endpoint_role": item.endpoint_role,
                    }
                    for item in row.compound_label_references
                ],
                "reception_antecedent_references": [
                    {
                        "reference_ordinal": item.reference_ordinal,
                        "endpoint_role": item.endpoint_role,
                    }
                    for item in row.reception_antecedent_references
                ],
                "grounded_phrases": [
                    {
                        "phrase_text_sha256": hashlib.sha256(
                            phrase.phrase_text.encode("utf-8")
                        ).hexdigest(),
                        "visible_feature_fields": [
                            list(field)
                            for field in phrase.visible_feature_fields
                        ],
                        "visible_feature_fingerprint_sha256": (
                            phrase.visible_feature_fingerprint_sha256
                        ),
                        "phrase_profile_id": phrase.phrase_profile_id,
                        "anchor_risk_rank": phrase.anchor_risk_rank,
                        "action_lifecycle": phrase.action_lifecycle,
                        "binding_family": phrase.binding_family,
                        "anchor_text_sha256": (
                            hashlib.sha256(
                                phrase.anchor_text.encode("utf-8")
                            ).hexdigest()
                            if phrase.anchor_text is not None
                            else None
                        ),
                        "byte_start": phrase.byte_start,
                        "byte_end": phrase.byte_end,
                        "anchor_byte_start": phrase.anchor_byte_start,
                        "anchor_byte_end": phrase.anchor_byte_end,
                    }
                    for phrase in row.grounded_phrases
                ],
                "grammatical_chunk_ordinal": row.grammatical_chunk_ordinal,
                "sentence_ordinal": row.sentence_ordinal,
                "clause_ordinal": row.clause_ordinal,
            }
            for row in value.atoms
        ],
        "sentences": [
            {
                "sentence_ordinal": row.sentence_ordinal,
                "section_role": row.section_role,
                "clause_atom_ids": list(row.clause_atom_ids),
                "byte_start": row.byte_start,
                "byte_end": row.byte_end,
                "grammatical_chunk_clause_counts": list(
                    row.grammatical_chunk_clause_counts
                ),
            }
            for row in value.sentences
        ],
        "observation_atom_count": value.observation_atom_count,
        "reception_atom_count": value.reception_atom_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _source_unknown_oracle_material(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return the canonical body-free material for the inverse oracle."""

    return {
        "schema_version": STEP11_SOURCE_UNKNOWN_ORACLE_SCHEMA,
        "rows": [dict(row) for row in rows],
    }


def _quote_projection(value: str) -> str:
    layout = STEP11_SURFACE_CATALOG["layout"]
    primary, alternate = layout["quote_pairs"]
    opening, closing = primary["open"], primary["close"]
    if opening not in value and closing not in value:
        return f"{opening}{value}{closing}"
    if alternate["open"] not in value and alternate["close"] not in value:
        return f"{alternate['open']}{value}{alternate['close']}"
    escaped = (
        value.replace("\\", "\\\\")
        .replace(opening, "\\" + opening)
        .replace(closing, "\\" + closing)
    )
    return f"{opening}{escaped}{closing}"


def _decode_quote_content(raw: str, *, primary_outer: bool) -> str:
    if not primary_outer:
        return raw
    primary, alternate = STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
    escaped_primary_present = any(
        "\\" + delimiter in raw
        for delimiter in (primary["open"], primary["close"])
    )
    if not escaped_primary_present:
        return raw
    if not any(
        delimiter in raw
        for delimiter in (alternate["open"], alternate["close"])
    ):
        raise Step11InverseSurfaceError("S11_PARSE_QUOTE_PAIR_NONCANONICAL")
    value: list[str] = []
    index = 0
    allowed = {"\\", primary["open"], primary["close"]}
    while index < len(raw):
        if raw[index] != "\\":
            value.append(raw[index])
            index += 1
            continue
        if index + 1 >= len(raw) or raw[index + 1] not in allowed:
            raise Step11InverseSurfaceError("S11_PARSE_QUOTE_ESCAPE_INVALID")
        value.append(raw[index + 1])
        index += 2
    return "".join(value)


def _scan_quoted(line: str) -> tuple[str, tuple[str, ...]]:
    pairs = STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
    if (
        type(pairs) is not list
        or len(pairs) != 2
        or any(
            type(row) is not dict
            or type(row.get("open")) is not str
            or type(row.get("close")) is not str
            or len(row["open"]) != 1
            or len(row["close"]) != 1
            for row in pairs
        )
    ):
        raise Step11InverseSurfaceError("S11_PARSE_QUOTE_CATALOG_INVALID")
    pair_by_open = {row["open"]: row for row in pairs}
    all_closings = {row["close"] for row in pairs}
    literal: list[str] = []
    fragments: list[str] = []
    index = 0
    while index < len(line):
        pair = pair_by_open.get(line[index])
        if pair is None:
            if line[index] in all_closings:
                raise Step11InverseSurfaceError("S11_PARSE_QUOTE_CLOSE_UNEXPECTED")
            literal.append(line[index])
            index += 1
            continue
        opening, closing = pair["open"], pair["close"]
        quote_start = index
        literal.append("\x00")
        index += 1
        raw: list[str] = []
        while index < len(line):
            char = line[index]
            if char == "\\" and opening == pairs[0]["open"]:
                if index + 1 >= len(line):
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_QUOTE_ESCAPE_INVALID"
                    )
                raw.extend((char, line[index + 1]))
                index += 2
                continue
            if char == opening:
                raise Step11InverseSurfaceError("S11_PARSE_QUOTE_ESCAPE_INVALID")
            if char == closing:
                index += 1
                break
            raw.append(char)
            index += 1
        else:
            raise Step11InverseSurfaceError("S11_PARSE_QUOTE_UNCLOSED")
        value = _decode_quote_content(
            "".join(raw), primary_outer=opening == pairs[0]["open"]
        )
        if not value:
            raise Step11InverseSurfaceError("S11_PARSE_EMPTY_FRAGMENT")
        if _quote_projection(value) != line[quote_start:index]:
            raise Step11InverseSurfaceError("S11_PARSE_QUOTE_PAIR_NONCANONICAL")
        fragments.append(value)
    return "".join(literal), tuple(fragments)


_GROUNDED_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
_GROUNDED_FEATURE_ORDER = (
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


def _grounded_lexicalization_contract() -> dict[str, Any]:
    grammar = STEP11_SURFACE_CATALOG.get("grounded_lexicalization")
    if (
        type(grammar) is not dict
        or grammar.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_grounded_lexicalization.rc0027.v2"
        or tuple(grammar.get("feature_order", ()))
        != _GROUNDED_FEATURE_ORDER
        or grammar.get("concatenation")
        != "ordered_attributive_atoms_without_separator"
        or type(grammar.get("feature_tokens")) is not dict
        or type(grammar.get("source_anchor_open")) is not str
        or type(grammar.get("source_anchor_close")) is not str
        or type(grammar.get("source_anchor_binding_families")) is not dict
        or type(grammar.get("maximum_source_anchor_scalars")) is not int
        or type(grammar.get("phrase_profile_registry")) is not dict
        or type(grammar.get("lifecycle_authority_policy")) is not dict
        or type(grammar.get("anchor_segment_policy")) is not dict
        or type(grammar.get("residual_information_loss_policy")) is not dict
        or type(grammar.get("anchor_owner_priority_policy")) is not dict
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )
    feature_tokens = grammar["feature_tokens"]
    normalised: dict[str, dict[str, str]] = {}
    for field_name in _GROUNDED_FEATURE_ORDER:
        rows = feature_tokens.get(field_name)
        if (
            type(rows) is not dict
            or not rows
            or any(
                type(value) is not str
                or not value
                or type(token) is not str
                for value, token in rows.items()
            )
        ):
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
            )
        visible_tokens = [token for token in rows.values() if token]
        if len(visible_tokens) != len(set(visible_tokens)):
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_FEATURE_TOKEN_NONINJECTIVE"
            )
        normalised[field_name] = dict(rows)
    if not all(normalised["nucleus_kind"].values()):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_FEATURE_HEAD_INVALID"
        )
    binding_families = grammar["source_anchor_binding_families"]
    if (
        binding_families
        != {
            "reported_profile": "に表れている",
            "action_lifecycle": "として示された",
            "relation_shift": "を起点にした",
        }
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_ANCHOR_FAMILY_CATALOG_INVALID"
        )
    registry = grammar["phrase_profile_registry"]
    rows = registry.get("profiles")
    specificity_policy = registry.get("specificity_policy")
    if (
        registry.get("selection")
        != "first_exact_matching_profile_by_priority"
        or registry.get("visible_feature_reconstruction")
        != "singleton_from_profile_match_or_lifecycle_projection"
        or registry.get("completed_sentence_bank") is not False
        or type(specificity_policy) is not dict
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_PROFILE_RECONSTRUCTION_POLICY_INVALID"
        )
    allowed_match_keys = {
        "semantic_roles",
        "temporal_scopes",
        "nucleus_kinds",
        "modalities",
        "source_fields",
        "referent_scopes",
        "polarities",
        "label_strengths",
        "semantic_qualifiers",
        "lifecycles",
        "all_attribute_codes",
        "any_attribute_codes",
    }
    profiles: list[_Step11GroundedProfileContract] = []
    if type(rows) is not list or not rows:
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_PROFILE_REGISTRY_INVALID"
        )
    for row in rows:
        if type(row) is not dict:
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_PROFILE_REGISTRY_INVALID"
            )
        match = row.get("match")
        visible_names = row.get("visible_feature_names")
        declared_values = row.get("visible_feature_values", {})
        if (
            set(row)
            != {
                "profile_id",
                "match",
                "noun_phrase",
                "visible_feature_names",
                "anchor_risk_rank",
                "binding_family",
            }
            or
            type(row.get("profile_id")) is not str
            or not row["profile_id"]
            or type(match) is not dict
            or bool(set(match) - allowed_match_keys)
            or type(row.get("noun_phrase")) is not str
            or not row["noun_phrase"]
            or type(visible_names) is not list
            or not visible_names
            or any(
                type(name) is not str or name not in _GROUNDED_FEATURE_ORDER
                for name in visible_names
            )
            or len(visible_names) != len(set(visible_names))
            or type(declared_values) is not dict
            or any(
                type(name) is not str
                or name not in _GROUNDED_FEATURE_ORDER
                or name not in visible_names
                or type(value) is not str
                or value not in normalised[name]
                for name, value in declared_values.items()
            )
            or type(row.get("anchor_risk_rank")) is not int
            or type(row.get("anchor_risk_rank")) is bool
            or row["anchor_risk_rank"] < 0
            or row.get("binding_family") not in binding_families
        ):
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_PROFILE_REGISTRY_INVALID"
            )
        normalised_match: dict[str, tuple[str, ...]] = {}
        for name, values in match.items():
            if (
                type(values) is not list
                or any(type(value) is not str or not value for value in values)
                or len(values) != len(set(values))
                or (
                    name
                    not in {"all_attribute_codes", "any_attribute_codes"}
                    and not values
                )
            ):
                raise Step11InverseSurfaceError(
                    "S11_PARSE_GROUNDED_PROFILE_REGISTRY_INVALID"
                )
            normalised_match[name] = tuple(values)
        relation_shift_profile = (
            row.get("binding_family") == "relation_shift"
        )
        exact_shift_condition = "operator:shift" in normalised_match.get(
            "all_attribute_codes", ()
        )
        if relation_shift_profile != exact_shift_condition:
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_PROFILE_BINDING_FAMILY_INVALID"
            )
        profiles.append(
            _Step11GroundedProfileContract(
                profile_id=row["profile_id"],
                noun_phrase=row["noun_phrase"],
                visible_feature_names=tuple(visible_names),
                anchor_risk_rank=row["anchor_risk_rank"],
                binding_family=row["binding_family"],
                match=normalised_match,
                visible_feature_values=dict(declared_values),
            )
        )
    if (
        len({row.profile_id for row in profiles}) != len(profiles)
        or len({row.noun_phrase for row in profiles}) != len(profiles)
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_PROFILE_REGISTRY_NONINJECTIVE"
        )
    if (
        tuple(specificity_policy.get("kind_only_generic_profile_ids", ()))
        != _GROUNDED_KIND_ONLY_GENERIC_PROFILE_IDS
        or specificity_policy.get(
            "unanchored_required_kind_only_generic"
        )
        != "fail_closed"
        or not set(_GROUNDED_KIND_ONLY_GENERIC_PROFILE_IDS)
        <= {row.profile_id for row in profiles}
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_PROFILE_SPECIFICITY_POLICY_INVALID"
        )
    residual_policy = grammar["residual_information_loss_policy"]
    if (
        tuple(residual_policy.get("semantic_attribute_prefixes", ()))
        != _GROUNDED_RESIDUAL_SEMANTIC_PREFIXES
        or tuple(residual_policy.get("high_signal_attribute_codes", ()))
        != _GROUNDED_RESIDUAL_HIGH_SIGNAL_CODES
        or residual_policy.get("concrete_action_attribute_code")
        != "semantic_role:concrete_action_evidence"
        or residual_policy.get("kind_implied_attribute_codes")
        != {
            "action": [
                "operator:action",
                "semantic_role:concrete_action_evidence",
            ]
        }
        or tuple(residual_policy.get("ordered_factors", ()))
        != _GROUNDED_RESIDUAL_ORDERED_FACTORS
        or residual_policy.get("dynamic_score_in_visible_fingerprint")
        is not False
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_RESIDUAL_INFORMATION_POLICY_INVALID"
        )
    owner_policy = grammar["anchor_owner_priority_policy"]
    if (
        tuple(owner_policy.get("ordered_classes", ()))
        != (
            "residual_information_loss_risk",
            "remaining_render_reachable",
        )
        or tuple(owner_policy.get("within_class_order", ()))
        != (
            "anchor_risk_rank_desc",
            "source_snapshot_order",
            "nucleus_id",
        )
        or owner_policy.get("selector_score_dependency") is not False
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_ANCHOR_OWNER_POLICY_INVALID"
        )
    lifecycle_policy = grammar["lifecycle_authority_policy"]
    action_projection = lifecycle_policy.get("action_projection")
    if (
        type(action_projection) is not dict
        or set(action_projection)
        != {
            "reported_completed",
            "reported_ongoing",
            "reported_not_completed",
            "intended",
        }
        or any(
            type(value) is not dict
            or set(value) != {"modality", "temporal_scope"}
            or value["modality"] not in normalised["modality"]
            or value["temporal_scope"] not in normalised["temporal_scope"]
            for value in action_projection.values()
        )
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LIFECYCLE_CATALOG_INVALID"
        )
    anchor_policy = grammar["anchor_segment_policy"]
    if (
        anchor_policy.get("minimum_scalars") != 2
        or anchor_policy.get("maximum_scalars")
        != grammar["maximum_source_anchor_scalars"]
        or anchor_policy.get("unicode_category_c_forbidden") is not True
        or anchor_policy.get("mechanical_prefix_truncation") is not False
        or anchor_policy.get("complete_run_first") is not True
        or tuple(anchor_policy.get("accepted_segment_authorities", ()))
        != _GROUNDED_ANCHOR_SEGMENT_AUTHORITIES
        or anchor_policy.get("long_run_subrange_authority") != "forbidden"
        or anchor_policy.get("whitespace_or_control_disposition")
        != "fail_closed"
        or anchor_policy.get("unsafe_result") != "fail_closed"
        or "clause_boundary_tokens" in anchor_policy
        or "safe_subrange_terminal_suffixes" in anchor_policy
        or tuple(anchor_policy.get("dangling_prefixes", ()))
        != _GROUNDED_ANCHOR_DANGLING_PREFIXES
        or tuple(anchor_policy.get("dangling_suffixes", ()))
        != _GROUNDED_ANCHOR_DANGLING_SUFFIXES
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_ANCHOR_POLICY_INVALID"
        )
    for profile in profiles:
        if _grounded_profile_reconstructed_values(
            profile,
            feature_tokens=normalised,
            action_projection=action_projection,
            explicit_values={},
        ) is None:
            raise Step11InverseSurfaceError(
                "S11_PARSE_GROUNDED_PROFILE_VISIBLE_NONINJECTIVE"
            )
    return {
        "feature_tokens": normalised,
        "source_anchor_open": grammar["source_anchor_open"],
        "source_anchor_close": grammar["source_anchor_close"],
        "source_anchor_binding_families": dict(binding_families),
        "maximum_source_anchor_scalars": grammar[
            "maximum_source_anchor_scalars"
        ],
        "profiles": tuple(profiles),
        "kind_only_generic_profile_ids": frozenset(
            _GROUNDED_KIND_ONLY_GENERIC_PROFILE_IDS
        ),
        "residual_information_loss_policy": {
            "semantic_attribute_prefixes": (
                _GROUNDED_RESIDUAL_SEMANTIC_PREFIXES
            ),
            "high_signal_attribute_codes": frozenset(
                _GROUNDED_RESIDUAL_HIGH_SIGNAL_CODES
            ),
            "concrete_action_attribute_code": (
                "semantic_role:concrete_action_evidence"
            ),
            "kind_implied_attribute_codes": {
                "action": frozenset(
                    {
                        "operator:action",
                        "semantic_role:concrete_action_evidence",
                    }
                )
            },
        },
        "action_projection": {
            name: dict(value) for name, value in action_projection.items()
        },
    }


def _grounded_profile_reconstructed_values(
    profile: _Step11GroundedProfileContract,
    *,
    feature_tokens: Mapping[str, Mapping[str, str]],
    action_projection: Mapping[str, Mapping[str, str]],
    explicit_values: Mapping[str, str],
) -> dict[str, str] | None:
    """Recover the exact visible values encoded by one registry profile."""

    condition_to_field = {
        "semantic_roles": "semantic_role",
        "temporal_scopes": "temporal_scope",
        "nucleus_kinds": "nucleus_kind",
        "modalities": "modality",
        "source_fields": "source_field",
        "referent_scopes": "referent_scope",
        "polarities": "polarity",
        "label_strengths": "label_strength",
        "semantic_qualifiers": "semantic_qualifier",
        "lifecycles": "action_lifecycle",
    }
    values = dict(profile.visible_feature_values)
    for field_name, value in explicit_values.items():
        previous = values.setdefault(field_name, value)
        if previous != value:
            return None
    selected_names = set(_GROUNDED_BASE_FEATURES) | set(
        profile.visible_feature_names
    ) | set(explicit_values)
    for condition, field_name in condition_to_field.items():
        options = profile.match.get(condition, ())
        if field_name not in selected_names and field_name != "action_lifecycle":
            continue
        if len(options) > 1:
            return None
        if len(options) == 1:
            previous = values.setdefault(field_name, options[0])
            if previous != options[0]:
                return None
    attribute_codes = frozenset(
        (
            *profile.match.get("all_attribute_codes", ()),
            *profile.match.get("any_attribute_codes", ()),
        )
    )
    if "operator:negation" in attribute_codes:
        values.setdefault("polarity", "negative")
    unit_roles = tuple(
        code.removeprefix("unit_role:")
        for code in attribute_codes
        if code in {"unit_role:antecedent", "unit_role:consequent"}
    )
    if len(set(unit_roles)) > 1:
        return None
    if unit_roles:
        values.setdefault("semantic_role", unit_roles[0])
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
            values.setdefault(
                "semantic_qualifier", f"source_semantic_role:{key}"
            )
            break
    if "semantic_qualifier" not in values:
        for key in ("constraint", "continuation", "shift", "action", "wish"):
            if f"operator:{key}" in attribute_codes:
                values["semantic_qualifier"] = f"source_operator:{key}"
                break
    lifecycle = values.get("action_lifecycle")
    if lifecycle in action_projection:
        for field_name, value in action_projection[lifecycle].items():
            previous = values.setdefault(field_name, value)
            if previous != value:
                return None
    if (
        values.get("nucleus_kind") is not None
        and values["nucleus_kind"] != "action"
    ):
        previous = values.setdefault(
            "action_lifecycle", "not_applicable"
        )
        if previous != "not_applicable":
            return None
    for field_name in selected_names:
        if field_name not in values:
            return None
    return values


def _grounded_phrase_prefixes(
    text: str, start: int
) -> tuple[tuple[Step11ParsedGroundedPhrase, int], ...]:
    """Parse every closed-grammar phrase beginning at one character offset."""

    contract = _grounded_lexicalization_contract()
    feature_tokens = contract["feature_tokens"]
    anchor_open = contract["source_anchor_open"]
    anchor_close = contract["source_anchor_close"]
    binding_families = contract["source_anchor_binding_families"]
    maximum_anchor_scalars = contract["maximum_source_anchor_scalars"]
    phrase_start = start
    binding_family: str | None = None
    anchor_text: str | None = None
    anchor_start: int | None = None
    anchor_end: int | None = None
    if text.startswith(anchor_open, start):
        close_index = text.find(anchor_close, start + len(anchor_open))
        if close_index < 0:
            return ()
        binding_start = close_index + len(anchor_close)
        family_matches = tuple(
            (family, binding)
            for family, binding in binding_families.items()
            if text.startswith(binding, binding_start)
        )
        if len(family_matches) != 1:
            return ()
        binding_family, anchor_binding = family_matches[0]
        anchor_start = start + len(anchor_open)
        anchor_end = close_index
        anchor_text = text[anchor_start:anchor_end]
        if not _step11_inverse_visible_anchor_text_safe(
            anchor_text, maximum_anchor_scalars
        ):
            return ()
        phrase_start = binding_start + len(anchor_binding)

    results: list[tuple[Step11ParsedGroundedPhrase, int]] = []

    for profile in contract["profiles"]:
        eligible_collision_fields = tuple(
            field_name
            for field_name in _GROUNDED_COLLISION_FEATURES
            if field_name not in profile.visible_feature_names
        )

        def visit_collision(
            field_ordinal: int,
            cursor: int,
            explicit_values: dict[str, str],
        ) -> None:
            if field_ordinal < len(eligible_collision_fields):
                field_name = eligible_collision_fields[field_ordinal]
                visit_collision(
                    field_ordinal + 1, cursor, dict(explicit_values)
                )
                for feature_value, token in feature_tokens[field_name].items():
                    if token and text.startswith(token, cursor):
                        visit_collision(
                            field_ordinal + 1,
                            cursor + len(token),
                            {**explicit_values, field_name: feature_value},
                        )
                return
            if not text.startswith(profile.noun_phrase, cursor):
                return
            phrase_end = cursor + len(profile.noun_phrase)
            values = _grounded_profile_reconstructed_values(
                profile,
                feature_tokens=feature_tokens,
                action_projection=contract["action_projection"],
                explicit_values=explicit_values,
            )
            if values is None:
                return
            selected_names = (
                set(_GROUNDED_BASE_FEATURES)
                | set(profile.visible_feature_names)
                | set(explicit_values)
            )
            fields = tuple(
                (field_name, values[field_name])
                for field_name in _GROUNDED_FEATURE_ORDER
                if field_name in selected_names
                and feature_tokens[field_name][values[field_name]]
            )
            if not fields or fields[-1][0] != "nucleus_kind":
                return
            phrase_text = text[phrase_start:phrase_end]
            fingerprint = artifact_sha256(
                {
                    "visible_feature_fields": [
                        list(row) for row in fields
                    ],
                    "phrase_profile_id": profile.profile_id,
                }
            )
            results.append(
                (
                    Step11ParsedGroundedPhrase(
                        phrase_text=phrase_text,
                        visible_feature_fields=fields,
                        visible_feature_fingerprint_sha256=fingerprint,
                        phrase_profile_id=profile.profile_id,
                        anchor_risk_rank=profile.anchor_risk_rank,
                        action_lifecycle=values["action_lifecycle"],
                        binding_family=binding_family,
                        anchor_text=anchor_text,
                        byte_start=len(
                            text[:phrase_start].encode("utf-8")
                        ),
                        byte_end=len(text[:phrase_end].encode("utf-8")),
                        anchor_byte_start=(
                            len(text[:anchor_start].encode("utf-8"))
                            if anchor_start is not None
                            else None
                        ),
                        anchor_byte_end=(
                            len(text[:anchor_end].encode("utf-8"))
                            if anchor_end is not None
                            else None
                        ),
                    ),
                    phrase_end,
                )
            )
        visit_collision(0, phrase_start, {})
    return tuple(dict.fromkeys(results))


def _match_grounded_template(
    text: str, template: str
) -> tuple[tuple[Step11ParsedGroundedPhrase, ...], ...]:
    """Match one catalog template and recover its phrase placeholders."""

    if type(template) is not str:
        return ()
    pieces: list[tuple[str, str]] = []
    cursor = 0
    placeholder_names: set[str] = set()
    for match in _GROUNDED_PLACEHOLDER_RE.finditer(template):
        if match.start() > cursor:
            pieces.append(("literal", template[cursor : match.start()]))
        name = match.group(1)
        if name in placeholder_names:
            return ()
        placeholder_names.add(name)
        pieces.append(("phrase", name))
        cursor = match.end()
    if cursor < len(template):
        pieces.append(("literal", template[cursor:]))
    if not placeholder_names:
        return ()
    matches: list[tuple[Step11ParsedGroundedPhrase, ...]] = []

    def visit(
        piece_ordinal: int,
        text_cursor: int,
        phrases: tuple[Step11ParsedGroundedPhrase, ...],
    ) -> None:
        if piece_ordinal == len(pieces):
            if text_cursor == len(text):
                matches.append(phrases)
            return
        kind, value = pieces[piece_ordinal]
        if kind == "literal":
            if text.startswith(value, text_cursor):
                visit(
                    piece_ordinal + 1,
                    text_cursor + len(value),
                    phrases,
                )
            return
        for phrase, phrase_end in _grounded_phrase_prefixes(
            text, text_cursor
        ):
            visit(piece_ordinal + 1, phrase_end, (*phrases, phrase))

    visit(0, 0, ())
    return tuple(dict.fromkeys(matches))


def _catalog_clause_stem(value: str) -> str:
    suffix = STEP11_SURFACE_CATALOG["group_grammar"]["sentence_suffix"]
    return value[: -len(suffix)] if value.endswith(suffix) else value


def _split_group_clauses(
    line: str,
) -> tuple[tuple[str, int, int, int], ...]:
    """Split one sentence-group line outside canonical source quotes."""

    grammar = STEP11_SURFACE_CATALOG.get("group_grammar")
    if type(grammar) is not dict:
        raise Step11InverseSurfaceError("S11_PARSE_GROUP_CATALOG_INVALID")
    separator = grammar.get("clause_separator")
    chunk_separator = grammar.get("grammatical_chunk_separator")
    suffix = grammar.get("sentence_suffix")
    if (
        type(separator) is not str
        or not separator
        or type(chunk_separator) is not str
        or not chunk_separator
        or type(suffix) is not str
        or not suffix
        or not line.endswith(suffix)
    ):
        raise Step11InverseSurfaceError("S11_PARSE_GROUP_SENTENCE_INVALID")
    stem_end = len(line) - len(suffix)
    if stem_end <= 0:
        raise Step11InverseSurfaceError("S11_PARSE_GROUP_SENTENCE_INVALID")
    pairs = STEP11_SURFACE_CATALOG["layout"].get("quote_pairs")
    if type(pairs) is not list or len(pairs) != 2:
        raise Step11InverseSurfaceError("S11_PARSE_QUOTE_CATALOG_INVALID")
    pair_by_open = {str(row["open"]): row for row in pairs}
    active_pair: Mapping[str, str] | None = None
    clauses: list[tuple[str, int, int, int]] = []
    clause_start = 0
    grammatical_chunk_ordinal = 1
    index = 0
    while index < stem_end:
        char = line[index]
        if active_pair is not None:
            if (
                char == "\\"
                and active_pair["open"] == pairs[0]["open"]
            ):
                if index + 1 >= stem_end:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_QUOTE_ESCAPE_INVALID"
                    )
                index += 2
                continue
            if char == active_pair["close"]:
                active_pair = None
            index += 1
            continue
        opening = pair_by_open.get(char)
        if opening is not None:
            active_pair = opening
            index += 1
            continue
        matched_separator = next(
            (
                value
                for value in (separator, chunk_separator)
                if line.startswith(value, index)
            ),
            None,
        )
        if matched_separator is not None:
            if index <= clause_start:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_GROUP_CLAUSE_EMPTY"
                )
            clauses.append(
                (
                    line[clause_start:index],
                    clause_start,
                    index,
                    grammatical_chunk_ordinal,
                )
            )
            index += len(matched_separator)
            clause_start = index
            if matched_separator == chunk_separator:
                grammatical_chunk_ordinal += 1
            continue
        index += 1
    if active_pair is not None:
        raise Step11InverseSurfaceError("S11_PARSE_QUOTE_UNCLOSED")
    if clause_start >= stem_end:
        raise Step11InverseSurfaceError("S11_PARSE_GROUP_CLAUSE_EMPTY")
    clauses.append(
        (
            line[clause_start:stem_end],
            clause_start,
            stem_end,
            grammatical_chunk_ordinal,
        )
    )
    return tuple(clauses)


def _natural_introduction_clause(
    clause: str,
) -> tuple[str, str, str, tuple[str, ...]] | None:
    skeleton, fragments = _scan_quoted(clause)
    if len(fragments) != 1:
        return None
    grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    natural = grammar.get("natural_introduction")
    forms = natural.get("forms") if type(natural) is dict else None
    if type(forms) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_REFERENCE_INTRODUCTION_CATALOG_INVALID"
        )
    matches: list[tuple[str, str, str]] = []
    for source_slot, by_role in forms.items():
        if type(source_slot) is not str or type(by_role) is not dict:
            raise Step11InverseSurfaceError(
                "S11_PARSE_REFERENCE_INTRODUCTION_CATALOG_INVALID"
            )
        for role, stems in by_role.items():
            if type(role) is not str or type(stems) is not list:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_REFERENCE_INTRODUCTION_CATALOG_INVALID"
                )
            for index, stem in enumerate(stems):
                if type(stem) is not str:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_REFERENCE_INTRODUCTION_CATALOG_INVALID"
                    )
                expected = stem.format(quoted_literal="\x00")
                if skeleton == expected:
                    matches.append(
                        (
                            (
                                "reference_introduction:natural:"
                                f"{source_slot}:{role}:{index}"
                            ),
                            source_slot,
                            role,
                        )
                    )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_REFERENCE_INTRODUCTION_AMBIGUOUS"
        )
    form_id, source_slot, endpoint_role = matches[0]
    return form_id, source_slot, endpoint_role, fragments


def _fused_observation_clause(
    clause: str,
) -> _Step11FusedObservationParse | None:
    """Parse one rc0027 literal-owning obligation unit.

    This inverse compiler uses only the declarative fused catalog.  Endpoint
    roles and source owners are deliberately not inferred from the chosen
    wording: the semantic matcher recomputes those from the current input and
    the active relation/unknown obligations.
    """

    grammar = STEP11_SURFACE_CATALOG.get("obligation_fused_grammar")
    if type(grammar) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    lexical_for_anchor = STEP11_SURFACE_CATALOG.get(
        "grounded_lexicalization", {}
    )
    if (
        type(lexical_for_anchor) is not dict
        or lexical_for_anchor.get("forward_emission") is not True
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )
    anchor_open = lexical_for_anchor.get("source_anchor_open")
    anchor_close = lexical_for_anchor.get("source_anchor_close")
    anchor_bindings = lexical_for_anchor.get(
        "source_anchor_binding_families"
    )
    if (
        type(anchor_open) is str
        and anchor_open
        and type(anchor_close) is str
        and anchor_close
        and type(anchor_bindings) is dict
        and anchor_bindings
        and all(type(value) is str and value for value in anchor_bindings.values())
    ):
        binding_alternation = "|".join(
            re.escape(value)
            for value in sorted(
                anchor_bindings.values(), key=len, reverse=True
            )
        )
        anchor_pattern = re.compile(
            re.escape(anchor_open)
            + r"[^" + re.escape(anchor_close) + r"]+"
            + re.escape(anchor_close)
            + "(?:" + binding_alternation + ")"
        )
        typed_anchor_rows = tuple(anchor_pattern.finditer(clause))
    else:
        typed_anchor_rows = ()
    if len(typed_anchor_rows) > 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_VISIBLE_SOURCE_ANCHOR_COUNT_INVALID"
        )
    if typed_anchor_rows:
        # The grounded anchor uses its own fixed quote pair.  Mask only those
        # two delimiters while the legacy literal scanner runs; the closed
        # grounded parser below validates and restores the typed anchor.
        row = typed_anchor_rows[0]
        matched_bindings = tuple(
            value
            for value in anchor_bindings.values()
            if row.group(0).endswith(value)
        )
        if len(matched_bindings) != 1:
            raise Step11InverseSurfaceError(
                "S11_PARSE_VISIBLE_SOURCE_ANCHOR_FAMILY_INVALID"
            )
        anchor_binding = matched_bindings[0]
        masked_anchor = (
            "‹"
            + clause[
                row.start() + len(anchor_open) :
                row.end() - len(anchor_close + anchor_binding)
            ]
            + "›"
            + anchor_binding
        )
        masked_clause = (
            clause[: row.start()]
            + masked_anchor
            + clause[row.end() :]
        )
        skeleton, fragments = _scan_quoted(masked_clause)
    else:
        skeleton, fragments = _scan_quoted(clause)

    unknown_tails = grammar.get("unknown_tails")
    if type(unknown_tails) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    grounded_unknown_atoms = lexical_for_anchor.get(
        "unknown_dimension_atoms"
    )
    grounded_unknown_predicate = lexical_for_anchor.get(
        "unknown_predicate"
    )
    if (
        type(grounded_unknown_atoms) is not dict
        or type(grounded_unknown_predicate) is not str
        or not grounded_unknown_predicate
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )
    combined_unknown_tails = {
        dimension: tuple(
            dict.fromkeys(
                (
                    *rows,
                    "ただ、"
                    + str(grounded_unknown_atoms.get(dimension, ""))
                    + grounded_unknown_predicate,
                )
            )
        )
        for dimension, rows in unknown_tails.items()
    }
    unknown_matches: list[_Step11FusedObservationParse] = []
    for dimension, rows in combined_unknown_tails.items():
        if type(dimension) is not str or type(rows) not in {list, tuple}:
            raise Step11InverseSurfaceError(
                "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
            )
        for index, tail in enumerate(rows):
            if type(tail) is not str or not tail.startswith("ただ、"):
                raise Step11InverseSurfaceError(
                    "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                )
            suffix = "が、" + tail.removeprefix("ただ、")
            if not clause.endswith(suffix):
                continue
            owner_clause = clause[: -len(suffix)]
            owner = _fused_observation_clause(owner_clause)
            if owner is None:
                owner_skeleton, owner_fragments = _scan_quoted(
                    owner_clause
                )
                owner_row = _observation_patterns().get(owner_skeleton)
                if owner_row is not None:
                    (
                        owner_form_id,
                        owner_claims,
                        owner_hints,
                        owner_relation_type,
                        owner_direction,
                        owner_unknown,
                        owner_denial,
                        owner_endpoint_roles,
                    ) = owner_row
                    owner_predicate, owner_status = (
                        _parsed_semantic_signature(
                            owner_form_id,
                            owner_hints,
                            section_role="observation",
                            reception_scope=None,
                        )
                    )
                    owner = _Step11FusedObservationParse(
                        form_id=owner_form_id,
                        claim_kinds=owner_claims,
                        source_slot_hints=owner_hints,
                        source_fragments=owner_fragments,
                        predicate_role=owner_predicate,
                        realization_status=owner_status,
                        relation_type=owner_relation_type,
                        relation_direction=owner_direction,
                        relation_endpoint_roles=owner_endpoint_roles,
                        unknown_dimension_class=owner_unknown,
                        self_denial_not_fact=owner_denial,
                    )
            if (
                owner is None
                or "nucleus_notice" not in owner.claim_kinds
                or (
                    "unknown_boundary" in owner.claim_kinds
                    and owner.unknown_dimension_class != dimension
                )
            ):
                continue
            unknown_matches.append(
                _Step11FusedObservationParse(
                    form_id=(
                        f"{owner.form_id}:unknown_fused:"
                        f"{dimension}:{index}"
                    ),
                    claim_kinds=(
                        *owner.claim_kinds,
                        *(
                            ()
                            if "unknown_boundary" in owner.claim_kinds
                            else ("unknown_boundary",)
                        ),
                    ),
                    source_slot_hints=owner.source_slot_hints,
                    source_fragments=owner.source_fragments,
                    predicate_role=owner.predicate_role,
                    realization_status=owner.realization_status,
                    relation_type=owner.relation_type,
                    relation_direction=owner.relation_direction,
                    relation_endpoint_roles=(
                        owner.relation_endpoint_roles
                    ),
                    unknown_dimension_class=dimension,
                    self_denial_not_fact=(
                        owner.self_denial_not_fact
                    ),
                    grounded_phrases=owner.grounded_phrases,
                )
            )
    unique_unknowns = tuple(dict.fromkeys(unknown_matches))
    if len(unique_unknowns) > 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_UNKNOWN_AMBIGUOUS"
        )
    if unique_unknowns:
        return unique_unknowns[0]

    matches: list[_Step11FusedObservationParse] = []

    def grounded_source_fragments(
        phrases: Sequence[Step11ParsedGroundedPhrase],
    ) -> tuple[str, ...]:
        return tuple(
            phrase.anchor_text
            for phrase in phrases
            if phrase.anchor_text is not None
        )

    # rc0027's public surface is compiled from the grounded lexical grammar,
    # not from the historical literal templates below.  Keep this inverse
    # compiler catalog-driven: it recognizes only the closed predicates and
    # relation atoms, while source ownership is resolved later from the
    # parsed feature tuples and the independently rebuilt source snapshot.
    lexical = STEP11_SURFACE_CATALOG.get("grounded_lexicalization")
    if type(lexical) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )
    observation_predicate = lexical.get("observation_predicate")
    coexisting_joiner = lexical.get("coexisting_joiner")
    coexisting_predicate = lexical.get("coexisting_predicate")
    relation_atoms = lexical.get("relation_atoms")
    if (
        type(observation_predicate) is not str
        or not observation_predicate
        or type(coexisting_joiner) is not str
        or not coexisting_joiner
        or type(coexisting_predicate) is not str
        or not coexisting_predicate
        or type(relation_atoms) is not dict
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )

    for phrases in _match_grounded_template(
        clause, "{grounded}" + observation_predicate
    ):
        if len(phrases) != 1:
            continue
        matches.append(
            _Step11FusedObservationParse(
                form_id="obligation_fused:grounded_standalone:0",
                claim_kinds=("nucleus_notice",),
                source_slot_hints=(),
                source_fragments=grounded_source_fragments(phrases),
                predicate_role="source_context",
                realization_status="undetermined",
                grounded_phrases=phrases,
            )
        )

    for phrases in _match_grounded_template(
        clause,
        (
            "{first_grounded}"
            + coexisting_joiner
            + "{second_grounded}"
            + coexisting_predicate
        ),
    ):
        if len(phrases) != 2:
            continue
        kinds = tuple(
            dict(phrase.visible_feature_fields).get("nucleus_kind")
            for phrase in phrases
        )
        mixed_reaction = kinds == ("reaction", "reaction")
        matches.append(
            _Step11FusedObservationParse(
                form_id="obligation_fused:grounded_coexisting:0",
                claim_kinds=(
                    "nucleus_notice",
                    *(("mixed_emotion_relation",) if mixed_reaction else ()),
                ),
                source_slot_hints=(),
                source_fragments=grounded_source_fragments(phrases),
                predicate_role=("affect" if mixed_reaction else "source_context"),
                realization_status=(
                    "selected_label" if mixed_reaction else "undetermined"
                ),
                relation_type=("coexists_with" if mixed_reaction else None),
                relation_direction=("bidirectional" if mixed_reaction else None),
                relation_endpoint_roles=(
                    ("affect", "affect") if mixed_reaction else ()
                ),
                grounded_phrases=phrases,
            )
        )

    if any(
        type(relation_type) is not str or type(directions) is not dict
        for relation_type, directions in relation_atoms.items()
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
        )
    grounded_relation_matches: list[_Step11FusedObservationParse] = []
    local_anaphors_for_grounded = lexical.get("local_anaphors")
    if type(local_anaphors_for_grounded) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    for relation_type, directions in relation_atoms.items():
        for direction, rule in directions.items():
            if (
                type(direction) is not str
                or type(rule) is not dict
                or set(rule) != {"endpoint_order", "left", "right"}
                or rule.get("endpoint_order")
                not in (["from", "to"], ["to", "from"])
                or type(rule.get("left")) is not str
                or type(rule.get("right")) is not str
            ):
                raise Step11InverseSurfaceError(
                    "S11_PARSE_GROUNDED_LEXICALIZATION_CATALOG_INVALID"
                )
            first, second = rule["endpoint_order"]
            template = (
                "{" + first + "_endpoint}"
                + rule["left"]
                + "{" + second + "_endpoint}"
                + rule["right"]
            )
            for phrases in _match_grounded_template(clause, template):
                if len(phrases) != 2:
                    continue
                grounded_relation_matches.append(
                    _Step11FusedObservationParse(
                        form_id=(
                            "obligation_fused:relation:"
                            f"{relation_type}:{direction}:0"
                        ),
                        claim_kinds=("nucleus_notice", "relation_notice"),
                        source_slot_hints=(),
                        source_fragments=grounded_source_fragments(phrases),
                        predicate_role="relation",
                        realization_status="undetermined",
                        relation_type=relation_type,
                        relation_direction=direction,
                        grounded_phrases=phrases,
                    )
                )
            for local_endpoint in ("from", "to"):
                local_position = (
                    0 if first == local_endpoint else 1
                )
                exact_position = 1 - local_position
                for local_role, raw_anaphor_rows in (
                    local_anaphors_for_grounded.items()
                ):
                    anaphor_rows = (
                        (raw_anaphor_rows,)
                        if type(raw_anaphor_rows) is str
                        else raw_anaphor_rows
                    )
                    if (
                        type(local_role) is not str
                        or type(anaphor_rows) not in {list, tuple}
                    ):
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                        )
                    for anaphor_index, anaphor in enumerate(anaphor_rows):
                        if type(anaphor) is not str or not anaphor:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                            )
                        endpoint_values = ["{exact_grounded}", "{exact_grounded}"]
                        endpoint_values[local_position] = anaphor
                        endpoint_values[exact_position] = "{exact_grounded}"
                        local_template = (
                            endpoint_values[0]
                            + rule["left"]
                            + endpoint_values[1]
                            + rule["right"]
                        )
                        for phrases in _match_grounded_template(
                            clause, local_template
                        ):
                            if len(phrases) != 1:
                                continue
                            grounded_relation_matches.append(
                                _Step11FusedObservationParse(
                                    form_id=(
                                        "obligation_fused:relation:"
                                        f"{relation_type}:{direction}:0:"
                                        f"local_{local_endpoint}:"
                                        f"{local_role}:{anaphor_index}"
                                    ),
                                    claim_kinds=(
                                        "nucleus_notice",
                                        "relation_notice",
                                    ),
                                    source_slot_hints=(),
                                    source_fragments=grounded_source_fragments(
                                        phrases
                                    ),
                                    predicate_role="relation",
                                    realization_status="undetermined",
                                    relation_type=relation_type,
                                    relation_direction=direction,
                                    grounded_phrases=phrases,
                                )
                            )
    matches.extend(grounded_relation_matches)

    # If the rc0027 grounded grammar recognized the clause, resolve it before
    # compiling any legacy rc0026 literal templates.  Some historical local
    # anaphors share the same Japanese bytes; mixing both grammar generations
    # would manufacture an ambiguity that is absent from the active catalog.
    grounded_unique = tuple(dict.fromkeys(matches))
    if grounded_unique:
        if len(grounded_unique) == 1:
            return grounded_unique[0]
        relation_rows = tuple(
            row
            for row in grounded_unique
            if row.form_id.startswith("obligation_fused:relation:")
        )

        def grounded_relation_head(
            row: _Step11FusedObservationParse,
        ) -> tuple[Any, ...]:
            parts = row.form_id.split(":")
            local = (
                tuple(parts[5:])
                if len(parts) >= 8 and parts[5].startswith("local_")
                else ()
            )
            if local:
                local = ("local_source_or_target", *local[1:])
            return (
                row.relation_type,
                parts[4] if len(parts) > 4 else "",
                local,
                tuple(
                    phrase.visible_feature_fingerprint_sha256
                    for phrase in row.grounded_phrases
                ),
            )

        if (
            len(relation_rows) == len(grounded_unique) == 2
            and len(
                {grounded_relation_head(row) for row in relation_rows}
            )
            == 1
            and {row.relation_direction for row in relation_rows}
            == {"source_to_target", "target_to_source"}
        ):
            row = relation_rows[0]
            parts = row.form_id.split(":")
            local_suffix = ""
            if len(parts) >= 8 and parts[5].startswith("local_"):
                local_suffix = (
                    ":local_source_or_target:"
                    f"{parts[6]}:{parts[7]}"
                )
            return _Step11FusedObservationParse(
                form_id=(
                    "obligation_fused:relation:"
                    f"{row.relation_type}:source_or_target:"
                    f"{parts[4]}{local_suffix}"
                ),
                claim_kinds=row.claim_kinds,
                source_slot_hints=row.source_slot_hints,
                source_fragments=row.source_fragments,
                predicate_role=row.predicate_role,
                realization_status=row.realization_status,
                relation_type=row.relation_type,
                relation_direction="source_or_target",
                relation_endpoint_roles=row.relation_endpoint_roles,
                grounded_phrases=row.grounded_phrases,
            )
        raise Step11InverseSurfaceError(
            "S11_PARSE_GROUNDED_OBSERVATION_AMBIGUOUS"
        )

    standalone = grammar.get("standalone_forms")
    if type(standalone) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if len(fragments) <= 1:
        for source_slot, rows in standalone.items():
            if type(source_slot) is not str or type(rows) is not list:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                )
            for index, template in enumerate(rows):
                if type(template) is not str:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                    )
                if skeleton != template.format(literal="\x00"):
                    grounded_matches = _match_grounded_template(
                        clause, template
                    )
                else:
                    grounded_matches = ()
                predicate_role = {
                    "action": "action",
                    "emotion": "affect",
                    "thought": "proposition",
                    "category": "proposition",
                }.get(source_slot)
                if predicate_role is None:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                    )
                if skeleton == template.format(literal="\x00"):
                    matches.append(
                        _Step11FusedObservationParse(
                            form_id=(
                                "obligation_fused:standalone:"
                                f"{source_slot}:{index}"
                            ),
                            claim_kinds=("nucleus_notice",),
                            source_slot_hints=(source_slot,),
                            source_fragments=fragments,
                            predicate_role=predicate_role,
                            realization_status=(
                                "selected_label"
                                if source_slot in {"emotion", "category"}
                                else "undetermined"
                            ),
                        )
                    )
                for grounded_phrases in grounded_matches:
                    if len(grounded_phrases) != 1:
                        continue
                    matches.append(
                        _Step11FusedObservationParse(
                            form_id=(
                                "obligation_fused:standalone:"
                                f"{source_slot}:{index}"
                            ),
                            claim_kinds=("nucleus_notice",),
                            source_slot_hints=(source_slot,),
                            source_fragments=grounded_source_fragments(
                                grounded_phrases
                            ),
                            predicate_role=predicate_role,
                            realization_status=(
                                "selected_label"
                                if source_slot in {"emotion", "category"}
                                else "undetermined"
                            ),
                            grounded_phrases=grounded_phrases,
                        )
                    )

    neutral_rows = grammar.get("neutral_pair_forms")
    if type(neutral_rows) is not list:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if len(fragments) <= 2:
        for index, template in enumerate(neutral_rows):
            if type(template) is not str:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                )
            expected = template.format(
                thought_literal="\x00", action_literal="\x00"
            )
            if skeleton == expected:
                matches.append(
                    _Step11FusedObservationParse(
                        form_id=f"obligation_fused:neutral_pair:{index}",
                        claim_kinds=("nucleus_notice",),
                        source_slot_hints=("thought", "action"),
                        source_fragments=fragments,
                        predicate_role="thought_action",
                        realization_status="undetermined",
                    )
                )
            for grounded_phrases in _match_grounded_template(
                clause, template
            ):
                if len(grounded_phrases) != 2:
                    continue
                matches.append(
                    _Step11FusedObservationParse(
                        form_id=(
                            f"obligation_fused:neutral_pair:{index}"
                        ),
                        claim_kinds=("nucleus_notice",),
                        source_slot_hints=("thought", "action"),
                        source_fragments=grounded_source_fragments(
                            grounded_phrases
                        ),
                        predicate_role="thought_action",
                        realization_status="undetermined",
                        grounded_phrases=grounded_phrases,
                    )
                )

    mixed_rows = grammar.get("mixed_emotion_forms")
    if type(mixed_rows) is not list:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if len(fragments) <= 2:
        for index, template in enumerate(mixed_rows):
            if type(template) is not str:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                )
            expected = template.format(
                first_literal="\x00", second_literal="\x00"
            )
            if skeleton == expected:
                matches.append(
                    _Step11FusedObservationParse(
                        form_id=(
                            "obligation_fused:mixed_emotion:"
                            f"{index}"
                        ),
                        claim_kinds=(
                            "nucleus_notice",
                            "mixed_emotion_relation",
                        ),
                        source_slot_hints=("emotion", "emotion"),
                        source_fragments=fragments,
                        predicate_role="affect",
                        realization_status="selected_label",
                        relation_type="coexists_with",
                        relation_direction="bidirectional",
                        relation_endpoint_roles=("affect", "affect"),
                    )
                )
            for grounded_phrases in _match_grounded_template(
                clause, template
            ):
                if len(grounded_phrases) != 2:
                    continue
                matches.append(
                    _Step11FusedObservationParse(
                        form_id=(
                            "obligation_fused:mixed_emotion:"
                            f"{index}"
                        ),
                        claim_kinds=(
                            "nucleus_notice",
                            "mixed_emotion_relation",
                        ),
                        source_slot_hints=("emotion", "emotion"),
                        source_fragments=grounded_source_fragments(
                            grounded_phrases
                        ),
                        predicate_role="affect",
                        realization_status="selected_label",
                        relation_type="coexists_with",
                        relation_direction="bidirectional",
                        relation_endpoint_roles=("affect", "affect"),
                        grounded_phrases=grounded_phrases,
                    )
                )

    relation_forms = grammar.get("relation_forms")
    local_anaphors = grammar.get("local_anaphors")
    if type(relation_forms) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if type(local_anaphors) is not dict or any(
        type(role) is not str
        or type(rows) is not list
        or any(type(value) is not str or not value for value in rows)
        for role, rows in local_anaphors.items()
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if len(fragments) <= 2:
        for relation_type, directions in relation_forms.items():
            if type(relation_type) is not str or type(directions) is not dict:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                )
            for direction, rows in directions.items():
                if type(direction) is not str or type(rows) is not list:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                    )
                for index, row in enumerate(rows):
                    if (
                        type(row) is not dict
                        or type(row.get("stem")) is not str
                        or row.get("relation_type") != relation_type
                        or row.get("relation_direction") != direction
                    ):
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
                        )
                    expected = row["stem"].format(
                        from_endpoint="\x00", to_endpoint="\x00"
                    )
                    if len(fragments) == 2 and skeleton == expected:
                        matches.append(
                            _Step11FusedObservationParse(
                                form_id=(
                                    "obligation_fused:relation:"
                                    f"{relation_type}:{direction}:{index}"
                                ),
                                claim_kinds=(
                                    "nucleus_notice",
                                    "relation_notice",
                                ),
                                source_slot_hints=(),
                                source_fragments=fragments,
                                predicate_role="relation",
                                realization_status="undetermined",
                                relation_type=relation_type,
                                relation_direction=direction,
                            )
                        )
                    for grounded_phrases in _match_grounded_template(
                        clause, row["stem"]
                    ):
                        if len(grounded_phrases) != 2:
                            continue
                        matches.append(
                            _Step11FusedObservationParse(
                                form_id=(
                                    "obligation_fused:relation:"
                                    f"{relation_type}:{direction}:{index}"
                                ),
                                claim_kinds=(
                                    "nucleus_notice",
                                    "relation_notice",
                                ),
                                source_slot_hints=(),
                                source_fragments=grounded_source_fragments(
                                    grounded_phrases
                                ),
                                predicate_role="relation",
                                realization_status="undetermined",
                                relation_type=relation_type,
                                relation_direction=direction,
                                grounded_phrases=grounded_phrases,
                            )
                        )
                    for local_role, anaphor_rows in local_anaphors.items():
                        for anaphor_index, anaphor in enumerate(
                            anaphor_rows
                        ):
                            for local_endpoint in ("from", "to"):
                                local_expected = row["stem"].format(
                                    from_endpoint=(
                                        anaphor
                                        if local_endpoint == "from"
                                        else "\x00"
                                    ),
                                    to_endpoint=(
                                        anaphor
                                        if local_endpoint == "to"
                                        else "\x00"
                                    ),
                                )
                                if skeleton != local_expected:
                                    grounded_local_template = row[
                                        "stem"
                                    ].format(
                                        from_endpoint=(
                                            anaphor
                                            if local_endpoint == "from"
                                            else "{from_endpoint}"
                                        ),
                                        to_endpoint=(
                                            anaphor
                                            if local_endpoint == "to"
                                            else "{to_endpoint}"
                                        ),
                                    )
                                else:
                                    grounded_local_template = ""
                                    matches.append(
                                        _Step11FusedObservationParse(
                                            form_id=(
                                                "obligation_fused:relation:"
                                                f"{relation_type}:{direction}:"
                                                f"{index}:local_{local_endpoint}:"
                                                f"{local_role}:{anaphor_index}"
                                            ),
                                            claim_kinds=(
                                                "nucleus_notice",
                                                "relation_notice",
                                            ),
                                            source_slot_hints=(),
                                            source_fragments=fragments,
                                            predicate_role="relation",
                                            realization_status="undetermined",
                                            relation_type=relation_type,
                                            relation_direction=direction,
                                        )
                                    )
                                if grounded_local_template:
                                    for grounded_phrases in (
                                        _match_grounded_template(
                                            clause,
                                            grounded_local_template,
                                        )
                                    ):
                                        if len(grounded_phrases) != 1:
                                            continue
                                        matches.append(
                                            _Step11FusedObservationParse(
                                                form_id=(
                                                    "obligation_fused:relation:"
                                                    f"{relation_type}:{direction}:"
                                                    f"{index}:local_{local_endpoint}:"
                                                    f"{local_role}:{anaphor_index}"
                                                ),
                                                claim_kinds=(
                                                    "nucleus_notice",
                                                    "relation_notice",
                                                ),
                                                source_slot_hints=(),
                                                source_fragments=(
                                                    grounded_source_fragments(
                                                        grounded_phrases
                                                    )
                                                ),
                                                predicate_role="relation",
                                                realization_status="undetermined",
                                                relation_type=relation_type,
                                                relation_direction=direction,
                                                grounded_phrases=(
                                                    grounded_phrases
                                                ),
                                            )
                                        )

    unique = tuple(dict.fromkeys(matches))
    if not unique:
        return None
    if len(unique) != 1:
        relation_rows = tuple(
            row
            for row in unique
            if row.form_id.startswith("obligation_fused:relation:")
        )
        def ambiguous_relation_head(
            row: _Step11FusedObservationParse,
        ) -> tuple[Any, ...]:
            parts = row.form_id.split(":")
            local = (
                tuple(parts[5:])
                if len(parts) >= 8 and parts[5].startswith("local_")
                else ()
            )
            if local:
                local = (
                    "local_source_or_target",
                    *local[1:],
                )
            return (
                row.relation_type,
                parts[4] if len(parts) > 4 else "",
                local,
                row.source_fragments,
                tuple(
                    phrase.visible_feature_fingerprint_sha256
                    for phrase in row.grounded_phrases
                ),
            )

        relation_heads = {
            ambiguous_relation_head(row) for row in relation_rows
        }
        if (
            len(relation_rows) == len(unique) == 2
            and len(relation_heads) == 1
            and {row.relation_direction for row in relation_rows}
            == {"source_to_target", "target_to_source"}
        ):
            row = relation_rows[0]
            parts = row.form_id.split(":")
            local_suffix = ""
            if len(parts) >= 8 and parts[5].startswith("local_"):
                local_suffix = (
                    ":local_source_or_target:"
                    f"{parts[6]}:{parts[7]}"
                )
            return _Step11FusedObservationParse(
                form_id=(
                    "obligation_fused:relation:"
                    f"{row.relation_type}:source_or_target:"
                    f"{parts[4]}{local_suffix}"
                ),
                claim_kinds=row.claim_kinds,
                source_slot_hints=row.source_slot_hints,
                source_fragments=row.source_fragments,
                predicate_role=row.predicate_role,
                realization_status=row.realization_status,
                relation_type=row.relation_type,
                relation_direction="source_or_target",
                relation_endpoint_roles=row.relation_endpoint_roles,
                grounded_phrases=row.grounded_phrases,
            )
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_AMBIGUOUS"
        )
    return unique[0]


def _reference_relation_clause(
    clause: str,
) -> tuple[
    str,
    str,
    str,
    tuple[str, str],
    tuple[Step11EndpointReference, Step11EndpointReference],
] | None:
    skeleton, fragments = _scan_quoted(clause)
    if fragments:
        return None
    grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    role_labels = grammar["role_labels"]
    ordinal_pattern = str(grammar["ordinal_pattern"])
    matches: list[
        tuple[
            str,
            str,
            str,
            tuple[str, str],
            tuple[Step11EndpointReference, Step11EndpointReference],
        ]
    ] = []
    for relation_type, directions in STEP11_SURFACE_CATALOG[
        "relation_forms"
    ].items():
        for direction, from_roles in directions.items():
            for from_role, to_roles in from_roles.items():
                for to_role, rows in to_roles.items():
                    from_token = (
                        rf"(?P<from_ordinal>{ordinal_pattern})つ目の"
                        + re.escape(str(role_labels[from_role]))
                    )
                    to_token = (
                        rf"(?P<to_ordinal>{ordinal_pattern})つ目の"
                        + re.escape(str(role_labels[to_role]))
                    )
                    for index, row in enumerate(rows):
                        stem = str(row["stem"])
                        pattern = re.escape(stem)
                        pattern = pattern.replace(
                            re.escape("{from_ref}"), from_token
                        ).replace(re.escape("{to_ref}"), to_token)
                        match = re.fullmatch(pattern, skeleton)
                        if match is None:
                            continue
                        references = (
                            Step11EndpointReference(
                                int(match.group("from_ordinal")),
                                str(from_role),
                            ),
                            Step11EndpointReference(
                                int(match.group("to_ordinal")),
                                str(to_role),
                            ),
                        )
                        matches.append(
                            (
                                (
                                    f"relation:{relation_type}:{direction}:"
                                    f"{from_role}:{to_role}:{index}"
                                ),
                                str(relation_type),
                                str(direction),
                                (str(from_role), str(to_role)),
                                references,
                            )
                        )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_REFERENCE_RELATION_AMBIGUOUS"
        )
    return matches[0]


def _mixed_emotion_compound_clause(
    clause: str,
) -> tuple[
    str,
    tuple[str, str],
] | None:
    """Parse an adjacent natural compound without visible ordinals."""

    skeleton, fragments = _scan_quoted(clause)
    if len(fragments) != 2:
        return None
    grammar = STEP11_SURFACE_CATALOG.get(
        "mixed_emotion_compound_grammar"
    )
    if (
        type(grammar) is not dict
        or type(grammar.get("adjacent_forms")) is not list
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_COMPOUND_CATALOG_INVALID"
        )
    matches: list[str] = []
    for index, template in enumerate(grammar["adjacent_forms"]):
        expected = str(template).format(
            first_literal="\x00",
            second_literal="\x00",
        )
        if skeleton == expected:
            matches.append(f"mixed_emotion_compound:natural:{index}")
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_COMPOUND_AMBIGUOUS"
        )
    return matches[0], (fragments[0], fragments[1])


def _mixed_emotion_relation_clause(clause: str) -> str | None:
    """Parse the nonadjacent quote-free mixed-valence relation."""

    skeleton, fragments = _scan_quoted(clause)
    if fragments:
        return None
    grammar = STEP11_SURFACE_CATALOG.get(
        "mixed_emotion_compound_grammar"
    )
    rows = (
        grammar.get("nonadjacent_relation_forms")
        if type(grammar) is dict
        else None
    )
    if type(rows) is not list:
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_RELATION_CATALOG_INVALID"
        )
    matches = tuple(
        f"mixed_emotion_relation:anaphoric:{index}"
        for index, row in enumerate(rows)
        if type(row) is str and skeleton == row
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_RELATION_AMBIGUOUS"
        )
    return matches[0]


def _unknown_reference_clause(
    clause: str,
) -> tuple[
    str,
    str,
    tuple[Step11EndpointReference, ...],
] | None:
    """Parse an anaphoric unknown with explicit typed target reference(s)."""

    skeleton, fragments = _scan_quoted(clause)
    if fragments:
        return None
    grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    role_labels = grammar["role_labels"]
    ordinal_pattern = str(grammar["ordinal_pattern"])
    rows_by_dimension = STEP11_SURFACE_CATALOG["observation_forms"].get(
        "unknown_anaphora"
    )
    if type(rows_by_dimension) is not dict:
        raise Step11InverseSurfaceError(
            "S11_PARSE_UNKNOWN_REFERENCE_CATALOG_INVALID"
        )
    matches: list[
        tuple[str, str, tuple[Step11EndpointReference, ...]]
    ] = []
    for key, rows in rows_by_dimension.items():
        if type(key) is not str or type(rows) is not list:
            raise Step11InverseSurfaceError(
                "S11_PARSE_UNKNOWN_REFERENCE_CATALOG_INVALID"
            )
        dimension = (
            "other_person_awareness" if key == "referent_other" else key
        )
        for index, row in enumerate(rows):
            if type(row) is not dict or set(row) != {"stem"}:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_UNKNOWN_REFERENCE_CATALOG_INVALID"
                )
            stems = dict.fromkeys(
                (str(row["stem"]), _catalog_clause_stem(str(row["stem"])))
            )
            if dimension == "relation":
                for from_role, from_label in role_labels.items():
                    for to_role, to_label in role_labels.items():
                        from_token = (
                            rf"(?P<from_ordinal>{ordinal_pattern})つ目の"
                            + re.escape(str(from_label))
                        )
                        to_token = (
                            rf"(?P<to_ordinal>{ordinal_pattern})つ目の"
                            + re.escape(str(to_label))
                        )
                        for stem in stems:
                            pattern = re.escape(stem).replace(
                                re.escape("{from_ref}"), from_token
                            ).replace(re.escape("{to_ref}"), to_token)
                            match = re.fullmatch(pattern, skeleton)
                            if match is None:
                                continue
                            from_ordinal = int(match.group("from_ordinal"))
                            to_ordinal = int(match.group("to_ordinal"))
                            if from_ordinal == to_ordinal:
                                raise Step11InverseSurfaceError(
                                    "S11_PARSE_UNKNOWN_TARGET_REFERENCE_DUPLICATE"
                                )
                            matches.append(
                                (
                                    f"unknown_anaphora:{key}:{index}",
                                    dimension,
                                    (
                                        Step11EndpointReference(
                                            from_ordinal, str(from_role)
                                        ),
                                        Step11EndpointReference(
                                            to_ordinal, str(to_role)
                                        ),
                                    ),
                                )
                            )
                continue
            for from_role, from_label in role_labels.items():
                for to_role, to_label in role_labels.items():
                    pair_token = (
                        rf"(?P<from_ordinal>{ordinal_pattern})つ目の"
                        + re.escape(str(from_label))
                        + "と"
                        + rf"(?P<to_ordinal>{ordinal_pattern})つ目の"
                        + re.escape(str(to_label))
                    )
                    for stem in stems:
                        pattern = re.escape(stem).replace(
                            re.escape("{target_ref}"), pair_token
                        )
                        match = re.fullmatch(pattern, skeleton)
                        if match is None:
                            continue
                        from_ordinal = int(match.group("from_ordinal"))
                        to_ordinal = int(match.group("to_ordinal"))
                        if from_ordinal == to_ordinal:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_UNKNOWN_TARGET_REFERENCE_DUPLICATE"
                            )
                        matches.append(
                            (
                                f"unknown_anaphora:{key}:{index}",
                                dimension,
                                (
                                    Step11EndpointReference(
                                        from_ordinal, str(from_role)
                                    ),
                                    Step11EndpointReference(
                                        to_ordinal, str(to_role)
                                    ),
                                ),
                            )
                        )
            for role, role_label in role_labels.items():
                token = (
                    rf"(?P<target_ordinal>{ordinal_pattern})つ目の"
                    + re.escape(str(role_label))
                )
                for stem in stems:
                    pattern = re.escape(stem).replace(
                        re.escape("{target_ref}"), token
                    )
                    match = re.fullmatch(pattern, skeleton)
                    if match is None:
                        continue
                    matches.append(
                        (
                            f"unknown_anaphora:{key}:{index}",
                            dimension,
                            (
                                Step11EndpointReference(
                                    int(match.group("target_ordinal")),
                                    str(role),
                                ),
                            ),
                        )
                    )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_UNKNOWN_TARGET_REFERENCE_AMBIGUOUS"
        )
    return matches[0]


def _observation_patterns() -> dict[
    str,
    tuple[
        str,
        tuple[str, ...],
        tuple[str, ...],
        str | None,
        str | None,
        str | None,
        bool,
        tuple[str, ...],
    ],
]:
    forms = STEP11_SURFACE_CATALOG["observation_forms"]
    patterns: dict[
        str,
        tuple[
            str,
            tuple[str, ...],
            tuple[str, ...],
            str | None,
            str | None,
            str | None,
            bool,
            tuple[str, ...],
        ],
    ] = {}

    def add(
        form_id: str,
        skeleton: str,
        claims: tuple[str, ...],
        hints: tuple[str, ...] = (),
        relation_type: str | None = None,
        direction: str | None = None,
        unknown: str | None = None,
        denial: bool = False,
        endpoint_roles: tuple[str, ...] = (),
    ) -> None:
        row = (
            form_id,
            claims,
            hints,
            relation_type,
            direction,
            unknown,
            denial,
            endpoint_roles,
        )
        for candidate in dict.fromkeys(
            (skeleton, _catalog_clause_stem(skeleton))
        ):
            if candidate in patterns and patterns[candidate] != row:
                existing = patterns[candidate]
                if existing[1:] != row[1:]:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_CATALOG_PATTERN_AMBIGUOUS"
                    )
                # The catalog keeps aliases whose semantic payload is
                # identical.  Canonicalise to the more specific boundary.
                specificity = (
                    "unknown_anaphora:",
                    "unknown_bound:",
                    "self_denial_bound:",
                )
                if row[0].startswith(specificity):
                    patterns[candidate] = row
                continue
            patterns[candidate] = row

    one = {
        "thought": (("nucleus_notice",), ("thought",), None, False),
        "action": (("nucleus_notice",), ("action",), None, False),
        "thought_unknown": (("nucleus_notice", "unknown_boundary"), ("thought",), "generic", False),
        "action_unknown": (("nucleus_notice", "unknown_boundary"), ("action",), "generic", False),
        "thought_self_denial": (("nucleus_notice", "self_denial_boundary"), ("thought",), None, True),
        "action_self_denial": (("nucleus_notice", "self_denial_boundary"), ("action",), None, True),
        "self_denial_only": (("self_denial_boundary",), ("thought",), None, True),
        "emotion": (("nucleus_notice",), ("emotion",), None, False),
        "category": (("nucleus_notice",), ("category",), None, False),
    }
    for key, (claims, hints, unknown, denial) in one.items():
        for index, rule in enumerate(forms[key]):
            add(f"{key}:{index}", f"{rule['prefix']}\x00{rule['suffix']}", claims, hints, unknown=unknown, denial=denial)
    two = {
        "thought_action": (("nucleus_notice",), ("thought", "action"), None, False),
        "thought_action_unknown": (("nucleus_notice", "unknown_boundary"), ("thought", "action"), "generic", False),
        "thought_action_self_denial": (("nucleus_notice", "self_denial_boundary"), ("thought", "action"), None, True),
        "thought_transition": (("source_context",), ("thought", "thought"), None, False),
        "action_transition": (("source_context",), ("action", "action"), None, False),
    }
    for key, (claims, hints, unknown, denial) in two.items():
        for index, rule in enumerate(forms[key]):
            add(f"{key}:{index}", f"{rule['prefix']}\x00{rule['middle']}\x00{rule['suffix']}", claims, hints, unknown=unknown, denial=denial)
    for index, rule in enumerate(forms["thought_action_transition"]):
        add(
            f"thought_action_transition:{index}",
            f"{rule['prefix']}\x00{rule['middle']}\x00{rule['middle2']}\x00{rule['suffix']}",
            ("nucleus_notice", "source_context"),
            ("thought", "thought", "action"),
        )
    for slot in ("thought", "action"):
        for index, rule in enumerate(forms["unknown_only"][slot]):
            add(f"unknown_only:{slot}:{index}", f"{rule['prefix']}\x00{rule['suffix']}", ("unknown_boundary",), (slot,), unknown="generic")
    for index, line in enumerate(forms["unknown_only"]["generic"]):
        add(f"unknown_only:generic:{index}", line, ("unknown_boundary",), unknown="generic")
    for index, line in enumerate(forms["self_denial_anaphora"]):
        add(
            f"self_denial_anaphora:{index}",
            line,
            ("self_denial_boundary",),
            denial=True,
        )
    for index, line in enumerate(forms["bounded_counter_anaphora"]):
        add(
            f"bounded_counter_anaphora:{index}",
            line,
            ("bounded_counterposition",),
            denial=True,
        )
    for dimension, rows in forms["unknown_dimension"].items():
        for index, line in enumerate(rows):
            add(f"unknown_dimension:{dimension}:{index}", line, ("unknown_boundary",), unknown=dimension)
    for dimension, rows in forms["unknown_bound"].items():
        for index, rule in enumerate(rows):
            add(
                f"unknown_bound:{dimension}:{index}",
                f"{rule['prefix']}\x00{rule['suffix']}",
                ("nucleus_notice", "unknown_boundary"),
                unknown=dimension,
            )
    for index, rule in enumerate(forms["self_denial_bound"]):
        add(
            f"self_denial_bound:{index}",
            f"{rule['prefix']}\x00{rule['suffix']}",
            ("nucleus_notice", "self_denial_boundary"),
            denial=True,
        )
    for index, rule in enumerate(forms["mixed_emotion"]):
        add(
            f"mixed_emotion:{index}",
            f"{rule['prefix']}\x00{rule['middle']}\x00{rule['suffix']}",
            ("nucleus_notice", "mixed_emotion_relation"),
            ("emotion", "emotion"),
            relation_type="coexists_with",
            direction="bidirectional",
            endpoint_roles=("affect", "affect"),
        )
    return patterns


def _reception_patterns() -> dict[
    str, tuple[str, str, str, str, tuple[str, ...]]
]:
    """Compile the declarative reception grammar to inverse skeletons.

    Direct reception sentences quote their exact target anchor(s).  Anaphoric
    sentences deliberately carry no quote; the matcher resolves those atoms
    from a unique act/scope/status target and an independently observed exact
    antecedent.  Neither path trusts the forward AST.
    """

    forms = STEP11_SURFACE_CATALOG["reception_forms"]
    result: dict[str, tuple[str, str, str, str, tuple[str, ...]]] = {}

    def add(
        skeleton: str,
        value: tuple[str, str, str, str, tuple[str, ...]],
    ) -> None:
        for candidate in dict.fromkeys(
            (skeleton, _catalog_clause_stem(skeleton))
        ):
            if candidate in result and result[candidate] != value:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_RECEPTION_AMBIGUOUS"
                )
            result[candidate] = value

    if {
        "sentence_templates",
        "content_forms",
        "anaphoric_content_forms",
        "act_predicates",
    } <= set(forms):
        templates = forms["sentence_templates"]
        content_sets = (
            ("direct", forms["content_forms"]),
            ("anaphoric", forms["anaphoric_content_forms"]),
        )
        predicates = forms["act_predicates"]
        if (
            type(templates) is not list
            or any(type(content_forms) is not dict for _, content_forms in content_sets)
            or type(predicates) is not dict
        ):
            raise Step11InverseSurfaceError("S11_PARSE_RECEPTION_CATALOG_INVALID")
        for act, act_rows in predicates.items():
            if type(act) is not str or type(act_rows) is not list:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_RECEPTION_CATALOG_INVALID"
                )
            for content_kind, content_forms in content_sets:
                for scope, statuses in content_forms.items():
                    if type(scope) is not str or type(statuses) is not dict:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_CATALOG_INVALID"
                        )
                    hints = {
                        "thought": ("thought",),
                        "action": ("action",),
                        "thought_action": ("thought", "action"),
                    }.get(scope, ())
                    for status, content_rows in statuses.items():
                        if type(status) is not str or type(content_rows) is not list:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_RECEPTION_CATALOG_INVALID"
                            )
                        for content_index, content in enumerate(content_rows):
                            if type(content) is not str:
                                raise Step11InverseSurfaceError(
                                    "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                )
                            try:
                                content_skeleton = content.format(
                                    first="\x00", second="\x00"
                                )
                            except (KeyError, ValueError) as exc:
                                raise Step11InverseSurfaceError(
                                    "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                ) from exc
                            # Canonical reception joins a continuative
                            # ``...ずに`` content atom to the following act
                            # predicate as ``...ず、``.  Rebuild that narrow
                            # morphology from the selected catalog atom before
                            # compiling the inverse sentence skeleton.
                            if content_skeleton.endswith("ずに"):
                                content_skeleton = (
                                    content_skeleton[:-2] + "ず、"
                                )
                            expected_fragment_count = 0
                            if content_kind == "direct":
                                expected_fragment_count = len(hints)
                                if scope == "relation":
                                    expected_fragment_count = 2
                            if content_skeleton.count("\x00") != expected_fragment_count:
                                raise Step11InverseSurfaceError(
                                    "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                )
                            for predicate_index, predicate in enumerate(act_rows):
                                if type(predicate) is not str:
                                    raise Step11InverseSurfaceError(
                                        "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                    )
                                for sentence_index, template in enumerate(templates):
                                    if type(template) is not str:
                                        raise Step11InverseSurfaceError(
                                            "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                        )
                                    try:
                                        skeleton = template.format(
                                            content=content_skeleton,
                                            predicate=predicate,
                                        )
                                    except (KeyError, ValueError) as exc:
                                        raise Step11InverseSurfaceError(
                                            "S11_PARSE_RECEPTION_CATALOG_INVALID"
                                        ) from exc
                                    form_id = (
                                        f"reception:{content_kind}:"
                                        f"{act}:{scope}:{status}:"
                                        f"{sentence_index}:{content_index}:"
                                        f"{predicate_index}"
                                    )
                                    add(
                                        skeleton,
                                        (
                                            form_id,
                                            act,
                                            scope,
                                            _canonical_status(status),
                                            hints,
                                        ),
                                    )
        return result

    # Transitional support for reading an older catalog during a rolling
    # source update.  These forms have no exact target fragments and the
    # matcher consequently refuses to bind them as current reception evidence.
    status_indices = STEP11_SURFACE_CATALOG.get(
        "reception_status_form_indices", {}
    )
    for act, scopes in forms.items():
        for scope, rows in scopes.items():
            statuses = status_indices.get(scope, {})
            status_by_index = {
                index: _canonical_status(status)
                for status, indices in statuses.items()
                for index in indices
            }
            for index, line in enumerate(rows):
                status = status_by_index.get(index, "undetermined")
                add(
                    line,
                    (
                        f"reception:{act}:{scope}:{status}:{index}",
                        act,
                        scope,
                        status,
                        (),
                    ),
                )
    return result


def _typed_reception_clause(
    clause: str,
) -> tuple[
    str,
    str,
    str,
    str,
    tuple[Step11EndpointReference, ...],
] | None:
    """Parse a visible rc0026 typed-fallback reception clause."""

    skeleton, fragments = _scan_quoted(clause)
    if fragments:
        return None
    reception = STEP11_SURFACE_CATALOG.get("reception_forms")
    typed = (
        reception.get("typed_reference_grammar")
        if type(reception) is dict
        else None
    )
    templates = reception.get("sentence_templates") if type(reception) is dict else None
    predicates = reception.get("act_predicates") if type(reception) is dict else None
    content_forms = typed.get("content_forms") if type(typed) is dict else None
    wrapper = typed.get("reference_wrapper") if type(typed) is dict else None
    if (
        type(templates) is not list
        or type(predicates) is not dict
        or type(content_forms) is not dict
        or type(wrapper) is not str
        or "{endpoint_ref}" not in wrapper
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
        )
    reference_grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    role_labels = reference_grammar["role_labels"]
    ordinal_pattern = str(reference_grammar["ordinal_pattern"])

    def token(name: str, role: str) -> str:
        # Visible delimiters are already present in every catalog content
        # form (for example ``〔{thought_ref}〕``).  This token therefore
        # matches only the inner typed reference.
        return (
            rf"(?P<{name}>{ordinal_pattern})つ目の"
            + re.escape(str(role_labels[role]))
        )

    matches: list[
        tuple[
            str,
            str,
            str,
            str,
            tuple[Step11EndpointReference, ...],
        ]
    ] = []
    for scope, statuses in content_forms.items():
        if type(scope) is not str or type(statuses) is not dict:
            raise Step11InverseSurfaceError(
                "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
            )
        role_combinations: tuple[tuple[tuple[str, str], ...], ...]
        if scope == "thought":
            # A source thought can contain an action-shaped proposition.  Its
            # local referent keeps the independently parsed endpoint role;
            # source-slot ownership is verified later against the registry.
            role_combinations = tuple(
                (("thought_ref", role),) for role in role_labels
            )
        elif scope == "action":
            role_combinations = ((("action_ref", "action"),),)
        elif scope == "thought_action":
            role_combinations = tuple(
                (
                    ("thought_ref", thought_role),
                    ("action_ref", "action"),
                )
                for thought_role in role_labels
            )
        elif scope == "relation":
            role_combinations = tuple(
                (("from_ref", left), ("to_ref", right))
                for left in role_labels
                for right in role_labels
            )
        elif scope == "relation_action":
            role_combinations = tuple(
                (
                    ("from_ref", left),
                    ("to_ref", right),
                    ("action_ref", "action"),
                )
                for left in role_labels
                for right in role_labels
            )
        else:
            raise Step11InverseSurfaceError(
                "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
            )
        for status, rows in statuses.items():
            if type(status) is not str or type(rows) is not list:
                raise Step11InverseSurfaceError(
                    "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
                )
            for content_index, content in enumerate(rows):
                if type(content) is not str:
                    raise Step11InverseSurfaceError(
                        "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
                    )
                for roles in role_combinations:
                    pattern_content = re.escape(content)
                    for name, role in roles:
                        pattern_content = pattern_content.replace(
                            re.escape("{" + name + "}"), token(name, role)
                        )
                    for act, act_rows in predicates.items():
                        if type(act) is not str or type(act_rows) is not list:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
                            )
                        for predicate_index, predicate in enumerate(act_rows):
                            for sentence_index, template in enumerate(templates):
                                if type(predicate) is not str or type(template) is not str:
                                    raise Step11InverseSurfaceError(
                                        "S11_PARSE_RECEPTION_TYPED_CATALOG_INVALID"
                                    )
                                expected = _catalog_clause_stem(
                                    template.format(
                                        content="__CONTENT__",
                                        predicate=predicate,
                                    )
                                )
                                pattern = re.escape(expected).replace(
                                    re.escape("__CONTENT__"), pattern_content
                                )
                                match = re.fullmatch(pattern, skeleton)
                                if match is None:
                                    continue
                                references = tuple(
                                    Step11EndpointReference(
                                        int(match.group(name)), role
                                    )
                                    for name, role in roles
                                )
                                if len(
                                    {row.reference_ordinal for row in references}
                                ) != len(references):
                                    raise Step11InverseSurfaceError(
                                        "S11_PARSE_RECEPTION_TYPED_REFERENCE_DUPLICATE"
                                    )
                                matches.append(
                                    (
                                        (
                                            "reception:typed:"
                                            f"{act}:{scope}:{status}:"
                                            f"{sentence_index}:{content_index}:"
                                            f"{predicate_index}"
                                        ),
                                        act,
                                        scope,
                                        _canonical_status(status),
                                        references,
                                    )
                                )
    if not matches:
        return None
    unique = tuple(dict.fromkeys(matches))
    if len(unique) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_RECEPTION_TYPED_AMBIGUOUS"
        )
    return unique[0]


def _parsed_semantic_signature(
    form_id: str,
    hints: Sequence[str],
    *,
    section_role: str,
    reception_scope: str | None,
) -> tuple[str, str]:
    """Derive claim strength independently from the rendered AST."""

    if section_role == "reception":
        return (reception_scope or "generic", "undetermined")
    if form_id.startswith("relation:"):
        return ("relation", "undetermined")
    if form_id.startswith("unknown"):
        role = hints[0] if hints else "unknown"
        return (role, "undetermined")
    if form_id.startswith("self_denial"):
        return ("speaker_identity_or_trait", "reported_evaluation")
    unique = set(hints)
    if "action" in unique and "thought" in unique:
        return ("thought_action", "undetermined")
    if "action" in unique:
        return ("action", "undetermined")
    if "thought" in unique:
        return ("thought", "reported_content")
    if "emotion" in unique:
        return ("emotion", "selected_label")
    if "category" in unique:
        return ("category", "selected_label")
    return ("source_context", "undetermined")


def parse_step11_natural_surface(body: bytes) -> Step11ParsedSurfaceWitness:
    if type(body) is not bytes or not body:
        raise Step11InverseSurfaceError("S11_PARSE_BYTES_REQUIRED")
    if validate_step11_surface_catalog():
        raise Step11InverseSurfaceError("S11_PARSE_CATALOG_INVALID")
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11InverseSurfaceError("S11_PARSE_UTF8_INVALID") from exc
    if unicodedata.normalize("NFC", text) != text or "\r" in text or text.endswith("\n") or text.startswith("\ufeff"):
        raise Step11InverseSurfaceError("S11_PARSE_CANONICAL_TEXT_INVALID")
    fused_grammar = STEP11_SURFACE_CATALOG.get(
        "obligation_fused_grammar", {}
    )
    forbidden_fragments = fused_grammar.get(
        "forbidden_generated_fragments", []
    )
    forbidden_patterns = fused_grammar.get(
        "forbidden_generated_patterns", []
    )
    if (
        type(forbidden_fragments) is not list
        or type(forbidden_patterns) is not list
        or any(type(row) is not str for row in forbidden_fragments)
        or any(type(row) is not str for row in forbidden_patterns)
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_FUSED_OBSERVATION_CATALOG_INVALID"
        )
    if any(fragment in text for fragment in forbidden_fragments) or any(
        re.search(pattern, text) is not None
        for pattern in forbidden_patterns
    ):
        raise Step11InverseSurfaceError(
            "S11_PARSE_VISIBLE_REFERENCE_BOOKKEEPING_FORBIDDEN"
        )
    labels = STEP11_SURFACE_CATALOG["labels"]
    prefix = f"{labels['observation']}\n"
    separator = f"\n\n{labels['reception']}\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        raise Step11InverseSurfaceError("S11_PARSE_SECTION_LAYOUT_INVALID")
    observation_text, reception_text = text[len(prefix) :].split(separator)
    if not observation_text or not reception_text or "\n\n" in observation_text or "\n\n" in reception_text:
        raise Step11InverseSurfaceError("S11_PARSE_SECTION_EMPTY_OR_NESTED")
    obs_patterns = _observation_patterns()
    reception_patterns = _reception_patterns()
    atoms: list[Step11ParsedAtom] = []
    sentences: list[Step11ParsedSentence] = []
    observation_start = len(prefix)
    reception_start = observation_start + len(observation_text) + len(separator)
    sentence_ordinal = 0
    next_reference_ordinal = 1
    introduced_reference_roles: dict[int, str] = {}
    for section, section_text, section_start in (
        ("observation", observation_text, observation_start),
        ("reception", reception_text, reception_start),
    ):
        line_char_offset = 0
        for line in section_text.split("\n"):
            if not line:
                raise Step11InverseSurfaceError("S11_PARSE_EMPTY_LINE")
            sentence_ordinal += 1
            line_global_start = section_start + line_char_offset
            sentence_byte_start = len(
                text[:line_global_start].encode("utf-8")
            )
            sentence_byte_end = sentence_byte_start + len(
                line.encode("utf-8")
            )
            clause_atom_ids: list[str] = []
            grammatical_chunk_counts: dict[int, int] = {}
            for clause_ordinal, (
                clause,
                clause_start,
                clause_end,
                grammatical_chunk_ordinal,
            ) in enumerate(_split_group_clauses(line), start=1):
                grammatical_chunk_counts[grammatical_chunk_ordinal] = (
                    grammatical_chunk_counts.get(
                        grammatical_chunk_ordinal, 0
                    )
                    + 1
                )
                introduced_reference: Step11EndpointReference | None = None
                compound_label_references: tuple[
                    Step11EndpointReference, ...
                ] = ()
                relation_references: tuple[
                    Step11EndpointReference, ...
                ] = ()
                unknown_target_references: tuple[
                    Step11EndpointReference, ...
                ] = ()
                reception_antecedent_references: tuple[
                    Step11EndpointReference, ...
                ] = ()
                grounded_phrases: tuple[
                    Step11ParsedGroundedPhrase, ...
                ] = ()
                if section == "observation":
                    fused_observation = _fused_observation_clause(clause)
                    if fused_observation is not None:
                        introduction = relation = mixed_compound = None
                        mixed_relation = unknown_reference = None
                    else:
                        introduction = _natural_introduction_clause(clause)
                        relation = _reference_relation_clause(clause)
                        mixed_compound = _mixed_emotion_compound_clause(
                            clause
                        )
                        mixed_relation = _mixed_emotion_relation_clause(
                            clause
                        )
                        unknown_reference = _unknown_reference_clause(clause)
                    if sum(
                        value is not None
                        for value in (
                            fused_observation,
                            introduction,
                            relation,
                            mixed_compound,
                            mixed_relation,
                            unknown_reference,
                        )
                    ) > 1:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_OBSERVATION_FORM_AMBIGUOUS"
                        )
                    if fused_observation is not None:
                        form_id = fused_observation.form_id
                        claims = fused_observation.claim_kinds
                        hints = fused_observation.source_slot_hints
                        fragments = fused_observation.source_fragments
                        predicate_role = fused_observation.predicate_role
                        realization_status = (
                            fused_observation.realization_status
                        )
                        relation_type = fused_observation.relation_type
                        direction = fused_observation.relation_direction
                        endpoint_roles = (
                            fused_observation.relation_endpoint_roles
                        )
                        unknown = (
                            fused_observation.unknown_dimension_class
                        )
                        denial = (
                            fused_observation.self_denial_not_fact
                        )
                        grounded_phrases = (
                            fused_observation.grounded_phrases
                        )
                        act = scope = explicit_status = None
                    elif any(
                        value is not None
                        for value in (
                            introduction,
                            relation,
                            mixed_compound,
                            mixed_relation,
                            unknown_reference,
                        )
                    ):
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_LEGACY_REFERENCE_SURFACE_FORBIDDEN"
                        )
                    elif mixed_compound is not None:
                        form_id, fragments = mixed_compound
                        compound_label_references = (
                            Step11EndpointReference(
                                next_reference_ordinal, "affect"
                            ),
                            Step11EndpointReference(
                                next_reference_ordinal + 1, "affect"
                            ),
                        )
                        for reference in compound_label_references:
                            introduced_reference_roles[
                                reference.reference_ordinal
                            ] = reference.endpoint_role
                        next_reference_ordinal += 2
                        claims = (
                            "nucleus_notice",
                            "mixed_emotion_relation",
                        )
                        hints = ("emotion", "emotion")
                        relation_type = "coexists_with"
                        direction = "bidirectional"
                        endpoint_roles = ("affect", "affect")
                        relation_references = compound_label_references
                        unknown = None
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = "affect"
                        realization_status = "selected_label"
                    elif introduction is not None:
                        (
                            form_id,
                            introduction_slot,
                            introduction_role,
                            fragments,
                        ) = introduction
                        introduced_reference = Step11EndpointReference(
                            next_reference_ordinal,
                            introduction_role,
                        )
                        introduced_reference_roles[
                            next_reference_ordinal
                        ] = introduction_role
                        next_reference_ordinal += 1
                        claims = ("nucleus_notice",)
                        hints = (introduction_slot,)
                        relation_type = direction = unknown = None
                        endpoint_roles = ()
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = introduced_reference.endpoint_role
                        realization_status = "undetermined"
                    elif mixed_relation is not None:
                        form_id = mixed_relation
                        claims = ("mixed_emotion_relation",)
                        hints = ()
                        fragments = ()
                        relation_type = "coexists_with"
                        direction = "bidirectional"
                        endpoint_roles = ("affect", "affect")
                        unknown = None
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = "affect"
                        realization_status = "selected_label"
                    elif relation is not None:
                        (
                            form_id,
                            relation_type,
                            direction,
                            endpoint_roles,
                            typed_relation_references,
                        ) = relation
                        relation_references = typed_relation_references
                        claims = ("relation_notice",)
                        hints = ()
                        fragments = ()
                        unknown = None
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = "relation"
                        realization_status = "undetermined"
                    elif unknown_reference is not None:
                        (
                            form_id,
                            unknown,
                            unknown_target_references,
                        ) = unknown_reference
                        claims = ("unknown_boundary",)
                        hints = ()
                        fragments = ()
                        relation_type = direction = None
                        endpoint_roles = ()
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = "unknown"
                        realization_status = "undetermined"
                    else:
                        skeleton, fragments = _scan_quoted(clause)
                        row = obs_patterns.get(skeleton)
                        if row is None:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_OBSERVATION_FORM_UNKNOWN"
                            )
                        (
                            form_id,
                            claims,
                            hints,
                            relation_type,
                            direction,
                            unknown,
                            denial,
                            endpoint_roles,
                        ) = row
                        if hints and len(hints) != len(fragments):
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_FRAGMENT_ARITY_INVALID"
                            )
                        if relation_type is not None:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_LEGACY_RELATION_FORBIDDEN"
                            )
                        act = scope = explicit_status = None
                        (
                            predicate_role,
                            realization_status,
                        ) = _parsed_semantic_signature(
                            form_id,
                            hints,
                            section_role=section,
                            reception_scope=scope,
                        )
                else:
                    typed_reception = _typed_reception_clause(clause)
                    if typed_reception is not None:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_LEGACY_TYPED_RECEPTION_FORBIDDEN"
                        )
                    skeleton, fragments = _scan_quoted(clause)
                    if fragments:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_LITERAL_FORBIDDEN"
                        )
                    reception = reception_patterns.get(skeleton)
                    if reception is None:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_FORM_UNKNOWN"
                        )
                    form_id, act, scope, explicit_status, hints = reception
                    if not form_id.startswith("reception:anaphoric:"):
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_NONANAPHORIC_FORBIDDEN"
                        )
                    claims = ("bound_reception",)
                    if fragments:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_FRAGMENT_ARITY_INVALID"
                        )
                    relation_type = direction = unknown = None
                    endpoint_roles = ()
                    denial = False
                    predicate_role = scope
                    realization_status = explicit_status
                for reference in (
                    *relation_references,
                    *unknown_target_references,
                    *reception_antecedent_references,
                ):
                    introduced_role = introduced_reference_roles.get(
                        reference.reference_ordinal
                    )
                    if introduced_role is None:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_REFERENCE_BEFORE_INTRODUCTION"
                        )
                    if introduced_role != reference.endpoint_role:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_REFERENCE_ROLE_MISMATCH"
                        )
                clause_global_start = line_global_start + clause_start
                clause_global_end = line_global_start + clause_end
                byte_start = len(
                    text[:clause_global_start].encode("utf-8")
                )
                byte_end = len(text[:clause_global_end].encode("utf-8"))
                atom_id = "nls3s11atom_" + hashlib.sha256(
                    (
                        f"{section}\x00{sentence_ordinal}\x00"
                        f"{clause_ordinal}\x00{clause}"
                    ).encode("utf-8")
                ).hexdigest()[:16]
                atoms.append(
                    Step11ParsedAtom(
                        atom_id=atom_id,
                        section_role=section,
                        form_id=form_id,
                        claim_kinds=claims,
                        source_slot_hints=hints,
                        source_fragments=fragments,
                        predicate_role=predicate_role,
                        realization_status=realization_status,
                        relation_type=relation_type,
                        relation_direction=direction,
                        relation_endpoint_roles=endpoint_roles,
                        unknown_dimension_class=unknown,
                        self_denial_not_fact=denial,
                        reception_act=act,
                        reception_scope=scope,
                        byte_start=byte_start,
                        byte_end=byte_end,
                        introduced_reference=introduced_reference,
                        relation_endpoint_references=relation_references,
                        unknown_target_references=(
                            unknown_target_references
                        ),
                        compound_label_references=(
                            compound_label_references
                        ),
                        reception_antecedent_references=(
                            reception_antecedent_references
                        ),
                        grammatical_chunk_ordinal=(
                            grammatical_chunk_ordinal
                        ),
                        sentence_ordinal=sentence_ordinal,
                        clause_ordinal=clause_ordinal,
                        grounded_phrases=tuple(
                            Step11ParsedGroundedPhrase(
                                phrase_text=phrase.phrase_text,
                                visible_feature_fields=(
                                    phrase.visible_feature_fields
                                ),
                                visible_feature_fingerprint_sha256=(
                                    phrase.visible_feature_fingerprint_sha256
                                ),
                                phrase_profile_id=phrase.phrase_profile_id,
                                anchor_risk_rank=phrase.anchor_risk_rank,
                                action_lifecycle=phrase.action_lifecycle,
                                binding_family=phrase.binding_family,
                                anchor_text=phrase.anchor_text,
                                byte_start=(
                                    byte_start + phrase.byte_start
                                ),
                                byte_end=byte_start + phrase.byte_end,
                                anchor_byte_start=(
                                    byte_start
                                    + phrase.anchor_byte_start
                                    if phrase.anchor_byte_start is not None
                                    else None
                                ),
                                anchor_byte_end=(
                                    byte_start + phrase.anchor_byte_end
                                    if phrase.anchor_byte_end is not None
                                    else None
                                ),
                            )
                            for phrase in grounded_phrases
                        ),
                    )
                )
                clause_atom_ids.append(atom_id)
            sentences.append(
                Step11ParsedSentence(
                    sentence_ordinal=sentence_ordinal,
                    section_role=section,
                    clause_atom_ids=tuple(clause_atom_ids),
                    byte_start=sentence_byte_start,
                    byte_end=sentence_byte_end,
                    grammatical_chunk_clause_counts=tuple(
                        grammatical_chunk_counts[index]
                        for index in range(
                            1, len(grammatical_chunk_counts) + 1
                        )
                    ),
                )
            )
            line_char_offset += len(line) + 1
    return Step11ParsedSurfaceWitness(
        schema_version=STEP11_PARSED_WITNESS_SCHEMA,
        surface_catalog_sha256=STEP11_SURFACE_CATALOG_SHA256,
        body_sha256=hashlib.sha256(body).hexdigest(),
        atoms=tuple(atoms),
        observation_atom_count=sum(row.section_role == "observation" for row in atoms),
        reception_atom_count=sum(row.section_role == "reception" for row in atoms),
        body_free_export_allowed=False,
        sentences=tuple(sentences),
    )


def _slots_for_nucleus(snapshot: Any, nucleus_id: str) -> tuple[str, ...]:
    row = next((item for item in snapshot.nuclei if item.source_id == nucleus_id), None)
    if row is None:
        return ()
    return tuple(sorted({_SOURCE_FIELD_TO_SLOT[field] for field in row.source_fields if field in _SOURCE_FIELD_TO_SLOT}, key=_SLOT_ORDER.__getitem__))


def _source_ordinal(nucleus: Any) -> int:
    """Independently recover the frozen source order from anchor ids."""

    ordinals: list[int] = []
    for value in getattr(nucleus, "surface_anchor_ids", ()):
        match = re.fullmatch(r"[A-Za-z_]*?([0-9]+)", str(value))
        if match is not None:
            ordinals.append(int(match.group(1)))
    return min(ordinals) if ordinals else 10**9


def _independent_endpoint_role(nucleus: Any) -> str:
    slots = tuple(
        sorted(
            {
                _SOURCE_FIELD_TO_SLOT[field]
                for field in nucleus.source_fields
                if field in _SOURCE_FIELD_TO_SLOT
            },
            key=_SLOT_ORDER.__getitem__,
        )
    )
    kind = str(nucleus.kind)
    predicate = str(nucleus.source_predicate_kind)
    modality = str(nucleus.modality)
    if slots == ("thought",) and kind == "wish":
        return "proposition"
    if "action" in slots or kind in {"action", "wish"} or predicate == "action":
        return "action"
    if (
        "emotion" in slots
        or modality == "feeling"
        or predicate == "feeling"
        or kind in {"state", "reaction", "change", "self_evaluation"}
    ):
        return "affect"
    return "proposition"


def _independent_generic_transition_requires_neutral_copresence(
    relation: Any,
    *,
    source_slots: tuple[str, ...],
    target_slots: tuple[str, ...],
) -> bool:
    """Recognise only the frozen generic field-transition source contract."""

    source_refs = frozenset(
        str(value) for value in relation.source_relation_ids
    )
    return (
        relation.grounding_kind == "bounded_structural_inference"
        and relation.source_relation_kind == "action_supports_change"
        and relation.relation_type == "supports_without_guarantee"
        and relation.relation_direction == "source_to_target"
        and _MATCH_GENERIC_TRANSITION_SOURCE_REF in source_refs
        and source_refs <= _MATCH_GENERIC_TRANSITION_ALLOWED_SOURCE_REFS
        and source_slots == ("thought",)
        and target_slots == ("action",)
    )


def _independent_source_boundary_companion_contract(
    *,
    snapshot: Any,
    by_id: Mapping[str, Mapping[str, Any]],
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    planning_frontier: Any,
) -> tuple[str, ...]:
    """Recompute the narrow boundary-companion frontier from frozen parents.

    This inverse calculation deliberately does not call the planning owner's
    boundary helpers. A forward regression therefore cannot make itself
    appear valid merely by returning a self-consistent frontier.
    """

    issues: set[str] = set()
    decisions = content_plan.get("decisions")
    nodes = discourse_plan.get("nodes")
    groups = discourse_plan.get("sentence_groups")
    if any(type(value) is not list for value in (decisions, nodes, groups)):
        return ("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID",)
    decision_by_id = {
        row.get("obligation_id"): row
        for row in decisions
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    if len(decision_by_id) != len(decisions) or set(decision_by_id) != set(
        by_id
    ):
        return ("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID",)
    base_active = frozenset(
        obligation_id
        for obligation_id, row in decision_by_id.items()
        if row.get("status") in _MATCH_ACTIVE_DECISION_STATUSES
    )
    node_by_obligation = {
        row.get("obligation_id"): row.get("node_id")
        for row in nodes
        if type(row) is dict
        and type(row.get("obligation_id")) is str
        and type(row.get("node_id")) is str
    }
    if set(node_by_obligation) != set(base_active):
        issues.add("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID")
    group_by_node: dict[str, str] = {}
    for group in groups:
        if (
            type(group) is not dict
            or type(group.get("sentence_group_id")) is not str
            or type(group.get("node_ids")) is not list
        ):
            issues.add("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID")
            continue
        for node_id in group["node_ids"]:
            if type(node_id) is not str or node_id in group_by_node:
                issues.add("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID")
                continue
            group_by_node[node_id] = group["sentence_group_id"]
    if set(group_by_node) != set(node_by_obligation.values()):
        issues.add("S11_MATCH_BOUNDARY_COMPANION_PARENT_INVALID")

    nucleus_by_id = {str(row.source_id): row for row in snapshot.nuclei}
    if len(nucleus_by_id) != len(snapshot.nuclei):
        issues.add("S11_MATCH_BOUNDARY_COMPANION_SOURCE_INVALID")
    base_rows_by_field: dict[str, list[tuple[int, str]]] = {
        field: [] for field in _MATCH_BOUNDARY_TEXT_FIELDS
    }
    for nucleus_id, nucleus in nucleus_by_id.items():
        source_fields = tuple(nucleus.source_fields)
        if (
            len(source_fields) != 1
            or source_fields[0] not in _MATCH_BOUNDARY_FIELD_ORDER
            or nucleus.grounding_kind != "explicit"
            or _BASE_NUCLEUS_SPAN_RE.fullmatch(
                str(nucleus.actual_source_id)
            )
            is None
        ):
            continue
        ordinals = tuple(
            int(match.group(1))
            for anchor_id in nucleus.surface_anchor_ids
            for match in [re.fullmatch(r"[A-Za-z_]*?([0-9]+)", str(anchor_id))]
            if match is not None
        )
        if ordinals:
            base_rows_by_field[source_fields[0]].append(
                (min(ordinals), nucleus_id)
            )
    for rows in base_rows_by_field.values():
        rows.sort()
        if len({ordinal for ordinal, _nucleus_id in rows}) != len(rows):
            issues.add("S11_MATCH_BOUNDARY_COMPANION_ORDER_AMBIGUOUS")

    position_by_nucleus: dict[str, tuple[str, int, int]] = {}
    boundary_ids: set[str] = set()
    for field, rows in base_rows_by_field.items():
        for index, (ordinal, nucleus_id) in enumerate(rows):
            position_by_nucleus[nucleus_id] = (field, index, ordinal)
        if rows:
            boundary_ids.update((rows[0][1], rows[-1][1]))

    notice_by_nucleus: dict[str, str] = {}
    for obligation_id, row in by_id.items():
        nucleus_ids = tuple(row.get("nucleus_ids", ()))
        if (
            row.get("kind") != "grounded_nucleus_notice"
            or len(nucleus_ids) != 1
            or row.get("relation_ids")
            or row.get("unknown_boundary_ids")
        ):
            continue
        nucleus_id = str(nucleus_ids[0])
        if nucleus_id in notice_by_nucleus:
            issues.add("S11_MATCH_BOUNDARY_COMPANION_NOTICE_AMBIGUOUS")
        notice_by_nucleus[nucleus_id] = obligation_id

    active_nucleus_ids = frozenset(
        str(nucleus_id)
        for obligation_id in base_active
        for nucleus_id in by_id.get(obligation_id, {}).get("nucleus_ids", ())
    )
    specs: list[tuple[str, str, str, str, int]] = []
    for nucleus_id in sorted(boundary_ids):
        nucleus = nucleus_by_id[nucleus_id]
        obligation_id = notice_by_nucleus.get(nucleus_id)
        if (
            nucleus.retention != "should"
            or nucleus.required is not False
            or obligation_id is None
            or decision_by_id.get(obligation_id, {}).get("status")
            != "deferred_by_budget"
        ):
            continue
        field, index, ordinal = position_by_nucleus[nucleus_id]
        adjacent_rows: list[str] = []
        for relation in snapshot.relations:
            if (
                relation.required is not False
                or relation.retention != "should"
                or tuple(relation.source_relation_ids)
                != ("whole_input_source_order",)
                or nucleus_id
                not in {relation.from_nucleus_id, relation.to_nucleus_id}
            ):
                continue
            adjacent_id = str(
                relation.to_nucleus_id
                if relation.from_nucleus_id == nucleus_id
                else relation.from_nucleus_id
            )
            adjacent_position = position_by_nucleus.get(adjacent_id)
            if (
                adjacent_id not in active_nucleus_ids
                or adjacent_position is None
                or adjacent_position[0] != field
                or abs(adjacent_position[1] - index) != 1
            ):
                continue
            adjacent_rows.append(adjacent_id)
        if len(adjacent_rows) > 1:
            issues.add("S11_MATCH_BOUNDARY_COMPANION_ADJACENCY_AMBIGUOUS")
            continue
        if adjacent_rows:
            specs.append(
                (obligation_id, nucleus_id, adjacent_rows[0], field, ordinal)
            )
    specs.sort(
        key=lambda row: (
            _MATCH_BOUNDARY_FIELD_ORDER[row[3]],
            row[4],
            row[0],
        )
    )
    if len(specs) > _MATCH_BOUNDARY_COMPANION_MAXIMUM:
        issues.add("S11_MATCH_BOUNDARY_COMPANION_LIMIT_EXCEEDED")

    expected: list[tuple[str, str, str, tuple[str, ...], str]] = []
    for obligation_id, nucleus_id, adjacent_id, _field, _ordinal in specs:
        targets = tuple(
            sorted(
                (
                    candidate_id
                    for candidate_id in base_active
                    if by_id[candidate_id].get("kind") != STANCE_KIND
                    and adjacent_id
                    in by_id[candidate_id].get("nucleus_ids", ())
                ),
                key=lambda candidate_id: (
                    _MATCH_BOUNDARY_TARGET_KIND_PRIORITY.get(
                        str(by_id[candidate_id].get("kind")), 99
                    ),
                    candidate_id,
                ),
            )
        )
        if not targets:
            issues.add("S11_MATCH_BOUNDARY_COMPANION_TARGET_UNRESOLVED")
            continue
        target_id = targets[0]
        group_id = group_by_node.get(node_by_obligation.get(target_id, ""))
        if group_id is None:
            issues.add("S11_MATCH_BOUNDARY_COMPANION_GROUP_UNRESOLVED")
            continue
        expected.append(
            (
                obligation_id,
                target_id,
                group_id,
                (nucleus_id,),
                _MATCH_BOUNDARY_COMPANION_REASON,
            )
        )

    actual = tuple(
        (
            str(row.obligation_id),
            str(row.integrated_into_obligation_id),
            str(row.target_sentence_group_id),
            tuple(str(value) for value in row.nucleus_ids),
            str(row.reason_code),
        )
        for row in planning_frontier.integrations
        if row.reason_code == _MATCH_BOUNDARY_COMPANION_REASON
    )
    expected_tuple = tuple(expected)
    if actual != expected_tuple:
        issues.add("S11_MATCH_BOUNDARY_COMPANION_CONTRACT_MISMATCH")
    expected_obligation_ids = {row[0] for row in expected_tuple}
    expected_nucleus_ids = {row[3][0] for row in expected_tuple}
    if (
        not expected_obligation_ids
        <= set(planning_frontier.integrated_obligation_ids)
        or not expected_nucleus_ids <= set(planning_frontier.active_nucleus_ids)
        or any(
            row.obligation_id in expected_obligation_ids
            and row.reason_code != _MATCH_BOUNDARY_COMPANION_REASON
            for row in planning_frontier.integrations
        )
    ):
        issues.add("S11_MATCH_BOUNDARY_COMPANION_CONTRACT_MISMATCH")
    return tuple(sorted(issues))


def _independent_relation_contract(
    *,
    snapshot: Any,
    by_id: Mapping[str, Mapping[str, Any]],
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    semantic_overlay: Any,
    binding_by_nucleus: Mapping[str, Any],
    nucleus_literal_texts: Mapping[str, frozenset[str]],
) -> tuple[tuple[Any, ...], tuple[str, ...]]:
    """Rebuild the visible relation contract without overlay classifiers."""

    del content_plan
    issues: set[str] = set()
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    active_obligation_ids = frozenset(
        str(row.get("obligation_id"))
        for row in discourse_plan.get("nodes", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    )
    active_nucleus_ids = frozenset(
        nucleus_id
        for obligation_id in active_obligation_ids
        for nucleus_id in by_id.get(obligation_id, {}).get("nucleus_ids", [])
    )
    display_nucleus_ids = active_nucleus_ids
    selected_relation_ids = frozenset(
        relation_id
        for obligation_id in active_obligation_ids
        for relation_id in by_id.get(obligation_id, {}).get("relation_ids", [])
    )
    display_relation_ids = selected_relation_ids

    def slots(nucleus: Any) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    _SOURCE_FIELD_TO_SLOT[field]
                    for field in nucleus.source_fields
                    if field in _SOURCE_FIELD_TO_SLOT
                },
                key=_SLOT_ORDER.__getitem__,
            )
        )

    def sort_key(relation: Any) -> tuple[Any, ...]:
        source = nucleus_by_id[relation.from_nucleus_id]
        target = nucleus_by_id[relation.to_nucleus_id]
        source_slots = slots(source)
        target_slots = slots(target)
        cross_field = source_slots != target_slots and bool(
            ({"thought", "action"} & set(source_slots))
            and ({"thought", "action"} & set(target_slots))
        )
        explicit = (
            relation.source_relation_kind != "uncertain_connection"
            and relation.relation_type != "qualifies"
        )
        return (
            0 if relation.required else 1,
            0 if explicit else 1,
            0 if cross_field else 1,
            _RELATION_TYPE_PRIORITY.get(str(relation.relation_type), 99),
            _source_ordinal(source),
            _source_ordinal(target),
            str(relation.source_relation_kind),
            str(relation.source_id),
        )

    source_rows = sorted(
        (
            row
            for row in snapshot.relations
            if row.source_id in display_relation_ids
            and {row.from_nucleus_id, row.to_nucleus_id}
            <= display_nucleus_ids
        ),
        key=sort_key,
    )
    primary_by_signature: dict[tuple[Any, ...], Any] = {}
    aliases_by_primary: dict[str, list[str]] = {}
    primary_rows: list[Any] = []
    for row in source_rows:
        signature = (
            str(row.from_nucleus_id),
            str(row.to_nucleus_id),
            str(row.source_relation_kind),
            str(row.relation_type),
            str(row.relation_direction),
            bool(row.required),
        )
        primary = primary_by_signature.get(signature)
        if primary is None:
            primary_by_signature[signature] = row
            aliases_by_primary[row.source_id] = [row.source_id]
            primary_rows.append(row)
        else:
            aliases_by_primary[primary.source_id].append(row.source_id)
    selected_rows = sorted(
        (
            row
            for row in primary_rows
            if bool(
                set(aliases_by_primary[row.source_id])
                & selected_relation_ids
            )
        ),
        key=sort_key,
    )
    overlay_by_primary: dict[str, Any] = {}
    for relation in semantic_overlay.relations:
        primary_id = str(relation.source_relation_id)
        if primary_id in overlay_by_primary:
            issues.add("S11_MATCH_RELATION_ID_DUPLICATE")
        overlay_by_primary[primary_id] = relation
    if set(overlay_by_primary) != {row.source_id for row in selected_rows}:
        issues.add("S11_MATCH_RELATION_SOURCE_CONTRACT_MISMATCH")

    verified: list[Any] = []
    for rank, source in enumerate(selected_rows):
        relation = overlay_by_primary.get(source.source_id)
        if relation is None:
            continue
        from_nucleus = nucleus_by_id.get(source.from_nucleus_id)
        to_nucleus = nucleus_by_id.get(source.to_nucleus_id)
        from_binding = binding_by_nucleus.get(source.from_nucleus_id)
        to_binding = binding_by_nucleus.get(source.to_nucleus_id)
        if any(
            row is None
            for row in (from_nucleus, to_nucleus, from_binding, to_binding)
        ):
            issues.add("S11_MATCH_RELATION_ENDPOINT_UNRESOLVED")
            continue
        from_slots = slots(from_nucleus)
        to_slots = slots(to_nucleus)
        from_texts = nucleus_literal_texts.get(
            source.from_nucleus_id, frozenset()
        )
        to_texts = nucleus_literal_texts.get(source.to_nucleus_id, frozenset())
        explicit = (
            source.source_relation_kind != "uncertain_connection"
            and source.relation_type != "qualifies"
        )
        cross_field = from_slots != to_slots and bool(
            ({"thought", "action"} & set(from_slots))
            and ({"thought", "action"} & set(to_slots))
        )
        optional_uncertain = (
            source.required is not True
            and source.source_relation_kind == "uncertain_connection"
        )
        generic_transition_copresence = (
            _independent_generic_transition_requires_neutral_copresence(
                source,
                source_slots=from_slots,
                target_slots=to_slots,
            )
        )
        same_event = bool(
            optional_uncertain
            and source.relation_type == "qualifies"
            and from_slots != to_slots
            and any(
                _independent_same_event_restatement(left, right)
                for left in from_texts
                for right in to_texts
            )
        )
        expected_type = str(source.relation_type)
        expected_direction = str(source.relation_direction)
        evidence_grade = (
            "exact_cross_field_source_relation"
            if from_slots != to_slots
            else "exact_same_field_relation"
        )
        if generic_transition_copresence:
            expected_type = "coexists_with"
            expected_direction = "bidirectional"
            evidence_grade = "cross_field_copresence_only"
        elif same_event:
            evidence_grade = "cross_field_same_event_restatement"
        elif optional_uncertain:
            expected_type = "coexists_with"
            expected_direction = "bidirectional"
            evidence_grade = (
                "cross_field_copresence_only"
                if from_slots != to_slots
                else "source_order_copresence_only"
            )
        expected = {
            "source_relation_ids": tuple(aliases_by_primary[source.source_id]),
            "source_relation_kind": str(source.source_relation_kind),
            "relation_type": expected_type,
            "relation_direction": expected_direction,
            "from_nucleus_id": str(source.from_nucleus_id),
            "to_nucleus_id": str(source.to_nucleus_id),
            "from_source_slots": from_slots,
            "to_source_slots": to_slots,
            "from_source_anchor_ids": tuple(from_binding.source_anchor_ids),
            "to_source_anchor_ids": tuple(to_binding.source_anchor_ids),
            "from_label_anchor_ids": tuple(
                from_binding.source_label_anchor_ids
            ),
            "to_label_anchor_ids": tuple(to_binding.source_label_anchor_ids),
            "from_endpoint_role": _independent_endpoint_role(from_nucleus),
            "to_endpoint_role": _independent_endpoint_role(to_nucleus),
            "required": bool(source.required),
            "explicit": explicit,
            "cross_field": cross_field,
            "source_order": (
                _source_ordinal(from_nucleus),
                _source_ordinal(to_nucleus),
            ),
            "priority_rank": rank,
            "evidence_grade": evidence_grade,
        }
        if any(getattr(relation, key, None) != value for key, value in expected.items()):
            issues.add("S11_MATCH_RELATION_SOURCE_CONTRACT_MISMATCH")
            continue
        for alias_id in relation.source_relation_ids:
            alias = next(
                (row for row in snapshot.relations if row.source_id == alias_id),
                None,
            )
            if alias is None or (
                str(alias.from_nucleus_id),
                str(alias.to_nucleus_id),
                str(alias.source_relation_kind),
                str(alias.relation_type),
                str(alias.relation_direction),
                bool(alias.required),
            ) != (
                str(source.from_nucleus_id),
                str(source.to_nucleus_id),
                str(source.source_relation_kind),
                str(source.relation_type),
                str(source.relation_direction),
                bool(source.required),
            ):
                issues.add("S11_MATCH_RELATION_ALIAS_SIGNATURE_MISMATCH")
        verified.append(relation)
    return tuple(verified), tuple(sorted(issues))


@dataclass(frozen=True, slots=True)
class _Step11IndependentReference:
    reference_ordinal: int
    endpoint_role: str
    source_slot: str
    source_literal: str
    source_anchor_ids: tuple[str, ...]
    nucleus_ids: tuple[str, ...]
    source_identity: tuple[Any, ...]


def _independent_reference_registry(
    *,
    active_nucleus_ids: frozenset[str],
    semantic_overlay: Any,
    relations: Sequence[Any],
) -> tuple[tuple[_Step11IndependentReference, ...], tuple[str, ...]]:
    """Rebuild the exact active reference registry without forward metadata."""

    issues: set[str] = set()
    anchor_by_id = {row.anchor_id: row for row in semantic_overlay.anchors}
    label_by_id = {
        row.label_anchor_id: row for row in semantic_overlay.label_anchors
    }
    role_by_anchor: dict[str, str] = {}
    for relation in relations:
        endpoint_rows = (
            (
                tuple(
                    (*relation.from_source_anchor_ids,
                     *relation.from_label_anchor_ids)
                ),
                str(relation.from_endpoint_role),
            ),
            (
                tuple(
                    (*relation.to_source_anchor_ids,
                     *relation.to_label_anchor_ids)
                ),
                str(relation.to_endpoint_role),
            ),
        )
        for anchor_ids, role in endpoint_rows:
            for anchor_id in anchor_ids:
                previous = role_by_anchor.setdefault(anchor_id, role)
                if previous != role:
                    issues.add("S11_MATCH_REFERENCE_ROLE_AMBIGUOUS")

    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for binding in semantic_overlay.nucleus_anchor_bindings:
        if binding.nucleus_id not in active_nucleus_ids:
            continue
        for anchor_id in binding.source_anchor_ids:
            anchor = anchor_by_id.get(anchor_id)
            if anchor is None:
                issues.add("S11_MATCH_REFERENCE_SOURCE_UNRESOLVED")
                continue
            identity = (
                "text",
                str(anchor.source_slot),
                int(anchor.start),
                int(anchor.end),
            )
            state = grouped.setdefault(
                identity,
                {
                    "source_slot": str(anchor.source_slot),
                    "source_literal": str(anchor.text),
                    "anchor_ids": set(),
                    "nucleus_ids": set(),
                    "roles": set(),
                },
            )
            state["anchor_ids"].add(anchor_id)
            state["nucleus_ids"].add(str(binding.nucleus_id))
            state["roles"].add(
                role_by_anchor.get(
                    anchor_id,
                    "action"
                    if anchor.source_slot == "action"
                    else "proposition",
                )
            )
        for anchor_id in binding.source_label_anchor_ids:
            anchor = label_by_id.get(anchor_id)
            if anchor is None:
                issues.add("S11_MATCH_REFERENCE_SOURCE_UNRESOLVED")
                continue
            identity = (
                "label",
                str(anchor.source_slot),
                str(anchor.source_field),
                int(anchor.source_ordinal),
            )
            state = grouped.setdefault(
                identity,
                {
                    "source_slot": str(anchor.source_slot),
                    "source_literal": str(anchor.label),
                    "anchor_ids": set(),
                    "nucleus_ids": set(),
                    "roles": set(),
                },
            )
            state["anchor_ids"].add(anchor_id)
            state["nucleus_ids"].add(str(binding.nucleus_id))
            state["roles"].add(
                role_by_anchor.get(
                    anchor_id,
                    "affect"
                    if anchor.source_slot == "emotion"
                    else "proposition",
                )
            )

    text_ranges = sorted(
        (
            str(identity[1]),
            int(identity[2]),
            int(identity[3]),
        )
        for identity in grouped
        if identity[0] == "text"
    )
    for index, (slot, start, end) in enumerate(text_ranges):
        for other_slot, other_start, other_end in text_ranges[index + 1 :]:
            if other_slot != slot or other_start >= end:
                break
            if start < other_end and other_start < end:
                issues.add("S11_MATCH_REFERENCE_RANGE_OVERLAP")

    ordered_identities = sorted(
        grouped,
        key=lambda identity: (
            _SLOT_ORDER[str(identity[1])],
            0 if identity[0] == "text" else 1,
            identity[2],
            identity[3],
        ),
    )
    result: list[_Step11IndependentReference] = []
    for ordinal, identity in enumerate(ordered_identities, start=1):
        state = grouped[identity]
        roles = set(state["roles"])
        nuclei = tuple(sorted(state["nucleus_ids"]))
        if len(roles) != 1 or not nuclei:
            issues.add("S11_MATCH_REFERENCE_CONTRACT_UNRESOLVED")
            continue
        result.append(
            _Step11IndependentReference(
                reference_ordinal=ordinal,
                endpoint_role=next(iter(roles)),
                source_slot=str(state["source_slot"]),
                source_literal=str(state["source_literal"]),
                source_anchor_ids=tuple(sorted(state["anchor_ids"])),
                nucleus_ids=nuclei,
                source_identity=identity,
            )
        )
    if not result:
        issues.add("S11_MATCH_REFERENCE_REGISTRY_EMPTY")
    return tuple(result), tuple(sorted(issues))


def _independent_mixed_emotion_surface_issues(
    atoms: Sequence[Step11ParsedAtom],
    *,
    expected_positive_label: str,
    expected_negative_label: str,
    expected_references: tuple[
        Step11EndpointReference, Step11EndpointReference
    ],
) -> tuple[str, ...]:
    """Check the rc0027 literal-owning mixed-emotion unit."""

    issues: set[str] = set()
    compounds = tuple(
        row
        for row in atoms
        if type(row) is Step11ParsedAtom
        and row.form_id.startswith(
            "obligation_fused:mixed_emotion:"
        )
    )
    if len(expected_references) != 2:
        issues.add("S11_MATCH_MIXED_EMOTION_UNRESOLVED")
        return tuple(sorted(issues))
    endpoint_rows = tuple(
        sorted(
            (
                (expected_references[0], expected_positive_label),
                (expected_references[1], expected_negative_label),
            ),
            key=lambda row: row[0].reference_ordinal,
        )
    )
    ordered_references = tuple(row[0] for row in endpoint_rows)
    if len(compounds) != 1:
        issues.add("S11_MATCH_MIXED_EMOTION_REALIZATION_MODE_MISMATCH")
        return tuple(sorted(issues))
    atom = compounds[0]
    if atom.source_fragments != tuple(row[1] for row in endpoint_rows):
        issues.add("S11_MATCH_MIXED_EMOTION_COMPOUND_ORDER_MISMATCH")
    if (
        not {"nucleus_notice", "mixed_emotion_relation"}
        <= set(atom.claim_kinds)
        or atom.source_slot_hints != ("emotion", "emotion")
        or atom.predicate_role != "affect"
        or atom.realization_status != "selected_label"
        or atom.relation_type != "coexists_with"
        or atom.relation_direction != "bidirectional"
        or atom.relation_endpoint_roles != ("affect", "affect")
        or atom.introduced_reference is not None
        or atom.compound_label_references
        or atom.relation_endpoint_references
        or atom.unknown_target_references
        or atom.reception_antecedent_references
    ):
        issues.add("S11_MATCH_MIXED_EMOTION_COMPOUND_CONTRACT_MISMATCH")
    return tuple(sorted(issues))


def _complete_source_clauses(value: str) -> frozenset[str]:
    rows = {
        match.group(0).strip()
        for match in re.finditer(r"[^。！？!?]+(?:[。！？!?]+|$)", value)
        if match.group(0).strip()
    }
    if value:
        rows.add(value)
    return frozenset(rows)


@dataclass(frozen=True, slots=True)
class _Step11IndependentNucleusSourceRange:
    nucleus_id: str
    evidence_span_id: str
    source_slot: str
    start: int
    end: int
    text: str


def _independent_display_range(
    source_text: str,
    canonical_display: str,
    source_start: int,
    source_end: int,
) -> tuple[int, int] | None:
    """Map one exact source range into NFC/whitespace-canonical display.

    This inverse-side implementation deliberately does not call the forward
    overlay range mapper.  A boundary that bisects an NFC composition, starts
    or ends in whitespace, or cannot be reproduced byte-for-byte fails closed.
    """

    if (
        type(source_text) is not str
        or type(canonical_display) is not str
        or type(source_start) is not int
        or type(source_end) is not int
        or source_start < 0
        or source_end <= source_start
        or source_end > len(source_text)
        or source_text[source_start].isspace()
        or source_text[source_end - 1].isspace()
    ):
        return None

    # source start/end, display start/end, raw token, canonical token
    tokens: list[tuple[int, int, int, int, str, str]] = []
    source_cursor = 0
    display_cursor = 0
    while source_cursor < len(source_text):
        while (
            source_cursor < len(source_text)
            and source_text[source_cursor].isspace()
        ):
            source_cursor += 1
        if source_cursor >= len(source_text):
            break
        token_start = source_cursor
        while (
            source_cursor < len(source_text)
            and not source_text[source_cursor].isspace()
        ):
            source_cursor += 1
        token_end = source_cursor
        raw_token = source_text[token_start:token_end]
        canonical_token = unicodedata.normalize("NFC", raw_token)
        if tokens:
            display_cursor += 1
        display_start = display_cursor
        display_cursor += len(canonical_token)
        tokens.append(
            (
                token_start,
                token_end,
                display_start,
                display_cursor,
                raw_token,
                canonical_token,
            )
        )
    if " ".join(row[5] for row in tokens) != canonical_display:
        return None
    start_token = next(
        (row for row in tokens if row[0] <= source_start < row[1]), None
    )
    end_token = next(
        (row for row in tokens if row[0] < source_end <= row[1]), None
    )
    if start_token is None or end_token is None:
        return None

    def boundary(
        token: tuple[int, int, int, int, str, str],
        source_boundary: int,
    ) -> int | None:
        token_start, _, display_start, _, raw_token, canonical_token = token
        relative = source_boundary - token_start
        prefix = unicodedata.normalize("NFC", raw_token[:relative])
        suffix = unicodedata.normalize("NFC", raw_token[relative:])
        if prefix + suffix != canonical_token:
            return None
        return display_start + len(prefix)

    display_start = boundary(start_token, source_start)
    display_end = boundary(end_token, source_end)
    if display_start is None or display_end is None:
        return None
    fragment = _normalise_text(source_text[source_start:source_end])
    if (
        not fragment
        or display_end <= display_start
        or display_end > len(canonical_display)
        or canonical_display[display_start:display_end] != fragment
    ):
        return None
    return display_start, display_end


def _independent_semantic_unit_source_range(
    actual_source_id: str,
    spans: Sequence[Any],
) -> tuple[Any, int, int] | None:
    """Resolve one opaque semantic-unit id from source spans independently."""

    matches: list[tuple[Any, int, int]] = []
    for span in spans:
        raw = str(getattr(span, "raw_text", ""))
        match = _TWO_PREDICATE_CONNECTIVE_RE.fullmatch(raw)
        if match is None:
            continue
        separator_index = match.start("right") - 1
        for role, fragment, start, end in (
            ("antecedent", match.group("left"), 0, separator_index),
            (
                "consequent",
                match.group("right"),
                match.start("right"),
                len(raw),
            ),
        ):
            candidate = "semantic_unit:u" + artifact_sha256(
                {
                    "adapter_version": (
                        GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
                    ),
                    "parent_nucleus_id": f"nucleus:{span.span_id}",
                    "source_span_id": str(span.span_id),
                    "start_index": start,
                    "end_index": end,
                    "source_fragment_sha256": artifact_sha256(
                        {"source_fragment": fragment}
                    ),
                    "unit_role": role,
                }
            )[:24]
            if candidate == actual_source_id:
                matches.append((span, start, end))
    return matches[0] if len(matches) == 1 else None


def _independent_dependent_relation_residue_end(
    *,
    nucleus_id: str,
    span: Any,
    spans: Sequence[Any],
    relations: Sequence[Any],
    active_relation_ids: frozenset[str],
) -> tuple[int, tuple[str, ...]]:
    """Recompute a relation-owned leading residue without forward helpers."""

    if (
        type(span.start_index) is not int
        or span.start_index < 0
        or span.source_field not in {"memo", "memo_action"}
    ):
        return 0, ()
    marker_rows = tuple(
        row
        for row in spans
        if row.source_field == span.source_field
        and row.detected_type == "relation_marker"
        and type(row.end_index) is int
        and row.end_index == span.start_index
    )
    if len(marker_rows) > 1:
        return 0, ("S11_MATCH_DEPENDENT_RESIDUE_MARKER_AMBIGUOUS",)
    if not marker_rows:
        return 0, ()
    marker_ref = f"evidence_relation_marker:{marker_rows[0].span_id}"
    owners = tuple(
        relation
        for relation in relations
        if relation.source_id in active_relation_ids
        and relation.to_nucleus_id == nucleus_id
        and marker_ref in relation.source_relation_ids
    )
    if len(owners) > 1:
        return 0, ("S11_MATCH_DEPENDENT_RESIDUE_RELATION_AMBIGUOUS",)
    if not owners:
        return 0, ()
    match = _MATCH_LEADING_DEPENDENT_RELATION_RESIDUE_RE.match(
        str(span.raw_text)
    )
    if match is None or match.end() >= len(str(span.raw_text)):
        return 0, ()
    return match.end(), ()


def _independent_nucleus_source_ranges(
    current_input: Mapping[str, Any],
    *,
    projection: Mapping[str, Any],
    snapshot: Any,
    active_nucleus_ids: frozenset[str],
    active_relation_ids: frozenset[str] = frozenset(),
) -> tuple[
    dict[str, _Step11IndependentNucleusSourceRange],
    tuple[str, ...],
]:
    """Rebuild exact nucleus ownership from app input and Evidence Ledger."""

    issues: set[str] = set()
    try:
        normalized = normalize_emlis_current_input(dict(current_input))
        spans = tuple(build_evidence_ledger(dict(current_input)))
        report = validate_evidence_ledger(
            spans,
            current_input=current_input,
        )
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        return {}, ("S11_MATCH_EVIDENCE_REBUILD_FAILED",)
    if not report.valid:
        return {}, ("S11_MATCH_EVIDENCE_REBUILD_FAILED",)
    source_texts = {
        "thought": normalized.get("memo"),
        "action": normalized.get("memo_action"),
    }
    if any(type(value) is not str for value in source_texts.values()):
        return {}, ("S11_MATCH_EVIDENCE_REBUILD_FAILED",)
    text_spans = tuple(
        row
        for row in spans
        if str(row.source_field) in {"memo", "memo_action"}
    )
    span_by_id = {str(row.span_id): row for row in text_spans}
    if len(span_by_id) != len(text_spans):
        return {}, ("S11_MATCH_EVIDENCE_REBUILD_FAILED",)
    nucleus_by_id = {
        str(row.source_id): row
        for row in snapshot.nuclei
        if str(row.source_id) in active_nucleus_ids
    }
    if set(nucleus_by_id) != set(active_nucleus_ids):
        issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")

    result: dict[str, _Step11IndependentNucleusSourceRange] = {}
    for nucleus_id in sorted(active_nucleus_ids):
        nucleus = nucleus_by_id.get(nucleus_id)
        if nucleus is None:
            continue
        slots = _slots_for_nucleus(snapshot, nucleus_id)
        text_slots = tuple(
            slot for slot in slots if slot in {"thought", "action"}
        )
        if not text_slots:
            continue
        actual_source_id = str(nucleus.actual_source_id)
        base_match = _BASE_NUCLEUS_SPAN_RE.fullmatch(actual_source_id)
        source_range: tuple[Any, int, int] | None = None
        if base_match is not None:
            span = span_by_id.get(base_match.group(1))
            if span is not None:
                relative_start, residue_issues = (
                    _independent_dependent_relation_residue_end(
                        nucleus_id=nucleus_id,
                        span=span,
                        spans=text_spans,
                        relations=snapshot.relations,
                        active_relation_ids=active_relation_ids,
                    )
                )
                issues.update(residue_issues)
                source_range = (
                    span,
                    relative_start,
                    len(str(span.raw_text)),
                )
        elif actual_source_id.startswith("semantic_unit:"):
            source_range = _independent_semantic_unit_source_range(
                actual_source_id,
                text_spans,
            )
        if source_range is None:
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        span, relative_start, relative_end = source_range
        source_slot = _SOURCE_FIELD_TO_SLOT.get(str(span.source_field))
        if source_slot not in text_slots:
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        source_text = source_texts[source_slot]
        assert type(source_text) is str
        span_start = int(span.start_index)
        span_end = int(span.end_index)
        if (
            span_start < 0
            or span_end <= span_start
            or span_end > len(source_text)
            or _normalise_text(source_text[span_start:span_end])
            != _normalise_text(str(span.raw_text))
        ):
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        span_display_range = _independent_display_range(
            source_text,
            str(projection[source_slot]),
            span_start,
            span_end,
        )
        if span_display_range is None:
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        span_display_start, span_display_end = span_display_range
        canonical_span = str(projection[source_slot])[
            span_display_start:span_display_end
        ]
        relative_display_range = _independent_display_range(
            str(span.raw_text),
            canonical_span,
            relative_start,
            relative_end,
        )
        if relative_display_range is None:
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        relative_display_start, relative_display_end = relative_display_range
        start = span_display_start + relative_display_start
        end = span_display_start + relative_display_end
        text = str(projection[source_slot])[start:end]
        if not text or nucleus_id in result:
            issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
            continue
        result[nucleus_id] = _Step11IndependentNucleusSourceRange(
            nucleus_id=nucleus_id,
            evidence_span_id=str(span.span_id),
            source_slot=source_slot,
            start=start,
            end=end,
            text=text,
        )
    expected_text_nuclei = {
        nucleus_id
        for nucleus_id in active_nucleus_ids
        if {
            slot
            for slot in _slots_for_nucleus(snapshot, nucleus_id)
            if slot in {"thought", "action"}
        }
    }
    if set(result) != expected_text_nuclei:
        issues.add("S11_MATCH_NUCLEUS_SOURCE_RANGE_UNRESOLVED")
    return result, tuple(sorted(issues))


def _independent_anchor_binding_contract(
    *,
    current_input: Mapping[str, Any],
    projection: Mapping[str, Any],
    snapshot: Any,
    active_nucleus_ids: frozenset[str],
    semantic_overlay: Any,
    active_relation_ids: frozenset[str] = frozenset(),
) -> tuple[dict[str, frozenset[str]], tuple[str, ...]]:
    """Validate overlay anchors against only source snapshot and app fields."""

    issues: set[str] = set()
    expected_labels = {
        ("emotion", "emotion_details", index): (label, strength)
        for index, (label, strength) in enumerate(projection["emotion_details"])
    }
    expected_labels.update(
        {
            ("category", "category", index): (label, None)
            for index, label in enumerate(projection["category"])
        }
    )
    evidence_alias_by_actual = {
        str(row.actual_source_id): str(row.alias_source_id)
        for row in snapshot.source_id_alias_bindings
        if str(row.source_kind) == "evidence"
    }
    label_by_id: dict[str, Any] = {}
    seen_label_keys: set[tuple[str, str, int]] = set()
    for row in semantic_overlay.label_anchors:
        key = (row.source_slot, row.source_field, row.source_ordinal)
        expected = expected_labels.get(key)
        material = {
            "source_slot": row.source_slot,
            "source_field": row.source_field,
            "source_ordinal": row.source_ordinal,
            "label": row.label,
            "strength": row.strength,
            "evidence_span_id": row.evidence_span_id,
            "label_sha256": row.label_sha256,
            "evidence_grade": row.evidence_grade,
        }
        expected_id = "s11lbl_" + artifact_sha256(material)[:16]
        if (
            expected != (row.label, row.strength)
            or row.label_sha256
            != hashlib.sha256(row.label.encode("utf-8")).hexdigest()
            or row.evidence_span_id not in evidence_alias_by_actual
            or not any(
                row.source_field in nucleus.source_fields
                and row.evidence_span_id in nucleus.surface_anchor_ids
                and evidence_alias_by_actual[row.evidence_span_id]
                in nucleus.evidence_ids
                for nucleus in snapshot.nuclei
            )
            or row.evidence_grade != "exact_structured_evidence_label"
            or row.label_anchor_id != expected_id
            or row.label_anchor_id in label_by_id
        ):
            issues.add("S11_MATCH_LABEL_ANCHOR_CONTRACT_MISMATCH")
        label_by_id[row.label_anchor_id] = row
        seen_label_keys.add(key)
    if seen_label_keys != set(expected_labels):
        issues.add("S11_MATCH_LABEL_ANCHOR_CONTRACT_MISMATCH")

    anchor_by_id: dict[str, Any] = {}
    nucleus_source_ranges, nucleus_source_range_issues = (
        _independent_nucleus_source_ranges(
            current_input,
            projection=projection,
            snapshot=snapshot,
            active_nucleus_ids=active_nucleus_ids,
            active_relation_ids=active_relation_ids,
        )
    )
    issues.update(nucleus_source_range_issues)
    for row in semantic_overlay.anchors:
        source = projection.get(row.source_slot)
        material = {
            "source_slot": row.source_slot,
            "role": row.role,
            "start": row.start,
            "end": row.end,
            "text_sha256": row.text_sha256,
        }
        expected_id = "s11anc_" + artifact_sha256(material)[:16]
        if (
            row.source_slot not in {"thought", "action"}
            or type(source) is not str
            or not 0 <= row.start < row.end <= len(source)
            or source[row.start : row.end] != row.text
            or row.text_sha256
            != hashlib.sha256(row.text.encode("utf-8")).hexdigest()
            or row.anchor_id != expected_id
            or row.anchor_id in anchor_by_id
        ):
            issues.add("S11_MATCH_SOURCE_ANCHOR_CONTRACT_MISMATCH")
        anchor_by_id[row.anchor_id] = row

    display_nucleus_ids = active_nucleus_ids
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    binding_by_id: dict[str, Any] = {}
    nucleus_literal_texts: dict[str, frozenset[str]] = {}
    for binding in semantic_overlay.nucleus_anchor_bindings:
        nucleus = nucleus_by_id.get(binding.nucleus_id)
        if nucleus is None or binding.nucleus_id in binding_by_id:
            issues.add("S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH")
            continue
        slots = _slots_for_nucleus(snapshot, binding.nucleus_id)
        source_anchors = tuple(
            anchor_by_id.get(anchor_id) for anchor_id in binding.source_anchor_ids
        )
        label_anchors = tuple(
            label_by_id.get(anchor_id)
            for anchor_id in binding.source_label_anchor_ids
        )
        expected_role = (
            "action"
            if "action" in slots
            else "thought"
            if "thought" in slots
            else "label"
        )
        expected_label_ids = tuple(
            row.label_anchor_id
            for row in semantic_overlay.label_anchors
            if row.evidence_span_id in set(nucleus.surface_anchor_ids)
            and evidence_alias_by_actual.get(row.evidence_span_id)
            in set(nucleus.evidence_ids)
        )
        text_slots = tuple(
            slot for slot in slots if slot in {"thought", "action"}
        )
        expected_source_range = nucleus_source_ranges.get(
            binding.nucleus_id
        )
        exact_source_range_green = (
            not text_slots
            and not source_anchors
            or len(source_anchors) == 1
            and expected_source_range is not None
            and source_anchors[0] is not None
            and source_anchors[0].role == "nucleus"
            and source_anchors[0].source_slot
            == expected_source_range.source_slot
            and source_anchors[0].start == expected_source_range.start
            and source_anchors[0].end == expected_source_range.end
            and source_anchors[0].text == expected_source_range.text
        )
        if (
            tuple(binding.source_slots) != slots
            or binding.source_role != expected_role
            or str(binding.modality) != str(nucleus.modality)
            or str(binding.temporal_scope) != str(nucleus.temporal_scope)
            or any(row is None for row in source_anchors)
            or any(row is None for row in label_anchors)
            or any(row.source_slot not in slots for row in source_anchors if row)
            or any(row.source_slot not in slots for row in label_anchors if row)
            or tuple(binding.source_label_anchor_ids) != expected_label_ids
            or not exact_source_range_green
            or (not source_anchors and not label_anchors)
        ):
            issues.add("S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH")
        binding_by_id[binding.nucleus_id] = binding
        nucleus_literal_texts[binding.nucleus_id] = frozenset(
            [row.text for row in source_anchors if row is not None]
            + [row.label for row in label_anchors if row is not None]
        )
    for nucleus in snapshot.nuclei:
        if nucleus.source_id not in display_nucleus_ids:
            continue
        label_texts = tuple(
            row.label
            for row in semantic_overlay.label_anchors
            if row.evidence_span_id in set(nucleus.surface_anchor_ids)
            and evidence_alias_by_actual.get(row.evidence_span_id)
            in set(nucleus.evidence_ids)
        )
        if label_texts:
            nucleus_literal_texts[nucleus.source_id] = frozenset(label_texts)
    if set(binding_by_id) != set(display_nucleus_ids):
        issues.add("S11_MATCH_NUCLEUS_BINDING_CONTRACT_MISMATCH")
    return nucleus_literal_texts, tuple(sorted(issues))


def _validated_parents(
    inventory_result: Any,
    content_plan: Any,
    discourse_plan: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise Step11InverseSurfaceError("S11_MATCH_INVENTORY_REQUIRED")
    ledger = inventory_result.ledger
    try:
        a = validate_semantic_obligation_inventory(ledger, source_snapshot=inventory_result.source_snapshot)
        b = validate_content_selection_policy(content_plan, inventory_result=inventory_result)
        c = validate_discourse_plan(discourse_plan, content_plan=content_plan, obligation_ledger=ledger)
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError) as exc:
        raise Step11InverseSurfaceError("S11_MATCH_PARENT_REVALIDATION_FAILED") from exc
    if a or b or c:
        raise Step11InverseSurfaceError("S11_MATCH_PARENT_REVALIDATION_FAILED")
    rows = ledger.get("obligations")
    if type(rows) is not list:
        raise Step11InverseSurfaceError("S11_MATCH_LEDGER_ROWS_INVALID")
    by_id = {row.get("obligation_id"): row for row in rows if type(row) is dict and type(row.get("obligation_id")) is str}
    if len(by_id) != len(rows):
        raise Step11InverseSurfaceError("S11_MATCH_LEDGER_IDENTITY_INVALID")
    return ledger, by_id


def _fragment_slots(
    witness: Step11ParsedSurfaceWitness,
    allowed: Mapping[str, tuple[str, ...]],
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    mapping: dict[str, tuple[str, ...]] = {}
    issues: list[str] = []
    for atom in witness.atoms:
        slots: list[str] = []
        for index, fragment in enumerate(atom.source_fragments):
            candidates = tuple(
                slot for slot, values in allowed.items() if fragment in values
            )
            if (
                not candidates
                and any(
                    phrase.anchor_text == fragment
                    for phrase in atom.grounded_phrases
                )
            ):
                candidates = tuple(
                    slot
                    for slot, values in allowed.items()
                    if any(
                        fragment in value for value in values
                    )
                )
            if not candidates and atom.self_denial_not_fact:
                core = _semantic_core_text(fragment)
                candidates = tuple(
                    slot
                    for slot, values in allowed.items()
                    if core
                    and any(
                        _semantic_core_text(value) == core for value in values
                    )
                )
            hint = atom.source_slot_hints[index] if index < len(atom.source_slot_hints) else None
            if hint is not None:
                candidates = tuple(slot for slot in candidates if slot == hint)
            if not candidates:
                issues.append("S11_MATCH_FRAGMENT_NOT_SOURCE_BACKED")
            slots.extend(candidates)
        mapping[atom.atom_id] = tuple(sorted(set(slots), key=_SLOT_ORDER.__getitem__))
    return mapping, tuple(sorted(set(issues)))


def _authorised_fragments_by_slot(
    projection: Mapping[str, Any],
    semantic_overlay: Any,
) -> dict[str, tuple[str, ...]]:
    allowed: dict[str, tuple[str, ...]] = {
        "thought": _allowed_text_fragments(projection["thought"]),
        "action": _allowed_text_fragments(projection["action"]),
        "emotion": (
            tuple(
                dict.fromkeys(
                    (*projection["emotion"], "・".join(projection["emotion"]))
                )
            )
            if projection["emotion"]
            else ()
        ),
        "category": (
            tuple(
                dict.fromkeys(
                    (*projection["category"], "・".join(projection["category"]))
                )
            )
            if projection["category"]
            else ()
        ),
    }
    for anchor in semantic_overlay.anchors:
        if anchor.source_slot not in {"thought", "action"}:
            continue
        allowed[anchor.source_slot] = tuple(
            dict.fromkeys((*allowed[anchor.source_slot], anchor.text))
        )
    return allowed


def _terminal_self_denial_obligation_pairs(
    by_id: Mapping[str, Mapping[str, Any]],
    discourse_plan: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    """Independently resolve targeted self/counter terminal pairs."""

    active_ids = {
        str(row.get("obligation_id"))
        for row in discourse_plan.get("nodes", [])
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    target_ids = sorted(
        obligation_id
        for obligation_id in active_ids
        if by_id.get(obligation_id, {}).get("kind")
        == "self_denial_boundary"
    )
    pairs: list[tuple[str, str]] = []
    consumed_counters: set[str] = set()
    for target_id in target_ids:
        target = by_id[target_id]
        nuclei = set(target.get("nucleus_ids", []))
        counters = tuple(
            obligation_id
            for obligation_id in active_ids
            if by_id.get(obligation_id, {}).get("kind")
            == "bounded_counterposition"
            and nuclei
            and set(by_id[obligation_id].get("nucleus_ids", [])) == nuclei
            and obligation_id in set(target.get("must_not_merge_with", []))
            and target_id
            in set(by_id[obligation_id].get("must_not_merge_with", []))
        )
        if len(counters) > 1:
            raise Step11InverseSurfaceError(
                "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID"
            )
        if not counters:
            continue
        if counters[0] in consumed_counters:
            raise Step11InverseSurfaceError(
                "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID"
            )
        consumed_counters.add(counters[0])
        pairs.append((target_id, counters[0]))
    active_counters = {
        obligation_id
        for obligation_id in active_ids
        if by_id.get(obligation_id, {}).get("kind")
        == "bounded_counterposition"
    }
    if active_counters != consumed_counters:
        raise Step11InverseSurfaceError(
            "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID"
        )
    if pairs:
        node_for_obligation = {
            str(row.get("obligation_id")): str(row.get("node_id"))
            for row in discourse_plan.get("nodes", [])
            if type(row) is dict
            and type(row.get("obligation_id")) is str
            and type(row.get("node_id")) is str
        }
        units = tuple(
            (
                node_for_obligation[self_id],
                node_for_obligation[counter_id],
            )
            for self_id, counter_id in pairs
        )
        observation_groups = tuple(
            tuple(group.get("node_ids", []))
            for group in discourse_plan.get("sentence_groups", [])
            if type(group) is dict
            and group.get("section_role") == "observation"
        )
        group_index = {
            node_id: index
            for index, group in enumerate(observation_groups)
            for node_id in group
        }
        edge_set = {
            (edge.get("from"), edge.get("to"), edge.get("type"))
            for edge in discourse_plan.get("edges", [])
            if type(edge) is dict
        }
        if any(
            left not in group_index
            or right not in group_index
            or group_index[left] == group_index[right]
            or (left, right, "separates_self_denial_from") not in edge_set
            for left, right in units
        ):
            raise Step11InverseSurfaceError(
                "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID"
            )
    return tuple(pairs)


def _independent_reception_owner_contract(
    *,
    snapshot: Any,
    by_id: Mapping[str, Mapping[str, Any]],
    discourse_plan: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Rebuild rc0026 reception ownership without trusting the overlay."""

    nodes = discourse_plan.get("nodes")
    if type(nodes) is not list or any(type(row) is not dict for row in nodes):
        raise Step11InverseSurfaceError(
            "S11_MATCH_RECEPTION_NODE_ROWS_INVALID"
        )
    node_by_obligation = {
        str(row.get("obligation_id")): row
        for row in nodes
        if type(row.get("obligation_id")) is str
    }
    if len(node_by_obligation) != len(nodes):
        raise Step11InverseSurfaceError(
            "S11_MATCH_RECEPTION_NODE_BINDING_CONTRACT_MISMATCH"
        )
    active_ids = frozenset(node_by_obligation)
    opportunities = getattr(snapshot, "reception_opportunities", None)
    nuclei = getattr(snapshot, "nuclei", None)
    if type(opportunities) is not tuple or type(nuclei) is not tuple:
        raise Step11InverseSurfaceError(
            "S11_MATCH_RECEPTION_SOURCE_AUTHORITY_INVALID"
        )
    opportunity_by_id = {
        row.source_id: row
        for row in opportunities
        if type(getattr(row, "source_id", None)) is str
    }
    nucleus_by_id = {
        row.source_id: row
        for row in nuclei
        if type(getattr(row, "source_id", None)) is str
    }
    if (
        len(opportunity_by_id) != len(opportunities)
        or len(nucleus_by_id) != len(nuclei)
    ):
        raise Step11InverseSurfaceError(
            "S11_MATCH_RECEPTION_SOURCE_AUTHORITY_INVALID"
        )

    def exact_owner_ids(
        nucleus_ids: Sequence[str],
        *,
        reception_act: str,
        preferred_obligation_ids: Sequence[str] = (),
    ) -> tuple[str, ...]:
        wanted = frozenset(nucleus_ids)
        candidates = tuple(
            obligation_id
            for obligation_id in sorted(active_ids)
            if by_id.get(obligation_id, {}).get("kind") != STANCE_KIND
            and frozenset(by_id.get(obligation_id, {}).get("nucleus_ids", []))
            == wanted
        )
        if not wanted or not candidates:
            return ()
        preferred = tuple(
            row for row in preferred_obligation_ids if row in candidates
        )
        pool = preferred or candidates
        act_ranks = _MATCH_RECEPTION_ACT_KIND_RANK.get(reception_act, {})

        def rank(obligation_id: str) -> tuple[int, int, str]:
            kind = str(by_id[obligation_id].get("kind"))
            return (
                int(act_ranks.get(kind, 20)),
                int(_MATCH_RECEPTION_OWNER_KIND_RANK.get(kind, 20)),
                obligation_id,
            )

        ordered = tuple(sorted(pool, key=rank))
        best_rank = rank(ordered[0])[:2]
        best = tuple(row for row in ordered if rank(row)[:2] == best_rank)
        if len(best) != 1:
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_EXACT_OWNER_AMBIGUOUS"
            )
        return best

    action_text = projection.get("action")
    if type(action_text) is not str:
        raise Step11InverseSurfaceError(
            "S11_MATCH_RECEPTION_ACTION_SOURCE_INVALID"
        )
    progressive = bool(
        action_text
        and _MATCH_MAIN_ACTION_PROGRESSIVE_RE.search(action_text) is not None
    )
    purpose_correction = bool(
        progressive
        and _MATCH_PURPOSE_NEGATION_PREFIX_RE.search(action_text) is not None
    )
    eligible_action_nuclei = frozenset(
        nucleus_id
        for nucleus_id, nucleus in nucleus_by_id.items()
        if getattr(nucleus, "kind", None) == "action"
        and "memo_action" in getattr(nucleus, "source_fields", ())
        and "semantic_role:concrete_action_evidence"
        in getattr(nucleus, "source_attribute_codes", ())
        and progressive
    )

    def action_lifecycle_for(
        nucleus_ids: Sequence[str],
    ) -> str:
        return _independent_action_lifecycle_for_nuclei(
            nucleus_ids,
            nucleus_by_id=nucleus_by_id,
            action_text=action_text,
        )

    def corrected_action_support(
        primary_nucleus_ids: Sequence[str],
    ) -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
        candidates = tuple(
            obligation_id
            for obligation_id in sorted(active_ids)
            if by_id.get(obligation_id, {}).get("kind")
            == "intention_or_next_action"
            and frozenset(by_id[obligation_id].get("nucleus_ids", []))
            and frozenset(by_id[obligation_id].get("nucleus_ids", []))
            <= eligible_action_nuclei
        )
        if len(candidates) > 1:
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_ACTION_OWNER_AMBIGUOUS"
            )
        if not candidates:
            return (), (), "none", "not_applicable"
        obligation_id = candidates[0]
        action_nuclei = tuple(by_id[obligation_id].get("nucleus_ids", []))
        if set(action_nuclei) <= set(primary_nucleus_ids):
            return (), (), "none", "reported_ongoing"
        return (
            (obligation_id,),
            action_nuclei,
            (
                "legacy_purpose_negation_scope_corrected_action"
                if purpose_correction
                else "source_progressive_concrete_action"
            ),
            "reported_ongoing",
        )

    result: dict[str, dict[str, Any]] = {}
    for reception_id in sorted(active_ids):
        reception = by_id.get(reception_id)
        if reception is None or reception.get("kind") != STANCE_KIND:
            continue
        source_target_ids = tuple(reception.get("target_obligation_ids", []))
        reception_node = node_by_obligation.get(reception_id)
        source_target_nodes = tuple(
            node_by_obligation.get(row) for row in source_target_ids
        )
        allowed_acts = tuple(reception.get("allowed_response_acts", []))
        if (
            not source_target_ids
            or len(source_target_ids) != len(set(source_target_ids))
            or not set(source_target_ids) <= active_ids
            or reception_node is None
            or reception_node.get("section_role") != "reception"
            or any(row is None for row in source_target_nodes)
            or not allowed_acts
            or len(allowed_acts) != len(set(allowed_acts))
        ):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH"
            )
        source_target_node_ids = tuple(
            str(row.get("node_id"))
            for row in source_target_nodes
            if row is not None
        )
        if tuple(reception_node.get("antecedent_node_ids", [])) != tuple(
            sorted(source_target_node_ids)
        ):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH"
            )
        source_target_nuclei = tuple(
            sorted(
                {
                    str(nucleus_id)
                    for obligation_id in source_target_ids
                    for nucleus_id in by_id[obligation_id].get(
                        "nucleus_ids", []
                    )
                }
            )
        )
        opportunity_ids = tuple(reception.get("reception_opportunity_ids", []))
        if (
            len(opportunity_ids) != len(set(opportunity_ids))
            or len(opportunity_ids) > 1
            or any(row not in opportunity_by_id for row in opportunity_ids)
        ):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_OPPORTUNITY_BINDING_INVALID"
            )
        opportunity = (
            opportunity_by_id[opportunity_ids[0]]
            if opportunity_ids
            else None
        )
        exact_target_nuclei = (
            tuple(opportunity.target_nucleus_ids)
            if opportunity is not None
            else source_target_nuclei
        )
        antecedent_ids = exact_owner_ids(
            exact_target_nuclei,
            reception_act=str(allowed_acts[0]),
            preferred_obligation_ids=source_target_ids,
        )
        if not antecedent_ids:
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_EXACT_OWNER_UNRESOLVED"
            )
        antecedent_nodes = tuple(
            node_by_obligation.get(row) for row in antecedent_ids
        )
        if any(row is None for row in antecedent_nodes):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_EXACT_OWNER_UNRESOLVED"
            )
        antecedent_node_ids = tuple(
            str(row.get("node_id"))
            for row in antecedent_nodes
            if row is not None
        )
        antecedent_nuclei = tuple(
            sorted(
                {
                    str(nucleus_id)
                    for obligation_id in antecedent_ids
                    for nucleus_id in by_id[obligation_id].get(
                        "nucleus_ids", []
                    )
                }
            )
        )
        if antecedent_nuclei != tuple(sorted(exact_target_nuclei)):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_EXACT_OWNER_MISMATCH"
            )
        support_ids: tuple[str, ...] = ()
        support_nuclei: tuple[str, ...] = ()
        support_role = "none"
        action_lifecycle = "not_applicable"
        if opportunity is not None and opportunity.support_nucleus_ids:
            support_ids = exact_owner_ids(
                opportunity.support_nucleus_ids,
                reception_act=str(allowed_acts[0]),
            )
            if not support_ids:
                raise Step11InverseSurfaceError(
                    "S11_MATCH_RECEPTION_SUPPORT_OWNER_UNRESOLVED"
                )
            support_nuclei = tuple(
                sorted(
                    {
                        str(nucleus_id)
                        for obligation_id in support_ids
                        for nucleus_id in by_id[obligation_id].get(
                            "nucleus_ids", []
                        )
                    }
                )
            )
            support_role = "source_opportunity_support"
        else:
            (
                support_ids,
                support_nuclei,
                support_role,
                action_lifecycle,
            ) = corrected_action_support(antecedent_nuclei)
        if action_lifecycle == "not_applicable":
            action_lifecycle = action_lifecycle_for(
                (*antecedent_nuclei, *support_nuclei)
            )
        support_nodes = tuple(
            node_by_obligation.get(row) for row in support_ids
        )
        if any(row is None for row in support_nodes):
            raise Step11InverseSurfaceError(
                "S11_MATCH_RECEPTION_SUPPORT_OWNER_UNRESOLVED"
            )
        material = {
            "reception_obligation_id": reception_id,
            "reception_node_id": str(reception_node.get("node_id")),
            "source_target_obligation_ids": list(source_target_ids),
            "source_target_node_ids": list(source_target_node_ids),
            "source_target_nucleus_ids": list(source_target_nuclei),
            "antecedent_obligation_ids": list(antecedent_ids),
            "antecedent_node_ids": list(antecedent_node_ids),
            "antecedent_nucleus_ids": list(antecedent_nuclei),
            "supporting_obligation_ids": list(support_ids),
            "supporting_node_ids": [
                str(row.get("node_id"))
                for row in support_nodes
                if row is not None
            ],
            "supporting_nucleus_ids": list(support_nuclei),
            "support_role": support_role,
            "source_reception_opportunity_ids": list(opportunity_ids),
            "action_lifecycle": action_lifecycle,
            "allowed_response_acts": list(allowed_acts),
            "evidence_grade": (
                "visible_typed_antecedent_exact_source_owner"
            ),
        }
        result[reception_id] = {
            **material,
            "binding_id": "s11recv_" + artifact_sha256(material)[:16],
        }
    return result


def match_step11_natural_surface(
    witness: Step11ParsedSurfaceWitness,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11VerifiedSurfaceBinding:
    if type(witness) is not Step11ParsedSurfaceWitness:
        raise Step11InverseSurfaceError("S11_MATCH_WITNESS_TYPE_INVALID")
    ledger, by_id = _validated_parents(inventory_result, content_plan, discourse_plan)
    projection = _project_input(current_input)
    snapshot = inventory_result.source_snapshot
    planning_frontier = build_step11_planning_frontier(
        inventory_result,
        content_plan,
        discourse_plan,
    )
    active = frozenset(planning_frontier.active_nucleus_ids)
    active_relations = frozenset(planning_frontier.active_relation_ids)
    boundary_companion_issues = (
        _independent_source_boundary_companion_contract(
            snapshot=snapshot,
            by_id=by_id,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
            planning_frontier=planning_frontier,
        )
    )
    semantic_overlay = build_step11_semantic_overlay(
        current_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
    )
    nucleus_literal_texts, anchor_binding_issues = (
        _independent_anchor_binding_contract(
            current_input=current_input,
            projection=projection,
            snapshot=snapshot,
            active_nucleus_ids=active,
            semantic_overlay=semantic_overlay,
            active_relation_ids=active_relations,
        )
    )
    allowed_by_slot = _authorised_fragments_by_slot(
        projection, semantic_overlay
    )
    fragment_slots, fragment_issues = _fragment_slots(
        witness, allowed_by_slot
    )
    issues = (
        set(fragment_issues)
        | set(anchor_binding_issues)
        | set(boundary_companion_issues)
    )
    if witness.schema_version != STEP11_PARSED_WITNESS_SCHEMA:
        issues.add("S11_MATCH_WITNESS_SCHEMA_MISMATCH")
    if witness.surface_catalog_sha256 != STEP11_SURFACE_CATALOG_SHA256:
        issues.add("S11_MATCH_WITNESS_CATALOG_MISMATCH")
    atom_by_id = {row.atom_id: row for row in witness.atoms}
    sentence_atom_ids = tuple(
        atom_id
        for sentence in witness.sentences
        for atom_id in sentence.clause_atom_ids
    )
    if (
        not witness.sentences
        or len(atom_by_id) != len(witness.atoms)
        or witness.observation_atom_count
        != sum(row.section_role == "observation" for row in witness.atoms)
        or witness.reception_atom_count
        != sum(row.section_role == "reception" for row in witness.atoms)
        or sentence_atom_ids != tuple(row.atom_id for row in witness.atoms)
        or tuple(row.sentence_ordinal for row in witness.sentences)
        != tuple(range(1, len(witness.sentences) + 1))
        or any(
            sentence.section_role not in {"observation", "reception"}
            or not sentence.clause_atom_ids
            or not sentence.grammatical_chunk_clause_counts
            or sum(sentence.grammatical_chunk_clause_counts)
            != len(sentence.clause_atom_ids)
            or any(
                type(count) is not int or count < 1
                for count in sentence.grammatical_chunk_clause_counts
            )
            or sentence.byte_start < 0
            or sentence.byte_end <= sentence.byte_start
            or any(
                atom_id not in atom_by_id
                or atom_by_id[atom_id].section_role
                != sentence.section_role
                or atom_by_id[atom_id].sentence_ordinal
                != sentence.sentence_ordinal
                or atom_by_id[atom_id].clause_ordinal != clause_ordinal
                or atom_by_id[atom_id].grammatical_chunk_ordinal < 1
                or atom_by_id[atom_id].byte_start < sentence.byte_start
                or atom_by_id[atom_id].byte_end > sentence.byte_end
                for clause_ordinal, atom_id in enumerate(
                    sentence.clause_atom_ids, start=1
                )
            )
            for sentence in witness.sentences
        )
    ):
        issues.add("S11_MATCH_SENTENCE_STRUCTURE_INVALID")
    if any(
        len(sentence.clause_atom_ids) > 4
        for sentence in witness.sentences
    ):
        issues.add("S11_MATCH_SENTENCE_DENSITY_EXCEEDED")
    maximum_grammatical_clauses = int(
        STEP11_SURFACE_CATALOG["group_grammar"]
        ["maximum_visible_clauses_per_grammatical_sentence"]
    )
    if any(
        max(sentence.grammatical_chunk_clause_counts, default=999)
        > maximum_grammatical_clauses
        or (
            all(
                atom_id in atom_by_id
                for atom_id in sentence.clause_atom_ids
            )
            and tuple(
                sum(
                    atom_by_id[atom_id].grammatical_chunk_ordinal
                    == ordinal
                    for atom_id in sentence.clause_atom_ids
                )
                for ordinal in range(
                    1,
                    len(sentence.grammatical_chunk_clause_counts) + 1,
                )
            )
            != sentence.grammatical_chunk_clause_counts
        )
        for sentence in witness.sentences
    ):
        issues.add("S11_MATCH_GRAMMATICAL_CHUNK_DENSITY_EXCEEDED")
    expected_sentence_roles = tuple(
        str(row.get("section_role"))
        for row in discourse_plan.get("sentence_groups", [])
        if type(row) is dict
    )
    if tuple(row.section_role for row in witness.sentences) != (
        expected_sentence_roles
    ):
        issues.add("S11_MATCH_DISCOURSE_SENTENCE_GROUP_MISMATCH")
    try:
        terminal_self_denial_pairs = (
            _terminal_self_denial_obligation_pairs(by_id, discourse_plan)
        )
    except Step11InverseSurfaceError:
        terminal_self_denial_pairs = ()
        issues.add("S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID")
    if validate_step11_semantic_overlay(
        semantic_overlay,
        current_input=current_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
    ):
        issues.add("S11_MATCH_OVERLAY_REVALIDATION_FAILED")
    observation_atoms = tuple(row for row in witness.atoms if row.section_role == "observation")
    reception_atoms = tuple(row for row in witness.atoms if row.section_role == "reception")
    ordered_observation_atoms = tuple(
        sorted(observation_atoms, key=lambda row: row.byte_start)
    )
    relation_ids: list[str] = []
    relation_atom_ids: dict[str, tuple[str, ...]] = {}
    authorised_relation_atom_ids: set[str] = set()
    anchor_by_id = {row.anchor_id: row for row in semantic_overlay.anchors}
    nucleus_anchor_texts = nucleus_literal_texts
    binding_by_nucleus = {
        row.nucleus_id: row
        for row in semantic_overlay.nucleus_anchor_bindings
    }
    (
        grounded_phrase_bindings,
        grounded_nuclei_by_atom,
        grounded_phrase_issues,
    ) = _independent_grounded_phrase_bindings(
        witness=witness,
        snapshot=snapshot,
        active_nucleus_ids=active,
        by_id=by_id,
        discourse_plan=discourse_plan,
        semantic_overlay=semantic_overlay,
        projection=projection,
    )
    issues.update(grounded_phrase_issues)
    relations, relation_contract_issues = _independent_relation_contract(
        snapshot=snapshot,
        by_id=by_id,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
        semantic_overlay=semantic_overlay,
        binding_by_nucleus=binding_by_nucleus,
        nucleus_literal_texts=nucleus_anchor_texts,
    )
    issues.update(relation_contract_issues)
    reference_registry, reference_registry_issues = (
        _independent_reference_registry(
            active_nucleus_ids=active,
            semantic_overlay=semantic_overlay,
            relations=relations,
        )
    )
    issues.update(reference_registry_issues)
    reference_by_ordinal = {
        row.reference_ordinal: row for row in reference_registry
    }
    exact_nuclei_by_atom = {
        atom.atom_id: frozenset(
            {
                *grounded_nuclei_by_atom.get(atom.atom_id, frozenset()),
                *(
                    nucleus_id
                    for nucleus_id, texts in nucleus_anchor_texts.items()
                    if texts
                    and (
                        bool(texts & set(atom.source_fragments))
                        or atom.self_denial_not_fact
                        and bool(
                            {
                                _semantic_core_text(value)
                                for value in texts
                            }
                            & {
                                _semantic_core_text(value)
                                for value in atom.source_fragments
                            }
                        )
                    )
                ),
            }
        )
        for atom in observation_atoms
    }

    def atom_owns_reference_literal(
        atom: Step11ParsedAtom,
        reference: _Step11IndependentReference,
    ) -> bool:
        matching_indices = tuple(
            index
            for index, fragment in enumerate(atom.source_fragments)
            if fragment == reference.source_literal
            and (
                index >= len(atom.source_slot_hints)
                or atom.source_slot_hints[index] == reference.source_slot
            )
            and reference.source_slot
            in tuple(
                slot
                for slot, values in allowed_by_slot.items()
                if fragment in values
            )
        )
        grounded_owner = bool(
            atom.grounded_phrases
            and set(reference.nucleus_ids)
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
        )
        return bool(
            grounded_owner
            or len(matching_indices) == 1
            and set(reference.nucleus_ids)
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
        )

    literal_owner_by_ordinal: dict[int, Step11ParsedAtom] = {}
    for reference in reference_registry:
        owners = tuple(
            atom
            for atom in observation_atoms
            if atom_owns_reference_literal(atom, reference)
        )
        if len(owners) != 1:
            issues.add("S11_MATCH_FUSED_LITERAL_OWNER_UNRESOLVED")
            if len(owners) > 1:
                issues.add("S11_MATCH_FUSED_LITERAL_OWNER_AMBIGUOUS")
            continue
        literal_owner_by_ordinal[reference.reference_ordinal] = owners[0]
    if set(literal_owner_by_ordinal) != set(reference_by_ordinal):
        issues.add("S11_MATCH_FUSED_LITERAL_OWNER_COVERAGE_MISMATCH")

    grounded_owner_sequence_by_atom = {
        atom.atom_id: tuple(
            binding.owner_nucleus_ids[0]
            for binding in grounded_phrase_bindings
            if binding.atom_id == atom.atom_id
            and len(binding.owner_nucleus_ids) == 1
        )
        for atom in observation_atoms
    }

    for atom in witness.atoms:
        if (
            atom.introduced_reference is not None
            or atom.compound_label_references
            or atom.relation_endpoint_references
            or atom.unknown_target_references
            or atom.reception_antecedent_references
        ):
            issues.add("S11_MATCH_VISIBLE_REFERENCE_BOOKKEEPING_FORBIDDEN")
    surface_active = frozenset(nucleus_anchor_texts)
    def relation_surface_signature(relation: Any) -> tuple[Any, ...]:
        return (
            str(relation.relation_type),
            str(relation.relation_direction),
            str(relation.from_nucleus_id),
            str(relation.to_nucleus_id),
            str(relation.from_endpoint_role),
            str(relation.to_endpoint_role),
        )
    relation_owner_by_atom_id: dict[str, tuple[Any, ...]] = {}

    for relation in relations:
        from_anchor_ids = set(
            (*relation.from_source_anchor_ids, *relation.from_label_anchor_ids)
        )
        to_anchor_ids = set(
            (*relation.to_source_anchor_ids, *relation.to_label_anchor_ids)
        )
        from_references = tuple(
            row
            for row in reference_registry
            if relation.from_nucleus_id in row.nucleus_ids
            and bool(from_anchor_ids & set(row.source_anchor_ids))
        )
        to_references = tuple(
            row
            for row in reference_registry
            if relation.to_nucleus_id in row.nucleus_ids
            and bool(to_anchor_ids & set(row.source_anchor_ids))
        )
        if (
            len(from_references) != 1
            or len(to_references) != 1
            or (
                len(from_references) == 1
                and len(to_references) == 1
                and from_references[0].reference_ordinal
                == to_references[0].reference_ordinal
            )
        ):
            issues.add("S11_MATCH_RELATION_ENDPOINT_UNRESOLVED")
            continue
        expected_roles = (
            str(relation.from_endpoint_role),
            str(relation.to_endpoint_role),
        )
        expected_prefix = (
            "obligation_fused:relation:"
            f"{relation.relation_type}:"
            f"{relation.relation_direction}:"
        )
        ambiguous_prefix = (
            "obligation_fused:relation:"
            f"{relation.relation_type}:source_or_target:"
        )

        def relation_surface_matches(atom: Step11ParsedAtom) -> bool:
            if not atom.form_id.startswith(
                (expected_prefix, ambiguous_prefix)
            ):
                return False
            if atom.grounded_phrases:
                parts = atom.form_id.split(":")
                local_marker = (
                    parts[5]
                    if len(parts) >= 8
                    and parts[5].startswith("local_")
                    else None
                )
                owner_sequence = grounded_owner_sequence_by_atom.get(
                    atom.atom_id, ()
                )
                if local_marker is not None:
                    local_role = parts[6]
                    local_endpoints = {
                        "local_from": ("from",),
                        "local_to": ("to",),
                        "local_source_or_target": ("from", "to"),
                    }.get(local_marker, ())
                    for local_endpoint in local_endpoints:
                        local_reference = (
                            from_references[0]
                            if local_endpoint == "from"
                            else to_references[0]
                        )
                        exact_reference = (
                            to_references[0]
                            if local_endpoint == "from"
                            else from_references[0]
                        )
                        expected_local_role = (
                            str(relation.from_endpoint_role)
                            if local_endpoint == "from"
                            else str(relation.to_endpoint_role)
                        )
                        local_owner = literal_owner_by_ordinal.get(
                            local_reference.reference_ordinal
                        )
                        exact_owner = literal_owner_by_ordinal.get(
                            exact_reference.reference_ordinal
                        )
                        if (
                            local_role == expected_local_role
                            and owner_sequence
                            == tuple(exact_reference.nucleus_ids)
                            and exact_owner is atom
                            and local_owner is not None
                            and local_owner is not atom
                            and local_owner.byte_start < atom.byte_start
                        ):
                            return True
                    return False
                rule = STEP11_SURFACE_CATALOG[
                    "grounded_lexicalization"
                ]["relation_atoms"][relation.relation_type][
                    relation.relation_direction
                ]
                expected_owner_by_endpoint = {
                    "from": str(relation.from_nucleus_id),
                    "to": str(relation.to_nucleus_id),
                }
                expected_sequence = tuple(
                    expected_owner_by_endpoint[endpoint]
                    for endpoint in rule["endpoint_order"]
                )
                return bool(
                    owner_sequence == expected_sequence
                    and literal_owner_by_ordinal.get(
                        from_references[0].reference_ordinal
                    )
                    is atom
                    and literal_owner_by_ordinal.get(
                        to_references[0].reference_ordinal
                    )
                    is atom
                )
            try:
                form_parts = atom.form_id.split(":")
                rule_index = int(form_parts[4])
                rule = STEP11_SURFACE_CATALOG[
                    "obligation_fused_grammar"
                ]["relation_forms"][relation.relation_type][
                    relation.relation_direction
                ][rule_index]
            except (IndexError, KeyError, TypeError, ValueError):
                return False
            stem = rule.get("stem") if type(rule) is dict else None
            if type(stem) is not str:
                return False
            local_marker = (
                form_parts[5]
                if len(form_parts) >= 8
                and form_parts[5].startswith("local_")
                else None
            )
            if local_marker is not None:
                local_role = form_parts[6]
                try:
                    anaphor_index = int(form_parts[7])
                    local_anaphor = STEP11_SURFACE_CATALOG[
                        "obligation_fused_grammar"
                    ]["local_anaphors"][local_role][anaphor_index]
                except (IndexError, KeyError, TypeError, ValueError):
                    return False
                if type(local_anaphor) is not str or not local_anaphor:
                    return False
                allowed_local_endpoints = {
                    "local_from": ("from",),
                    "local_to": ("to",),
                    "local_source_or_target": ("from", "to"),
                }.get(local_marker, ())
                for local_endpoint in allowed_local_endpoints:
                    local_reference = (
                        from_references[0]
                        if local_endpoint == "from"
                        else to_references[0]
                    )
                    exact_reference = (
                        to_references[0]
                        if local_endpoint == "from"
                        else from_references[0]
                    )
                    expected_local_role = (
                        str(relation.from_endpoint_role)
                        if local_endpoint == "from"
                        else str(relation.to_endpoint_role)
                    )
                    local_owner = literal_owner_by_ordinal.get(
                        local_reference.reference_ordinal
                    )
                    exact_owner = literal_owner_by_ordinal.get(
                        exact_reference.reference_ordinal
                    )
                    if (
                        local_role != expected_local_role
                        or exact_owner is not atom
                        or local_owner is None
                        or local_owner is atom
                        or local_owner.byte_start >= atom.byte_start
                        or atom.source_fragments
                        != (exact_reference.source_literal,)
                    ):
                        continue
                    # The exact stem/anaphor pairing was compiled by the
                    # inverse parser; independently require that the catalog
                    # rule actually contains both endpoint positions before
                    # accepting its local-owner interpretation.
                    if not all(
                        token in stem
                        for token in (
                            "{from_endpoint}",
                            "{to_endpoint}",
                        )
                    ):
                        continue
                    return True
                return False
            endpoint_literals = {
                "{from_endpoint}": from_references[0].source_literal,
                "{to_endpoint}": to_references[0].source_literal,
            }
            order = tuple(
                endpoint_literals[token]
                for token in sorted(
                    endpoint_literals,
                    key=lambda value: stem.index(value),
                )
            )
            return bool(
                len(order) == 2
                and atom.source_fragments == order
                and literal_owner_by_ordinal.get(
                    from_references[0].reference_ordinal
                )
                is atom
                and literal_owner_by_ordinal.get(
                    to_references[0].reference_ordinal
                )
                is atom
            )

        matches = tuple(
            atom
            for atom in observation_atoms
            if atom.form_id.startswith(
                (expected_prefix, ambiguous_prefix)
            )
            and "nucleus_notice" in atom.claim_kinds
            and "relation_notice" in atom.claim_kinds
            and relation_surface_matches(atom)
            and atom.introduced_reference is None
            and not atom.compound_label_references
            and not atom.relation_endpoint_references
            and not atom.unknown_target_references
            and not atom.reception_antecedent_references
            and atom.relation_type == relation.relation_type
            and atom.relation_direction
            in {relation.relation_direction, "source_or_target"}
            and atom.relation_endpoint_roles in {(), expected_roles}
        )
        if len(matches) != 1:
            issues.add("S11_MATCH_RELATION_UNRESOLVED")
            issues.add("S11_MATCH_RELATION_FUSED_ENDPOINT_MISMATCH")
            continue
        atom = matches[0]
        exact_nuclei_by_atom[atom.atom_id] = frozenset(
            {
                *exact_nuclei_by_atom.get(atom.atom_id, frozenset()),
                *from_references[0].nucleus_ids,
                *to_references[0].nucleus_ids,
            }
        )
        signature = relation_surface_signature(relation)
        previous_signature = relation_owner_by_atom_id.get(atom.atom_id)
        if previous_signature is not None and previous_signature != signature:
            issues.add("S11_MATCH_RELATION_ATOM_OWNER_COLLISION")
            continue
        relation_owner_by_atom_id[atom.atom_id] = signature
        matched_ids = (atom.atom_id,)
        source_ids = tuple(dict.fromkeys(relation.source_relation_ids))
        if not source_ids or relation.source_relation_id not in source_ids:
            issues.add("S11_MATCH_RELATION_SOURCE_CONTRACT_MISMATCH")
            continue
        for source_relation_id in source_ids:
            relation_ids.append(source_relation_id)
            relation_atom_ids[source_relation_id] = matched_ids
        authorised_relation_atom_ids.add(atom.atom_id)
    unknowns = tuple(
        row
        for row in semantic_overlay.unknowns
        if not row.target_nucleus_ids
        or set(row.target_nucleus_ids) <= surface_active
    )
    unknown_ids: list[str] = []
    unknown_atom_ids: dict[str, tuple[str, ...]] = {}
    compatible_source_unknown_ids: dict[str, frozenset[str]] = {}
    authorised_unknown_atom_ids: set[str] = set()
    snapshot_unknown_by_id = {
        row.source_id: row for row in snapshot.unknowns
    }
    independent_source_unknown_type_by_id = {
        source.source_id: _independent_source_unknown_type(
            str(source.dimension_code),
            " ".join(
                text
                for nucleus_id in sorted(source.affected_nucleus_ids)
                for text in sorted(
                    nucleus_anchor_texts.get(nucleus_id, frozenset())
                )
            ),
            contextual_text=(
                str(projection["thought"])
                + "\n"
                + str(projection["action"])
            ),
        )
        for source in snapshot.unknowns
        if source.required is True
        and set(source.affected_nucleus_ids) & set(surface_active)
    }

    def atom_owns_source_anchor_ranges(
        atom: Step11ParsedAtom,
        source_anchor_ids: tuple[str, ...],
        *,
        allow_terminal_sentence_mark_equivalence: bool = False,
    ) -> bool:
        """Prove exact source-range ownership without trusting forward AST.

        Unknowns require byte-exact fragments.  Self-denial additionally has
        a pre-existing, narrowly scoped semantic-core rule that treats only
        terminal sentence marks as equivalent; no other range relaxation is
        permitted here.
        """

        if not source_anchor_ids:
            return False
        atom_slots = set(fragment_slots.get(atom.atom_id, ()))
        introduced = atom.introduced_reference
        introduced_reference = (
            reference_by_ordinal.get(introduced.reference_ordinal)
            if type(introduced) is Step11EndpointReference
            else None
        )
        for anchor_id in source_anchor_ids:
            anchor = anchor_by_id.get(anchor_id)
            if anchor is None or anchor.source_slot not in {"thought", "action"}:
                return False
            if (
                introduced_reference is not None
                and introduced is not None
                and introduced.endpoint_role
                == introduced_reference.endpoint_role
                and introduced_reference.source_identity
                == (
                    "text",
                    anchor.source_slot,
                    anchor.start,
                    anchor.end,
                )
            ):
                continue
            if not atom.source_fragments:
                return False
            source_text = str(projection[anchor.source_slot])
            exact_fragment_owners = 0
            for index, fragment in enumerate(atom.source_fragments):
                hint = (
                    atom.source_slot_hints[index]
                    if index < len(atom.source_slot_hints)
                    else None
                )
                if hint is not None and hint != anchor.source_slot:
                    continue
                if hint is None and anchor.source_slot not in atom_slots:
                    continue
                search_fragments = [
                    (fragment, anchor.start, anchor.end)
                ]
                if allow_terminal_sentence_mark_equivalence:
                    semantic_core = re.sub(
                        r"[。！？!?]+$", "", fragment
                    ).rstrip()
                    anchor_core = re.sub(
                        r"[。！？!?]+$", "", anchor.text
                    ).rstrip()
                    if semantic_core and semantic_core == anchor_core:
                        search_fragments.append(
                            (
                                semantic_core,
                                anchor.start,
                                anchor.start + len(anchor_core),
                            )
                        )
                for search_fragment, expected_start, expected_end in dict.fromkeys(
                    search_fragments
                ):
                    cursor = 0
                    occurrences: list[tuple[int, int]] = []
                    while True:
                        start = source_text.find(search_fragment, cursor)
                        if start < 0:
                            break
                        end = start + len(search_fragment)
                        occurrences.append((start, end))
                        cursor = start + 1
                    if occurrences == [(expected_start, expected_end)]:
                        exact_fragment_owners += 1
            if (
                source_text[anchor.start : anchor.end] != anchor.text
                or exact_fragment_owners != 1
            ):
                return False
        return True

    def nonrelation_unknown_antecedents(
        atom: Step11ParsedAtom,
        *,
        target_nucleus_ids: set[str],
    ) -> tuple[Step11ParsedAtom, ...]:
        return (
            (atom,)
            if target_nucleus_ids
            and target_nucleus_ids
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
            and "nucleus_notice" in atom.claim_kinds
            and "unknown_boundary" in atom.claim_kinds
            and bool(atom.source_fragments or atom.grounded_phrases)
            and not atom.unknown_target_references
            else ()
        )

    def relation_unknown_antecedents(
        atom: Step11ParsedAtom,
        *,
        target_nucleus_ids: set[str],
    ) -> tuple[Step11ParsedAtom, ...]:
        return (
            (atom,)
            if target_nucleus_ids
            and atom.atom_id in authorised_relation_atom_ids
            and "nucleus_notice" in atom.claim_kinds
            and "relation_notice" in atom.claim_kinds
            and "unknown_boundary" in atom.claim_kinds
            and bool(atom.source_fragments or atom.grounded_phrases)
            and not atom.relation_endpoint_references
            and not atom.unknown_target_references
            and set(
                exact_nuclei_by_atom.get(atom.atom_id, frozenset())
            )
            == target_nucleus_ids
            else ()
        )

    def unknown_atom_matches(
        atom: Step11ParsedAtom,
        *,
        wanted: str,
        anchor_texts: set[str],
        target_nucleus_ids: set[str],
        exact_source_anchor_owns_target: bool,
        source_bound_relation_unknown: bool,
    ) -> bool:
        if (
            atom.unknown_dimension_class != wanted
            or "nucleus_notice" not in atom.claim_kinds
            or "unknown_boundary" not in atom.claim_kinds
            or not (atom.source_fragments or atom.grounded_phrases)
            or atom.introduced_reference is not None
            or atom.compound_label_references
            or atom.relation_endpoint_references
            or atom.unknown_target_references
            or atom.reception_antecedent_references
            or not exact_source_anchor_owns_target
            or not target_nucleus_ids
            or not target_nucleus_ids
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
        ):
            return False
        if wanted == "relation" or source_bound_relation_unknown:
            return len(
                relation_unknown_antecedents(
                    atom,
                    target_nucleus_ids=target_nucleus_ids,
                )
            ) == 1
        return len(
            nonrelation_unknown_antecedents(
                atom,
                target_nucleus_ids=target_nucleus_ids,
            )
        ) == 1

    for unknown in unknowns:
        wanted = _unknown_class(unknown.unknown_type)
        unknown_anchor_texts = {
            anchor_by_id[anchor_id].text
            for anchor_id in unknown.source_anchor_ids
            if anchor_id in anchor_by_id
        }
        directly_compatible_ids = frozenset(
            source_id
            for source_id in unknown.source_unknown_ids
            if source_id in snapshot_unknown_by_id
            and independent_source_unknown_type_by_id.get(source_id)
            is not None
            and _unknown_class(
                str(independent_source_unknown_type_by_id[source_id])
            )
            == wanted
        )
        compatible_ids = directly_compatible_ids
        compatible_source_unknown_ids[unknown.unknown_id] = compatible_ids
        if compatible_ids != frozenset(unknown.source_unknown_ids):
            issues.add("S11_MATCH_UNKNOWN_ALIAS_TYPE_MISMATCH")
        source_owned_target_nuclei = {
            nucleus_id
            for source_id in compatible_ids
            for nucleus_id in snapshot_unknown_by_id[
                source_id
            ].affected_nucleus_ids
        }
        exact_target_ownership = bool(
            not unknown.source_unknown_ids
            or compatible_ids
            and set(unknown.target_nucleus_ids)
            <= source_owned_target_nuclei
        )
        if not exact_target_ownership:
            issues.add("S11_MATCH_UNKNOWN_TARGET_OWNERSHIP_MISMATCH")
        source_bound_relation_unknown = bool(
            wanted == "relation"
            and not unknown.source_unknown_ids
            and unknown.epistemic_basis == "explicit_unknown"
            and unknown.surface_policy == "preserve_open"
            and "grammar_relation" in unknown.source_rules
            and unknown.source_anchor_ids
            and all(
                anchor_id in anchor_by_id
                and anchor_by_id[anchor_id].role in {"unknown", "nucleus"}
                and any(
                    anchor_id
                    in binding_by_nucleus[nucleus_id].source_anchor_ids
                    for nucleus_id in unknown.target_nucleus_ids
                    if nucleus_id in binding_by_nucleus
                )
                for anchor_id in unknown.source_anchor_ids
            )
        )
        # A generic surface boundary is useful as an additional open marker,
        # but it is not evidence for a typed cause/referent/future (or any
        # other typed) unknown.  Typed obligations require an exact inverse
        # classification.
        matches = tuple(
            atom
            for atom in observation_atoms
            if unknown_atom_matches(
                atom,
                wanted=wanted,
                anchor_texts=unknown_anchor_texts,
                target_nucleus_ids=set(unknown.target_nucleus_ids),
                exact_source_anchor_owns_target=bool(
                    unknown_anchor_texts
                    and exact_target_ownership
                    and (
                        not unknown.target_nucleus_ids
                        or set(unknown.target_nucleus_ids) <= surface_active
                    )
                ),
                source_bound_relation_unknown=source_bound_relation_unknown,
            )
        )
        if matches:
            unknown_ids.append(unknown.unknown_id)
            unknown_atom_ids[unknown.unknown_id] = tuple(
                dict.fromkeys(row.atom_id for row in matches)
            )
            authorised_unknown_atom_ids.update(
                row.atom_id for row in matches
            )
            if wanted != "relation" and not source_bound_relation_unknown:
                for row in matches:
                    if not row.form_id.startswith("unknown_anaphora:"):
                        continue
                    if relation_unknown_antecedents(
                        row,
                        target_nucleus_ids=set(
                            unknown.target_nucleus_ids
                        ),
                    ):
                        continue
                    antecedents = nonrelation_unknown_antecedents(
                        row,
                        target_nucleus_ids=set(unknown.target_nucleus_ids),
                    )
                    if len(antecedents) == 1:
                        # This atom is not a free extra observation.  It is the
                        # one exact source owner independently required by the
                        # following anaphoric unknown boundary.
                        authorised_unknown_atom_ids.add(
                            antecedents[0].atom_id
                        )
        else:
            issues.add("S11_MATCH_UNKNOWN_UNRESOLVED")
            if any(
                atom.unknown_dimension_class == wanted
                for atom in observation_atoms
            ):
                issues.add("S11_MATCH_UNKNOWN_TARGET_UNRESOLVED")
    visible_source_unknown_ids = {
        source_id
        for unknown in semantic_overlay.unknowns
        for source_id in unknown.source_unknown_ids
    }
    suppression_atom_ids_by_source: dict[str, tuple[str, ...]] = {}
    surface_bound_anchor_ids = tuple(
        dict.fromkeys(
            anchor_id
            for nucleus_id in sorted(surface_active)
            for anchor_id in getattr(
                binding_by_nucleus.get(nucleus_id),
                "source_anchor_ids",
                (),
            )
        )
    )

    def exact_current_input_anchor(anchor_id: str) -> bool:
        anchor = anchor_by_id.get(anchor_id)
        if anchor is None or anchor.source_slot not in {"thought", "action"}:
            return False
        field_text = projection[anchor.source_slot]
        return bool(
            0 <= anchor.start < anchor.end <= len(field_text)
            and field_text[anchor.start : anchor.end] == anchor.text
            and hashlib.sha256(anchor.text.encode("utf-8")).hexdigest()
            == anchor.text_sha256
        )

    for suppressed in semantic_overlay.suppressed_unknowns:
        source = (
            snapshot_unknown_by_id.get(suppressed.source_unknown_id)
            if type(suppressed) is Step11SuppressedUnknown
            else None
        )
        expected_target_ids = (
            tuple(
                sorted(set(source.affected_nucleus_ids) & set(surface_active))
            )
            if source is not None
            else ()
        )
        expected_source_anchor_ids = tuple(
            anchor_id
            for nucleus_id in expected_target_ids
            for anchor_id in getattr(
                binding_by_nucleus.get(nucleus_id),
                "source_anchor_ids",
                (),
            )
            if anchor_id in anchor_by_id
            and _RELATIVE_TEMPORAL_DEICTIC_RE.search(
                anchor_by_id[anchor_id].text
            )
            is not None
        )
        expected_source_anchor_ids = tuple(
            dict.fromkeys(expected_source_anchor_ids)
        )
        expected_slots = tuple(
            sorted(
                {
                    slot
                    for nucleus_id in expected_target_ids
                    for slot in _slots_for_nucleus(snapshot, nucleus_id)
                },
                key=_SLOT_ORDER.__getitem__,
            )
        )
        expected_context_anchor_ids: list[str] = []
        for anchor_id in surface_bound_anchor_ids:
            anchor = anchor_by_id.get(anchor_id)
            if anchor is None:
                continue
            if anchor_id in expected_source_anchor_ids:
                marker = _RELATIVE_TEMPORAL_DEICTIC_RE.search(anchor.text)
                if (
                    marker is not None
                    and _CONTEXTUAL_PRECEDING_EVENT_RE.search(
                        anchor.text[: marker.start()]
                    )
                    is not None
                ):
                    expected_context_anchor_ids.append(anchor_id)
                continue
            if _CONTEXTUAL_PRECEDING_EVENT_RE.search(anchor.text) is not None:
                expected_context_anchor_ids.append(anchor_id)
        expected_context = tuple(dict.fromkeys(expected_context_anchor_ids))
        suppression_valid = bool(
            type(suppressed) is Step11SuppressedUnknown
            and source is not None
            and source.required is True
            and str(source.source_role) == "original_input"
            and str(source.surface_policy) == "do_not_claim"
            and suppressed.original_dimension_code
            == str(source.dimension_code)
            and "TEMPORAL_REFERENT"
            in suppressed.original_dimension_code.upper()
            and suppressed.source_unknown_id
            not in visible_source_unknown_ids
            and tuple(suppressed.target_nucleus_ids)
            == expected_target_ids
            and bool(expected_target_ids)
            and tuple(suppressed.source_slots) == expected_slots
            and tuple(suppressed.source_anchor_ids)
            == expected_source_anchor_ids
            and bool(expected_source_anchor_ids)
            and all(
                exact_current_input_anchor(anchor_id)
                for anchor_id in expected_source_anchor_ids
            )
            and tuple(suppressed.context_anchor_ids) == expected_context
            and bool(expected_context)
            and all(
                exact_current_input_anchor(anchor_id)
                for anchor_id in expected_context
            )
            and suppressed.suppression_reason
            == "context_resolved_temporal_referent"
            and suppressed.evidence_grade
            == "exact_current_input_context_resolution"
        )
        if not suppression_valid:
            issues.add("S11_MATCH_UNKNOWN_SUPPRESSION_CONTRACT_MISMATCH")
            continue
        required_anchor_ids = {
            *suppressed.source_anchor_ids,
            *suppressed.context_anchor_ids,
        }
        # The temporal source and its independently recovered context can
        # belong to different nuclei, and therefore to different canonical
        # observation atoms.  Require one exact visible owner per anchor and
        # combine those owners; never require an artificial line that quotes
        # both source spans together.
        owner_atoms_by_anchor: dict[str, tuple[Step11ParsedAtom, ...]] = {}
        for anchor_id in required_anchor_ids:
            anchor = anchor_by_id[anchor_id]
            owner_nucleus_ids = {
                nucleus_id
                for nucleus_id, binding_row in binding_by_nucleus.items()
                if anchor_id in binding_row.source_anchor_ids
            }
            owner_atoms_by_anchor[anchor_id] = tuple(
                atom
                for atom in observation_atoms
                if "nucleus_notice" in atom.claim_kinds
                and anchor.text in atom.source_fragments
                and bool(
                    owner_nucleus_ids
                    & set(
                        exact_nuclei_by_atom.get(
                            atom.atom_id, frozenset()
                        )
                    )
                )
            )
        source_owner_nucleus_ids = {
            nucleus_id
            for anchor_id in suppressed.source_anchor_ids
            for atom in owner_atoms_by_anchor.get(anchor_id, ())
            for nucleus_id in exact_nuclei_by_atom.get(
                atom.atom_id, frozenset()
            )
        }
        if (
            any(
                len(owner_atoms_by_anchor.get(anchor_id, ())) != 1
                for anchor_id in required_anchor_ids
            )
            or not set(suppressed.target_nucleus_ids)
            <= source_owner_nucleus_ids
        ):
            issues.add("S11_MATCH_UNKNOWN_SUPPRESSION_TARGET_UNRESOLVED")
            continue
        suppression_atom_ids_by_source[suppressed.source_unknown_id] = tuple(
            dict.fromkeys(
                atom.atom_id
                for anchor_id in required_anchor_ids
                for atom in owner_atoms_by_anchor[anchor_id]
            )
        )

    source_unknown_oracle_rows: list[dict[str, Any]] = []
    visible_unknowns_by_source: dict[str, list[Any]] = {}
    for unknown in semantic_overlay.unknowns:
        for source_id in unknown.source_unknown_ids:
            visible_unknowns_by_source.setdefault(source_id, []).append(unknown)
    contextual_input_text = (
        str(projection["thought"]) + "\n" + str(projection["action"])
    )
    nucleus_ids_by_anchor = {
        anchor_id: nucleus_id
        for nucleus_id, binding in binding_by_nucleus.items()
        for anchor_id in binding.source_anchor_ids
    }

    def exact_anchor_range_material(anchor_id: str) -> dict[str, Any] | None:
        anchor = anchor_by_id.get(anchor_id)
        if anchor is None or not exact_current_input_anchor(anchor_id):
            return None
        return {
            "source_slot": anchor.source_slot,
            "start": anchor.start,
            "end": anchor.end,
            "text_sha256": anchor.text_sha256,
        }

    for source in sorted(snapshot.unknowns, key=lambda row: row.source_id):
        expected_target_ids = tuple(
            sorted(set(source.affected_nucleus_ids) & set(surface_active))
        )
        if source.required is not True or not expected_target_ids:
            continue
        target_anchor_ids = tuple(
            dict.fromkeys(
                anchor_id
                for nucleus_id in expected_target_ids
                for anchor_id in getattr(
                    binding_by_nucleus.get(nucleus_id),
                    "source_anchor_ids",
                    (),
                )
            )
        )
        target_anchors = tuple(
            anchor_by_id[anchor_id]
            for anchor_id in target_anchor_ids
            if anchor_id in anchor_by_id
        )
        source_text = " ".join(row.text for row in target_anchors)
        expected_type = _independent_source_unknown_type(
            str(source.dimension_code),
            source_text,
            contextual_text=contextual_input_text,
        )
        temporal_resolved = bool(
            "TEMPORAL_REFERENT" in str(source.dimension_code).upper()
            and expected_type is None
            and source.source_id in suppression_atom_ids_by_source
        )
        visible_rows = tuple(
            dict.fromkeys(visible_unknowns_by_source.get(source.source_id, ()))
        )
        row_material: dict[str, Any] = {
            "source_unknown_id": source.source_id,
            "dimension_code": str(source.dimension_code),
            "target_nucleus_ids": list(expected_target_ids),
            "target_ranges": [
                material
                for anchor_id in target_anchor_ids
                if (material := exact_anchor_range_material(anchor_id))
                is not None
            ],
        }
        if temporal_resolved:
            if visible_rows:
                issues.add("S11_MATCH_UNKNOWN_SUPPRESSION_CONTRACT_MISMATCH")
            row_material.update(
                {
                    "classification": "suppressed_temporal_referent",
                    "decision_state": "not_applicable",
                    "source_ranges": [],
                    "context_ranges": [],
                }
            )
            source_unknown_oracle_rows.append(row_material)
            continue
        if expected_type is None:
            issues.add("S11_MATCH_REQUIRED_UNKNOWN_UNCLASSIFIABLE")
            row_material.update(
                {
                    "classification": "unclassifiable",
                    "decision_state": "not_applicable",
                    "source_ranges": [],
                    "context_ranges": [],
                }
            )
            source_unknown_oracle_rows.append(row_material)
            continue
        if len(visible_rows) != 1:
            issues.add("S11_MATCH_SOURCE_UNKNOWN_ORACLE_MISMATCH")
            row_material.update(
                {
                    "classification": expected_type,
                    "decision_state": (
                        "open"
                        if expected_type == "decision_state"
                        else "completed"
                        if expected_type
                        == "post_decision_comparative_merit"
                        else "not_applicable"
                    ),
                    "source_ranges": [],
                    "context_ranges": [],
                }
            )
            source_unknown_oracle_rows.append(row_material)
            continue
        unknown = visible_rows[0]
        coalesced_expected_target_ids = tuple(
            sorted(
                {
                    nucleus_id
                    for candidate in snapshot.unknowns
                    if candidate.source_id
                    in set(unknown.source_unknown_ids)
                    for nucleus_id in candidate.affected_nucleus_ids
                    if nucleus_id in surface_active
                }
            )
        )
        expected_slots = tuple(
            sorted(
                {
                    slot
                    for nucleus_id in coalesced_expected_target_ids
                    for slot in _slots_for_nucleus(snapshot, nucleus_id)
                },
                key=_SLOT_ORDER.__getitem__,
            )
        )
        source_ranges = tuple(
            material
            for anchor_id in unknown.source_anchor_ids
            if (material := exact_anchor_range_material(anchor_id)) is not None
        )
        source_anchor_rows = tuple(
            anchor_by_id.get(anchor_id)
            for anchor_id in unknown.source_anchor_ids
        )
        source_ranges_owned = bool(
            source_anchor_rows
            and len(source_ranges) == len(source_anchor_rows)
            and all(
                anchor is not None
                and anchor.role in {"unknown", "nucleus"}
                and anchor.source_slot in expected_slots
                and any(
                    anchor.source_slot == target.source_slot
                    and anchor.start < target.end
                    and target.start < anchor.end
                    for target in target_anchors
                )
                for anchor in source_anchor_rows
            )
        )
        expected_decision_state = (
            "open"
            if expected_type == "decision_state"
            else "completed"
            if expected_type == "post_decision_comparative_merit"
            else "not_applicable"
        )
        expected_context_anchor_ids: tuple[str, ...] = ()
        expected_context_nucleus_ids: tuple[str, ...] = ()
        if expected_type == "decision_state":
            expected_context_anchor_ids = tuple(unknown.source_anchor_ids)
            expected_context_nucleus_ids = tuple(
                sorted(
                    set(coalesced_expected_target_ids)
                    | {
                        nucleus_ids_by_anchor[anchor_id]
                        for anchor_id in expected_context_anchor_ids
                        if anchor_id in nucleus_ids_by_anchor
                    }
                )
            )
        elif expected_type == "post_decision_comparative_merit":
            completed_anchor_ids = tuple(
                anchor.anchor_id
                for anchor in semantic_overlay.anchors
                if anchor.role == "nucleus"
                and re.search(
                    r"(?:決めた|選んだ|決定した|確定した|ことにした)",
                    anchor.text,
                )
                is not None
            )
            expected_context_anchor_ids = (
                completed_anchor_ids or tuple(unknown.source_anchor_ids)
            )
            expected_context_nucleus_ids = tuple(
                sorted(
                    {
                        nucleus_ids_by_anchor[anchor_id]
                        for anchor_id in expected_context_anchor_ids
                        if anchor_id in nucleus_ids_by_anchor
                    }
                    or set(coalesced_expected_target_ids)
                )
            )
        context_ranges = tuple(
            material
            for anchor_id in expected_context_anchor_ids
            if (material := exact_anchor_range_material(anchor_id)) is not None
        )
        unknown_material = {
            "unknown_type": unknown.unknown_type,
            "source_slots": list(unknown.source_slots),
            "source_anchor_ids": list(unknown.source_anchor_ids),
            "target_nucleus_ids": list(unknown.target_nucleus_ids),
            "source_unknown_ids": list(unknown.source_unknown_ids),
            "source_rules": list(unknown.source_rules),
            "epistemic_basis": unknown.epistemic_basis,
            "decision_state": unknown.decision_state,
            "context_nucleus_ids": list(unknown.context_nucleus_ids),
            "context_anchor_ids": list(unknown.context_anchor_ids),
            "surface_policy": "preserve_open",
        }
        signature_valid = unknown.unknown_id == (
            "s11unk_" + artifact_sha256(unknown_material)[:16]
        )
        contract_valid = bool(
            unknown.unknown_type == expected_type
            and tuple(unknown.target_nucleus_ids)
            == coalesced_expected_target_ids
            and tuple(unknown.source_slots) == expected_slots
            and source_ranges_owned
            and "frozen_required_unknown" in unknown.source_rules
            and unknown.epistemic_basis == "frozen_required"
            and unknown.surface_policy == "preserve_open"
            and unknown.decision_state == expected_decision_state
            and tuple(unknown.context_nucleus_ids)
            == expected_context_nucleus_ids
            and tuple(unknown.context_anchor_ids)
            == expected_context_anchor_ids
            and len(context_ranges) == len(expected_context_anchor_ids)
            and signature_valid
        )
        if not contract_valid:
            issues.add("S11_MATCH_SOURCE_UNKNOWN_ORACLE_MISMATCH")
        row_material.update(
            {
                "classification": expected_type,
                "decision_state": expected_decision_state,
                "source_ranges": list(source_ranges),
                "context_nucleus_ids": list(expected_context_nucleus_ids),
                "context_ranges": list(context_ranges),
                "overlay_signature_sha256": artifact_sha256(
                    unknown_material
                ),
            }
        )
        source_unknown_oracle_rows.append(row_material)
    source_unknown_oracle_sha256 = artifact_sha256(
        _source_unknown_oracle_material(source_unknown_oracle_rows)
    )
    positive_label_ids = tuple(
        row.label_anchor_id
        for row in semantic_overlay.label_anchors
        if row.source_slot == "emotion"
        and row.label in _EMOTION_VALENCE["positive"]
    )
    negative_label_ids = tuple(
        row.label_anchor_id
        for row in semantic_overlay.label_anchors
        if row.source_slot == "emotion"
        and row.label in _EMOTION_VALENCE["negative"]
    )
    # rc0027 always owns both selected labels in one fused natural unit.
    legacy_mixed_atoms = tuple(
        atom
        for atom in observation_atoms
        if atom.form_id.startswith("mixed_emotion:")
    )
    authorised_mixed_emotion_atom_ids: set[str] = set()
    integrated_mixed_emotion_requirement_ids: list[str] = []
    if positive_label_ids and negative_label_ids:
        requirements = tuple(semantic_overlay.mixed_emotion_requirements)
        expected_material = {
            "positive_label_anchor_ids": list(positive_label_ids),
            "negative_label_anchor_ids": list(negative_label_ids),
            "relation_type": "coexists_with",
            "relation_direction": "bidirectional",
            "required": True,
            "evidence_grade": "exact_current_input_mixed_valence",
        }
        expected_requirement_id = (
            "s11mix_" + artifact_sha256(expected_material)[:16]
        )
        requirement_valid = bool(
            len(requirements) == 1
            and requirements[0].requirement_id == expected_requirement_id
            and tuple(requirements[0].positive_label_anchor_ids)
            == positive_label_ids
            and tuple(requirements[0].negative_label_anchor_ids)
            == negative_label_ids
            and requirements[0].relation_type == "coexists_with"
            and requirements[0].relation_direction == "bidirectional"
            and requirements[0].required is True
            and requirements[0].evidence_grade
            == "exact_current_input_mixed_valence"
        )
        if not requirement_valid:
            issues.add("S11_MATCH_MIXED_EMOTION_CONTRACT_MISMATCH")
        else:
            positive_references = tuple(
                row
                for row in reference_registry
                if positive_label_ids[0] in row.source_anchor_ids
            )
            negative_references = tuple(
                row
                for row in reference_registry
                if negative_label_ids[0] in row.source_anchor_ids
            )
            if (
                len(positive_references) != 1
                or len(negative_references) != 1
                or positive_references[0].endpoint_role != "affect"
                or negative_references[0].endpoint_role != "affect"
                or positive_references[0].reference_ordinal
                == negative_references[0].reference_ordinal
            ):
                issues.add("S11_MATCH_MIXED_EMOTION_UNRESOLVED")
                expected_references: tuple[Step11EndpointReference, ...] = ()
            else:
                expected_references = (
                    Step11EndpointReference(
                        positive_references[0].reference_ordinal,
                        "affect",
                    ),
                    Step11EndpointReference(
                        negative_references[0].reference_ordinal,
                        "affect",
                    ),
                )
            grounded_mixed_atoms = tuple(
                atom
                for atom in observation_atoms
                if atom.form_id.startswith(
                    "obligation_fused:grounded_coexisting:"
                )
                and "mixed_emotion_relation" in atom.claim_kinds
            )
            if (
                grounded_mixed_atoms
                and len(positive_references) == 1
                and len(negative_references) == 1
            ):
                expected_owner_sequence = tuple(
                    reference.nucleus_ids[0]
                    for reference in sorted(
                        (positive_references[0], negative_references[0]),
                        key=lambda row: row.reference_ordinal,
                    )
                    if len(reference.nucleus_ids) == 1
                )
                compound_issues = (
                    ()
                    if len(grounded_mixed_atoms) == 1
                    and len(expected_owner_sequence) == 2
                    and grounded_owner_sequence_by_atom.get(
                        grounded_mixed_atoms[0].atom_id, ()
                    )
                    == expected_owner_sequence
                    and grounded_mixed_atoms[0].relation_type
                    == "coexists_with"
                    and grounded_mixed_atoms[0].relation_direction
                    == "bidirectional"
                    else (
                        "S11_MATCH_MIXED_EMOTION_COMPOUND_ORDER_MISMATCH",
                    )
                )
            else:
                compound_issues = _independent_mixed_emotion_surface_issues(
                    observation_atoms,
                    expected_positive_label=(
                        positive_references[0].source_literal
                        if len(positive_references) == 1
                        else ""
                    ),
                    expected_negative_label=(
                        negative_references[0].source_literal
                        if len(negative_references) == 1
                        else ""
                    ),
                    expected_references=expected_references,
                )
            issues.update(compound_issues)
            matches = tuple(
                atom
                for atom in observation_atoms
                if atom.form_id.startswith(
                    (
                        "obligation_fused:mixed_emotion:",
                        "obligation_fused:grounded_coexisting:",
                    )
                )
                and "mixed_emotion_relation" in atom.claim_kinds
                and not compound_issues
            )
            if len(matches) != 1:
                issues.add("S11_MATCH_MIXED_EMOTION_UNRESOLVED")
            else:
                authorised_mixed_emotion_atom_ids.add(matches[0].atom_id)
                integrated_mixed_emotion_requirement_ids.append(
                    expected_requirement_id
                )
    elif semantic_overlay.mixed_emotion_requirements or legacy_mixed_atoms:
        issues.add("S11_MATCH_MIXED_EMOTION_CONTRACT_MISMATCH")
    if legacy_mixed_atoms:
        issues.add("S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED")
    denial_atoms = tuple(
        row for row in observation_atoms if row.self_denial_not_fact
    )
    self_evaluation_by_id = {
        row.self_evaluation_id: row
        for row in semantic_overlay.reported_self_evaluations
        if row.source_anchor_id in anchor_by_id
    }
    self_evaluation_target_nuclei: dict[str, frozenset[str]] = {}
    for evaluation_id, evaluation in self_evaluation_by_id.items():
        evaluation_anchor = anchor_by_id[evaluation.source_anchor_id]
        evaluation_material = (
            evaluation_anchor.source_slot,
            evaluation_anchor.start,
            evaluation_anchor.end,
            evaluation_anchor.text_sha256,
        )
        self_evaluation_target_nuclei[evaluation_id] = frozenset(
            nucleus_id
            for nucleus_id, binding in binding_by_nucleus.items()
            if any(
                anchor_id in anchor_by_id
                and (
                    anchor_by_id[anchor_id].source_slot,
                    anchor_by_id[anchor_id].start,
                    anchor_by_id[anchor_id].end,
                    anchor_by_id[anchor_id].text_sha256,
                )
                == evaluation_material
                for anchor_id in binding.source_anchor_ids
            )
        )
    # The exact overlay, not a coarse upstream flag, owns the denial scope.
    denial_required = bool(semantic_overlay.reported_self_evaluations)
    if denial_required and not denial_atoms:
        issues.add("S11_MATCH_SELF_DENIAL_UNRESOLVED")
    authorised_denial_atom_ids: set[str] = set()
    covered_self_evaluation_ids: set[str] = set()
    denial_owned_nuclei_by_atom: dict[str, frozenset[str]] = {}

    def denial_evaluation_ids_for(
        atom: Step11ParsedAtom,
    ) -> set[str]:
        result = {
            evaluation_id
            for evaluation_id, evaluation in self_evaluation_by_id.items()
            if self_evaluation_target_nuclei.get(evaluation_id)
            and self_evaluation_target_nuclei[evaluation_id]
            <= exact_nuclei_by_atom.get(atom.atom_id, frozenset())
            and atom_owns_source_anchor_ranges(
                atom,
                (evaluation.source_anchor_id,),
                allow_terminal_sentence_mark_equivalence=True,
            )
        }
        # If equal bytes occur in more than one source slot, the sentence does
        # not prove which reported evaluation is being denied.
        cores = {_semantic_core_text(value) for value in atom.source_fragments}
        if any(
            len(
                {
                    self_evaluation_by_id[evaluation_id].source_slot
                    for evaluation_id in result
                    if _semantic_core_text(
                        anchor_by_id[
                            self_evaluation_by_id[
                                evaluation_id
                            ].source_anchor_id
                        ].text
                    )
                    == core
                }
            )
            > 1
            for core in cores
        ):
            issues.add("S11_MATCH_SELF_DENIAL_SLOT_AMBIGUOUS")
            return set()
        return result

    for denial in denial_atoms:
        if denial.source_fragments:
            covered = denial_evaluation_ids_for(denial)
            if covered:
                authorised_denial_atom_ids.add(denial.atom_id)
                covered_self_evaluation_ids.update(covered)
                denial_owned_nuclei_by_atom[denial.atom_id] = frozenset(
                    nucleus_id
                    for evaluation_id in covered
                    for nucleus_id in self_evaluation_target_nuclei.get(
                        evaluation_id, frozenset()
                    )
                )
            continue
        position = ordered_observation_atoms.index(denial)
        immediate_antecedent = (
            ordered_observation_atoms[position - 1]
            if position > 0
            else None
        )
        # Anaphoric boundary and counter atoms are both resolved from every
        # preceding exact source owner.  Only one semantic-key owner may
        # survive; physical adjacency is not treated as ownership.
        if (
            immediate_antecedent is not None
            and immediate_antecedent.self_denial_not_fact
            and immediate_antecedent.source_fragments
        ):
            covered = denial_evaluation_ids_for(immediate_antecedent)
        else:
            antecedent_candidates = tuple(
                (preceding, denial_evaluation_ids_for(preceding))
                for preceding in ordered_observation_atoms
                if preceding.byte_start < denial.byte_start
                and preceding.source_fragments
                and not preceding.self_denial_not_fact
                and "nucleus_notice" in preceding.claim_kinds
            )
            antecedent_candidates = tuple(
                (preceding, evaluation_ids)
                for preceding, evaluation_ids in antecedent_candidates
                if evaluation_ids
            )
            if len(antecedent_candidates) == 1:
                covered = antecedent_candidates[0][1]
            else:
                covered = set()
                if len(antecedent_candidates) > 1:
                    issues.add(
                        "S11_MATCH_SELF_DENIAL_ANTECEDENT_OWNER_AMBIGUOUS"
                    )
        if covered:
            authorised_denial_atom_ids.add(denial.atom_id)
            covered_self_evaluation_ids.update(covered)
            denial_owned_nuclei_by_atom[denial.atom_id] = frozenset(
                nucleus_id
                for evaluation_id in covered
                for nucleus_id in self_evaluation_target_nuclei.get(
                    evaluation_id, frozenset()
                )
            )
        else:
            issues.add("S11_MATCH_SELF_DENIAL_ANTECEDENT_UNRESOLVED")
    if not set(self_evaluation_by_id) <= covered_self_evaluation_ids:
        issues.add("S11_MATCH_SELF_DENIAL_UNRESOLVED")

    terminal_self_atom_by_obligation: dict[str, str] = {}
    terminal_counter_atom_by_obligation: dict[str, str] = {}
    terminal_owned_nuclei_by_atom: dict[str, frozenset[str]] = {}
    if terminal_self_denial_pairs:
        suffix_length = 2 * len(terminal_self_denial_pairs)
        suffix = ordered_observation_atoms[-suffix_length:]
        remaining_pairs = set(terminal_self_denial_pairs)
        if len(suffix) != suffix_length:
            issues.add("S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID")
        else:
            for index in range(0, suffix_length, 2):
                boundary_atom = suffix[index]
                counter_atom = suffix[index + 1]
                candidate_pairs = tuple(
                    pair
                    for pair in remaining_pairs
                    if set(by_id[pair[0]].get("nucleus_ids", []))
                    == set(
                        denial_owned_nuclei_by_atom.get(
                            boundary_atom.atom_id, frozenset()
                        )
                    )
                )
                pair_nuclei = (
                    frozenset(by_id[candidate_pairs[0][0]].get("nucleus_ids", []))
                    if len(candidate_pairs) == 1
                    else frozenset()
                )
                counter_nuclei = (
                    frozenset(by_id[candidate_pairs[0][1]].get("nucleus_ids", []))
                    if len(candidate_pairs) == 1
                    else frozenset()
                )
                if (
                    len(candidate_pairs) != 1
                    or not pair_nuclei
                    or pair_nuclei != counter_nuclei
                    or not boundary_atom.self_denial_not_fact
                    or not boundary_atom.form_id.startswith(
                        "self_denial_anaphora:"
                    )
                    or boundary_atom.source_fragments
                    or boundary_atom.atom_id
                    not in authorised_denial_atom_ids
                    or pair_nuclei
                    != denial_owned_nuclei_by_atom.get(
                        boundary_atom.atom_id, frozenset()
                    )
                    or not counter_atom.self_denial_not_fact
                    or not counter_atom.form_id.startswith(
                        "bounded_counter_anaphora:"
                    )
                    or counter_atom.source_fragments
                    or counter_atom.atom_id
                    not in authorised_denial_atom_ids
                    or pair_nuclei
                    != denial_owned_nuclei_by_atom.get(
                        counter_atom.atom_id, frozenset()
                    )
                    or boundary_atom.atom_id == counter_atom.atom_id
                ):
                    issues.add(
                        "S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID"
                    )
                    continue
                self_id, counter_id = candidate_pairs[0]
                remaining_pairs.remove((self_id, counter_id))
                terminal_self_atom_by_obligation[self_id] = (
                    boundary_atom.atom_id
                )
                terminal_counter_atom_by_obligation[counter_id] = (
                    counter_atom.atom_id
                )
                terminal_owned_nuclei_by_atom[
                    boundary_atom.atom_id
                ] = pair_nuclei
                terminal_owned_nuclei_by_atom[
                    counter_atom.atom_id
                ] = pair_nuclei
            if remaining_pairs:
                issues.add("S11_MATCH_SELF_DENIAL_TERMINAL_PAIR_INVALID")

    active_source_slots = {
        slot
        for nucleus_id in surface_active
        for slot in _slots_for_nucleus(snapshot, nucleus_id)
    }
    active_stance_rows = tuple(
        by_id[obligation_id]
        for obligation_id in {
            row.get("obligation_id")
            for row in discourse_plan.get("nodes", [])
            if type(row) is dict
        }
        if obligation_id in by_id
        and by_id[obligation_id].get("kind") == STANCE_KIND
    )
    expected_reception_by_obligation: dict[
        str, set[tuple[str, str, str, frozenset[str]]]
    ] = {}

    def aggregate_action_status(statuses: set[str]) -> str:
        if len(statuses) == 1:
            return next(iter(statuses))
        return "undetermined"

    for row in active_stance_rows:
        target_ids = tuple(row.get("target_obligation_ids", []))
        target_rows = tuple(
            by_id[target_id]
            for target_id in target_ids
            if target_id in by_id
        )
        if not target_ids or len(target_rows) != len(target_ids):
            expected_reception_by_obligation[str(row["obligation_id"])] = set()
            continue
        target_nucleus_ids = {
            nucleus_id
            for target in target_rows
            for nucleus_id in target.get("nucleus_ids", [])
        }
        target_relation_ids = {
            relation_id
            for target in target_rows
            for relation_id in target.get("relation_ids", [])
        }
        verified_relations = tuple(
            relation
            for relation in semantic_overlay.relations
            if relation.source_relation_id in relation_atom_ids
        )
        explicit_relation_candidates = tuple(
            relation
            for relation in verified_relations
            if target_relation_ids & set(relation.source_relation_ids)
        )
        resolved_target_relation_ids = {
            relation_id
            for relation in explicit_relation_candidates
            for relation_id in relation.source_relation_ids
        }
        reception_relation_endpoint_keys = {
            (
                tuple(relation.from_source_anchor_ids),
                tuple(relation.to_source_anchor_ids),
            )
            for relation in explicit_relation_candidates
        }
        verified_reception_relation = (
            explicit_relation_candidates[0]
            if target_relation_ids
            and not target_relation_ids - resolved_target_relation_ids
            and len(reception_relation_endpoint_keys) == 1
            else None
        )
        if verified_reception_relation is not None:
            relation_endpoints = {
                verified_reception_relation.from_nucleus_id,
                verified_reception_relation.to_nucleus_id,
            }
            if (
                relation_endpoints <= surface_active
                and (
                    not target_nucleus_ids
                    and bool(target_relation_ids)
                    or bool(
                        target_nucleus_ids & relation_endpoints
                    )
                )
            ):
                target_nucleus_ids = set(relation_endpoints)
            else:
                verified_reception_relation = None
        target_bindings = tuple(
            binding_by_nucleus[nucleus_id]
            for nucleus_id in sorted(target_nucleus_ids)
            if nucleus_id in binding_by_nucleus
        )
        target_roles = {binding.source_role for binding in target_bindings}
        target_anchor_texts = frozenset(
            text
            for nucleus_id in target_nucleus_ids
            for text in nucleus_anchor_texts.get(nucleus_id, set())
        )
        if verified_reception_relation is not None:
            expected_scope = "relation"
        elif {"thought", "action"} <= target_roles:
            expected_scope = "thought_action"
        elif "thought" in target_roles and projection["thought"]:
            expected_scope = "thought"
        elif "action" in target_roles and projection["action"]:
            expected_scope = "action"
        else:
            expected_scope = "unresolved"
        action_statuses = {
            _canonical_status(binding.realization_status)
            for binding in target_bindings
            if binding.source_role == "action"
        }
        if expected_scope in {"action", "thought_action"}:
            expected_statuses = {
                aggregate_action_status(action_statuses)
            }
        elif expected_scope == "thought":
            expected_statuses = {"reported_content"}
        elif expected_scope == "relation":
            expected_statuses = {
                aggregate_action_status(action_statuses)
            }
        else:
            expected_statuses = set()
        expected_arity = (
            2 if expected_scope in {"thought_action", "relation"} else 1
        )
        signatures: set[tuple[str, str, str, frozenset[str]]] = set()
        if (
            len(target_anchor_texts) == expected_arity
            and len(expected_statuses) == 1
        ):
            signatures = {
                (
                    act,
                    expected_scope,
                    next(iter(expected_statuses)),
                    target_anchor_texts,
                )
                for act in row.get("allowed_response_acts", [])
                if type(act) is str
            }
        expected_reception_by_obligation[str(row["obligation_id"])] = signatures
    allowed_reception_signatures = {
        signature
        for signatures in expected_reception_by_obligation.values()
        for signature in signatures
    }

    try:
        expected_reception_binding_by_obligation = (
            _independent_reception_owner_contract(
                snapshot=snapshot,
                by_id=by_id,
                discourse_plan=discourse_plan,
                projection=projection,
            )
        )
    except Step11InverseSurfaceError:
        expected_reception_binding_by_obligation = {}
        issues.add("S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH")
    overlay_reception_binding_by_obligation = {
        row.reception_obligation_id: row
        for row in semantic_overlay.reception_antecedent_bindings
    }
    if (
        len(overlay_reception_binding_by_obligation)
        != len(semantic_overlay.reception_antecedent_bindings)
        or set(overlay_reception_binding_by_obligation)
        != set(expected_reception_binding_by_obligation)
    ):
        issues.add("S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH")
    for obligation_id, expected in expected_reception_binding_by_obligation.items():
        actual = overlay_reception_binding_by_obligation.get(obligation_id)
        if actual is None or {
            "binding_id": actual.binding_id,
            "reception_obligation_id": actual.reception_obligation_id,
            "reception_node_id": actual.reception_node_id,
            "source_target_obligation_ids": list(
                actual.source_target_obligation_ids
            ),
            "source_target_node_ids": list(actual.source_target_node_ids),
            "source_target_nucleus_ids": list(
                actual.source_target_nucleus_ids
            ),
            "antecedent_obligation_ids": list(
                actual.antecedent_obligation_ids
            ),
            "antecedent_node_ids": list(actual.antecedent_node_ids),
            "antecedent_nucleus_ids": list(actual.antecedent_nucleus_ids),
            "supporting_obligation_ids": list(
                actual.supporting_obligation_ids
            ),
            "supporting_node_ids": list(actual.supporting_node_ids),
            "supporting_nucleus_ids": list(
                actual.supporting_nucleus_ids
            ),
            "support_role": actual.support_role,
            "source_reception_opportunity_ids": list(
                actual.source_reception_opportunity_ids
            ),
            "action_lifecycle": actual.action_lifecycle,
            "allowed_response_acts": list(actual.allowed_response_acts),
            "evidence_grade": actual.evidence_grade,
        } != expected:
            issues.add("S11_MATCH_RECEPTION_BINDING_CONTRACT_MISMATCH")

    # Multiple required reception obligations can be projections of the same
    # source relation in one discourse group.  When one exact local-referent
    # set strictly contains every other set, the forward surface integrates
    # them into that maximal typed atom.  The exact per-obligation overlay
    # remains unchanged above; this is only the independently recomputed
    # visible-surface equivalence class.
    reception_group_by_node = {
        str(node_id): str(group.get("sentence_group_id"))
        for group in discourse_plan.get("sentence_groups", [])
        if type(group) is dict
        and group.get("section_role") == "reception"
        and type(group.get("sentence_group_id")) is str
        for node_id in group.get("node_ids", [])
        if type(node_id) is str
    }
    surface_reception_contract_by_obligation = {
        obligation_id: dict(expected)
        for obligation_id, expected in (
            expected_reception_binding_by_obligation.items()
        )
    }
    reception_families: dict[
        tuple[Any, ...], list[tuple[str, dict[str, Any]]]
    ] = {}
    for obligation_id, expected in (
        expected_reception_binding_by_obligation.items()
    ):
        family = (
            tuple(expected["source_target_obligation_ids"]),
            tuple(expected["allowed_response_acts"]),
        )
        reception_families.setdefault(family, []).append(
            (obligation_id, expected)
        )
    for rows in reception_families.values():
        if len(rows) < 2:
            continue
        visible_sets = {
            obligation_id: frozenset(
                (
                    *expected["antecedent_nucleus_ids"],
                    *expected["supporting_nucleus_ids"],
                )
            )
            for obligation_id, expected in rows
        }
        maximal = tuple(
            (obligation_id, expected)
            for obligation_id, expected in rows
            if all(
                other_set <= visible_sets[obligation_id]
                for other_set in visible_sets.values()
            )
        )
        if len(maximal) != 1:
            continue
        _maximal_id, maximal_contract = maximal[0]
        family_group_ids = {
            reception_group_by_node.get(
                str(expected["reception_node_id"])
            )
            for _obligation_id, expected in rows
        }
        if len(family_group_ids) != 1 or None in family_group_ids:
            # A comparable reception family is one semantic atom.  Splitting
            # it across discourse groups prevents canonical integration and
            # must fail independently even if both clauses parse.
            issues.add("S11_MATCH_DUPLICATE_SEMANTIC_ATOM")
            issues.add("S11_MATCH_RECEPTION_BINDING_UNRESOLVED")
        for obligation_id, _expected in rows:
            surface_reception_contract_by_obligation[obligation_id] = dict(
                maximal_contract
            )

    def obligation_observation_atom_ids(obligation_id: str) -> tuple[str, ...]:
        row = by_id[obligation_id]
        kind = row.get("kind")
        if kind == "grounded_relation_preservation":
            return tuple(
                dict.fromkeys(
                    atom_id
                    for relation_id in row.get("relation_ids", [])
                    for atom_id in relation_atom_ids.get(relation_id, ())
                )
            )
        if kind == "unknown_boundary_preservation":
            wanted = set(row.get("unknown_boundary_ids", []))
            return tuple(
                dict.fromkeys(
                    (
                        *(
                            atom_id
                            for unknown in semantic_overlay.unknowns
                            if wanted & set(unknown.source_unknown_ids)
                            for atom_id in unknown_atom_ids.get(
                                unknown.unknown_id, ()
                            )
                        ),
                        *(
                            atom_id
                            for source_id in sorted(wanted)
                            for atom_id in suppression_atom_ids_by_source.get(
                                source_id, ()
                            )
                        ),
                    )
                )
            )
        if kind == "self_denial_boundary":
            atom_id = terminal_self_atom_by_obligation.get(obligation_id)
            return (atom_id,) if atom_id is not None else ()
        if kind == "bounded_counterposition":
            atom_id = terminal_counter_atom_by_obligation.get(obligation_id)
            return (atom_id,) if atom_id is not None else ()
        nuclei = frozenset(row.get("nucleus_ids", []))

        # A fused observation may carry more than one source slot (for
        # example, one thought plus one action).  Reception ownership is
        # nevertheless scoped to the exact antecedent nuclei.  Rebuild that
        # scoped owner from the independent source-reference registry and the
        # parser's slot hints; comparing the antecedent with the atom-wide
        # nucleus set would incorrectly reject an action-only antecedent in a
        # neutral pair.  This is deliberately an exact-set test, not a subset
        # relaxation: every wanted nucleus must be carried by a uniquely
        # owned reference, and no intersecting reference may straddle the
        # requested scope.
        scoped_owners: list[str] = []
        if nuclei:
            for atom in observation_atoms:
                owned_references = tuple(
                    reference
                    for reference in reference_registry
                    if literal_owner_by_ordinal.get(
                        reference.reference_ordinal
                    )
                    is atom
                    and bool(set(reference.nucleus_ids) & set(nuclei))
                )
                if not owned_references or any(
                    not set(reference.nucleus_ids) <= set(nuclei)
                    for reference in owned_references
                ):
                    continue
                scoped_nuclei = frozenset(
                    nucleus_id
                    for reference in owned_references
                    for nucleus_id in reference.nucleus_ids
                )
                if scoped_nuclei != nuclei:
                    continue
                if atom.grounded_phrases:
                    if any(
                        sum(
                            set(phrase_binding.owner_nucleus_ids)
                            == set(reference.nucleus_ids)
                            for phrase_binding in grounded_phrase_bindings
                            if phrase_binding.atom_id == atom.atom_id
                        )
                        != 1
                        for reference in owned_references
                    ):
                        continue
                elif any(
                    len(
                        tuple(
                            index
                            for index, fragment in enumerate(
                                atom.source_fragments
                            )
                            if fragment == reference.source_literal
                            and (
                                index < len(atom.source_slot_hints)
                                and atom.source_slot_hints[index]
                                == reference.source_slot
                                or index >= len(atom.source_slot_hints)
                                and atom.atom_id
                                in authorised_relation_atom_ids
                            )
                        )
                    )
                    != 1
                    for reference in owned_references
                ):
                    continue
                scoped_owners.append(atom.atom_id)
        return tuple(dict.fromkeys(scoped_owners))

    expected_reception_by_obligation: dict[
        str, set[tuple[Any, ...]]
    ] = {}
    reception_binding_ids_by_atom: dict[str, tuple[str, ...]] = {}
    integrated_reception_binding_ids: list[str] = []
    for obligation_id, expected in (
        surface_reception_contract_by_obligation.items()
    ):
        antecedent_owner_ids: list[str] = []
        support_owner_ids: list[str] = []
        antecedent_owned_nuclei: list[str] = []
        support_owned_nuclei: list[str] = []
        owner_valid = True
        for antecedent_id in expected["antecedent_obligation_ids"]:
            owners = obligation_observation_atom_ids(antecedent_id)
            if len(owners) != 1:
                owner_valid = False
                break
            antecedent_owner_ids.append(owners[0])
            carried = terminal_owned_nuclei_by_atom.get(
                owners[0], exact_nuclei_by_atom.get(owners[0], frozenset())
            )
            wanted = frozenset(by_id[antecedent_id].get("nucleus_ids", []))
            if not wanted or not wanted <= carried:
                owner_valid = False
                break
            antecedent_owned_nuclei.extend(sorted(wanted))
        for support_id in expected["supporting_obligation_ids"]:
            owners = obligation_observation_atom_ids(support_id)
            if len(owners) != 1:
                owner_valid = False
                break
            support_owner_ids.append(owners[0])
            carried = terminal_owned_nuclei_by_atom.get(
                owners[0], exact_nuclei_by_atom.get(owners[0], frozenset())
            )
            wanted = frozenset(by_id[support_id].get("nucleus_ids", []))
            if not wanted or not wanted <= carried:
                owner_valid = False
                break
            support_owned_nuclei.extend(sorted(wanted))
        antecedent_owner_ids = list(dict.fromkeys(antecedent_owner_ids))
        support_owner_ids = list(dict.fromkeys(support_owner_ids))
        owned_nuclei = set(
            (*antecedent_owned_nuclei, *support_owned_nuclei)
        )
        expected_visible_nuclei = frozenset(
            (
                *expected["antecedent_nucleus_ids"],
                *expected["supporting_nucleus_ids"],
            )
        )
        if (
            not owner_valid
            or not expected["antecedent_nucleus_ids"]
            or expected_visible_nuclei != owned_nuclei
        ):
            issues.add("S11_MATCH_RECEPTION_ANTECEDENT_OWNER_INVALID")
            expected_reception_by_obligation[obligation_id] = set()
            continue
        target_bindings = tuple(
            binding_by_nucleus[nucleus_id]
            for nucleus_id in sorted(expected_visible_nuclei)
            if nucleus_id in binding_by_nucleus
        )
        target_roles = {row.source_role for row in target_bindings}
        relation_owner_ids = tuple(
            obligation_id
            for obligation_id in dict.fromkeys(
                (
                    *expected["source_target_obligation_ids"],
                    *expected["antecedent_obligation_ids"],
                )
            )
            if by_id[obligation_id].get("kind")
            == "grounded_relation_preservation"
            and frozenset(
                by_id[obligation_id].get("nucleus_ids", [])
            )
            == expected_visible_nuclei
        )
        if len(relation_owner_ids) > 1:
            issues.add("S11_MATCH_RECEPTION_ANTECEDENT_OWNER_INVALID")
            expected_reception_by_obligation[obligation_id] = set()
            continue
        relation_owned = bool(relation_owner_ids)
        if relation_owned:
            scope = (
                "relation_action" if "action" in target_roles else "relation"
            )
        elif {"thought", "action"} <= target_roles:
            scope = "thought_action"
        elif "thought" in target_roles:
            scope = "thought"
        elif "action" in target_roles:
            scope = "action"
        else:
            issues.add("S11_MATCH_RECEPTION_ANTECEDENT_OWNER_INVALID")
            expected_reception_by_obligation[obligation_id] = set()
            continue
        reference_rows = tuple(
            row
            for row in reference_registry
            if set(row.nucleus_ids) & expected_visible_nuclei
        )
        referenced_nuclei = {
            nucleus_id
            for row in reference_rows
            for nucleus_id in row.nucleus_ids
            if nucleus_id in expected_visible_nuclei
        }
        reference_signature = tuple(
            (row.reference_ordinal, row.endpoint_role)
            for row in sorted(
                reference_rows, key=lambda item: item.reference_ordinal
            )
        )
        if referenced_nuclei != set(expected_visible_nuclei):
            issues.add("S11_MATCH_RECEPTION_VISIBLE_REFERENT_UNBOUND")
            expected_reception_by_obligation[obligation_id] = set()
            continue
        status = (
            "reported_content"
            if scope == "thought"
            else str(expected["action_lifecycle"])
            if "action" in target_roles
            else "undetermined"
        )
        signatures = {
            (
                act,
                scope,
                status,
                reference_signature,
                tuple(expected["antecedent_obligation_ids"]),
                tuple(expected["antecedent_node_ids"]),
                tuple(expected["antecedent_nucleus_ids"]),
                tuple(expected["supporting_obligation_ids"]),
                tuple(expected["supporting_node_ids"]),
                tuple(expected["supporting_nucleus_ids"]),
                tuple(antecedent_owner_ids),
                tuple(support_owner_ids),
            )
            for act in expected["allowed_response_acts"]
        }
        expected_reception_by_obligation[obligation_id] = signatures
    allowed_reception_signatures = {
        signature
        for signatures in expected_reception_by_obligation.values()
        for signature in signatures
    }
    reception_binding_ids_by_signature: dict[
        tuple[Any, ...], tuple[str, ...]
    ] = {}
    for obligation_id, signatures in expected_reception_by_obligation.items():
        binding_id = str(
            expected_reception_binding_by_obligation[obligation_id][
                "binding_id"
            ]
        )
        for signature in signatures:
            reception_binding_ids_by_signature[signature] = tuple(
                sorted(
                    {
                        *reception_binding_ids_by_signature.get(
                            signature, ()
                        ),
                        binding_id,
                    }
                )
            )

    def reception_signature(
        atom: Step11ParsedAtom,
    ) -> tuple[Any, ...] | None:
        if (
            not atom.form_id.startswith("reception:anaphoric:")
            or atom.source_fragments
            or atom.introduced_reference is not None
            or atom.compound_label_references
            or atom.relation_endpoint_references
            or atom.unknown_target_references
            or atom.reception_antecedent_references
        ):
            issues.add("S11_MATCH_RECEPTION_REFERENCE_MODE_MISMATCH")
            return None
        semantic_head = (
            atom.reception_act,
            atom.reception_scope,
            _canonical_status(atom.realization_status),
        )
        head_candidates = tuple(
            signature
            for signature in allowed_reception_signatures
            if signature[:3] == semantic_head
        )
        if len(head_candidates) != 1:
            issues.add("S11_MATCH_RECEPTION_ANAPHORA_AMBIGUOUS")
            return None
        signature = head_candidates[0]
        binding_ids = reception_binding_ids_by_signature.get(signature, ())
        if not binding_ids:
            return None
        previous = reception_binding_ids_by_atom.get(atom.atom_id)
        if previous is not None and previous != binding_ids:
            return None
        reception_binding_ids_by_atom[atom.atom_id] = binding_ids
        return signature

    literal_ranges: list[tuple[str, str, int, int, str]] = []
    for atom in observation_atoms:
        for fragment_index, fragment in enumerate(atom.source_fragments):
            fragment_source_slots = tuple(
                slot
                for slot, values in allowed_by_slot.items()
                if fragment in values
            )
            if fragment_index < len(atom.source_slot_hints):
                fragment_source_slots = tuple(
                    slot
                    for slot in fragment_source_slots
                    if slot == atom.source_slot_hints[fragment_index]
                )
            for slot in fragment_source_slots:
                if slot in {"thought", "action"}:
                    source_text = str(projection[slot])
                    cursor = 0
                    found = False
                    while True:
                        start = source_text.find(fragment, cursor)
                        if start < 0:
                            break
                        found = True
                        literal_ranges.append(
                            (
                                atom.atom_id,
                                slot,
                                start,
                                start + len(fragment),
                                fragment,
                            )
                        )
                        cursor = start + 1
                    if not found:
                        issues.add("S11_MATCH_LITERAL_SOURCE_RANGE_INVALID")
                    continue
                labels = tuple(projection[slot])
                for ordinal, label in enumerate(labels):
                    if fragment == label or label in fragment.split("・"):
                        literal_ranges.append(
                            (
                                atom.atom_id,
                                slot,
                                ordinal,
                                ordinal + 1,
                                label,
                            )
                        )
    for left_index, left in enumerate(literal_ranges):
        for right in literal_ranges[left_index + 1 :]:
            if left[1] != right[1] or not (
                left[2] < right[3] and right[2] < left[3]
            ):
                continue
            issues.add("S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED")

    semantic_signatures: set[tuple[Any, ...]] = set()
    for atom in witness.atoms:
        signature = (
            atom.section_role,
            atom.form_id,
            atom.claim_kinds,
            atom.source_fragments,
            tuple(
                (
                    phrase.visible_feature_fingerprint_sha256,
                    phrase.phrase_profile_id,
                    phrase.action_lifecycle,
                    phrase.binding_family,
                    phrase.anchor_text,
                )
                for phrase in atom.grounded_phrases
            ),
            grounded_owner_sequence_by_atom.get(atom.atom_id, ()),
            atom.predicate_role,
            _canonical_status(atom.realization_status),
            atom.relation_type,
            atom.relation_direction,
            atom.unknown_dimension_class,
            atom.self_denial_not_fact,
            atom.reception_act,
            atom.reception_scope,
            (
                (
                    atom.introduced_reference.reference_ordinal,
                    atom.introduced_reference.endpoint_role,
                )
                if atom.introduced_reference is not None
                else None
            ),
            tuple(
                (row.reference_ordinal, row.endpoint_role)
                for row in atom.compound_label_references
                if type(row) is Step11EndpointReference
            ),
            tuple(
                (row.reference_ordinal, row.endpoint_role)
                for row in atom.relation_endpoint_references
                if type(row) is Step11EndpointReference
            ),
            tuple(
                (row.reference_ordinal, row.endpoint_role)
                for row in atom.unknown_target_references
                if type(row) is Step11EndpointReference
            ),
            tuple(
                (row.reference_ordinal, row.endpoint_role)
                for row in atom.reception_antecedent_references
                if type(row) is Step11EndpointReference
            ),
        )
        if signature in semantic_signatures:
            issues.add("S11_MATCH_DUPLICATE_SEMANTIC_ATOM")
        semantic_signatures.add(signature)
    for left_index, left in enumerate(observation_atoms):
        for right in observation_atoms[left_index + 1 :]:
            if (
                left.source_fragments
                and left.source_fragments == right.source_fragments
                and left.predicate_role == right.predicate_role
                and (
                    set(left.claim_kinds) < set(right.claim_kinds)
                    or set(right.claim_kinds) < set(left.claim_kinds)
                )
            ):
                issues.add("S11_MATCH_SEMANTIC_SUBSUMPTION")

    # Every parsed semantic atom must have a source-side authorisation.  This
    # is intentionally separate from required-obligation coverage: a body may
    # cover every required row and still smuggle in an unsupported relation,
    # unknown dimension, self-judgement, or reception act.
    for atom in observation_atoms:
        atom_slots = set(fragment_slots.get(atom.atom_id, ()))
        authorised = True
        for claim in atom.claim_kinds:
            if claim in {"nucleus_notice", "source_context"}:
                grounded_authority = bool(
                    atom.grounded_phrases
                    and exact_nuclei_by_atom.get(atom.atom_id)
                )
                literal_authority = bool(atom.source_fragments) and bool(
                    atom_slots
                ) and atom_slots <= active_source_slots
                claim_authorised = bool(
                    (grounded_authority or literal_authority)
                    and (
                        claim == "source_context"
                        or bool(exact_nuclei_by_atom.get(atom.atom_id))
                        or atom.atom_id in authorised_unknown_atom_ids
                        or atom.atom_id in authorised_denial_atom_ids
                    )
                )
            elif claim == "relation_notice":
                claim_authorised = (
                    atom.atom_id in authorised_relation_atom_ids
                    or atom.atom_id
                    in authorised_mixed_emotion_atom_ids
                )
            elif claim == "mixed_emotion_relation":
                claim_authorised = (
                    atom.atom_id in authorised_mixed_emotion_atom_ids
                )
            elif claim == "unknown_boundary":
                claim_authorised = atom.atom_id in authorised_unknown_atom_ids
            elif claim in {
                "self_denial_boundary",
                "bounded_counterposition",
            }:
                claim_authorised = (
                    atom.atom_id in authorised_denial_atom_ids
                )
            else:
                claim_authorised = False
            authorised = authorised and claim_authorised
        if not atom.claim_kinds or not authorised:
            issues.add("S11_MATCH_SURPLUS_SEMANTIC_ATOM")
        bound_nuclei = exact_nuclei_by_atom.get(atom.atom_id, frozenset())
        bound_roles = {
            binding_by_nucleus[nucleus_id].source_role
            for nucleus_id in bound_nuclei
            if nucleus_id in binding_by_nucleus
        }
        # A typed reference introduction carries the independently rebuilt
        # endpoint role validated against ``reference_registry`` above.  Its
        # physical source slot remains an ownership fact, not a semantic role:
        # legacy app projection can place an action predicate inside thought.
        if (
            atom.introduced_reference is not None
            and atom.predicate_role
            != atom.introduced_reference.endpoint_role
        ):
            issues.add("S11_MATCH_PREDICATE_ROLE_MISMATCH")
        elif (
            atom.introduced_reference is None
            and atom.predicate_role == "action"
            and bound_roles - {"action"}
        ):
            issues.add("S11_MATCH_PREDICATE_ROLE_MISMATCH")
        elif (
            atom.introduced_reference is None
            and atom.predicate_role == "thought"
            and bound_roles - {"thought"}
        ):
            issues.add("S11_MATCH_PREDICATE_ROLE_MISMATCH")
        elif (
            atom.introduced_reference is None
            and atom.predicate_role == "thought_action"
            and not ({"thought", "action"} <= bound_roles)
        ):
            issues.add("S11_MATCH_PREDICATE_ROLE_MISMATCH")
        parsed_status = _canonical_status(atom.realization_status)
        if atom.predicate_role in {"action", "thought_action"}:
            expected_action_statuses = {
                _canonical_status(
                    binding_by_nucleus[nucleus_id].realization_status
                )
                for nucleus_id in bound_nuclei
                if nucleus_id in binding_by_nucleus
                and binding_by_nucleus[nucleus_id].source_role == "action"
            }
            if parsed_status != "undetermined" and (
                parsed_status not in expected_action_statuses
                or len(expected_action_statuses) != 1
            ):
                issues.add("S11_MATCH_MODALITY_STATUS_MISMATCH")
        elif atom.predicate_role == "thought" and parsed_status != "reported_content":
            issues.add("S11_MATCH_MODALITY_STATUS_MISMATCH")
    for atom in reception_atoms:
        signature = reception_signature(atom)
        if (
            atom.claim_kinds != ("bound_reception",)
            or signature not in allowed_reception_signatures
            or len(atom.source_fragments) != len(set(atom.source_fragments))
        ):
            issues.add("S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH")
            issues.add("S11_MATCH_SURPLUS_SEMANTIC_ATOM")
        elif signature is not None:
            integrated_reception_binding_ids.extend(
                reception_binding_ids_by_signature[signature]
            )
    expected_reception_binding_ids = {
        value["binding_id"]
        for value in expected_reception_binding_by_obligation.values()
    }
    if (
        set(integrated_reception_binding_ids)
        != expected_reception_binding_ids
        or len(integrated_reception_binding_ids)
        != len(set(integrated_reception_binding_ids))
    ):
        issues.add("S11_MATCH_RECEPTION_BINDING_UNRESOLVED")
    required_ids = tuple(content_plan.get("required_coverage_obligation_ids", []))
    bindings: list[Step11BindingRow] = []
    for obligation_id in required_ids:
        row = by_id.get(obligation_id)
        if row is None:
            issues.add("S11_MATCH_REQUIRED_OBLIGATION_UNKNOWN")
            continue
        kind = row.get("kind")
        atom_ids: tuple[str, ...] = ()
        basis = "source_fragment"
        if kind == STANCE_KIND:
            allowed_signatures = expected_reception_by_obligation.get(
                str(obligation_id), set()
            )
            matched_reception_atoms = tuple(
                atom
                for atom in reception_atoms
                if reception_signature(atom) in allowed_signatures
            )
            atom_ids = tuple(atom.atom_id for atom in matched_reception_atoms)
            basis = (
                "bound_reception_anaphoric_exact_semantic_owner"
                if matched_reception_atoms
                and all(
                    atom.form_id.startswith("reception:anaphoric:")
                    and not atom.source_fragments
                    and not atom.reception_antecedent_references
                    for atom in matched_reception_atoms
                )
                else "bound_reception_act_scope_status_exact_target"
            )
        elif kind == "grounded_relation_preservation":
            wanted_ids = set(row.get("relation_ids", []))
            atom_ids = tuple(
                dict.fromkeys(
                    atom_id
                    for relation_id in sorted(wanted_ids & set(relation_ids))
                    for atom_id in relation_atom_ids.get(relation_id, ())
                )
            )
            basis = "relation_type_direction_endpoint"
        elif kind == "unknown_boundary_preservation":
            wanted_unknown_ids = set(row.get("unknown_boundary_ids", []))
            owned_unknowns = tuple(
                unknown
                for unknown in semantic_overlay.unknowns
                if wanted_unknown_ids & set(unknown.source_unknown_ids)
            )
            atom_ids = tuple(
                dict.fromkeys(
                    (
                        *(
                            atom_id
                            for unknown in owned_unknowns
                            for atom_id in unknown_atom_ids.get(
                                unknown.unknown_id, ()
                            )
                        ),
                        *(
                            atom_id
                            for source_id in sorted(wanted_unknown_ids)
                            for atom_id in suppression_atom_ids_by_source.get(
                                source_id, ()
                            )
                        ),
                    )
                )
            )
            covered_unknown_ids = {
                source_id
                for unknown in owned_unknowns
                if unknown_atom_ids.get(unknown.unknown_id)
                for source_id in compatible_source_unknown_ids.get(
                    unknown.unknown_id, frozenset()
                )
                if source_id in wanted_unknown_ids
            }
            covered_unknown_ids.update(
                wanted_unknown_ids
                & set(suppression_atom_ids_by_source)
            )
            if covered_unknown_ids != wanted_unknown_ids:
                atom_ids = ()
                issues.add("S11_MATCH_UNKNOWN_SOURCE_ID_UNRESOLVED")
            basis = (
                "context_resolved_temporal_unknown_suppression"
                if wanted_unknown_ids
                & set(suppression_atom_ids_by_source)
                else "unknown_id_dimension_exact_target"
            )
        elif kind in {"self_denial_boundary", "bounded_counterposition"}:
            if str(obligation_id) in terminal_self_atom_by_obligation:
                atom_ids = (
                    terminal_self_atom_by_obligation[str(obligation_id)],
                )
                basis = "terminal_identity_fact_boundary"
            elif str(obligation_id) in terminal_counter_atom_by_obligation:
                atom_ids = (
                    terminal_counter_atom_by_obligation[str(obligation_id)],
                )
                basis = "terminal_bounded_counterposition"
            else:
                atom_ids = tuple(
                    atom.atom_id
                    for atom in observation_atoms
                    if atom.self_denial_not_fact
                    and kind in atom.claim_kinds
                    and atom.atom_id in authorised_denial_atom_ids
                )
                basis = "identity_fact_denial"
        else:
            wanted_nuclei = tuple(row.get("nucleus_ids", []))
            text_nuclei = tuple(
                nucleus_id
                for nucleus_id in wanted_nuclei
                if nucleus_anchor_texts.get(nucleus_id)
            )
            matched_by_nucleus = {
                nucleus_id: tuple(
                    atom.atom_id
                    for atom in observation_atoms
                    if "nucleus_notice" in atom.claim_kinds
                    and nucleus_id
                    in exact_nuclei_by_atom.get(atom.atom_id, frozenset())
                )
                for nucleus_id in text_nuclei
            }
            if text_nuclei and all(matched_by_nucleus.values()):
                atom_ids = tuple(
                    dict.fromkeys(
                        atom_id
                        for nucleus_id in text_nuclei
                        for atom_id in matched_by_nucleus[nucleus_id]
                    )
                )
                basis = "exact_nucleus_anchor"
            elif text_nuclei:
                atom_ids = ()
                basis = "exact_nucleus_anchor"
            else:
                slots = {
                    slot
                    for nucleus_id in wanted_nuclei
                    for slot in _slots_for_nucleus(snapshot, nucleus_id)
                }
                atom_ids = tuple(
                    atom.atom_id
                    for atom in observation_atoms
                    if "nucleus_notice" in atom.claim_kinds
                    and slots
                    & set(fragment_slots.get(atom.atom_id, ()))
                )
                basis = "exact_label_slot"
        if not atom_ids:
            issues.add("S11_MATCH_REQUIRED_OBLIGATION_UNBOUND")
        bindings.append(Step11BindingRow(str(obligation_id), str(kind), tuple(dict.fromkeys(atom_ids)), basis))
    return Step11VerifiedSurfaceBinding(
        schema_version=STEP11_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256=artifact_sha256(_witness_material(witness)),
        obligation_ledger_sha256=artifact_sha256(ledger),
        content_plan_sha256=artifact_sha256(content_plan),
        discourse_plan_sha256=artifact_sha256(discourse_plan),
        binding_rows=tuple(bindings),
        required_obligation_ids=required_ids,
        integrated_relation_ids=tuple(sorted(relation_ids)),
        integrated_unknown_ids=tuple(sorted(unknown_ids)),
        source_unknown_oracle_sha256=source_unknown_oracle_sha256,
        integrated_mixed_emotion_requirement_ids=tuple(
            sorted(integrated_mixed_emotion_requirement_ids)
        ),
        integrated_reception_binding_ids=tuple(
            sorted(integrated_reception_binding_ids)
        ),
        source_fragment_count=sum(
            len(row.source_fragments) + len(row.grounded_phrases)
            for row in witness.atoms
        ),
        issue_codes=tuple(sorted(issues)),
        verified=not issues,
        grounded_phrase_bindings=grounded_phrase_bindings,
    )


def _binding_material(value: Step11VerifiedSurfaceBinding) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "obligation_ledger_sha256": value.obligation_ledger_sha256,
        "content_plan_sha256": value.content_plan_sha256,
        "discourse_plan_sha256": value.discourse_plan_sha256,
        "binding_rows": [
            {"obligation_id": row.obligation_id, "obligation_kind": row.obligation_kind, "atom_ids": list(row.atom_ids), "match_basis": row.match_basis}
            for row in value.binding_rows
        ],
        "required_obligation_ids": list(value.required_obligation_ids),
        "integrated_relation_ids": list(value.integrated_relation_ids),
        "integrated_unknown_ids": list(value.integrated_unknown_ids),
        "source_unknown_oracle_sha256": (
            value.source_unknown_oracle_sha256
        ),
        "integrated_mixed_emotion_requirement_ids": list(
            value.integrated_mixed_emotion_requirement_ids
        ),
        "integrated_reception_binding_ids": list(
            value.integrated_reception_binding_ids
        ),
        "source_fragment_count": value.source_fragment_count,
        "issue_codes": list(value.issue_codes),
        "verified": value.verified,
        "grounded_phrase_bindings": [
            {
                "binding_id": row.binding_id,
                "atom_id": row.atom_id,
                "visible_feature_fingerprint_sha256": (
                    row.visible_feature_fingerprint_sha256
                ),
                "phrase_profile_id": row.phrase_profile_id,
                "anchor_risk_rank": row.anchor_risk_rank,
                "action_lifecycle": row.action_lifecycle,
                "binding_family": row.binding_family,
                "owner_nucleus_ids": list(row.owner_nucleus_ids),
                "owner_obligation_ids": list(row.owner_obligation_ids),
                "source_anchor_ids": list(row.source_anchor_ids),
                "source_anchor_slot": row.source_anchor_slot,
                "source_anchor_start": row.source_anchor_start,
                "source_anchor_end": row.source_anchor_end,
                "source_anchor_text_sha256": (
                    row.source_anchor_text_sha256
                ),
                "source_anchor_use_reason_code": (
                    row.source_anchor_use_reason_code
                ),
                "match_candidate_count": row.match_candidate_count,
            }
            for row in value.grounded_phrase_bindings
        ],
    }


# Compatibility entry points.  The inverse parser/matcher stays independent;
# forward candidate ownership and selection live in the separate hard-gate
# module and are imported lazily to avoid an inverse-to-forward dependency at
# module import time.
def evaluate_step11_natural_surface_candidate(
    candidate: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11HardGateResult:
    from emlis_ai_step11_hard_gate_v3 import (
        evaluate_step11_natural_surface_candidate as _evaluate,
    )

    return _evaluate(
        candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )


def select_step11_natural_surface_candidates(
    candidates: Sequence[Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    candidate_limit: int = 12,
) -> Step11SelectionResult:
    from emlis_ai_step11_hard_gate_v3 import (
        select_step11_natural_surface_candidates as _select,
    )

    return _select(
        candidates,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
        candidate_limit=candidate_limit,
    )


__all__ = [
    "STEP11_HARD_GATE_SCHEMA",
    "STEP11_PARSED_WITNESS_SCHEMA",
    "STEP11_SELECTION_SCHEMA",
    "STEP11_SOURCE_UNKNOWN_ORACLE_SCHEMA",
    "STEP11_VERIFIED_BINDING_SCHEMA",
    "Step11BindingRow",
    "Step11EndpointReference",
    "Step11GateOutcome",
    "Step11GroundedPhraseBinding",
    "Step11HardGateResult",
    "Step11InverseSurfaceError",
    "Step11ParsedAtom",
    "Step11ParsedGroundedPhrase",
    "Step11ParsedSentence",
    "Step11ParsedSurfaceWitness",
    "Step11SelectionResult",
    "Step11SelectorAttributes",
    "Step11VerifiedSurfaceBinding",
    "evaluate_step11_natural_surface_candidate",
    "match_step11_natural_surface",
    "parse_step11_natural_surface",
    "select_step11_natural_surface_candidates",
]


# ---------------------------------------------------------------------------
# rc0028 runtime-disconnected independent inverse surface (append-only)
#
# The rc0027 module above remains byte-for-byte stable.  This inverse reads
# only final body bytes and the shared declarative experiment catalog.  It
# never imports the forward surface, lexicalizer, runtime adapter, or gate.
# Successor authority imports are local to the match entry point.

STEP11_RC0028_EXPERIMENT_PARSED_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_parsed_witness.v1"
)
STEP11_RC0028_EXPERIMENT_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_verified_binding.v1"
)

_STEP11_RC0028_EXPERIMENT_BODY_BYTE_MAX = 1_000_000
_STEP11_RC0028_EXPERIMENT_STRUCTURE_LINE_MAX = 1_024
_STEP11_RC0028_EXPERIMENT_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Step11Rc0028ExperimentInverseSurfaceError(ValueError):
    """Fail closed with one body-free experiment machine code."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"STEP11_RC0028_[A-Z0-9_]{2,95}", code) is None
        ):
            code = "STEP11_RC0028_INVERSE_SURFACE_REJECTED"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParsedConstructionRoleOwner:
    owner_ordinal: int
    lexical_role_kind: str
    construction_position: str
    role_position_key: str
    role_position_atom_code: str


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParsedConstructionAtom:
    ordinal: int
    construction_code: str
    construction_atom_code: str
    role_owner_bindings: tuple[
        Step11Rc0028ExperimentParsedConstructionRoleOwner, ...
    ]


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParsedRelationAtom:
    ordinal: int
    effective_relation_type: str
    from_owner_ordinal: int
    to_owner_ordinal: int
    direction: str
    relation_surface_key: str


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParsedSemanticLinkAtom:
    ordinal: int
    relation_type: str
    from_owner_ordinal: int
    to_owner_ordinal: int
    direction: str
    semantic_link_surface_key: str


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentParsedExplicitUnknownAtom:
    ordinal: int
    dimension: str
    affected_owner_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentParsedSurfaceWitness:
    schema_version: str
    body_sha256: str
    experiment_catalog_sha256: str
    base_witness: Step11ParsedSurfaceWitness
    construction_atoms: tuple[
        Step11Rc0028ExperimentParsedConstructionAtom, ...
    ]
    relation_atoms: tuple[Step11Rc0028ExperimentParsedRelationAtom, ...]
    semantic_link_atoms: tuple[
        Step11Rc0028ExperimentParsedSemanticLinkAtom, ...
    ]
    explicit_unknown_atoms: tuple[
        Step11Rc0028ExperimentParsedExplicitUnknownAtom, ...
    ]
    structure_line_count: int
    body_free_export_allowed: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentVerifiedSurfaceBinding:
    schema_version: str
    parsed_witness_sha256: str
    base_witness_sha256: str
    successor_snapshot_sha256: str
    experiment_catalog_sha256: str
    bound_owner_ordinal_count: int
    construction_instance_binding_count: int
    construction_slot_binding_count: int
    participation_binding_count: int
    relation_binding_count: int
    relation_endpoint_binding_count: int
    semantic_link_binding_count: int
    explicit_unknown_binding_count: int
    semantic_coverage_authorized: bool
    issue_codes: tuple[str, ...]
    hard_verified: bool
    body_free_export_allowed: bool = False


def _step11_rc0028_inverse_catalog() -> tuple[dict[str, Any], str]:
    # Local-only import: importing rc0027 matcher must not load rc0028.
    from emlis_ai_step11_rc0028_experiment_surface_catalog_v3 import (
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256,
        validate_step11_rc0028_experiment_surface_catalog,
    )

    catalog = STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
    issues = validate_step11_rc0028_experiment_surface_catalog(catalog)
    if issues:
        raise Step11Rc0028ExperimentInverseSurfaceError(issues[0])
    return catalog, STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0028_exact_inverse_map(
    value: Any,
    *,
    failure_code: str,
) -> dict[str, str]:
    if (
        type(value) is not dict
        or not value
        or any(
            type(key) is not str
            or not key
            or type(item) is not str
            or not item
            for key, item in value.items()
        )
        or len(set(value.values())) != len(value)
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(failure_code)
    return {item: key for key, item in value.items()}


def _step11_rc0028_parse_owner_token(
    value: str,
    *,
    owner_token_to_ordinal: Mapping[str, str],
) -> int:
    ordinal_text = owner_token_to_ordinal.get(value)
    if type(ordinal_text) is not str or not ordinal_text.isdecimal():
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_OWNER_ORDINAL_INVALID"
        )
    ordinal = int(ordinal_text)
    if ordinal < 1:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_OWNER_ORDINAL_INVALID"
        )
    return ordinal


def _step11_rc0028_parse_construction_line(
    core: str,
    *,
    ordinal: int,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
) -> Step11Rc0028ExperimentParsedConstructionAtom:
    construction_prefix = morphology["construction_prefix"]
    construction_open = morphology["construction_open"]
    construction_suffix = morphology["construction_suffix"]
    clause_separator = morphology["clause_separator"]
    owner_noun = morphology["owner_noun"]
    owner_possessive = morphology["owner_possessive"]
    line_start = construction_prefix + clause_separator
    if not core.startswith(line_start) or not core.endswith(construction_suffix):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_PARSE_FAILED"
        )
    payload = core[len(line_start) : -len(construction_suffix)]
    construction_token_to_code = _step11_rc0028_exact_inverse_map(
        catalog.get("construction_surface_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    construction_matches = tuple(
        (token, code)
        for token, code in construction_token_to_code.items()
        if payload.startswith(token + construction_open + clause_separator)
    )
    if len(construction_matches) != 1:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_PARSE_FAILED"
        )
    construction_token, construction_code = construction_matches[0]
    role_payload = payload[
        len(construction_token + construction_open + clause_separator) :
    ]
    role_parts = role_payload.split(clause_separator)
    if not role_parts or any(not part for part in role_parts):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )

    role_token_to_key = _step11_rc0028_exact_inverse_map(
        catalog.get("role_position_surface_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    owner_token_to_ordinal = _step11_rc0028_exact_inverse_map(
        catalog.get("owner_ordinal_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    role_atom_codes = catalog.get("role_position_atom_codes")
    construction_atom_codes = catalog.get("construction_atom_codes")
    if type(role_atom_codes) is not dict or type(construction_atom_codes) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
        )
    bindings: list[Step11Rc0028ExperimentParsedConstructionRoleOwner] = []
    for part in role_parts:
        matches: list[tuple[int, str]] = []
        for owner_token, ordinal_text in owner_token_to_ordinal.items():
            prefix = owner_token + owner_noun + owner_possessive
            if not part.startswith(prefix):
                continue
            role_token = part[len(prefix) :]
            role_key = role_token_to_key.get(role_token)
            if type(role_key) is not str:
                continue
            matches.append((int(ordinal_text), role_key))
        if len(matches) != 1:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )
        owner_ordinal, role_key = matches[0]
        role_components = role_key.split(":")
        atom_code = role_atom_codes.get(role_key)
        if (
            len(role_components) != 2
            or any(not item for item in role_components)
            or type(atom_code) is not str
            or not atom_code
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
            )
        bindings.append(
            Step11Rc0028ExperimentParsedConstructionRoleOwner(
                owner_ordinal=owner_ordinal,
                lexical_role_kind=role_components[0],
                construction_position=role_components[1],
                role_position_key=role_key,
                role_position_atom_code=atom_code,
            )
        )
    construction_atom_code = construction_atom_codes.get(construction_code)
    if type(construction_atom_code) is not str or not construction_atom_code:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
        )
    return Step11Rc0028ExperimentParsedConstructionAtom(
        ordinal=ordinal,
        construction_code=construction_code,
        construction_atom_code=construction_atom_code,
        role_owner_bindings=tuple(bindings),
    )


def _step11_rc0028_parse_edge_line(
    core: str,
    *,
    ordinal: int,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    semantic_link: bool,
) -> (
    Step11Rc0028ExperimentParsedRelationAtom
    | Step11Rc0028ExperimentParsedSemanticLinkAtom
):
    owner_noun = morphology["owner_noun"]
    clause_separator = morphology["clause_separator"]
    if semantic_link:
        line_suffix = morphology["semantic_link_suffix"]
        endpoint_separator = morphology["semantic_link_join"]
        endpoint_tail = morphology["semantic_link_between"]
    else:
        line_suffix = morphology["relation_suffix"]
        endpoint_separator = morphology["relation_from_to_separator"]
        endpoint_tail = morphology["relation_to_suffix"]
    if not core.endswith(line_suffix):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_RELATION_PARSE_FAILED"
        )
    payload = core[: -len(line_suffix)]
    registry_name = (
        "semantic_link_surface_tokens"
        if semantic_link
        else "relation_surface_tokens"
    )
    token_to_key = _step11_rc0028_exact_inverse_map(
        catalog.get(registry_name),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    owner_token_to_ordinal = _step11_rc0028_exact_inverse_map(
        catalog.get("owner_ordinal_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    matches: list[tuple[int, int, str]] = []
    for surface_token, surface_key in token_to_key.items():
        visible_token = clause_separator + surface_token
        if not payload.endswith(visible_token):
            continue
        endpoint_text = payload[: -len(visible_token)]
        for from_token, from_text in owner_token_to_ordinal.items():
            for to_token, to_text in owner_token_to_ordinal.items():
                expected = (
                    from_token
                    + owner_noun
                    + endpoint_separator
                    + to_token
                    + owner_noun
                    + endpoint_tail
                )
                if endpoint_text == expected:
                    matches.append((int(from_text), int(to_text), surface_key))
    if len(matches) != 1:
        code = (
            "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH"
            if semantic_link
            else "STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
        )
        raise Step11Rc0028ExperimentInverseSurfaceError(code)
    from_ordinal, to_ordinal, surface_key = matches[0]
    components = surface_key.rsplit(":", 1)
    if len(components) != 2 or components[1] not in {
        "source_to_target",
        "bidirectional",
    }:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    relation_type, direction = components
    if semantic_link:
        return Step11Rc0028ExperimentParsedSemanticLinkAtom(
            ordinal=ordinal,
            relation_type=relation_type,
            from_owner_ordinal=from_ordinal,
            to_owner_ordinal=to_ordinal,
            direction=direction,
            semantic_link_surface_key=surface_key,
        )
    return Step11Rc0028ExperimentParsedRelationAtom(
        ordinal=ordinal,
        effective_relation_type=relation_type,
        from_owner_ordinal=from_ordinal,
        to_owner_ordinal=to_ordinal,
        direction=direction,
        relation_surface_key=surface_key,
    )


def _step11_rc0028_parse_unknown_line(
    core: str,
    *,
    ordinal: int,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
) -> Step11Rc0028ExperimentParsedExplicitUnknownAtom:
    unknown_prefix = morphology["unknown_prefix"]
    clause_separator = morphology["clause_separator"]
    owner_noun = morphology["owner_noun"]
    owner_separator = morphology["owner_separator"]
    owner_suffix = morphology["unknown_owner_suffix"]
    unknown_suffix = morphology["unknown_suffix"]
    line_start = unknown_prefix + clause_separator
    if not core.startswith(line_start) or not core.endswith(unknown_suffix):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH"
        )
    payload = core[len(line_start) : -len(unknown_suffix)]
    unknown_token_to_dimension = _step11_rc0028_exact_inverse_map(
        catalog.get("unknown_surface_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    owner_token_to_ordinal = _step11_rc0028_exact_inverse_map(
        catalog.get("owner_ordinal_tokens"),
        failure_code="STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    )
    matches: list[tuple[str, tuple[int, ...]]] = []
    for unknown_token, dimension in unknown_token_to_dimension.items():
        visible_unknown = clause_separator + unknown_token
        if not payload.endswith(visible_unknown):
            continue
        owners_text = payload[: -len(visible_unknown)]
        if not owners_text.endswith(owner_suffix):
            continue
        owners_text = owners_text[: -len(owner_suffix)]
        owner_phrases = owners_text.split(owner_separator)
        if not owner_phrases or any(not item for item in owner_phrases):
            continue
        try:
            owner_ordinals = tuple(
                _step11_rc0028_parse_owner_token(
                    item[: -len(owner_noun)],
                    owner_token_to_ordinal=owner_token_to_ordinal,
                )
                for item in owner_phrases
                if item.endswith(owner_noun)
            )
        except Step11Rc0028ExperimentInverseSurfaceError:
            continue
        if len(owner_ordinals) != len(owner_phrases):
            continue
        matches.append((dimension, owner_ordinals))
    if len(matches) != 1:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH"
        )
    dimension, owner_ordinals = matches[0]
    return Step11Rc0028ExperimentParsedExplicitUnknownAtom(
        ordinal=ordinal,
        dimension=dimension,
        affected_owner_ordinals=owner_ordinals,
    )


def _step11_rc0028_construction_material(
    value: Step11Rc0028ExperimentParsedConstructionAtom,
) -> dict[str, Any]:
    return {
        "ordinal": value.ordinal,
        "construction_code": value.construction_code,
        "construction_atom_code": value.construction_atom_code,
        "role_owner_bindings": [
            {
                "owner_ordinal": row.owner_ordinal,
                "lexical_role_kind": row.lexical_role_kind,
                "construction_position": row.construction_position,
                "role_position_key": row.role_position_key,
                "role_position_atom_code": row.role_position_atom_code,
            }
            for row in value.role_owner_bindings
        ],
    }


def _step11_rc0028_relation_material(
    value: Step11Rc0028ExperimentParsedRelationAtom,
) -> dict[str, Any]:
    return {
        "ordinal": value.ordinal,
        "effective_relation_type": value.effective_relation_type,
        "from_owner_ordinal": value.from_owner_ordinal,
        "to_owner_ordinal": value.to_owner_ordinal,
        "direction": value.direction,
        "relation_surface_key": value.relation_surface_key,
    }


def _step11_rc0028_semantic_link_material(
    value: Step11Rc0028ExperimentParsedSemanticLinkAtom,
) -> dict[str, Any]:
    return {
        "ordinal": value.ordinal,
        "relation_type": value.relation_type,
        "from_owner_ordinal": value.from_owner_ordinal,
        "to_owner_ordinal": value.to_owner_ordinal,
        "direction": value.direction,
        "semantic_link_surface_key": value.semantic_link_surface_key,
    }


def _step11_rc0028_explicit_unknown_material(
    value: Step11Rc0028ExperimentParsedExplicitUnknownAtom,
) -> dict[str, Any]:
    return {
        "ordinal": value.ordinal,
        "dimension": value.dimension,
        "affected_owner_ordinals": list(value.affected_owner_ordinals),
    }


def step11_rc0028_experiment_parsed_witness_material(
    value: Step11Rc0028ExperimentParsedSurfaceWitness,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0028ExperimentParsedSurfaceWitness:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSED_WITNESS_TYPE_INVALID"
        )
    if (
        value.schema_version
        != STEP11_RC0028_EXPERIMENT_PARSED_WITNESS_SCHEMA
        or type(value.body_sha256) is not str
        or _STEP11_RC0028_EXPERIMENT_SHA256_RE.fullmatch(value.body_sha256)
        is None
        or type(value.experiment_catalog_sha256) is not str
        or _STEP11_RC0028_EXPERIMENT_SHA256_RE.fullmatch(
            value.experiment_catalog_sha256
        )
        is None
        or type(value.base_witness) is not Step11ParsedSurfaceWitness
        or type(value.construction_atoms) is not tuple
        or any(
            type(row) is not Step11Rc0028ExperimentParsedConstructionAtom
            for row in value.construction_atoms
        )
        or type(value.relation_atoms) is not tuple
        or any(
            type(row) is not Step11Rc0028ExperimentParsedRelationAtom
            for row in value.relation_atoms
        )
        or type(value.semantic_link_atoms) is not tuple
        or any(
            type(row) is not Step11Rc0028ExperimentParsedSemanticLinkAtom
            for row in value.semantic_link_atoms
        )
        or type(value.explicit_unknown_atoms) is not tuple
        or any(
            type(row)
            is not Step11Rc0028ExperimentParsedExplicitUnknownAtom
            for row in value.explicit_unknown_atoms
        )
        or type(value.structure_line_count) is not int
        or type(value.structure_line_count) is bool
        or not 0
        <= value.structure_line_count
        <= _STEP11_RC0028_EXPERIMENT_STRUCTURE_LINE_MAX
        or value.body_free_export_allowed is not False
        or value.structure_line_count
        != (
            len(value.construction_atoms)
            + len(value.relation_atoms)
            + len(value.semantic_link_atoms)
            + len(value.explicit_unknown_atoms)
        )
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSED_WITNESS_INVALID"
        )
    try:
        base_witness_material = _witness_material(value.base_witness)
        construction_material = [
            _step11_rc0028_construction_material(row)
            for row in value.construction_atoms
        ]
        relation_material = [
            _step11_rc0028_relation_material(row)
            for row in value.relation_atoms
        ]
        semantic_link_material = [
            _step11_rc0028_semantic_link_material(row)
            for row in value.semantic_link_atoms
        ]
        explicit_unknown_material = [
            _step11_rc0028_explicit_unknown_material(row)
            for row in value.explicit_unknown_atoms
        ]
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSED_WITNESS_INVALID"
        ) from exc
    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_witness": base_witness_material,
        "construction_atoms": construction_material,
        "relation_atoms": relation_material,
        "semantic_link_atoms": semantic_link_material,
        "explicit_unknown_atoms": explicit_unknown_material,
        "structure_line_count": value.structure_line_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def parse_step11_rc0028_experiment_surface(
    body: bytes,
    *forward_metadata: Any,
    **forward_metadata_by_name: Any,
) -> Step11Rc0028ExperimentParsedSurfaceWitness:
    """Parse final bytes only; all candidate/forward metadata is rejected."""

    if forward_metadata or forward_metadata_by_name:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSER_FORWARD_METADATA_FORBIDDEN"
        )
    if (
        type(body) is not bytes
        or not body
        or len(body) > _STEP11_RC0028_EXPERIMENT_BODY_BYTE_MAX
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSER_BODY_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0028_inverse_catalog()
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSER_UTF8_INVALID"
        ) from exc
    if (
        unicodedata.normalize("NFC", text) != text
        or "\r" in text
        or text.endswith("\n")
        or text.startswith("\ufeff")
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSER_CANONICAL_TEXT_INVALID"
        )

    labels = STEP11_SURFACE_CATALOG.get("labels")
    morphology = catalog.get("line_morphology")
    if type(labels) is not dict or type(morphology) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    required_morphology = {
        "atom_separator",
        "clause_separator",
        "construction_open",
        "construction_prefix",
        "construction_suffix",
        "owner_noun",
        "owner_possessive",
        "owner_separator",
        "relation_from_to_separator",
        "relation_suffix",
        "relation_to_suffix",
        "semantic_link_between",
        "semantic_link_join",
        "semantic_link_suffix",
        "unknown_owner_suffix",
        "unknown_prefix",
        "unknown_suffix",
    }
    if (
        not required_morphology <= set(morphology)
        or any(
            type(morphology[key]) is not str or not morphology[key]
            for key in required_morphology
        )
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    observation_label = labels.get("observation")
    reception_label = labels.get("reception")
    if type(observation_label) is not str or type(reception_label) is not str:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_PARSE_FAILED"
        )
    prefix = observation_label + "\n"
    section_separator = "\n\n" + reception_label + "\n"
    if not text.startswith(prefix) or text.count(section_separator) != 1:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_PARSE_FAILED"
        )
    observation, reception = text[len(prefix) :].split(section_separator)
    observation_lines = observation.split("\n")
    if not observation_lines or any(not line for line in observation_lines):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_PARSE_FAILED"
        )

    clause_separator = morphology["clause_separator"]
    construction_prefix = morphology["construction_prefix"]
    construction_suffix = morphology["construction_suffix"]
    relation_marker = morphology["relation_to_suffix"] + clause_separator
    relation_suffix = morphology["relation_suffix"]
    semantic_link_marker = (
        morphology["semantic_link_between"] + clause_separator
    )
    semantic_link_suffix = morphology["semantic_link_suffix"]
    unknown_prefix = morphology["unknown_prefix"]
    unknown_suffix = morphology["unknown_suffix"]
    base_lines: list[str] = []
    constructions: list[Step11Rc0028ExperimentParsedConstructionAtom] = []
    relations: list[Step11Rc0028ExperimentParsedRelationAtom] = []
    semantic_links: list[Step11Rc0028ExperimentParsedSemanticLinkAtom] = []
    explicit_unknowns: list[
        Step11Rc0028ExperimentParsedExplicitUnknownAtom
    ] = []
    structure_started = False
    current_structure_rank = -1
    for line in observation_lines:
        is_construction = (
            line.startswith(construction_prefix + clause_separator)
            and line.endswith(construction_suffix)
        )
        is_unknown = (
            line.startswith(unknown_prefix + clause_separator)
            and line.endswith(unknown_suffix)
        )
        is_semantic_link = (
            semantic_link_marker in line
            and line.endswith(semantic_link_suffix)
        )
        is_relation = (
            relation_marker in line and line.endswith(relation_suffix)
        )
        if not any(
            (is_construction, is_relation, is_semantic_link, is_unknown)
        ):
            if structure_started:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_STRUCTURE_LINE_ORDER_INVALID"
                )
            base_lines.append(line)
            continue
        structure_started = True
        if sum(
            (is_construction, is_relation, is_semantic_link, is_unknown)
        ) != 1:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_STRUCTURE_LINE_PARSE_FAILED"
            )
        if is_construction:
            if current_structure_rank > 0:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_STRUCTURE_LINE_ORDER_INVALID"
                )
            current_structure_rank = 0
            constructions.append(
                _step11_rc0028_parse_construction_line(
                    line,
                    ordinal=len(constructions) + 1,
                    catalog=catalog,
                    morphology=morphology,
                )
            )
        elif is_relation:
            if current_structure_rank > 1:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_STRUCTURE_LINE_ORDER_INVALID"
                )
            current_structure_rank = 1
            parsed_relation = _step11_rc0028_parse_edge_line(
                line,
                ordinal=len(relations) + 1,
                catalog=catalog,
                morphology=morphology,
                semantic_link=False,
            )
            if type(parsed_relation) is not Step11Rc0028ExperimentParsedRelationAtom:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_RELATION_PARSE_FAILED"
                )
            relations.append(parsed_relation)
        elif is_semantic_link:
            if current_structure_rank > 2:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_STRUCTURE_LINE_ORDER_INVALID"
                )
            current_structure_rank = 2
            parsed_link = _step11_rc0028_parse_edge_line(
                line,
                ordinal=len(semantic_links) + 1,
                catalog=catalog,
                morphology=morphology,
                semantic_link=True,
            )
            if type(parsed_link) is not Step11Rc0028ExperimentParsedSemanticLinkAtom:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH"
                )
            semantic_links.append(parsed_link)
        else:
            if current_structure_rank > 3:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_STRUCTURE_LINE_ORDER_INVALID"
                )
            current_structure_rank = 3
            explicit_unknowns.append(
                _step11_rc0028_parse_unknown_line(
                    line,
                    ordinal=len(explicit_unknowns) + 1,
                    catalog=catalog,
                    morphology=morphology,
                )
            )
        if (
            len(constructions)
            + len(relations)
            + len(semantic_links)
            + len(explicit_unknowns)
            > _STEP11_RC0028_EXPERIMENT_STRUCTURE_LINE_MAX
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED"
            )
    if not base_lines or not reception:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_PARSE_FAILED"
        )
    base_text = (
        prefix
        + "\n".join(base_lines)
        + section_separator
        + reception
    )
    base_body = base_text.encode("utf-8", errors="strict")
    try:
        base_witness = parse_step11_natural_surface(base_body)
    except Step11InverseSurfaceError as exc:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_PARSE_FAILED"
        ) from exc
    if base_witness.body_sha256 != hashlib.sha256(base_body).hexdigest():
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_BASE_SURFACE_COMMITMENT_MISMATCH"
        )
    return Step11Rc0028ExperimentParsedSurfaceWitness(
        schema_version=STEP11_RC0028_EXPERIMENT_PARSED_WITNESS_SCHEMA,
        body_sha256=hashlib.sha256(body).hexdigest(),
        experiment_catalog_sha256=catalog_sha256,
        base_witness=base_witness,
        construction_atoms=tuple(constructions),
        relation_atoms=tuple(relations),
        semantic_link_atoms=tuple(semantic_links),
        explicit_unknown_atoms=tuple(explicit_unknowns),
        structure_line_count=(
            len(constructions)
            + len(relations)
            + len(semantic_links)
            + len(explicit_unknowns)
        ),
    )


def _step11_rc0028_independent_owner_registry(
    successor_snapshot: Any,
    *,
    maximum_owner_ordinal: int,
) -> tuple[tuple[str, str], ...]:
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    kind_by_id: dict[str, str] = {}

    def bind(owner_id: Any, owner_kind: str) -> None:
        if (
            type(owner_id) is not str
            or not owner_id
            or owner_kind not in {"nucleus", "semantic_unit"}
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH"
            )
        previous = kind_by_id.get(owner_id)
        if previous is not None and previous != owner_kind:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH"
            )
        kind_by_id[owner_id] = owner_kind

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
    for row in successor_snapshot.base_snapshot.nuclei:
        owner_id = row.actual_source_id
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
            (*nucleus_order, *semantic_unit_order, *sorted(kind_by_id))
        )
    )
    if not ordered or len(ordered) > maximum_owner_ordinal:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED"
        )
    return tuple((owner_id, kind_by_id[owner_id]) for owner_id in ordered)


def _step11_rc0028_expected_constructions(
    successor_snapshot: Any,
    *,
    owner_ordinal_by_id: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> tuple[
    tuple[Step11Rc0028ExperimentParsedConstructionAtom, ...], int, int
]:
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    instances = authority.construction_instances
    slots = authority.construction_slots
    participations = authority.source_owner_participations
    if (
        len({row.construction_instance_id for row in instances})
        != len(instances)
        or len({row.construction_slot_id for row in slots}) != len(slots)
        or len({row.participation_id for row in participations})
        != len(participations)
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )
    slot_by_id = {row.construction_slot_id: row for row in slots}
    participation_by_id = {
        row.participation_id: row for row in participations
    }
    facets_by_slot: dict[str, list[Any]] = {}
    for facet in witness.facets:
        facets_by_slot.setdefault(facet.construction_slot_id, []).append(facet)
    if set(facets_by_slot) != set(slot_by_id) or any(
        len(rows) != 1 for rows in facets_by_slot.values()
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )
    construction_codes = catalog.get("construction_atom_codes")
    role_codes = catalog.get("role_position_atom_codes")
    if type(construction_codes) is not dict or type(role_codes) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
        )

    seen_slots: list[str] = []
    seen_participations: list[str] = []
    expected: list[Step11Rc0028ExperimentParsedConstructionAtom] = []
    for ordinal, instance in enumerate(instances, 1):
        construction_atom_code = construction_codes.get(
            instance.construction_code
        )
        if type(construction_atom_code) is not str:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
            )
        role_bindings: list[
            Step11Rc0028ExperimentParsedConstructionRoleOwner
        ] = []
        if not instance.slot_ids:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )
        for slot_id in instance.slot_ids:
            slot = slot_by_id.get(slot_id)
            facet_rows = facets_by_slot.get(slot_id, ())
            if (
                slot is None
                or len(facet_rows) != 1
                or slot.construction_instance_id
                != instance.construction_instance_id
            ):
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            facet = facet_rows[0]
            if (
                facet.source_owner_id != instance.construction_instance_id
                or facet.parent_nucleus_id != instance.parent_nucleus_id
                or facet.construction_code != instance.construction_code
                or facet.lexical_role_kind != slot.lexical_role_kind
                or facet.construction_position != slot.construction_position
                or tuple(facet.participation_ids)
                != tuple(slot.participation_ids)
            ):
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            role_key = (
                slot.lexical_role_kind + ":" + slot.construction_position
            )
            role_atom_code = role_codes.get(role_key)
            if type(role_atom_code) is not str:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
                )
            if not slot.participation_ids:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            seen_slots.append(slot_id)
            for participation_id in slot.participation_ids:
                participation = participation_by_id.get(participation_id)
                if (
                    participation is None
                    or participation.construction_slot_id != slot_id
                    or participation.parent_nucleus_id
                    != instance.parent_nucleus_id
                ):
                    raise Step11Rc0028ExperimentInverseSurfaceError(
                        "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH"
                    )
                if participation.semantic_equivalence_authorized is not False:
                    raise Step11Rc0028ExperimentInverseSurfaceError(
                        "STEP11_RC0028_PARTICIPATION_EQUIVALENCE_MISMATCH"
                    )
                if (
                    participation.source_span_id != slot.source_span_id
                    or type(participation.intersection_start_index) is not int
                    or type(participation.intersection_end_index) is not int
                    or not (
                        slot.slot_start_index
                        <= participation.intersection_start_index
                        < participation.intersection_end_index
                        <= slot.slot_end_index
                    )
                ):
                    raise Step11Rc0028ExperimentInverseSurfaceError(
                        "STEP11_RC0028_PARTICIPATION_RANGE_MISMATCH"
                    )
                owner_ordinal = owner_ordinal_by_id.get(
                    participation.target_owner_id
                )
                if type(owner_ordinal) is not int:
                    raise Step11Rc0028ExperimentInverseSurfaceError(
                        "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH"
                    )
                role_bindings.append(
                    Step11Rc0028ExperimentParsedConstructionRoleOwner(
                        owner_ordinal=owner_ordinal,
                        lexical_role_kind=slot.lexical_role_kind,
                        construction_position=slot.construction_position,
                        role_position_key=role_key,
                        role_position_atom_code=role_atom_code,
                    )
                )
                seen_participations.append(participation_id)
        if set(instance.participation_ids) != {
            participation_id
            for slot_id in instance.slot_ids
            for participation_id in slot_by_id[slot_id].participation_ids
        }:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )
        expected.append(
            Step11Rc0028ExperimentParsedConstructionAtom(
                ordinal=ordinal,
                construction_code=instance.construction_code,
                construction_atom_code=construction_atom_code,
                role_owner_bindings=tuple(role_bindings),
            )
        )
    if (
        len(seen_slots) != len(set(seen_slots))
        or set(seen_slots) != set(slot_by_id)
        or len(seen_participations) != len(set(seen_participations))
        or set(seen_participations) != set(participation_by_id)
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )
    return tuple(expected), len(seen_slots), len(seen_participations)


def _step11_rc0028_expected_relations(
    successor_snapshot: Any,
    *,
    owner_ordinal_by_id: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> tuple[
    tuple[Step11Rc0028ExperimentParsedRelationAtom, ...], int
]:
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    endpoint_by_relation: dict[str, list[Any]] = {}
    for endpoint in witness.relation_endpoint_bindings:
        endpoint_by_relation.setdefault(endpoint.relation_id, []).append(
            endpoint
        )
    expected: list[Step11Rc0028ExperimentParsedRelationAtom] = []
    endpoint_count = 0
    surface_tokens = catalog.get("relation_surface_tokens")
    if type(surface_tokens) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    for ordinal, relation in enumerate(authority.relation_authorities, 1):
        endpoints = endpoint_by_relation.get(
            relation.experiment_relation_id, ()
        )
        if len(endpoints) != 2:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
            )
        by_role = {row.relation_endpoint_role: row for row in endpoints}
        if set(by_role) != {"from", "to"}:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_ROLE_MISMATCH"
            )
        if relation.authority_basis == "grounded_plan_projection":
            if (
                relation.refines_source_relation_id is not None
                or relation.effective_relation_type
                != relation.source_relation_type
                or relation.experiment_retention != "source_projection"
            ):
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_SOURCE_RELATION_TYPE_MISMATCH"
                )
        elif relation.authority_basis == "source_explicit_refinement":
            if (
                relation.source_relation_type != "uncertain_connection"
                or relation.effective_relation_type != "coexistence"
                or relation.refines_source_relation_id
                != relation.source_relation_id
                or relation.source_grounding_kind
                != "bounded_structural_inference"
                or relation.source_retention != "should"
                or relation.experiment_retention
                != "experiment_required_refinement"
            ):
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_RELATION_REFINEMENT_AUTHORITY_MISMATCH"
                )
        else:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_REFINEMENT_AUTHORITY_MISMATCH"
            )
        expected_direction = (
            "bidirectional"
            if relation.effective_relation_type == "coexistence"
            else "source_to_target"
        )
        if relation.direction != expected_direction:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_DIRECTION_MISMATCH"
            )
        for role, owner_id in (
            ("from", relation.from_source_owner_id),
            ("to", relation.to_source_owner_id),
        ):
            endpoint = by_role[role]
            if endpoint.source_owner_id != owner_id:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH"
                )
            if (
                endpoint.source_relation_id != relation.source_relation_id
                or endpoint.relation_direction != relation.direction
                or endpoint.effective_relation_type
                != relation.effective_relation_type
            ):
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_RELATION_ENDPOINT_ROLE_MISMATCH"
                )
        surface_key = (
            relation.effective_relation_type + ":" + relation.direction
        )
        if surface_key not in surface_tokens:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EFFECTIVE_RELATION_TYPE_MISMATCH"
            )
        from_ordinal = owner_ordinal_by_id.get(
            relation.from_source_owner_id
        )
        to_ordinal = owner_ordinal_by_id.get(relation.to_source_owner_id)
        if type(from_ordinal) is not int or type(to_ordinal) is not int:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH"
            )
        expected.append(
            Step11Rc0028ExperimentParsedRelationAtom(
                ordinal=ordinal,
                effective_relation_type=relation.effective_relation_type,
                from_owner_ordinal=from_ordinal,
                to_owner_ordinal=to_ordinal,
                direction=relation.direction,
                relation_surface_key=surface_key,
            )
        )
        endpoint_count += 2
    if set(endpoint_by_relation) != {
        row.experiment_relation_id
        for row in authority.relation_authorities
    }:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
        )
    return tuple(expected), endpoint_count


def _step11_rc0028_expected_semantic_links(
    successor_snapshot: Any,
    *,
    owner_ordinal_by_id: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> tuple[Step11Rc0028ExperimentParsedSemanticLinkAtom, ...]:
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    if tuple(witness.semantic_link_bindings) != tuple(
        authority.semantic_link_bindings
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH"
        )
    surface_tokens = catalog.get("semantic_link_surface_tokens")
    if type(surface_tokens) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    expected: list[Step11Rc0028ExperimentParsedSemanticLinkAtom] = []
    for ordinal, link in enumerate(authority.semantic_link_bindings, 1):
        surface_key = link.relation_type + ":" + link.direction
        if surface_key not in surface_tokens:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_TYPE_MISMATCH"
            )
        from_ordinal = owner_ordinal_by_id.get(link.from_semantic_unit_id)
        to_ordinal = owner_ordinal_by_id.get(link.to_semantic_unit_id)
        if type(from_ordinal) is not int or type(to_ordinal) is not int:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_ENDPOINT_MISMATCH"
            )
        expected.append(
            Step11Rc0028ExperimentParsedSemanticLinkAtom(
                ordinal=ordinal,
                relation_type=link.relation_type,
                from_owner_ordinal=from_ordinal,
                to_owner_ordinal=to_ordinal,
                direction=link.direction,
                semantic_link_surface_key=surface_key,
            )
        )
    return tuple(expected)


def _step11_rc0028_expected_explicit_unknowns(
    successor_snapshot: Any,
    *,
    owner_ordinal_by_id: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> tuple[Step11Rc0028ExperimentParsedExplicitUnknownAtom, ...]:
    authority = successor_snapshot.relation_construction_authority
    witness = successor_snapshot.lexical_role_witness
    if tuple(witness.explicit_unknown_bindings) != tuple(
        authority.explicit_unknown_authorities
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH"
        )
    unknown_tokens = catalog.get("unknown_surface_tokens")
    if type(unknown_tokens) is not dict:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    expected: list[Step11Rc0028ExperimentParsedExplicitUnknownAtom] = []
    for ordinal, unknown in enumerate(
        authority.explicit_unknown_authorities, 1
    ):
        if unknown.dimension not in unknown_tokens:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH"
            )
        owner_ordinals: list[int] = []
        for owner in unknown.affected_source_owners:
            owner_ordinal = owner_ordinal_by_id.get(owner.owner_id)
            if type(owner_ordinal) is not int:
                raise Step11Rc0028ExperimentInverseSurfaceError(
                    "STEP11_RC0028_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
                )
            owner_ordinals.append(owner_ordinal)
        if not owner_ordinals:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
            )
        expected.append(
            Step11Rc0028ExperimentParsedExplicitUnknownAtom(
                ordinal=ordinal,
                dimension=unknown.dimension,
                affected_owner_ordinals=tuple(owner_ordinals),
            )
        )
    return tuple(expected)


def _step11_rc0028_compare_constructions(
    parsed: Sequence[Step11Rc0028ExperimentParsedConstructionAtom],
    expected: Sequence[Step11Rc0028ExperimentParsedConstructionAtom],
) -> None:
    if len(parsed) != len(expected):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH"
        )
    for left, right in zip(parsed, expected):
        if (
            left.ordinal != right.ordinal
            or left.construction_code != right.construction_code
            or left.construction_atom_code != right.construction_atom_code
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH"
            )
        if left.role_owner_bindings != right.role_owner_bindings:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )


def _step11_rc0028_compare_relations(
    parsed: Sequence[Step11Rc0028ExperimentParsedRelationAtom],
    expected: Sequence[Step11Rc0028ExperimentParsedRelationAtom],
) -> None:
    if len(parsed) != len(expected):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
        )
    for left, right in zip(parsed, expected):
        if left.effective_relation_type != right.effective_relation_type:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EFFECTIVE_RELATION_TYPE_MISMATCH"
            )
        if left.direction != right.direction:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_DIRECTION_MISMATCH"
            )
        if (
            left.from_owner_ordinal != right.from_owner_ordinal
            or left.to_owner_ordinal != right.to_owner_ordinal
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH"
            )
        if (
            left.ordinal != right.ordinal
            or left.relation_surface_key != right.relation_surface_key
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_ROLE_MISMATCH"
            )


def _step11_rc0028_compare_semantic_links(
    parsed: Sequence[Step11Rc0028ExperimentParsedSemanticLinkAtom],
    expected: Sequence[Step11Rc0028ExperimentParsedSemanticLinkAtom],
) -> None:
    if len(parsed) != len(expected):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH"
        )
    for left, right in zip(parsed, expected):
        if left.relation_type != right.relation_type:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_TYPE_MISMATCH"
            )
        if left.direction != right.direction:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_DIRECTION_MISMATCH"
            )
        if (
            left.from_owner_ordinal != right.from_owner_ordinal
            or left.to_owner_ordinal != right.to_owner_ordinal
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_ENDPOINT_MISMATCH"
            )
        if (
            left.ordinal != right.ordinal
            or left.semantic_link_surface_key
            != right.semantic_link_surface_key
        ):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH"
            )


def _step11_rc0028_compare_explicit_unknowns(
    parsed: Sequence[Step11Rc0028ExperimentParsedExplicitUnknownAtom],
    expected: Sequence[Step11Rc0028ExperimentParsedExplicitUnknownAtom],
) -> None:
    parsed_signatures = [
        (row.dimension, row.affected_owner_ordinals) for row in parsed
    ]
    if len(parsed) < len(expected):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_MISSING"
        )
    if len(parsed) > len(expected):
        if len(set(parsed_signatures)) != len(parsed_signatures):
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_DUPLICATE"
            )
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH"
        )
    if len(set(parsed_signatures)) != len(parsed_signatures):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_EXPLICIT_UNKNOWN_DUPLICATE"
        )
    for left, right in zip(parsed, expected):
        if left.dimension != right.dimension:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH"
            )
        if left.affected_owner_ordinals != right.affected_owner_ordinals:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
            )
        if left.ordinal != right.ordinal:
            raise Step11Rc0028ExperimentInverseSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH"
            )


def step11_rc0028_experiment_verified_binding_material(
    value: Step11Rc0028ExperimentVerifiedSurfaceBinding,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0028ExperimentVerifiedSurfaceBinding:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_VERIFIED_BINDING_TYPE_INVALID"
        )
    if (
        value.schema_version
        != STEP11_RC0028_EXPERIMENT_VERIFIED_BINDING_SCHEMA
        or any(
            type(item) is not str
            or _STEP11_RC0028_EXPERIMENT_SHA256_RE.fullmatch(item) is None
            for item in (
                value.parsed_witness_sha256,
                value.base_witness_sha256,
                value.successor_snapshot_sha256,
                value.experiment_catalog_sha256,
            )
        )
        or any(
            type(item) is not int or type(item) is bool or item < 0
            for item in (
                value.bound_owner_ordinal_count,
                value.construction_instance_binding_count,
                value.construction_slot_binding_count,
                value.participation_binding_count,
                value.relation_binding_count,
                value.relation_endpoint_binding_count,
                value.semantic_link_binding_count,
                value.explicit_unknown_binding_count,
            )
        )
        or value.semantic_coverage_authorized is not False
        or value.issue_codes != ()
        or value.hard_verified is not True
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_VERIFIED_BINDING_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "base_witness_sha256": value.base_witness_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "bound_owner_ordinal_count": value.bound_owner_ordinal_count,
        "construction_instance_binding_count": (
            value.construction_instance_binding_count
        ),
        "construction_slot_binding_count": (
            value.construction_slot_binding_count
        ),
        "participation_binding_count": value.participation_binding_count,
        "relation_binding_count": value.relation_binding_count,
        "relation_endpoint_binding_count": (
            value.relation_endpoint_binding_count
        ),
        "semantic_link_binding_count": value.semantic_link_binding_count,
        "explicit_unknown_binding_count": (
            value.explicit_unknown_binding_count
        ),
        "semantic_coverage_authorized": (
            value.semantic_coverage_authorized
        ),
        "issue_codes": list(value.issue_codes),
        "hard_verified": value.hard_verified,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def match_step11_rc0028_experiment_surface(
    witness: Step11Rc0028ExperimentParsedSurfaceWitness,
    *,
    successor_snapshot: Any,
) -> Step11Rc0028ExperimentVerifiedSurfaceBinding:
    """Independently match parsed structure to the accepted successor."""

    if type(witness) is not Step11Rc0028ExperimentParsedSurfaceWitness:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_PARSED_WITNESS_TYPE_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0028_inverse_catalog()
    witness_material = step11_rc0028_experiment_parsed_witness_material(
        witness
    )
    if witness.experiment_catalog_sha256 != catalog_sha256:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_COMMITMENT_MISMATCH"
        )

    # Dynamic local load keeps the accepted E1b reverse-import audit frozen.
    # No forward, lexicalizer, runtime, or gate owner is available here.
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

    if type(successor_snapshot) is not GroundedLexicalRoleExperimentSnapshotSuccessor:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH"
        )
    if (
        successor_snapshot.semantic_coverage_authorized is not False
        or successor_snapshot.experimental_only is not True
        or successor_snapshot.runtime_connected is not False
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM"
        )
    maximum_owner_ordinal = catalog.get("max_owner_ordinal")
    if type(maximum_owner_ordinal) is not int or type(maximum_owner_ordinal) is bool:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
        )
    try:
        owner_registry = _step11_rc0028_independent_owner_registry(
            successor_snapshot,
            maximum_owner_ordinal=maximum_owner_ordinal,
        )
        owner_ordinal_by_id = {
            owner_id: ordinal
            for ordinal, (owner_id, _owner_kind) in enumerate(
                owner_registry, 1
            )
        }
        expected_constructions, slot_count, participation_count = (
            _step11_rc0028_expected_constructions(
                successor_snapshot,
                owner_ordinal_by_id=owner_ordinal_by_id,
                catalog=catalog,
            )
        )
        expected_relations, endpoint_count = (
            _step11_rc0028_expected_relations(
                successor_snapshot,
                owner_ordinal_by_id=owner_ordinal_by_id,
                catalog=catalog,
            )
        )
        expected_links = _step11_rc0028_expected_semantic_links(
            successor_snapshot,
            owner_ordinal_by_id=owner_ordinal_by_id,
            catalog=catalog,
        )
        expected_unknowns = _step11_rc0028_expected_explicit_unknowns(
            successor_snapshot,
            owner_ordinal_by_id=owner_ordinal_by_id,
            catalog=catalog,
        )
    except Step11Rc0028ExperimentInverseSurfaceError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH"
        ) from exc

    snapshot_issues = validate_grounded_lexical_role_experiment_snapshot_successor(
        successor_snapshot
    )
    if snapshot_issues:
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH"
        )
    _step11_rc0028_compare_constructions(
        witness.construction_atoms, expected_constructions
    )
    _step11_rc0028_compare_relations(
        witness.relation_atoms, expected_relations
    )
    _step11_rc0028_compare_semantic_links(
        witness.semantic_link_atoms, expected_links
    )
    _step11_rc0028_compare_explicit_unknowns(
        witness.explicit_unknown_atoms, expected_unknowns
    )
    resource_bounds = successor_snapshot.relation_construction_authority.resource_bounds
    if (
        len(expected_constructions) > resource_bounds.max_construction_instances
        or slot_count > resource_bounds.max_lexical_construction_slots
        or participation_count
        > resource_bounds.max_source_owner_participations
        or len(expected_relations) != resource_bounds.exact_effective_relations
        or len(expected_links) != resource_bounds.exact_semantic_links
        or len(expected_unknowns) != resource_bounds.exact_explicit_unknowns
    ):
        raise Step11Rc0028ExperimentInverseSurfaceError(
            "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED"
        )

    binding = Step11Rc0028ExperimentVerifiedSurfaceBinding(
        schema_version=STEP11_RC0028_EXPERIMENT_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256=artifact_sha256(witness_material),
        base_witness_sha256=artifact_sha256(
            _witness_material(witness.base_witness)
        ),
        successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        experiment_catalog_sha256=catalog_sha256,
        bound_owner_ordinal_count=len(owner_registry),
        construction_instance_binding_count=len(expected_constructions),
        construction_slot_binding_count=slot_count,
        participation_binding_count=participation_count,
        relation_binding_count=len(expected_relations),
        relation_endpoint_binding_count=endpoint_count,
        semantic_link_binding_count=len(expected_links),
        explicit_unknown_binding_count=len(expected_unknowns),
        semantic_coverage_authorized=False,
        issue_codes=(),
        hard_verified=True,
    )
    step11_rc0028_experiment_verified_binding_material(binding)
    return binding


__all__ = [
    *__all__,
    "STEP11_RC0028_EXPERIMENT_PARSED_WITNESS_SCHEMA",
    "STEP11_RC0028_EXPERIMENT_VERIFIED_BINDING_SCHEMA",
    "Step11Rc0028ExperimentInverseSurfaceError",
    "Step11Rc0028ExperimentParsedConstructionAtom",
    "Step11Rc0028ExperimentParsedConstructionRoleOwner",
    "Step11Rc0028ExperimentParsedExplicitUnknownAtom",
    "Step11Rc0028ExperimentParsedRelationAtom",
    "Step11Rc0028ExperimentParsedSemanticLinkAtom",
    "Step11Rc0028ExperimentParsedSurfaceWitness",
    "Step11Rc0028ExperimentVerifiedSurfaceBinding",
    "match_step11_rc0028_experiment_surface",
    "parse_step11_rc0028_experiment_surface",
    "step11_rc0028_experiment_parsed_witness_material",
    "step11_rc0028_experiment_verified_binding_material",
]


# ---------------------------------------------------------------------------
# rc0029 experiment-only common-Surface inverse (append-only)
#
# This parser observes final bytes and the versioned declarative catalog only.
# It has no import edge to the forward Surface, lexicalizer, runtime, or gate.
# The matcher receives the resulting witness and the validated successor, and
# independently solves the visible-handle-to-source graph binding.

STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_parsed_witness.v1"
)
STEP11_RC0029_EXPERIMENT_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_verified_binding.v1"
)

_STEP11_RC0029_BODY_BYTE_MAX = 1_000_000
_STEP11_RC0029_HANDLE_MAX = 64
_STEP11_RC0029_OWNER_MAX = 24
_STEP11_RC0029_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STEP11_RC0029_OPAQUE_HANDLE_RE = re.compile(
    r"(?:その|もう一方の|さらに別の|[0-9]+つ目の)内容"
)


class Step11Rc0029ExperimentInverseSurfaceError(ValueError):
    """Fail closed without copying source or final-body text into errors."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"STEP11_RC0029_[A-Z0-9_]{2,95}", code) is None
        ):
            code = "STEP11_RC0029_INVERSE_SURFACE_REJECTED"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedNaturalHandle:
    handle_index: int
    handle_text: str
    grounded_phrase_text: str
    qualifier_tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedConstructionRoleOwner:
    handle_index: int
    lexical_role_kind: str | None
    construction_position: str | None
    role_position_key: str | None


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedConstructionAtom:
    ordinal: int
    construction_code: str
    role_owner_bindings: tuple[
        Step11Rc0029ExperimentParsedConstructionRoleOwner, ...
    ]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedRelationAtom:
    ordinal: int
    effective_relation_type: str
    from_handle_index: int
    to_handle_index: int
    direction: str
    relation_surface_key: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedSemanticLinkAtom:
    ordinal: int
    relation_type: str
    from_handle_index: int
    to_handle_index: int
    direction: str
    semantic_link_surface_key: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedExplicitUnknownAtom:
    ordinal: int
    dimension: str
    affected_handle_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedReceptionBinding:
    reception_line_ordinal: int
    reception_act: str
    reception_scope: str
    antecedent_handle_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedSurfaceWitness:
    schema_version: str
    body_sha256: str
    experiment_catalog_sha256: str
    base_witness: Step11ParsedSurfaceWitness
    natural_handles: tuple[Step11Rc0029ExperimentParsedNaturalHandle, ...]
    construction_atoms: tuple[
        Step11Rc0029ExperimentParsedConstructionAtom, ...
    ]
    relation_atoms: tuple[Step11Rc0029ExperimentParsedRelationAtom, ...]
    semantic_link_atoms: tuple[
        Step11Rc0029ExperimentParsedSemanticLinkAtom, ...
    ]
    explicit_unknown_atoms: tuple[
        Step11Rc0029ExperimentParsedExplicitUnknownAtom, ...
    ]
    reception_bindings: tuple[
        Step11Rc0029ExperimentParsedReceptionBinding, ...
    ]
    fused_structure_item_count: int
    fused_structure_group_count: int
    added_observation_line_count: int
    body_free_export_allowed: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentVerifiedSurfaceBinding:
    schema_version: str
    parsed_witness_sha256: str
    base_witness_sha256: str
    successor_snapshot_sha256: str
    experiment_catalog_sha256: str
    natural_handle_binding_count: int
    construction_instance_binding_count: int
    construction_slot_binding_count: int
    participation_binding_count: int
    relation_binding_count: int
    relation_endpoint_binding_count: int
    semantic_link_binding_count: int
    explicit_unknown_binding_count: int
    reception_binding_count: int
    unique_solution_count: int
    semantic_coverage_authorized: bool
    issue_codes: tuple[str, ...]
    hard_verified: bool
    body_free_export_allowed: bool = False


def _step11_rc0029_inverse_catalog() -> tuple[dict[str, Any], str]:
    # Local-only import keeps rc0029 absent from the default inverse graph.
    from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
        STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
        validate_step11_rc0029_experiment_surface_catalog,
    )

    catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG
    issues = validate_step11_rc0029_experiment_surface_catalog(catalog)
    if issues:
        raise Step11Rc0029ExperimentInverseSurfaceError(issues[0])
    return catalog, STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0029_inverse_map(
    value: Any, *, code: str
) -> dict[str, str]:
    if (
        type(value) is not dict
        or not value
        or any(
            type(key) is not str
            or not key
            or type(token) is not str
            or not token
            for key, token in value.items()
        )
        or len(set(value.values())) != len(value)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(code)
    return {token: key for key, token in value.items()}


def _step11_rc0029_handle_material_index(
    value: Step11Rc0029ExperimentParsedNaturalHandle,
) -> dict[str, Any]:
    return {
        "handle_index": value.handle_index,
        "qualifier_tokens": list(value.qualifier_tokens),
    }


def step11_rc0029_experiment_parsed_witness_material(
    value: Step11Rc0029ExperimentParsedSurfaceWitness,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029ExperimentParsedSurfaceWitness:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_TYPE_INVALID"
        )
    if (
        value.schema_version
        != STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA
        or _STEP11_RC0029_SHA256_RE.fullmatch(value.body_sha256) is None
        or _STEP11_RC0029_SHA256_RE.fullmatch(
            value.experiment_catalog_sha256
        )
        is None
        or type(value.base_witness) is not Step11ParsedSurfaceWitness
        or value.added_observation_line_count != 0
        or value.body_free_export_allowed is not False
        or value.fused_structure_item_count
        != (
            len(value.construction_atoms)
            + len(value.relation_atoms)
            + len(value.semantic_link_atoms)
            + len(value.explicit_unknown_atoms)
        )
        or value.fused_structure_group_count
        != sum(
            bool(rows)
            for rows in (
                value.construction_atoms,
                value.relation_atoms,
                value.semantic_link_atoms,
                value.explicit_unknown_atoms,
            )
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_INVALID"
        )
    handle_indices = tuple(row.handle_index for row in value.natural_handles)
    if (
        handle_indices != tuple(range(1, len(handle_indices) + 1))
        or len(handle_indices) > _STEP11_RC0029_OWNER_MAX
        or len({row.handle_text for row in value.natural_handles})
        != len(value.natural_handles)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_SET_INVALID"
        )

    def roles(row: Step11Rc0029ExperimentParsedConstructionAtom) -> list[dict[str, Any]]:
        return [
            {
                "handle_index": item.handle_index,
                "lexical_role_kind": item.lexical_role_kind,
                "construction_position": item.construction_position,
                "role_position_key": item.role_position_key,
            }
            for item in row.role_owner_bindings
        ]

    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_witness": _witness_material(value.base_witness),
        "natural_handles": [
            _step11_rc0029_handle_material_index(row)
            for row in value.natural_handles
        ],
        "construction_atoms": [
            {
                "ordinal": row.ordinal,
                "construction_code": row.construction_code,
                "role_owner_bindings": roles(row),
            }
            for row in value.construction_atoms
        ],
        "relation_atoms": [
            {
                "ordinal": row.ordinal,
                "effective_relation_type": row.effective_relation_type,
                "from_handle_index": row.from_handle_index,
                "to_handle_index": row.to_handle_index,
                "direction": row.direction,
                "relation_surface_key": row.relation_surface_key,
            }
            for row in value.relation_atoms
        ],
        "semantic_link_atoms": [
            {
                "ordinal": row.ordinal,
                "relation_type": row.relation_type,
                "from_handle_index": row.from_handle_index,
                "to_handle_index": row.to_handle_index,
                "direction": row.direction,
                "semantic_link_surface_key": row.semantic_link_surface_key,
            }
            for row in value.semantic_link_atoms
        ],
        "explicit_unknown_atoms": [
            {
                "ordinal": row.ordinal,
                "dimension": row.dimension,
                "affected_handle_indices": list(
                    row.affected_handle_indices
                ),
            }
            for row in value.explicit_unknown_atoms
        ],
        "reception_bindings": [
            {
                "reception_line_ordinal": row.reception_line_ordinal,
                "reception_act": row.reception_act,
                "reception_scope": row.reception_scope,
                "antecedent_handle_indices": list(
                    row.antecedent_handle_indices
                ),
            }
            for row in value.reception_bindings
        ],
        "fused_structure_item_count": value.fused_structure_item_count,
        "fused_structure_group_count": value.fused_structure_group_count,
        "added_observation_line_count": value.added_observation_line_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _step11_rc0029_split_handle_sequence(
    value: str,
    *,
    joiner: str,
    morphology: Mapping[str, str],
) -> tuple[str, ...]:
    handle_open = morphology["handle_open"]
    handle_close = morphology["handle_close"]
    if not value.startswith(handle_open):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
        )
    handles: list[str] = []
    position = 0
    while position < len(value):
        if not value.startswith(handle_open, position):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
            )
        start = position + len(handle_open)
        end = value.find(handle_close, start)
        if end < 0:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
            )
        handle = value[start:end]
        if (
            not handle
            or len(handle) > _STEP11_RC0029_HANDLE_MAX
            or handle_open in handle
            or handle_close in handle
            or "\r" in handle
            or "\n" in handle
            or unicodedata.normalize("NFC", handle) != handle
            or _STEP11_RC0029_OPAQUE_HANDLE_RE.search(handle) is not None
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_INVALID"
            )
        handles.append(handle)
        position = end + len(handle_close)
        if position == len(value):
            break
        if not value.startswith(joiner, position):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
            )
        position += len(joiner)
    return tuple(handles)


def _step11_rc0029_parse_structure_item(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    register_handle: Any,
    ordinals: Mapping[str, int],
) -> tuple[str, Any]:
    construction_by_token = _step11_rc0029_inverse_map(
        catalog.get("construction_surface_tokens"),
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    relation_by_token = _step11_rc0029_inverse_map(
        catalog.get("relation_surface_tokens"),
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    link_by_token = _step11_rc0029_inverse_map(
        catalog.get("semantic_link_surface_tokens"),
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    unknown_by_token = _step11_rc0029_inverse_map(
        catalog.get("unknown_surface_tokens"),
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    matches: list[tuple[str, Any]] = []

    construction_suffix = morphology["construction_suffix"]
    if value.endswith(construction_suffix):
        core = value[: -len(construction_suffix)]
        for token, construction_code in construction_by_token.items():
            tail = morphology["construction_open"] + token
            if not core.endswith(tail):
                continue
            owner_text = core[: -len(tail)]
            try:
                handles = _step11_rc0029_split_handle_sequence(
                    owner_text,
                    joiner=morphology["construction_owner_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            if not handles or len(handles) != len(set(handles)):
                continue
            matches.append(
                (
                    "construction",
                    Step11Rc0029ExperimentParsedConstructionAtom(
                        ordinal=ordinals["construction"],
                        construction_code=construction_code,
                        role_owner_bindings=tuple(
                            Step11Rc0029ExperimentParsedConstructionRoleOwner(
                                handle_index=register_handle(handle),
                                lexical_role_kind=None,
                                construction_position=None,
                                role_position_key=None,
                            )
                            for handle in handles
                        ),
                    ),
                )
            )

    relation_suffix = morphology["relation_suffix"]
    if value.endswith(relation_suffix):
        core = value[: -len(relation_suffix)]
        for token, surface_key in relation_by_token.items():
            tail = morphology["relation_to"] + token
            if not core.endswith(tail):
                continue
            endpoints = core[: -len(tail)]
            separator = morphology["relation_from"]
            candidates = tuple(
                index
                for index in range(len(endpoints))
                if endpoints.startswith(separator, index)
            )
            for index in candidates:
                try:
                    left = _step11_rc0029_split_handle_sequence(
                        endpoints[:index], joiner="\x00", morphology=morphology
                    )
                    right = _step11_rc0029_split_handle_sequence(
                        endpoints[index + len(separator) :],
                        joiner="\x00",
                        morphology=morphology,
                    )
                except Step11Rc0029ExperimentInverseSurfaceError:
                    continue
                if len(left) != 1 or len(right) != 1:
                    continue
                relation_type, direction = surface_key.rsplit(":", 1)
                matches.append(
                    (
                        "relation",
                        Step11Rc0029ExperimentParsedRelationAtom(
                            ordinal=ordinals["relation"],
                            effective_relation_type=relation_type,
                            from_handle_index=register_handle(left[0]),
                            to_handle_index=register_handle(right[0]),
                            direction=direction,
                            relation_surface_key=surface_key,
                        ),
                    )
                )

    link_suffix = morphology["link_suffix"]
    if value.endswith(link_suffix):
        core = value[: -len(link_suffix)]
        for token, surface_key in link_by_token.items():
            tail = morphology["link_between"] + token
            if not core.endswith(tail):
                continue
            endpoints = core[: -len(tail)]
            try:
                handles = _step11_rc0029_split_handle_sequence(
                    endpoints,
                    joiner=morphology["link_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            if len(handles) != 2:
                continue
            relation_type, direction = surface_key.rsplit(":", 1)
            matches.append(
                (
                    "semantic_link",
                    Step11Rc0029ExperimentParsedSemanticLinkAtom(
                        ordinal=ordinals["semantic_link"],
                        relation_type=relation_type,
                        from_handle_index=register_handle(handles[0]),
                        to_handle_index=register_handle(handles[1]),
                        direction=direction,
                        semantic_link_surface_key=surface_key,
                    ),
                )
            )

    unknown_suffix = morphology["unknown_suffix"]
    if value.endswith(unknown_suffix):
        core = value[: -len(unknown_suffix)]
        for token, dimension in unknown_by_token.items():
            tail = morphology["unknown_between"] + token
            if not core.endswith(tail):
                continue
            owners = core[: -len(tail)]
            try:
                handles = _step11_rc0029_split_handle_sequence(
                    owners,
                    joiner=morphology["unknown_owner_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            if not handles or len(handles) != len(set(handles)):
                continue
            matches.append(
                (
                    "explicit_unknown",
                    Step11Rc0029ExperimentParsedExplicitUnknownAtom(
                        ordinal=ordinals["explicit_unknown"],
                        dimension=dimension,
                        affected_handle_indices=tuple(
                            register_handle(handle) for handle in handles
                        ),
                    ),
                )
            )

    if len(matches) != 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    return matches[0]


def parse_step11_rc0029_experiment_surface(
    body: bytes,
    *forward_metadata: Any,
    **forward_metadata_by_name: Any,
) -> Step11Rc0029ExperimentParsedSurfaceWitness:
    """Parse canonical final bytes; reject every forward metadata argument."""

    if forward_metadata or forward_metadata_by_name:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_FORWARD_METADATA_FORBIDDEN"
        )
    if (
        type(body) is not bytes
        or not body
        or len(body) > _STEP11_RC0029_BODY_BYTE_MAX
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_BODY_INVALID"
        )
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_UTF8_INVALID"
        ) from exc
    if (
        unicodedata.normalize("NFC", text) != text
        or "\r" in text
        or text.endswith("\n")
        or text.startswith("\ufeff")
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_CANONICAL_TEXT_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0029_inverse_catalog()
    morphology = catalog.get("morphology")
    required_morphology = {
        "handle_open",
        "handle_close",
        "structural_prefix",
        "item_join",
        "construction_open",
        "construction_owner_join",
        "construction_suffix",
        "relation_from",
        "relation_to",
        "relation_suffix",
        "link_join",
        "link_between",
        "link_suffix",
        "unknown_owner_join",
        "unknown_between",
        "unknown_suffix",
        "observation_insert",
        "reception_handle_join",
        "reception_prefix",
    }
    if (
        type(morphology) is not dict
        or not required_morphology <= set(morphology)
        or any(
            type(morphology[key]) is not str or not morphology[key]
            for key in required_morphology
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CATALOG_TOKEN_MISMATCH"
        )
    labels = STEP11_SURFACE_CATALOG.get("labels")
    if type(labels) is not dict:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        )
    observation_label = labels.get("observation")
    reception_label = labels.get("reception")
    prefix = str(observation_label) + "\n"
    section_separator = "\n\n" + str(reception_label) + "\n"
    if (
        type(observation_label) is not str
        or type(reception_label) is not str
        or not text.startswith(prefix)
        or text.count(section_separator) != 1
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        )
    observation, reception = text[len(prefix) :].split(section_separator)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SURFACE_LAYOUT_INVALID"
        )

    handle_texts: list[str] = []
    handle_index_by_text: dict[str, int] = {}

    def register_handle(value: str) -> int:
        if value not in handle_index_by_text:
            if len(handle_texts) >= _STEP11_RC0029_OWNER_MAX:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED"
                )
            handle_texts.append(value)
            handle_index_by_text[value] = len(handle_texts)
        return handle_index_by_text[value]

    construction_atoms: list[Step11Rc0029ExperimentParsedConstructionAtom] = []
    relation_atoms: list[Step11Rc0029ExperimentParsedRelationAtom] = []
    semantic_link_atoms: list[
        Step11Rc0029ExperimentParsedSemanticLinkAtom
    ] = []
    explicit_unknown_atoms: list[
        Step11Rc0029ExperimentParsedExplicitUnknownAtom
    ] = []
    structure_marker = (
        morphology["observation_insert"] + morphology["structural_prefix"]
    )
    tail = observation_lines[-1]
    marker_count = tail.count(structure_marker)
    if marker_count > 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    payload = ""
    if marker_count == 1:
        if not tail.endswith(morphology["observation_insert"]):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        base_tail, payload = tail.split(structure_marker, 1)
        payload = payload[: -len(morphology["observation_insert"])]
        if not base_tail or not payload:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        observation_lines[-1] = (
            base_tail + morphology["observation_insert"]
        )
    rank = {
        "construction": 0,
        "relation": 1,
        "semantic_link": 2,
        "explicit_unknown": 3,
    }
    current_rank = -1
    for item in (
        payload.split(morphology["item_join"]) if payload else ()
    ):
        if not item:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        kind, parsed = _step11_rc0029_parse_structure_item(
            item,
            catalog=catalog,
            morphology=morphology,
            register_handle=register_handle,
            ordinals={
                "construction": len(construction_atoms) + 1,
                "relation": len(relation_atoms) + 1,
                "semantic_link": len(semantic_link_atoms) + 1,
                "explicit_unknown": len(explicit_unknown_atoms) + 1,
            },
        )
        if rank[kind] < current_rank:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_ORDER_INVALID"
            )
        current_rank = rank[kind]
        {
            "construction": construction_atoms,
            "relation": relation_atoms,
            "semantic_link": semantic_link_atoms,
            "explicit_unknown": explicit_unknown_atoms,
        }[kind].append(parsed)

    reconstructed_reception: list[str] = []
    reception_handle_indices: list[tuple[int, ...]] = []
    for line in reception_lines:
        prefix_candidates: list[tuple[tuple[str, ...], str]] = []
        reception_prefix = morphology["reception_prefix"]
        for index in range(len(line)):
            if not line.startswith(reception_prefix, index):
                continue
            try:
                handles = _step11_rc0029_split_handle_sequence(
                    line[:index],
                    joiner=morphology["reception_handle_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            remainder = line[index + len(reception_prefix) :]
            if handles and remainder:
                prefix_candidates.append((handles, remainder))
        if len(prefix_candidates) != 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ANTECEDENT_MISSING"
            )
        handles, remainder = prefix_candidates[0]
        indices = tuple(register_handle(handle) for handle in handles)
        if len(indices) != len(set(indices)):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ANTECEDENT_DUPLICATE"
            )
        reception_handle_indices.append(indices)
        reconstructed_reception.append(remainder)

    base_text = (
        prefix
        + "\n".join(observation_lines)
        + section_separator
        + "\n".join(reconstructed_reception)
    )
    base_body = base_text.encode("utf-8", errors="strict")
    try:
        parsed_base = parse_step11_natural_surface(base_body)
    except Step11InverseSurfaceError as exc:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        ) from exc
    base_reception_atoms = tuple(
        atom
        for atom in parsed_base.atoms
        if atom.section_role == "reception" and atom.reception_act is not None
    )
    if len(base_reception_atoms) != len(reception_handle_indices):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_CARDINALITY_MISMATCH"
        )

    parsed_receptions: list[
        Step11Rc0029ExperimentParsedReceptionBinding
    ] = []
    reference_by_atom_id: dict[
        str, tuple[Step11EndpointReference, ...]
    ] = {}
    for ordinal, (atom, handle_indices) in enumerate(
        zip(base_reception_atoms, reception_handle_indices), 1
    ):
        scope = atom.reception_scope
        endpoint_role = (
            scope if scope in {"thought", "action"} else "thought"
        )
        references = tuple(
            Step11EndpointReference(
                reference_ordinal=handle_index,
                endpoint_role=endpoint_role,
            )
            for handle_index in handle_indices
        )
        reference_by_atom_id[atom.atom_id] = references
        parsed_receptions.append(
            Step11Rc0029ExperimentParsedReceptionBinding(
                reception_line_ordinal=ordinal,
                reception_act=str(atom.reception_act),
                reception_scope=str(scope),
                antecedent_handle_indices=handle_indices,
            )
        )
    from dataclasses import replace as _step11_rc0029_replace

    augmented_atoms = tuple(
        _step11_rc0029_replace(
            atom,
            reception_antecedent_references=reference_by_atom_id[atom.atom_id],
        )
        if atom.atom_id in reference_by_atom_id
        else atom
        for atom in parsed_base.atoms
    )
    base_witness = _step11_rc0029_replace(parsed_base, atoms=augmented_atoms)

    # A visible handle is its grounded phrase plus at most one closed,
    # source-authorized topology qualifier.  The Parser derives this split
    # from final bytes and the catalog only; the Matcher independently checks
    # the qualifier against the source graph after solving the binding.
    qualifier_values = tuple(
        dict.fromkeys(
            (
                *catalog["role_position_surface_tokens"].values(),
                *catalog["owner_role_surface_tokens"].values(),
            )
        )
    )
    natural_handles: list[Step11Rc0029ExperimentParsedNaturalHandle] = []
    for index, handle_text in enumerate(handle_texts, 1):
        decompositions: list[tuple[str, tuple[str, ...]]] = []
        if handle_text in base_text:
            decompositions.append((handle_text, ()))
        for boundary, character in enumerate(handle_text):
            if character != "の" or boundary == 0:
                continue
            grounded_phrase = handle_text[:boundary]
            suffix = handle_text[boundary + 1 :]
            if not suffix or grounded_phrase not in base_text:
                continue
            memo: dict[tuple[int, int], tuple[tuple[str, ...], ...]] = {}

            def qualifier_sequences(
                position: int, minimum_rank: int
            ) -> tuple[tuple[str, ...], ...]:
                key = (position, minimum_rank)
                if key in memo:
                    return memo[key]
                rows: list[tuple[str, ...]] = []
                for rank in range(minimum_rank + 1, len(qualifier_values)):
                    token = qualifier_values[rank]
                    if not suffix.startswith(token, position):
                        continue
                    end = position + len(token)
                    if end == len(suffix):
                        rows.append((token,))
                    elif suffix.startswith("と", end):
                        for tail_tokens in qualifier_sequences(end + 1, rank):
                            rows.append((token, *tail_tokens))
                            if len(rows) > 1:
                                break
                    if len(rows) > 1:
                        break
                memo[key] = tuple(rows[:2])
                return memo[key]

            for qualifier_tuple in qualifier_sequences(0, -1):
                decompositions.append((grounded_phrase, qualifier_tuple))
                if len(decompositions) > 1:
                    break
            if len(decompositions) > 1:
                break
        if len(decompositions) != 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_AMBIGUOUS"
            )
        grounded_phrase, qualifiers = decompositions[0]
        if not grounded_phrase:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_GROUNDING_MISSING"
            )
        natural_handles.append(
            Step11Rc0029ExperimentParsedNaturalHandle(
                handle_index=index,
                handle_text=handle_text,
                grounded_phrase_text=grounded_phrase,
                qualifier_tokens=qualifiers,
            )
        )

    witness = Step11Rc0029ExperimentParsedSurfaceWitness(
        schema_version=STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA,
        body_sha256=hashlib.sha256(body).hexdigest(),
        experiment_catalog_sha256=catalog_sha256,
        base_witness=base_witness,
        natural_handles=tuple(natural_handles),
        construction_atoms=tuple(construction_atoms),
        relation_atoms=tuple(relation_atoms),
        semantic_link_atoms=tuple(semantic_link_atoms),
        explicit_unknown_atoms=tuple(explicit_unknown_atoms),
        reception_bindings=tuple(parsed_receptions),
        fused_structure_item_count=(
            len(construction_atoms)
            + len(relation_atoms)
            + len(semantic_link_atoms)
            + len(explicit_unknown_atoms)
        ),
        fused_structure_group_count=sum(
            bool(rows)
            for rows in (
                construction_atoms,
                relation_atoms,
                semantic_link_atoms,
                explicit_unknown_atoms,
            )
        ),
        added_observation_line_count=0,
    )
    step11_rc0029_experiment_parsed_witness_material(witness)
    return witness


def match_step11_rc0029_experiment_surface(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    successor_snapshot: Any,
) -> Step11Rc0029ExperimentVerifiedSurfaceBinding:
    """Active compact-family matcher; no source-order correspondence."""

    return _step11_rc0029_final_match_surface(
        witness, successor_snapshot=successor_snapshot
    )


def _step11_rc0029_final_counts(
    values: Sequence[tuple[Any, ...]],
) -> dict[tuple[Any, ...], int]:
    result: dict[tuple[Any, ...], int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _step11_rc0029_final_required_receptions(
    successor_snapshot: Any,
    *,
    ordinal_by_id: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> tuple[tuple[str, tuple[int, ...], tuple[int, ...]], ...]:
    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    if len(actual_by_source) != len(nuclei):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_SOURCE_MISMATCH"
        )
    result: list[tuple[str, tuple[int, ...], tuple[int, ...]]] = []
    for opportunity in successor_snapshot.base_snapshot.reception_opportunities:
        if not (
            opportunity.retention == "required"
            or opportunity.safety_required is True
        ):
            continue
        act = str(opportunity.reception_act)
        if act not in catalog["reception_act_surface_tokens"]:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ACT_MISMATCH"
            )
        try:
            targets = tuple(
                ordinal_by_id[actual_by_source[str(source_id)]]
                for source_id in opportunity.target_nucleus_ids
            )
            supports = tuple(
                ordinal_by_id[actual_by_source[str(source_id)]]
                for source_id in opportunity.support_nucleus_ids
            )
        except KeyError as exc:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_SOURCE_MISMATCH"
            ) from exc
        if (
            not targets
            or len(targets) != len(set(targets))
            or len(supports) != len(set(supports))
            or set(targets) & set(supports)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_SOURCE_MISMATCH"
            )
        result.append((act, targets, supports))
    if not result:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
        )
    return tuple(result)


def _step11_rc0029_final_owner_heads(
    successor_snapshot: Any,
    *,
    owner_registry: Sequence[tuple[str, str]],
    required_owner_ordinals: frozenset[int],
    catalog: Mapping[str, Any],
) -> dict[int, tuple[str, str]]:
    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    by_actual = {str(row.actual_source_id): row for row in nuclei}
    by_source = {str(row.source_id): row for row in nuclei}
    if len(by_actual) != len(nuclei) or len(by_source) != len(nuclei):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        )
    parents_by_semantic: dict[str, set[str]] = {}
    for row in successor_snapshot.relation_construction_authority.source_owner_participations:
        if row.target_owner_kind == "semantic_unit":
            parents_by_semantic.setdefault(str(row.target_owner_id), set()).add(
                str(row.parent_nucleus_id)
            )
    heads = catalog["owner_kind_surface_tokens"]
    result: dict[int, tuple[str, str]] = {}
    for ordinal in sorted(required_owner_ordinals):
        if not 1 <= ordinal <= len(owner_registry):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
            )
        owner_id, _owner_kind = owner_registry[ordinal - 1]
        nucleus = by_actual.get(owner_id)
        if nucleus is None:
            parents = parents_by_semantic.get(owner_id, set())
            if len(parents) != 1:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
                )
            parent_id = next(iter(parents))
            nucleus = by_actual.get(parent_id) or by_source.get(parent_id)
        if nucleus is None:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
            )
        head_kind = str(nucleus.kind)
        head_text = heads.get(head_kind)
        if type(head_text) is not str or not head_text:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
            )
        result[ordinal] = (head_kind, head_text)
    return result


def _step11_rc0029_final_reception_role_alignment(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    expected_receptions: Sequence[
        tuple[str, tuple[int, ...], tuple[int, ...]]
    ],
    owner_heads: Mapping[int, tuple[str, str]],
) -> tuple[bool, ...]:
    head_by_handle = {
        row.handle_index: row.semantic_head_kind
        for row in witness.natural_handles
    }
    expected_keys = tuple(
        (
            act,
            tuple(sorted(owner_heads[row][0] for row in targets)),
            tuple(sorted(owner_heads[row][0] for row in supports)),
        )
        for act, targets, supports in expected_receptions
    )
    parsed_keys = tuple(
        (
            row.reception_act,
            tuple(
                sorted(
                    head_by_handle[index]
                    for index in row.target_handle_indices
                )
            ),
            tuple(
                sorted(
                    head_by_handle[index]
                    for index in row.supporting_handle_indices
                )
            ),
        )
        for row in witness.reception_bindings
    )
    if len(parsed_keys) != len(expected_keys):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
        )
    expected_positions: dict[tuple[Any, ...], list[int]] = {}
    for index, key in enumerate(expected_keys):
        expected_positions.setdefault(key, []).append(index)
    parsed_positions: dict[tuple[Any, ...], list[int]] = {}
    for index, key in enumerate(parsed_keys):
        parsed_positions.setdefault(key, []).append(index)
    if set(parsed_positions) != set(expected_positions) or any(
        len(parsed_positions[key]) != len(expected_positions[key])
        for key in expected_positions
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH"
        )
    # A repeated closed head signature cannot prove which opportunity was
    # mapped to the base clause.  Fail closed rather than using source order.
    if any(len(rows) != 1 for rows in expected_positions.values()):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_AMBIGUOUS"
        )
    additional_by_expected = [False] * len(expected_keys)
    for key, parsed_rows in parsed_positions.items():
        expected_index = expected_positions[key][0]
        parsed_index = parsed_rows[0]
        additional_by_expected[expected_index] = witness.reception_bindings[
            parsed_index
        ].additional_clause
    return tuple(additional_by_expected)


def _step11_rc0029_final_expected_handle_signatures(
    *,
    required_owner_ordinals: frozenset[int],
    owner_heads: Mapping[int, tuple[str, str]],
    allowed_qualifiers: Mapping[int, frozenset[str]],
    catalog: Mapping[str, Any],
) -> dict[int, tuple[str, str, tuple[str, ...]]]:
    qualifier_order = tuple(
        dict.fromkeys(
            (
                *catalog["role_position_surface_tokens"].values(),
                *catalog["owner_role_surface_tokens"].values(),
            )
        )
    )
    rank = {token: index for index, token in enumerate(qualifier_order)}
    owners_by_head: dict[str, list[int]] = {}
    for ordinal in required_owner_ordinals:
        owners_by_head.setdefault(owner_heads[ordinal][1], []).append(ordinal)
    result: dict[int, tuple[str, str, tuple[str, ...]]] = {}
    for rows in owners_by_head.values():
        ordered_rows = tuple(sorted(rows))
        if len(ordered_rows) == 1:
            ordinal = ordered_rows[0]
            kind, text = owner_heads[ordinal]
            result[ordinal] = (kind, text, ())
            continue
        authorized_by_token: dict[str, set[int]] = {}
        for ordinal in ordered_rows:
            for token in allowed_qualifiers.get(ordinal, frozenset()):
                authorized_by_token.setdefault(token, set()).add(ordinal)
        for ordinal in ordered_rows:
            unique_tokens = tuple(
                sorted(
                    (
                        token
                        for token in allowed_qualifiers.get(
                            ordinal, frozenset()
                        )
                        if authorized_by_token.get(token) == {ordinal}
                    ),
                    key=lambda token: (rank.get(token, 10_000), token),
                )
            )
            if not unique_tokens:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_NATURAL_HANDLE_COLLISION"
                )
            kind, text = owner_heads[ordinal]
            result[ordinal] = (kind, text, (unique_tokens[0],))
    if (
        set(result) != set(required_owner_ordinals)
        or len(set(result.values())) != len(result)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_COLLISION"
        )
    return result


def _step11_rc0029_final_linear_binding(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    expected_signatures: Mapping[
        int, tuple[str, str, tuple[str, ...]]
    ],
) -> tuple[dict[int, int], int]:
    owner_by_signature = {
        signature: ordinal
        for ordinal, signature in expected_signatures.items()
    }
    if len(owner_by_signature) != len(expected_signatures):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_COLLISION"
        )
    binding: dict[int, int] = {}
    for handle in witness.natural_handles:
        signature = (
            handle.semantic_head_kind,
            handle.semantic_head_text,
            handle.qualifier_tokens,
        )
        owner_ordinal = owner_by_signature.get(signature)
        candidate_count = int(owner_ordinal is not None)
        if candidate_count != 1 or owner_ordinal is None:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
            )
        binding[handle.handle_index] = owner_ordinal
    injective = len(set(binding.values())) == len(binding)
    complete = set(binding.values()) == set(expected_signatures)
    solution_count = int(injective and complete and len(binding) == len(expected_signatures))
    if solution_count != 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
        )
    return binding, solution_count


def _step11_rc0029_final_expected_component_count(
    *,
    construction_rows: Sequence[tuple[str, tuple[str, ...], int]],
    relation_rows: Sequence[tuple[str, str, int, int]],
    link_rows: Sequence[tuple[str, str, int, int]],
    unknown_rows: Sequence[tuple[str, tuple[int, ...]]],
    reception_rows: Sequence[tuple[str, tuple[int, ...], tuple[int, ...]]],
) -> int:
    parent: dict[int, int] = {}

    def find(value: int) -> int:
        parent.setdefault(value, value)
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def add(values: Sequence[int]) -> None:
        unique = tuple(dict.fromkeys(values))
        if not unique:
            return
        anchor = find(unique[0])
        for value in unique[1:]:
            other = find(value)
            if anchor != other:
                parent[other] = anchor

    for _code, _role_keys, owner in construction_rows:
        add((owner,))
    for _kind, _direction, left, right in relation_rows:
        add((left, right))
    for _kind, _direction, left, right in link_rows:
        add((left, right))
    for _dimension, owners in unknown_rows:
        add(owners)
    for _act, targets, supports in reception_rows:
        add((*targets, *supports))
    return len({find(value) for value in parent})


def _step11_rc0029_final_compare_semantics(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    binding: Mapping[int, int],
    expected_constructions: Sequence[
        tuple[str, tuple[str, ...], int]
    ],
    expected_relations: Sequence[tuple[str, str, int, int]],
    expected_links: Sequence[tuple[str, str, int, int]],
    expected_unknowns: Sequence[tuple[str, tuple[int, ...]]],
    expected_receptions: Sequence[
        tuple[str, tuple[int, ...], tuple[int, ...]]
    ],
) -> None:
    for row in witness.construction_atoms:
        if not row.role_owner_bindings:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )
        handle_indices = {
            role.handle_index for role in row.role_owner_bindings
        }
        if (
            len(handle_indices) != 1
            or not handle_indices <= set(binding)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH"
            )
    parsed_constructions = tuple(
        (
            row.construction_code,
            tuple(
                str(role.role_position_key)
                for role in row.role_owner_bindings
            ),
            binding[row.role_owner_bindings[0].handle_index],
        )
        for row in witness.construction_atoms
    )
    if len(parsed_constructions) != len(expected_constructions):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple((code,) for code, _roles, _owner in parsed_constructions)
    ) != _step11_rc0029_final_counts(
        tuple((code,) for code, _roles, _owner in expected_constructions)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple((code, roles) for code, roles, _owner in parsed_constructions)
    ) != _step11_rc0029_final_counts(
        tuple((code, roles) for code, roles, _owner in expected_constructions)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
        )
    if _step11_rc0029_final_counts(parsed_constructions) != (
        _step11_rc0029_final_counts(expected_constructions)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH"
        )

    parsed_relations = tuple(
        (
            row.effective_relation_type,
            row.direction,
            binding[row.from_handle_index],
            binding[row.to_handle_index],
        )
        for row in witness.relation_atoms
    )
    if len(parsed_relations) != len(expected_relations):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple((row[0],) for row in parsed_relations)
    ) != _step11_rc0029_final_counts(
        tuple((row[0],) for row in expected_relations)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EFFECTIVE_RELATION_TYPE_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple(row[:2] for row in parsed_relations)
    ) != _step11_rc0029_final_counts(
        tuple(row[:2] for row in expected_relations)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RELATION_DIRECTION_MISMATCH"
        )
    if _step11_rc0029_final_counts(parsed_relations) != (
        _step11_rc0029_final_counts(expected_relations)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RELATION_ENDPOINT_MISMATCH"
        )

    parsed_links = tuple(
        (
            row.relation_type,
            row.direction,
            binding[row.from_handle_index],
            binding[row.to_handle_index],
        )
        for row in witness.semantic_link_atoms
    )
    if len(parsed_links) != len(expected_links):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SEMANTIC_LINK_BINDING_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple((row[0],) for row in parsed_links)
    ) != _step11_rc0029_final_counts(
        tuple((row[0],) for row in expected_links)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SEMANTIC_LINK_TYPE_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple(row[:2] for row in parsed_links)
    ) != _step11_rc0029_final_counts(
        tuple(row[:2] for row in expected_links)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SEMANTIC_LINK_DIRECTION_MISMATCH"
        )
    if _step11_rc0029_final_counts(parsed_links) != (
        _step11_rc0029_final_counts(expected_links)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SEMANTIC_LINK_ENDPOINT_MISMATCH"
        )

    parsed_unknowns = tuple(
        (
            row.dimension,
            tuple(binding[index] for index in row.affected_handle_indices),
        )
        for row in witness.explicit_unknown_atoms
    )
    if len(parsed_unknowns) < len(expected_unknowns):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EXPLICIT_UNKNOWN_MISSING"
        )
    if len(parsed_unknowns) > len(expected_unknowns):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EXPLICIT_UNKNOWN_DUPLICATE"
        )
    if _step11_rc0029_final_counts(
        tuple((row[0],) for row in parsed_unknowns)
    ) != _step11_rc0029_final_counts(
        tuple((row[0],) for row in expected_unknowns)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH"
        )
    if _step11_rc0029_final_counts(parsed_unknowns) != (
        _step11_rc0029_final_counts(expected_unknowns)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
        )

    parsed_receptions = tuple(
        (
            row.reception_act,
            tuple(
                sorted(binding[index] for index in row.target_handle_indices)
            ),
            tuple(
                sorted(
                    binding[index]
                    for index in row.supporting_handle_indices
                )
            ),
        )
        for row in witness.reception_bindings
    )
    normalized_expected_receptions = tuple(
        (act, tuple(sorted(targets)), tuple(sorted(supports)))
        for act, targets, supports in expected_receptions
    )
    if len(parsed_receptions) != len(normalized_expected_receptions):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
        )
    if _step11_rc0029_final_counts(
        tuple((row[0],) for row in parsed_receptions)
    ) != _step11_rc0029_final_counts(
        tuple((row[0],) for row in normalized_expected_receptions)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_ACT_MISMATCH"
        )
    if _step11_rc0029_final_counts(parsed_receptions) != (
        _step11_rc0029_final_counts(normalized_expected_receptions)
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH"
        )


def _step11_rc0029_final_match_surface(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    successor_snapshot: Any,
) -> Step11Rc0029ExperimentVerifiedSurfaceBinding:
    """Linearly bind closed visible signatures to exact source authority."""

    if type(witness) is not Step11Rc0029ExperimentParsedSurfaceWitness:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_TYPE_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0029_inverse_catalog()
    if witness.experiment_catalog_sha256 != catalog_sha256:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CATALOG_COMMITMENT_MISMATCH"
        )
    for atom in witness.construction_atoms:
        for role in atom.role_owner_bindings:
            role_key = role.role_position_key
            if type(role_key) is not str or role_key.count(":") != 1:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            expected_kind, expected_position = role_key.split(":", 1)
            if role.construction_position != expected_position:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            if role.lexical_role_kind != expected_kind:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
    base_reception_atoms = tuple(
        atom
        for atom in witness.base_witness.atoms
        if atom.section_role == "reception" and atom.reception_act is not None
    )
    for row in witness.reception_bindings:
        if not 1 <= row.reception_line_ordinal <= len(base_reception_atoms):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
            )
        base_atom = base_reception_atoms[row.reception_line_ordinal - 1]
        if row.reception_scope != str(base_atom.reception_scope):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ACT_ASSOCIATION_MISMATCH"
            )
        if (
            not row.additional_clause
            and row.reception_act != str(base_atom.reception_act)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ACT_ASSOCIATION_MISMATCH"
            )
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    expected_type = successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    if type(successor_snapshot) is not expected_type:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        )
    if (
        successor_snapshot.semantic_coverage_authorized is not False
        or successor_snapshot.experimental_only is not True
        or successor_snapshot.runtime_connected is not False
        or successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            successor_snapshot
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        )
    (
        owner_registry,
        ordinal_by_id,
        source_constructions,
        source_relations,
        source_links,
        source_unknowns,
        slot_count,
        participation_count,
        endpoint_count,
    ) = _step11_rc0029_expected_contract(
        successor_snapshot, catalog=catalog
    )

    expected_constructions: list[
        tuple[str, tuple[str, ...], int]
    ] = []
    for row in source_constructions:
        owners = tuple(
            binding.owner_ordinal for binding in row.role_owner_bindings
        )
        role_keys = tuple(
            str(binding.role_position_key)
            for binding in row.role_owner_bindings
        )
        catalog_layout = catalog["construction_role_layouts"].get(
            row.construction_code
        )
        if (
            not owners
            or len(set(owners)) != 1
            or type(catalog_layout) is not list
            or role_keys != tuple(catalog_layout)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH"
            )
        expected_constructions.append(
            (row.construction_code, role_keys, owners[0])
        )
    expected_relations = tuple(
        (
            row.effective_relation_type,
            row.direction,
            row.from_owner_ordinal,
            row.to_owner_ordinal,
        )
        for row in source_relations
    )
    expected_links = tuple(
        (
            row.relation_type,
            row.direction,
            row.from_owner_ordinal,
            row.to_owner_ordinal,
        )
        for row in source_links
    )
    expected_unknowns = tuple(
        (row.dimension, row.affected_owner_ordinals)
        for row in source_unknowns
    )
    expected_receptions = _step11_rc0029_final_required_receptions(
        successor_snapshot,
        ordinal_by_id=ordinal_by_id,
        catalog=catalog,
    )
    required_owner_ordinals = frozenset(
        (
            *(
                owner
                for _code, _role_keys, owner in expected_constructions
            ),
            *(
                owner
                for _kind, _direction, left, right in expected_relations
                for owner in (left, right)
            ),
            *(
                owner
                for _kind, _direction, left, right in expected_links
                for owner in (left, right)
            ),
            *(
                owner
                for _dimension, owners in expected_unknowns
                for owner in owners
            ),
            *(
                owner
                for _act, targets, supports in expected_receptions
                for owner in (*targets, *supports)
            ),
        )
    )
    if not required_owner_ordinals:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_REQUIRED_ATOM_MISSING"
        )
    owner_heads = _step11_rc0029_final_owner_heads(
        successor_snapshot,
        owner_registry=owner_registry,
        required_owner_ordinals=required_owner_ordinals,
        catalog=catalog,
    )
    additional_by_expected = _step11_rc0029_final_reception_role_alignment(
        witness,
        expected_receptions=expected_receptions,
        owner_heads=owner_heads,
    )
    allowed = {
        ordinal: set(tokens)
        for ordinal, tokens in _step11_rc0029_allowed_qualifiers(
            constructions=source_constructions,
            relations=source_relations,
            links=source_links,
            unknowns=source_unknowns,
            catalog=catalog,
        ).items()
    }
    reception_tokens = catalog["owner_role_surface_tokens"]
    for index, (_act, targets, supports) in enumerate(expected_receptions):
        target_token = (
            reception_tokens["reception_target"]
            if additional_by_expected[index]
            else reception_tokens["reception_antecedent"]
        )
        for ordinal in targets:
            allowed.setdefault(ordinal, set()).add(target_token)
        for ordinal in supports:
            allowed.setdefault(ordinal, set()).add(
                reception_tokens["reception_support"]
            )
    expected_signatures = _step11_rc0029_final_expected_handle_signatures(
        required_owner_ordinals=required_owner_ordinals,
        owner_heads=owner_heads,
        allowed_qualifiers={
            ordinal: frozenset(tokens) for ordinal, tokens in allowed.items()
        },
        catalog=catalog,
    )
    binding, solution_count = _step11_rc0029_final_linear_binding(
        witness, expected_signatures=expected_signatures
    )
    _step11_rc0029_final_compare_semantics(
        witness,
        binding=binding,
        expected_constructions=tuple(expected_constructions),
        expected_relations=expected_relations,
        expected_links=expected_links,
        expected_unknowns=expected_unknowns,
        expected_receptions=expected_receptions,
    )
    expected_component_count = _step11_rc0029_final_expected_component_count(
        construction_rows=tuple(expected_constructions),
        relation_rows=expected_relations,
        link_rows=expected_links,
        unknown_rows=expected_unknowns,
        reception_rows=expected_receptions,
    )
    if witness.fused_structure_group_count != expected_component_count:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_GROUP_COMMITMENT_MISMATCH"
        )
    expected_family_count = sum(
        bool(rows)
        for rows in (
            expected_constructions,
            expected_relations,
            expected_links,
            expected_unknowns,
        )
    )
    if witness.fused_structure_item_count != expected_family_count:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_STRUCTURE_DEPTH_EXCEEDED"
        )
    resource_bounds = (
        successor_snapshot.relation_construction_authority.resource_bounds
    )
    if (
        len(expected_constructions)
        > resource_bounds.max_construction_instances
        or slot_count > resource_bounds.max_lexical_construction_slots
        or participation_count
        > resource_bounds.max_source_owner_participations
        or len(expected_relations)
        != resource_bounds.exact_effective_relations
        or len(expected_links) != resource_bounds.exact_semantic_links
        or len(expected_unknowns) != resource_bounds.exact_explicit_unknowns
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED"
        )
    parsed_material = step11_rc0029_experiment_parsed_witness_material(
        witness
    )
    result = Step11Rc0029ExperimentVerifiedSurfaceBinding(
        schema_version=STEP11_RC0029_EXPERIMENT_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256=artifact_sha256(parsed_material),
        base_witness_sha256=artifact_sha256(
            _witness_material(witness.base_witness)
        ),
        successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        experiment_catalog_sha256=catalog_sha256,
        natural_handle_binding_count=len(binding),
        construction_instance_binding_count=len(expected_constructions),
        construction_slot_binding_count=slot_count,
        participation_binding_count=participation_count,
        relation_binding_count=len(expected_relations),
        relation_endpoint_binding_count=endpoint_count,
        semantic_link_binding_count=len(expected_links),
        explicit_unknown_binding_count=len(expected_unknowns),
        reception_binding_count=len(expected_receptions),
        unique_solution_count=solution_count,
        semantic_coverage_authorized=False,
        issue_codes=(),
        hard_verified=True,
    )
    step11_rc0029_experiment_verified_binding_material(result)
    return result


def _step11_rc0029_expected_contract(
    successor_snapshot: Any,
    *,
    catalog: Mapping[str, Any],
) -> tuple[Any, ...]:
    try:
        owner_registry = _step11_rc0028_independent_owner_registry(
            successor_snapshot,
            maximum_owner_ordinal=_STEP11_RC0029_OWNER_MAX,
        )
        ordinal_by_id = {
            owner_id: ordinal
            for ordinal, (owner_id, _kind) in enumerate(owner_registry, 1)
        }
        construction_tokens = catalog["construction_surface_tokens"]
        role_tokens = catalog["role_position_surface_tokens"]
        synthetic_catalog = {
            "construction_atom_codes": {
                code: "construction_" + code for code in construction_tokens
            },
            "construction_surface_tokens": construction_tokens,
            "role_position_atom_codes": {
                key: "role_" + key.replace(":", "_") for key in role_tokens
            },
            "role_position_surface_tokens": role_tokens,
            "relation_surface_tokens": catalog["relation_surface_tokens"],
            "semantic_link_surface_tokens": catalog[
                "semantic_link_surface_tokens"
            ],
            "unknown_surface_tokens": catalog["unknown_surface_tokens"],
        }
        constructions, slot_count, participation_count = (
            _step11_rc0028_expected_constructions(
                successor_snapshot,
                owner_ordinal_by_id=ordinal_by_id,
                catalog=synthetic_catalog,
            )
        )
        relations, endpoint_count = _step11_rc0028_expected_relations(
            successor_snapshot,
            owner_ordinal_by_id=ordinal_by_id,
            catalog=synthetic_catalog,
        )
        links = _step11_rc0028_expected_semantic_links(
            successor_snapshot,
            owner_ordinal_by_id=ordinal_by_id,
            catalog=synthetic_catalog,
        )
        unknowns = _step11_rc0028_expected_explicit_unknowns(
            successor_snapshot,
            owner_ordinal_by_id=ordinal_by_id,
            catalog=synthetic_catalog,
        )
    except Step11Rc0028ExperimentInverseSurfaceError as exc:
        code = exc.code.replace("STEP11_RC0028_", "STEP11_RC0029_", 1)
        raise Step11Rc0029ExperimentInverseSurfaceError(code) from exc
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        ) from exc
    return (
        owner_registry,
        ordinal_by_id,
        constructions,
        relations,
        links,
        unknowns,
        slot_count,
        participation_count,
        endpoint_count,
    )


def _step11_rc0029_bind_constraint(
    binding: dict[int, int],
    reverse: dict[int, int],
    *,
    handle_index: int,
    owner_ordinal: int,
    code: str,
) -> None:
    if (
        binding.get(handle_index, owner_ordinal) != owner_ordinal
        or reverse.get(owner_ordinal, handle_index) != handle_index
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(code)
    binding[handle_index] = owner_ordinal
    reverse[owner_ordinal] = handle_index


def _step11_rc0029_allowed_qualifiers(
    *,
    constructions: Sequence[Any],
    relations: Sequence[Any],
    links: Sequence[Any],
    unknowns: Sequence[Any],
    catalog: Mapping[str, Any],
) -> dict[int, frozenset[str]]:
    values: dict[int, set[str]] = {}

    def add(ordinal: int, token: str) -> None:
        values.setdefault(ordinal, set()).add(token)

    role_tokens = catalog["role_position_surface_tokens"]
    owner_tokens = catalog["owner_role_surface_tokens"]
    for atom in constructions:
        for role in atom.role_owner_bindings:
            token = role_tokens.get(role.role_position_key)
            if type(token) is not str:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_CATALOG_TOKEN_MISMATCH"
                )
            add(role.owner_ordinal, token)
    for atom in relations:
        add(atom.from_owner_ordinal, owner_tokens["relation_from"])
        add(atom.to_owner_ordinal, owner_tokens["relation_to"])
    for atom in links:
        add(atom.from_owner_ordinal, owner_tokens["semantic_link_from"])
        add(atom.to_owner_ordinal, owner_tokens["semantic_link_to"])
    for atom in unknowns:
        for ordinal in atom.affected_owner_ordinals:
            add(ordinal, owner_tokens["explicit_unknown"])
    return {ordinal: frozenset(tokens) for ordinal, tokens in values.items()}


def step11_rc0029_experiment_verified_binding_material(
    value: Step11Rc0029ExperimentVerifiedSurfaceBinding,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029ExperimentVerifiedSurfaceBinding:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_VERIFIED_BINDING_TYPE_INVALID"
        )
    if (
        value.schema_version
        != STEP11_RC0029_EXPERIMENT_VERIFIED_BINDING_SCHEMA
        or any(
            type(item) is not str
            or _STEP11_RC0029_SHA256_RE.fullmatch(item) is None
            for item in (
                value.parsed_witness_sha256,
                value.base_witness_sha256,
                value.successor_snapshot_sha256,
                value.experiment_catalog_sha256,
            )
        )
        or any(
            type(item) is not int or type(item) is bool or item < 0
            for item in (
                value.natural_handle_binding_count,
                value.construction_instance_binding_count,
                value.construction_slot_binding_count,
                value.participation_binding_count,
                value.relation_binding_count,
                value.relation_endpoint_binding_count,
                value.semantic_link_binding_count,
                value.explicit_unknown_binding_count,
                value.reception_binding_count,
                value.unique_solution_count,
            )
        )
        or value.unique_solution_count != 1
        or value.semantic_coverage_authorized is not False
        or value.issue_codes != ()
        or value.hard_verified is not True
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_VERIFIED_BINDING_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "base_witness_sha256": value.base_witness_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "natural_handle_binding_count": value.natural_handle_binding_count,
        "construction_instance_binding_count": (
            value.construction_instance_binding_count
        ),
        "construction_slot_binding_count": value.construction_slot_binding_count,
        "participation_binding_count": value.participation_binding_count,
        "relation_binding_count": value.relation_binding_count,
        "relation_endpoint_binding_count": value.relation_endpoint_binding_count,
        "semantic_link_binding_count": value.semantic_link_binding_count,
        "explicit_unknown_binding_count": value.explicit_unknown_binding_count,
        "reception_binding_count": value.reception_binding_count,
        "unique_solution_count": value.unique_solution_count,
        "semantic_coverage_authorized": value.semantic_coverage_authorized,
        "issue_codes": list(value.issue_codes),
        "hard_verified": value.hard_verified,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def match_step11_rc0029_experiment_surface(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    successor_snapshot: Any,
) -> Step11Rc0029ExperimentVerifiedSurfaceBinding:
    """Bind the final-byte witness to source authority with one solution."""

    if type(witness) is not Step11Rc0029ExperimentParsedSurfaceWitness:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_TYPE_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0029_inverse_catalog()
    if witness.experiment_catalog_sha256 != catalog_sha256:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CATALOG_COMMITMENT_MISMATCH"
        )
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    expected_type = successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    if type(successor_snapshot) is not expected_type:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        )
    if (
        successor_snapshot.semantic_coverage_authorized is not False
        or successor_snapshot.experimental_only is not True
        or successor_snapshot.runtime_connected is not False
        or successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            successor_snapshot
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SOURCE_COMMITMENT_MISMATCH"
        )
    (
        owner_registry,
        ordinal_by_id,
        expected_constructions,
        expected_relations,
        expected_links,
        expected_unknowns,
        slot_count,
        participation_count,
        endpoint_count,
    ) = _step11_rc0029_expected_contract(
        successor_snapshot, catalog=catalog
    )
    if len(witness.construction_atoms) != len(expected_constructions):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH"
        )
    if len(witness.relation_atoms) != len(expected_relations):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RELATION_ENDPOINT_CARDINALITY_MISMATCH"
        )
    if len(witness.semantic_link_atoms) != len(expected_links):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SEMANTIC_LINK_BINDING_MISMATCH"
        )
    if len(witness.explicit_unknown_atoms) != len(expected_unknowns):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_EXPLICIT_UNKNOWN_MISSING"
        )

    binding: dict[int, int] = {}
    reverse: dict[int, int] = {}
    for parsed, expected in zip(
        witness.construction_atoms, expected_constructions
    ):
        expected_owner_sequence = tuple(
            dict.fromkeys(
                role.owner_ordinal
                for role in expected.role_owner_bindings
            )
        )
        parsed_handle_sequence = tuple(
            role.handle_index for role in parsed.role_owner_bindings
        )
        if (
            parsed.construction_code != expected.construction_code
            or len(parsed_handle_sequence) != len(expected_owner_sequence)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
            )
        for handle_index, owner_ordinal in zip(
            parsed_handle_sequence, expected_owner_sequence
        ):
            _step11_rc0029_bind_constraint(
                binding,
                reverse,
                handle_index=handle_index,
                owner_ordinal=owner_ordinal,
                code="STEP11_RC0029_PARTICIPATION_OWNER_MISMATCH",
            )
    for parsed, expected in zip(witness.relation_atoms, expected_relations):
        if parsed.effective_relation_type != expected.effective_relation_type:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_EFFECTIVE_RELATION_TYPE_MISMATCH"
            )
        if parsed.direction != expected.direction:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RELATION_DIRECTION_MISMATCH"
            )
        for handle_index, owner_ordinal in (
            (parsed.from_handle_index, expected.from_owner_ordinal),
            (parsed.to_handle_index, expected.to_owner_ordinal),
        ):
            _step11_rc0029_bind_constraint(
                binding,
                reverse,
                handle_index=handle_index,
                owner_ordinal=owner_ordinal,
                code="STEP11_RC0029_RELATION_ENDPOINT_MISMATCH",
            )
    for parsed, expected in zip(witness.semantic_link_atoms, expected_links):
        if parsed.relation_type != expected.relation_type:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_SEMANTIC_LINK_TYPE_MISMATCH"
            )
        if parsed.direction != expected.direction:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_SEMANTIC_LINK_DIRECTION_MISMATCH"
            )
        for handle_index, owner_ordinal in (
            (parsed.from_handle_index, expected.from_owner_ordinal),
            (parsed.to_handle_index, expected.to_owner_ordinal),
        ):
            _step11_rc0029_bind_constraint(
                binding,
                reverse,
                handle_index=handle_index,
                owner_ordinal=owner_ordinal,
                code="STEP11_RC0029_SEMANTIC_LINK_ENDPOINT_MISMATCH",
            )
    for parsed, expected in zip(
        witness.explicit_unknown_atoms, expected_unknowns
    ):
        if parsed.dimension != expected.dimension:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH"
            )
        if len(parsed.affected_handle_indices) != len(
            expected.affected_owner_ordinals
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
            )
        for handle_index, owner_ordinal in zip(
            parsed.affected_handle_indices,
            expected.affected_owner_ordinals,
        ):
            _step11_rc0029_bind_constraint(
                binding,
                reverse,
                handle_index=handle_index,
                owner_ordinal=owner_ordinal,
                code="STEP11_RC0029_EXPLICIT_UNKNOWN_OWNER_MISMATCH",
            )

    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in successor_snapshot.base_snapshot.nuclei
    }
    opportunities = tuple(successor_snapshot.base_snapshot.reception_opportunities)
    if len(witness.reception_bindings) != len(opportunities):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
        )
    used_opportunities: set[int] = set()
    for parsed in witness.reception_bindings:
        possible: list[tuple[int, tuple[int, ...]]] = []
        for opportunity_index, opportunity in enumerate(opportunities):
            if opportunity_index in used_opportunities:
                continue
            if str(opportunity.reception_act) != parsed.reception_act:
                continue
            try:
                owner_ordinals = tuple(
                    ordinal_by_id[actual_by_source[source_id]]
                    for source_id in dict.fromkeys(
                        (
                            *opportunity.target_nucleus_ids,
                            *opportunity.support_nucleus_ids,
                        )
                    )
                )
            except KeyError as exc:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_RECEPTION_SOURCE_MISMATCH"
                ) from exc
            if len(owner_ordinals) != len(parsed.antecedent_handle_indices):
                continue
            if any(
                handle_index in binding
                and binding[handle_index] != owner_ordinal
                for handle_index, owner_ordinal in zip(
                    parsed.antecedent_handle_indices, owner_ordinals
                )
            ):
                continue
            possible.append((opportunity_index, owner_ordinals))
        if len(possible) != 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH"
            )
        opportunity_index, owner_ordinals = possible[0]
        used_opportunities.add(opportunity_index)
        for handle_index, owner_ordinal in zip(
            parsed.antecedent_handle_indices, owner_ordinals
        ):
            _step11_rc0029_bind_constraint(
                binding,
                reverse,
                handle_index=handle_index,
                owner_ordinal=owner_ordinal,
                code="STEP11_RC0029_RECEPTION_ANTECEDENT_MISMATCH",
            )
    if len(used_opportunities) != len(opportunities):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_CARDINALITY_MISMATCH"
        )

    if set(binding) != {row.handle_index for row in witness.natural_handles}:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
        )
    allowed_qualifiers = _step11_rc0029_allowed_qualifiers(
        constructions=expected_constructions,
        relations=expected_relations,
        links=expected_links,
        unknowns=expected_unknowns,
        catalog=catalog,
    )
    reception_tokens = catalog["owner_role_surface_tokens"]
    for ordinal in binding.values():
        allowed_qualifiers.setdefault(ordinal, frozenset())
    for handle in witness.natural_handles:
        owner_ordinal = binding[handle.handle_index]
        allowed = set(allowed_qualifiers.get(owner_ordinal, ())) | {
            reception_tokens["reception_target"],
            reception_tokens["reception_antecedent"],
            reception_tokens["reception_support"],
        }
        if not set(handle.qualifier_tokens) <= allowed:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_SOURCE_MISMATCH"
            )

    resource_bounds = successor_snapshot.relation_construction_authority.resource_bounds
    if (
        len(expected_constructions) > resource_bounds.max_construction_instances
        or slot_count > resource_bounds.max_lexical_construction_slots
        or participation_count > resource_bounds.max_source_owner_participations
        or len(expected_relations) != resource_bounds.exact_effective_relations
        or len(expected_links) != resource_bounds.exact_semantic_links
        or len(expected_unknowns) != resource_bounds.exact_explicit_unknowns
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED"
        )
    material = step11_rc0029_experiment_parsed_witness_material(witness)
    result = Step11Rc0029ExperimentVerifiedSurfaceBinding(
        schema_version=STEP11_RC0029_EXPERIMENT_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256=artifact_sha256(material),
        base_witness_sha256=artifact_sha256(_witness_material(witness.base_witness)),
        successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
        experiment_catalog_sha256=catalog_sha256,
        natural_handle_binding_count=len(binding),
        construction_instance_binding_count=len(expected_constructions),
        construction_slot_binding_count=slot_count,
        participation_binding_count=participation_count,
        relation_binding_count=len(expected_relations),
        relation_endpoint_binding_count=endpoint_count,
        semantic_link_binding_count=len(expected_links),
        explicit_unknown_binding_count=len(expected_unknowns),
        reception_binding_count=len(witness.reception_bindings),
        unique_solution_count=1,
        semantic_coverage_authorized=False,
        issue_codes=(),
        hard_verified=True,
    )
    step11_rc0029_experiment_verified_binding_material(result)
    return result


__all__ += [
    "STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA",
    "STEP11_RC0029_EXPERIMENT_VERIFIED_BINDING_SCHEMA",
    "Step11Rc0029ExperimentInverseSurfaceError",
    "Step11Rc0029ExperimentParsedConstructionAtom",
    "Step11Rc0029ExperimentParsedConstructionRoleOwner",
    "Step11Rc0029ExperimentParsedExplicitUnknownAtom",
    "Step11Rc0029ExperimentParsedNaturalHandle",
    "Step11Rc0029ExperimentParsedReceptionBinding",
    "Step11Rc0029ExperimentParsedRelationAtom",
    "Step11Rc0029ExperimentParsedSemanticLinkAtom",
    "Step11Rc0029ExperimentParsedSurfaceWitness",
    "Step11Rc0029ExperimentVerifiedSurfaceBinding",
    "match_step11_rc0029_experiment_surface",
    "parse_step11_rc0029_experiment_surface",
    "step11_rc0029_experiment_parsed_witness_material",
    "step11_rc0029_experiment_verified_binding_material",
]


# ---------------------------------------------------------------------------
# rc0029 final compact-family grammar synchronization
#
# The first append above was the RED consumer scaffold.  These final
# definitions intentionally shadow only rc0029 names after the compact
# catalog was frozen.  The default/rc0028 prefixes stay byte-identical.  The
# parser still accepts final bytes plus the declarative catalog only.


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedNaturalHandle:
    handle_index: int
    handle_text: str
    grounded_phrase_text: str
    semantic_head_kind: str
    semantic_head_text: str
    qualifier_tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedReceptionBinding:
    reception_line_ordinal: int
    reception_act: str
    reception_scope: str
    target_handle_indices: tuple[int, ...]
    supporting_handle_indices: tuple[int, ...]
    additional_clause: bool

    @property
    def antecedent_handle_indices(self) -> tuple[int, ...]:
        """Compatibility name: an opportunity target is the antecedent."""

        return self.target_handle_indices


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentParsedSurfaceWitness:
    schema_version: str
    body_sha256: str
    experiment_catalog_sha256: str
    base_witness: Step11ParsedSurfaceWitness
    natural_handles: tuple[Step11Rc0029ExperimentParsedNaturalHandle, ...]
    construction_atoms: tuple[
        Step11Rc0029ExperimentParsedConstructionAtom, ...
    ]
    relation_atoms: tuple[Step11Rc0029ExperimentParsedRelationAtom, ...]
    semantic_link_atoms: tuple[
        Step11Rc0029ExperimentParsedSemanticLinkAtom, ...
    ]
    explicit_unknown_atoms: tuple[
        Step11Rc0029ExperimentParsedExplicitUnknownAtom, ...
    ]
    reception_bindings: tuple[
        Step11Rc0029ExperimentParsedReceptionBinding, ...
    ]
    fused_structure_item_count: int
    fused_structure_group_count: int
    added_observation_line_count: int
    body_free_export_allowed: bool = False


def _step11_rc0029_final_handle_material(
    value: Step11Rc0029ExperimentParsedNaturalHandle,
) -> dict[str, Any]:
    return {
        "handle_index": value.handle_index,
        "semantic_head_kind": value.semantic_head_kind,
        "semantic_head_text": value.semantic_head_text,
        "qualifier_tokens": list(value.qualifier_tokens),
    }


def step11_rc0029_experiment_parsed_witness_material(
    value: Step11Rc0029ExperimentParsedSurfaceWitness,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0029ExperimentParsedSurfaceWitness:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_TYPE_INVALID"
        )
    family_count = sum(
        bool(rows)
        for rows in (
            value.construction_atoms,
            value.relation_atoms,
            value.semantic_link_atoms,
            value.explicit_unknown_atoms,
        )
    )
    if (
        value.schema_version
        != STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA
        or _STEP11_RC0029_SHA256_RE.fullmatch(value.body_sha256) is None
        or _STEP11_RC0029_SHA256_RE.fullmatch(
            value.experiment_catalog_sha256
        )
        is None
        or type(value.base_witness) is not Step11ParsedSurfaceWitness
        or value.added_observation_line_count != 0
        or value.body_free_export_allowed is not False
        or value.fused_structure_item_count != family_count
        or type(value.fused_structure_group_count) is not int
        or not 1 <= value.fused_structure_group_count <= len(
            value.natural_handles
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSED_WITNESS_INVALID"
        )
    handle_indices = tuple(row.handle_index for row in value.natural_handles)
    if (
        handle_indices != tuple(range(1, len(handle_indices) + 1))
        or len(handle_indices) > _STEP11_RC0029_OWNER_MAX
        or len({row.handle_text for row in value.natural_handles})
        != len(value.natural_handles)
        or any(
            not row.semantic_head_kind
            or not row.semantic_head_text
            or row.grounded_phrase_text != row.semantic_head_text
            or len(row.qualifier_tokens) > 1
            for row in value.natural_handles
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_SET_INVALID"
        )

    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "base_witness": _witness_material(value.base_witness),
        "natural_handles": [
            _step11_rc0029_final_handle_material(row)
            for row in value.natural_handles
        ],
        "construction_atoms": [
            {
                "ordinal": row.ordinal,
                "construction_code": row.construction_code,
                "handle_indices": [
                    binding.handle_index
                    for binding in row.role_owner_bindings
                ],
                "role_position_keys": [
                    binding.role_position_key
                    for binding in row.role_owner_bindings
                ],
            }
            for row in value.construction_atoms
        ],
        "relation_atoms": [
            {
                "ordinal": row.ordinal,
                "effective_relation_type": row.effective_relation_type,
                "from_handle_index": row.from_handle_index,
                "to_handle_index": row.to_handle_index,
                "direction": row.direction,
                "relation_surface_key": row.relation_surface_key,
            }
            for row in value.relation_atoms
        ],
        "semantic_link_atoms": [
            {
                "ordinal": row.ordinal,
                "relation_type": row.relation_type,
                "from_handle_index": row.from_handle_index,
                "to_handle_index": row.to_handle_index,
                "direction": row.direction,
                "semantic_link_surface_key": row.semantic_link_surface_key,
            }
            for row in value.semantic_link_atoms
        ],
        "explicit_unknown_atoms": [
            {
                "ordinal": row.ordinal,
                "dimension": row.dimension,
                "affected_handle_indices": list(
                    row.affected_handle_indices
                ),
            }
            for row in value.explicit_unknown_atoms
        ],
        "reception_bindings": [
            {
                "reception_line_ordinal": row.reception_line_ordinal,
                "reception_act": row.reception_act,
                "reception_scope": row.reception_scope,
                "target_handle_indices": list(row.target_handle_indices),
                "supporting_handle_indices": list(
                    row.supporting_handle_indices
                ),
                "additional_clause": row.additional_clause,
            }
            for row in value.reception_bindings
        ],
        "fused_structure_item_count": value.fused_structure_item_count,
        "fused_structure_group_count": value.fused_structure_group_count,
        "added_observation_line_count": value.added_observation_line_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _step11_rc0029_final_single_handle_prefix(
    value: str,
    *,
    morphology: Mapping[str, str],
) -> tuple[str, str]:
    handle_open = morphology["handle_open"]
    handle_close = morphology["handle_close"]
    if not value.startswith(handle_open):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
        )
    end = value.find(handle_close, len(handle_open))
    if end < 0:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
        )
    literal = value[: end + len(handle_close)]
    handles = _step11_rc0029_split_handle_sequence(
        literal,
        joiner="\x00",
        morphology=morphology,
    )
    if len(handles) != 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_PARSE_FAILED"
        )
    return handles[0], value[len(literal) :]


def _step11_rc0029_final_ordered_token_keys(
    value: str,
    *,
    token_by_key: Mapping[str, str],
    joiner: str,
    code: str,
) -> tuple[str, ...]:
    rows = tuple(token_by_key.items())
    if not rows or len({token for _key, token in rows}) != len(rows):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CATALOG_TOKEN_MISMATCH"
        )
    memo: dict[tuple[int, int], tuple[tuple[str, ...], ...]] = {}

    def solve(position: int, minimum_rank: int) -> tuple[tuple[str, ...], ...]:
        memo_key = (position, minimum_rank)
        if memo_key in memo:
            return memo[memo_key]
        matches: list[tuple[str, ...]] = []
        for rank in range(minimum_rank, len(rows)):
            key, token = rows[rank]
            if not value.startswith(token, position):
                continue
            end = position + len(token)
            if end == len(value):
                matches.append((key,))
            elif value.startswith(joiner, end):
                for tail in solve(end + len(joiner), rank):
                    matches.append((key, *tail))
                    if len(matches) > 1:
                        break
            if len(matches) > 1:
                break
        memo[memo_key] = tuple(matches[:2])
        return memo[memo_key]

    solutions = solve(0, 0)
    if len(solutions) != 1 or not solutions[0]:
        raise Step11Rc0029ExperimentInverseSurfaceError(code)
    return solutions[0]


def _step11_rc0029_final_parse_construction_family(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    register_handle: Any,
) -> tuple[Step11Rc0029ExperimentParsedConstructionAtom, ...]:
    suffix = morphology["construction_suffix"]
    if not value.endswith(suffix):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    core = value[: -len(suffix)]
    segments = core.split(morphology["construction_owner_group_join"])
    result: list[Step11Rc0029ExperimentParsedConstructionAtom] = []
    for segment in segments:
        handle, remainder = _step11_rc0029_final_single_handle_prefix(
            segment, morphology=morphology
        )
        link = morphology["construction_handle_link"]
        if not remainder.startswith(link):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        token_keys = _step11_rc0029_final_ordered_token_keys(
            remainder[len(link) :],
            token_by_key=catalog["construction_surface_tokens"],
            joiner=morphology["construction_token_join"],
            code="STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED",
        )
        handle_index = register_handle(handle)
        for construction_code in token_keys:
            layout = catalog["construction_role_layouts"].get(
                construction_code
            )
            if (
                type(layout) is not list
                or not layout
                or any(
                    type(role_key) is not str
                    or role_key
                    not in catalog["role_position_surface_tokens"]
                    or role_key.count(":") != 1
                    for role_key in layout
                )
            ):
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            result.append(
                Step11Rc0029ExperimentParsedConstructionAtom(
                    ordinal=len(result) + 1,
                    construction_code=construction_code,
                    role_owner_bindings=tuple(
                        Step11Rc0029ExperimentParsedConstructionRoleOwner(
                            handle_index=handle_index,
                            lexical_role_kind=role_key.split(":", 1)[0],
                            construction_position=role_key.split(":", 1)[1],
                            role_position_key=role_key,
                        )
                        for role_key in layout
                    ),
                )
            )
    if not result:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    return tuple(result)


def _step11_rc0029_final_relation_segment(
    value: str,
    *,
    morphology: Mapping[str, str],
    relation_by_token: Mapping[str, str],
    register_handle: Any,
    from_handle_text: str | None = None,
) -> tuple[str, str, str, str]:
    if from_handle_text is None:
        from_handle_text, remainder = (
            _step11_rc0029_final_single_handle_prefix(
                value, morphology=morphology
            )
        )
        marker = morphology["relation_from"]
        if not remainder.startswith(marker):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        remainder = remainder[len(marker) :]
    else:
        remainder = value
    to_handle_text, remainder = _step11_rc0029_final_single_handle_prefix(
        remainder, morphology=morphology
    )
    marker = morphology["relation_to"]
    if not remainder.startswith(marker):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    token = remainder[len(marker) :]
    surface_key = relation_by_token.get(token)
    if surface_key is None:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    relation_type, direction = surface_key.rsplit(":", 1)
    register_handle(from_handle_text)
    register_handle(to_handle_text)
    return from_handle_text, to_handle_text, relation_type, direction


def _step11_rc0029_final_parse_relation_family(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    register_handle: Any,
) -> tuple[Step11Rc0029ExperimentParsedRelationAtom, ...]:
    suffix = morphology["relation_suffix"]
    if not value.endswith(suffix):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    relation_by_token = _step11_rc0029_inverse_map(
        catalog["relation_surface_tokens"],
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    result: list[Step11Rc0029ExperimentParsedRelationAtom] = []
    chains = value[: -len(suffix)].split(
        morphology["relation_chain_join"]
    )
    for chain in chains:
        steps = chain.split(morphology["relation_chain_step"])
        previous_to: str | None = None
        for step_index, step in enumerate(steps):
            (
                from_handle,
                to_handle,
                relation_type,
                direction,
            ) = _step11_rc0029_final_relation_segment(
                step,
                morphology=morphology,
                relation_by_token=relation_by_token,
                register_handle=register_handle,
                from_handle_text=(previous_to if step_index else None),
            )
            surface_key = relation_type + ":" + direction
            result.append(
                Step11Rc0029ExperimentParsedRelationAtom(
                    ordinal=len(result) + 1,
                    effective_relation_type=relation_type,
                    from_handle_index=register_handle(from_handle),
                    to_handle_index=register_handle(to_handle),
                    direction=direction,
                    relation_surface_key=surface_key,
                )
            )
            previous_to = to_handle
    if not result:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    return tuple(result)


def _step11_rc0029_final_parse_link_family(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    register_handle: Any,
) -> tuple[Step11Rc0029ExperimentParsedSemanticLinkAtom, ...]:
    suffix = morphology["link_suffix"]
    if not value.endswith(suffix):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    link_by_token = _step11_rc0029_inverse_map(
        catalog["semantic_link_surface_tokens"],
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    result: list[Step11Rc0029ExperimentParsedSemanticLinkAtom] = []
    for item in value[: -len(suffix)].split(morphology["link_item_join"]):
        from_handle, remainder = _step11_rc0029_final_single_handle_prefix(
            item, morphology=morphology
        )
        joiner = morphology["link_handle_join"]
        if not remainder.startswith(joiner):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        to_handle, remainder = _step11_rc0029_final_single_handle_prefix(
            remainder[len(joiner) :], morphology=morphology
        )
        between = morphology["link_between"]
        if not remainder.startswith(between):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        surface_key = link_by_token.get(remainder[len(between) :])
        if surface_key is None:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        relation_type, direction = surface_key.rsplit(":", 1)
        result.append(
            Step11Rc0029ExperimentParsedSemanticLinkAtom(
                ordinal=len(result) + 1,
                relation_type=relation_type,
                from_handle_index=register_handle(from_handle),
                to_handle_index=register_handle(to_handle),
                direction=direction,
                semantic_link_surface_key=surface_key,
            )
        )
    if not result:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    return tuple(result)


def _step11_rc0029_final_parse_unknown_family(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
    register_handle: Any,
) -> tuple[Step11Rc0029ExperimentParsedExplicitUnknownAtom, ...]:
    suffix = morphology["unknown_suffix"]
    if not value.endswith(suffix):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    unknown_by_token = _step11_rc0029_inverse_map(
        catalog["unknown_surface_tokens"],
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    result: list[Step11Rc0029ExperimentParsedExplicitUnknownAtom] = []
    for item in value[: -len(suffix)].split(
        morphology["unknown_item_join"]
    ):
        between = morphology["unknown_between"]
        if item.count(between) != 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        owner_text, token = item.split(between, 1)
        dimension = unknown_by_token.get(token)
        if dimension is None:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        handles = _step11_rc0029_split_handle_sequence(
            owner_text,
            joiner=morphology["unknown_owner_join"],
            morphology=morphology,
        )
        if not handles or len(handles) != len(set(handles)):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        result.append(
            Step11Rc0029ExperimentParsedExplicitUnknownAtom(
                ordinal=len(result) + 1,
                dimension=dimension,
                affected_handle_indices=tuple(
                    register_handle(handle) for handle in handles
                ),
            )
        )
    if not result:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    return tuple(result)


def _step11_rc0029_final_reception_prefix_candidates(
    value: str,
    *,
    morphology: Mapping[str, str],
) -> tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...]:
    target_suffix = morphology["reception_target_suffix"]
    support_suffix = morphology["reception_support_suffix"]
    candidates: list[tuple[tuple[str, ...], tuple[str, ...], str]] = []
    for target_end in range(len(value)):
        if not value.startswith(target_suffix, target_end):
            continue
        visible_prefix = value[:target_end]
        remainder = value[target_end + len(target_suffix) :]
        support_options: list[tuple[tuple[str, ...], str]] = [((), visible_prefix)]
        for support_end in range(len(visible_prefix)):
            if not visible_prefix.startswith(support_suffix, support_end):
                continue
            try:
                supports = _step11_rc0029_split_handle_sequence(
                    visible_prefix[:support_end],
                    joiner=morphology["reception_support_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            support_options.append(
                (
                    supports,
                    visible_prefix[support_end + len(support_suffix) :],
                )
            )
        for supports, target_text in support_options:
            try:
                targets = _step11_rc0029_split_handle_sequence(
                    target_text,
                    joiner=morphology["reception_target_join"],
                    morphology=morphology,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            if (
                targets
                and len(targets) == len(set(targets))
                and len(supports) == len(set(supports))
                and not (set(targets) & set(supports))
                and remainder
            ):
                candidates.append((supports, targets, remainder))
    return tuple(dict.fromkeys(candidates))


def _step11_rc0029_final_additional_clause(
    value: str,
    *,
    catalog: Mapping[str, Any],
    morphology: Mapping[str, str],
) -> tuple[tuple[str, ...], tuple[str, ...], str] | None:
    act_by_token = _step11_rc0029_inverse_map(
        catalog["reception_act_surface_tokens"],
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    matches: list[tuple[tuple[str, ...], tuple[str, ...], str]] = []
    for supports, targets, remainder in (
        _step11_rc0029_final_reception_prefix_candidates(
            value, morphology=morphology
        )
    ):
        act = act_by_token.get(remainder)
        if act is not None:
            matches.append((supports, targets, act))
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_AMBIGUOUS"
        )
    return matches[0]


def _step11_rc0029_final_component_count(
    *,
    constructions: Sequence[Step11Rc0029ExperimentParsedConstructionAtom],
    relations: Sequence[Step11Rc0029ExperimentParsedRelationAtom],
    links: Sequence[Step11Rc0029ExperimentParsedSemanticLinkAtom],
    unknowns: Sequence[Step11Rc0029ExperimentParsedExplicitUnknownAtom],
    receptions: Sequence[Step11Rc0029ExperimentParsedReceptionBinding],
) -> int:
    parent: dict[int, int] = {}

    def find(value: int) -> int:
        parent.setdefault(value, value)
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def add(values: Sequence[int]) -> None:
        unique = tuple(dict.fromkeys(values))
        if not unique:
            return
        anchor = find(unique[0])
        for value in unique[1:]:
            other = find(value)
            if anchor != other:
                parent[other] = anchor

    for row in constructions:
        add(tuple(item.handle_index for item in row.role_owner_bindings))
    for row in relations:
        add((row.from_handle_index, row.to_handle_index))
    for row in links:
        add((row.from_handle_index, row.to_handle_index))
    for row in unknowns:
        add(row.affected_handle_indices)
    for row in receptions:
        add((*row.target_handle_indices, *row.supporting_handle_indices))
    return len({find(value) for value in parent})


def parse_step11_rc0029_experiment_surface(
    body: bytes,
    *forward_metadata: Any,
    **forward_metadata_by_name: Any,
) -> Step11Rc0029ExperimentParsedSurfaceWitness:
    """Parse the frozen compact-family grammar from canonical final bytes."""

    if forward_metadata or forward_metadata_by_name:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_FORWARD_METADATA_FORBIDDEN"
        )
    if (
        type(body) is not bytes
        or not body
        or len(body) > _STEP11_RC0029_BODY_BYTE_MAX
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_BODY_INVALID"
        )
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_UTF8_INVALID"
        ) from exc
    if (
        unicodedata.normalize("NFC", text) != text
        or "\r" in text
        or text.endswith("\n")
        or text.startswith("\ufeff")
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_PARSER_CANONICAL_TEXT_INVALID"
        )
    catalog, catalog_sha256 = _step11_rc0029_inverse_catalog()
    morphology = catalog.get("morphology")
    required_morphology = {
        "handle_open",
        "handle_close",
        "structural_prefix",
        "family_join",
        "construction_handle_link",
        "construction_token_join",
        "construction_owner_group_join",
        "construction_suffix",
        "relation_from",
        "relation_to",
        "relation_chain_step",
        "relation_chain_join",
        "relation_suffix",
        "link_handle_join",
        "link_between",
        "link_item_join",
        "link_suffix",
        "unknown_owner_join",
        "unknown_between",
        "unknown_item_join",
        "unknown_suffix",
        "observation_insert",
        "reception_target_join",
        "reception_target_suffix",
        "reception_support_join",
        "reception_support_suffix",
        "reception_additional_join",
    }
    if (
        type(morphology) is not dict
        or not required_morphology <= set(morphology)
        or any(
            type(morphology[key]) is not str or not morphology[key]
            for key in required_morphology
        )
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_CATALOG_TOKEN_MISMATCH"
        )
    labels = STEP11_SURFACE_CATALOG.get("labels")
    observation_label = labels.get("observation") if type(labels) is dict else None
    reception_label = labels.get("reception") if type(labels) is dict else None
    if type(observation_label) is not str or type(reception_label) is not str:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        )
    prefix = observation_label + "\n"
    separator = "\n\n" + reception_label + "\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        )
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_SURFACE_LAYOUT_INVALID"
        )

    handle_texts: list[str] = []
    handle_index_by_text: dict[str, int] = {}

    def register_handle(value: str) -> int:
        # Reuse the closed quoted-handle validator on every occurrence.
        _step11_rc0029_split_handle_sequence(
            morphology["handle_open"] + value + morphology["handle_close"],
            joiner="\x00",
            morphology=morphology,
        )
        if value not in handle_index_by_text:
            if len(handle_texts) >= _STEP11_RC0029_OWNER_MAX:
                raise Step11Rc0029ExperimentInverseSurfaceError(
                    "STEP11_RC0029_RESOURCE_BOUND_EXCEEDED"
                )
            handle_texts.append(value)
            handle_index_by_text[value] = len(handle_texts)
        return handle_index_by_text[value]

    structure_marker = (
        morphology["observation_insert"] + morphology["structural_prefix"]
    )
    tail = observation_lines[-1]
    marker_count = tail.count(structure_marker)
    if marker_count > 1 or not tail.endswith("。"):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
        )
    if marker_count == 1:
        base_tail, payload = tail.split(structure_marker, 1)
        payload = payload[:-1]
        if not base_tail or not payload:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
        observation_lines[-1] = (
            base_tail + morphology["observation_insert"]
        )
        family_values = payload.split(morphology["family_join"])
        if (
            not 1 <= len(family_values) <= 4
            or any(not row for row in family_values)
        ):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_PARSE_FAILED"
            )
    else:
        # A reception-only successor has no C/R/L/U family to append to the
        # observation.  It is still recoverable from the visibly bound
        # reception prefix below, and the independent matcher requires the
        # exact zero-family source contract.  Any omitted family for a source
        # that does own C/R/L/U atoms therefore still fails closed there.
        family_values = []
    constructions: tuple[Step11Rc0029ExperimentParsedConstructionAtom, ...] = ()
    relations: tuple[Step11Rc0029ExperimentParsedRelationAtom, ...] = ()
    links: tuple[Step11Rc0029ExperimentParsedSemanticLinkAtom, ...] = ()
    unknowns: tuple[Step11Rc0029ExperimentParsedExplicitUnknownAtom, ...] = ()
    current_rank = -1
    for family_value in family_values:
        attempts: list[tuple[int, Any]] = []
        for rank, parser in enumerate(
            (
                _step11_rc0029_final_parse_construction_family,
                _step11_rc0029_final_parse_relation_family,
                _step11_rc0029_final_parse_link_family,
                _step11_rc0029_final_parse_unknown_family,
            )
        ):
            try:
                parsed_rows = parser(
                    family_value,
                    catalog=catalog,
                    morphology=morphology,
                    register_handle=register_handle,
                )
            except Step11Rc0029ExperimentInverseSurfaceError:
                continue
            attempts.append((rank, parsed_rows))
        if len(attempts) != 1 or attempts[0][0] <= current_rank:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_FUSED_STRUCTURE_ORDER_INVALID"
            )
        current_rank, parsed_rows = attempts[0]
        if current_rank == 0:
            constructions = parsed_rows
        elif current_rank == 1:
            relations = parsed_rows
        elif current_rank == 2:
            links = parsed_rows
        else:
            unknowns = parsed_rows

    # Strip explicit additional opportunity clauses first, then the optional
    # mapped prefix.  Every base reception line must be visibly bound.
    reconstructed_reception: list[str] = []
    line_rows: list[
        tuple[
            tuple[tuple[str, ...], tuple[str, ...]] | None,
            tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...],
        ]
    ] = []
    add_join = morphology["reception_additional_join"]
    for line in reception_lines:
        if not line.endswith("。"):
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_SURFACE_INVALID"
            )
        without_period = line[:-1]
        decompositions: list[
            tuple[
                str,
                tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...],
            ]
        ] = []
        for position in range(len(without_period)):
            if not without_period.startswith(add_join, position):
                continue
            parts = without_period[position + len(add_join) :].split(add_join)
            parsed_parts: list[
                tuple[tuple[str, ...], tuple[str, ...], str]
            ] = []
            for part in parts:
                parsed_part = _step11_rc0029_final_additional_clause(
                    part,
                    catalog=catalog,
                    morphology=morphology,
                )
                if parsed_part is None:
                    break
                parsed_parts.append(parsed_part)
            else:
                decompositions.append(
                    (without_period[:position] + "。", tuple(parsed_parts))
                )
        if len(decompositions) > 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_BINDING_AMBIGUOUS"
            )
        if decompositions:
            mapped_source, additional_rows = decompositions[0]
        else:
            mapped_source, additional_rows = line, ()
        mapped_candidates = (
            _step11_rc0029_final_reception_prefix_candidates(
                mapped_source, morphology=morphology
            )
        )
        mapped_candidates = tuple(
            (supports, targets, remainder)
            for supports, targets, remainder in mapped_candidates
            if remainder.endswith("。")
        )
        if len(mapped_candidates) > 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_BINDING_AMBIGUOUS"
            )
        mapped: tuple[tuple[str, ...], tuple[str, ...]] | None = None
        if mapped_candidates:
            supports, targets, base_line = mapped_candidates[0]
            mapped = (supports, targets)
        else:
            base_line = mapped_source
        if mapped is None and not additional_rows:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_RECEPTION_ANTECEDENT_MISSING"
            )
        reconstructed_reception.append(base_line)
        line_rows.append((mapped, additional_rows))

    base_text = (
        prefix
        + "\n".join(observation_lines)
        + separator
        + "\n".join(reconstructed_reception)
    )
    base_body = base_text.encode("utf-8", errors="strict")
    try:
        parsed_base = parse_step11_natural_surface(base_body)
    except Step11InverseSurfaceError as exc:
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_PARSE_FAILED"
        ) from exc
    base_reception_atoms = tuple(
        atom
        for atom in parsed_base.atoms
        if atom.section_role == "reception" and atom.reception_act is not None
    )
    if len(base_reception_atoms) != len(line_rows):
        raise Step11Rc0029ExperimentInverseSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_CARDINALITY_MISMATCH"
        )

    parsed_receptions: list[Step11Rc0029ExperimentParsedReceptionBinding] = []
    references_by_atom: dict[str, tuple[Step11EndpointReference, ...]] = {}
    for line_ordinal, (atom, (mapped, additional_rows)) in enumerate(
        zip(base_reception_atoms, line_rows), start=1
    ):
        line_target_indices: list[int] = []
        if mapped is not None:
            supports, targets = mapped
            target_indices = tuple(register_handle(row) for row in targets)
            support_indices = tuple(register_handle(row) for row in supports)
            line_target_indices.extend(target_indices)
            parsed_receptions.append(
                Step11Rc0029ExperimentParsedReceptionBinding(
                    reception_line_ordinal=line_ordinal,
                    reception_act=str(atom.reception_act),
                    reception_scope=str(atom.reception_scope),
                    target_handle_indices=target_indices,
                    supporting_handle_indices=support_indices,
                    additional_clause=False,
                )
            )
        for supports, targets, act in additional_rows:
            target_indices = tuple(register_handle(row) for row in targets)
            support_indices = tuple(register_handle(row) for row in supports)
            line_target_indices.extend(target_indices)
            parsed_receptions.append(
                Step11Rc0029ExperimentParsedReceptionBinding(
                    reception_line_ordinal=line_ordinal,
                    reception_act=act,
                    reception_scope=str(atom.reception_scope),
                    target_handle_indices=target_indices,
                    supporting_handle_indices=support_indices,
                    additional_clause=True,
                )
            )
        endpoint_role = (
            atom.reception_scope
            if atom.reception_scope in {"thought", "action"}
            else "thought"
        )
        references_by_atom[atom.atom_id] = tuple(
            Step11EndpointReference(
                reference_ordinal=index,
                endpoint_role=str(endpoint_role),
            )
            for index in dict.fromkeys(line_target_indices)
        )
    from dataclasses import replace as _step11_rc0029_final_replace

    base_witness = _step11_rc0029_final_replace(
        parsed_base,
        atoms=tuple(
            _step11_rc0029_final_replace(
                atom,
                reception_antecedent_references=references_by_atom[
                    atom.atom_id
                ],
            )
            if atom.atom_id in references_by_atom
            else atom
            for atom in parsed_base.atoms
        ),
    )

    head_by_token = _step11_rc0029_inverse_map(
        catalog["owner_kind_surface_tokens"],
        code="STEP11_RC0029_CATALOG_TOKEN_MISMATCH",
    )
    qualifier_tokens = tuple(
        dict.fromkeys(
            (
                *catalog["role_position_surface_tokens"].values(),
                *catalog["owner_role_surface_tokens"].values(),
            )
        )
    )
    natural_handles: list[Step11Rc0029ExperimentParsedNaturalHandle] = []
    for handle_index, handle_text in enumerate(handle_texts, start=1):
        decompositions: list[tuple[str, str, tuple[str, ...]]] = []
        for head_text, head_kind in head_by_token.items():
            if not handle_text.endswith(head_text):
                continue
            prefix_text = handle_text[: -len(head_text)]
            if not prefix_text:
                decompositions.append((head_kind, head_text, ()))
            elif prefix_text in qualifier_tokens:
                decompositions.append(
                    (head_kind, head_text, (prefix_text,))
                )
        if len(decompositions) != 1:
            raise Step11Rc0029ExperimentInverseSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_AMBIGUOUS"
            )
        head_kind, head_text, qualifiers = decompositions[0]
        natural_handles.append(
            Step11Rc0029ExperimentParsedNaturalHandle(
                handle_index=handle_index,
                handle_text=handle_text,
                grounded_phrase_text=head_text,
                semantic_head_kind=head_kind,
                semantic_head_text=head_text,
                qualifier_tokens=qualifiers,
            )
        )
    component_count = _step11_rc0029_final_component_count(
        constructions=constructions,
        relations=relations,
        links=links,
        unknowns=unknowns,
        receptions=parsed_receptions,
    )
    witness = Step11Rc0029ExperimentParsedSurfaceWitness(
        schema_version=STEP11_RC0029_EXPERIMENT_PARSED_WITNESS_SCHEMA,
        body_sha256=hashlib.sha256(body).hexdigest(),
        experiment_catalog_sha256=catalog_sha256,
        base_witness=base_witness,
        natural_handles=tuple(natural_handles),
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_bindings=tuple(parsed_receptions),
        fused_structure_item_count=len(family_values),
        fused_structure_group_count=component_count,
        added_observation_line_count=0,
    )
    step11_rc0029_experiment_parsed_witness_material(witness)
    return witness


def match_step11_rc0029_experiment_surface(
    witness: Step11Rc0029ExperimentParsedSurfaceWitness,
    *,
    successor_snapshot: Any,
) -> Step11Rc0029ExperimentVerifiedSurfaceBinding:
    """Active compact-family matcher; no source-order correspondence."""

    return _step11_rc0029_final_match_surface(
        witness, successor_snapshot=successor_snapshot
    )


# ---------------------------------------------------------------------------
# rc0030 experiment-only body inverse (append-only P3 owner)
# ---------------------------------------------------------------------------

import weakref

STEP11_RC0030_EXPERIMENT_PARSED_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_parsed_witness.v1"
)
STEP11_RC0030_EXPERIMENT_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_verified_binding.v1"
)
STEP11_RC0030_VERIFIED_BASE_REUSE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_verified_base_reuse.v1"
)
STEP11_RC0030_BASE_BODY_PARSED_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_base_body_parsed_witness.v1"
)

_STEP11_RC0030_BODY_BYTE_MAX = 1_000_000
_STEP11_RC0030_DECOMPOSITION_LOCUS_MAX = 38
_STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX = 76
_STEP11_RC0030_STORED_DECOMPOSITION_MAX = 2
_STEP11_RC0030_BODY_SCAN_PASS_MAX = 2
_STEP11_RC0030_OWNER_MAX = 24
_STEP11_RC0030_OWNER_COMPARISON_MAX = 576
_STEP11_RC0030_RECEPTION_MOVE_MAX = 3
_STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX = 2
_STEP11_RC0030_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Step11Rc0030ExperimentInverseSurfaceError(ValueError):
    """Fail closed without including source or final-body text."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"STEP11_RC0030_[A-Z0-9_]{2,95}", code) is None
        ):
            code = "STEP11_RC0030_INVERSE_SURFACE_REJECTED"
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ParsedSemanticAtom:
    atom_id: str
    semantic_family: str
    semantic_key: str
    direction: str
    owner_expressions: tuple[str, ...]
    sentence_group_ordinal: int
    grammatical_chunk_ordinal: int
    pack_ordinal: int
    item_ordinal: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ParsedReceptionBinding:
    binding_id: str
    reception_line_ordinal: int
    move_ordinal: int
    reception_act: str
    target_expression: str
    supporting_expression: str | None
    target_expression_sha256: str
    supporting_expression_sha256: str | None


@dataclass(frozen=True, slots=True, repr=False, weakref_slot=True)
class Step11Rc0030ExperimentParsedSurfaceWitness:
    schema_version: str
    body_sha256: str
    experiment_catalog_sha256: str
    semantic_atoms: tuple[Step11Rc0030ParsedSemanticAtom, ...]
    reception_bindings: tuple[Step11Rc0030ParsedReceptionBinding, ...]
    observation_group_count: int
    reception_group_count: int
    base_prefix_commitments: tuple[str, ...]
    decomposition_locus_count: int
    evaluated_decomposition_count: int
    peak_stored_decomposition_count: int
    body_scan_pass_count: int
    body_free_export_allowed: bool = False


@dataclass(frozen=True, slots=True, repr=False, weakref_slot=True)
class Step11Rc0030BaseBodyParsedWitness:
    schema_version: str
    body_sha256: str
    base_witness: Step11ParsedSurfaceWitness
    observation_line_sha256: tuple[str, ...]
    observation_stem_sha256: tuple[str, ...]
    observation_group_count: int
    reception_group_count: int
    body_scan_pass_count: int
    body_free_export_allowed: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030VerifiedBaseBodyReuse:
    schema_version: str
    source_atom_id: str
    semantic_family: str
    base_parsed_atom_id: str
    base_obligation_id: str
    match_basis: str
    base_surface_sha256: str
    source_authority_sha256: str
    independent_binding_sha256: str
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030VerifiedSemanticBinding:
    source_atom_id: str
    semantic_family: str
    parsed_atom_id: str | None
    verified_reuse_binding_sha256: str | None
    match_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030VerifiedReceptionBinding:
    source_reception_opportunity_id: str
    source_scope: str
    parsed_binding_id: str
    reception_line_ordinal: int
    move_ordinal: int
    reception_act: str
    target_owner_count: int
    supporting_owner_count: int
    association_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentVerifiedSurfaceBinding:
    schema_version: str
    parsed_witness_sha256: str
    base_witness_sha256: str
    successor_snapshot_sha256: str
    source_authority_sha256: str
    experiment_catalog_sha256: str
    semantic_bindings: tuple[Step11Rc0030VerifiedSemanticBinding, ...]
    reception_bindings: tuple[Step11Rc0030VerifiedReceptionBinding, ...]
    reception_binding_count: int
    owner_binding_comparison_count: int
    unique_solution_count: int
    semantic_coverage_authorized: bool
    issue_codes: tuple[str, ...]
    hard_verified: bool
    body_free_export_allowed: bool = False


def _step11_rc0030_witness_origin_registry():
    registry: dict[int, weakref.ReferenceType[Any]] = {}

    def register(value: Any) -> None:
        key = id(value)

        def remove(
            reference: weakref.ReferenceType[Any],
            *,
            registry_key: int = key,
        ) -> None:
            if registry.get(registry_key) is reference:
                registry.pop(registry_key, None)

        registry[key] = weakref.ref(value, remove)

    def validate(value: Any) -> bool:
        reference = registry.get(id(value))
        return reference is not None and reference() is value

    return register, validate


(
    _step11_rc0030_register_final_witness,
    _step11_rc0030_validate_final_witness_origin,
) = _step11_rc0030_witness_origin_registry()
(
    _step11_rc0030_register_base_witness,
    _step11_rc0030_validate_base_witness_origin,
) = _step11_rc0030_witness_origin_registry()


def _step11_rc0030_inverse_catalog() -> tuple[dict[str, Any], str]:
    owner = __import__(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "validate_step11_rc0030_experiment_surface_catalog",
        ),
    )
    catalog = owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    issues = owner.validate_step11_rc0030_experiment_surface_catalog(catalog)
    if issues:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_CATALOG_COMMITMENT_MISMATCH"
        )
    return catalog, owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0030_semantic_terminal_index(
    catalog: Mapping[str, Any],
) -> tuple[tuple[str, str, str, str], ...]:
    morphology = catalog["clause_morphology"]
    result: list[tuple[str, str, str, str]] = []
    for key, fragment in catalog["construction_clause_fragments"].items():
        result.append(
            (
                morphology["construction_item_link"] + fragment,
                "construction",
                key,
                "",
            )
        )
    for family, registry in (
        ("relation", catalog["relation_clause_fragments"]),
        ("semantic_link", catalog["semantic_link_clause_fragments"]),
    ):
        for key, fragment in registry.items():
            semantic_type, direction = key.rsplit(":", 1)
            link = (
                morphology["bidirectional_item_link"]
                if direction == "bidirectional"
                else morphology["directed_item_link"]
            )
            result.append((link + fragment, family, semantic_type, direction))
    for key, fragment in catalog["unknown_clause_fragments"].items():
        result.append(
            (
                morphology["unknown_item_link"] + fragment,
                "explicit_unknown",
                key,
                "",
            )
        )
    terminals = tuple(sorted(result, key=lambda row: (-len(row[0]), row)))
    if len({row[0] for row in terminals}) != len(terminals):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_CATALOG_FRAGMENT_AMBIGUOUS"
        )
    return terminals


def _step11_rc0030_parse_owner_expression(
    prefix: str,
    *,
    family: str,
    direction: str,
    morphology: Mapping[str, str],
) -> tuple[str, ...]:
    if not prefix or any(
        char in prefix
        for char in (
            "\r",
            "\n",
            "「",
            "」",
            "、",
            "。",
            "！",
            "？",
            "!",
            "?",
        )
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_OWNER_EXPRESSION_INVALID"
        )
    if family in {"construction", "explicit_unknown"}:
        return (prefix,)
    separator = (
        morphology["symmetric_join"]
        if direction == "bidirectional"
        else morphology["source_particle"]
    )
    positions = tuple(
        match.start() for match in re.finditer(re.escape(separator), prefix)
    )
    decompositions = tuple(
        (prefix[:position], prefix[position + len(separator) :])
        for position in positions
        if prefix[:position] and prefix[position + len(separator) :]
    )
    if len(decompositions) != 1:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_OWNER_EXPRESSION_AMBIGUOUS"
        )
    return decompositions[0]


def _step11_rc0030_parse_semantic_item(
    value: str,
    *,
    terminal: tuple[str, str, str, str],
    morphology: Mapping[str, str],
    sentence_group_ordinal: int,
    grammatical_chunk_ordinal: int,
    pack_ordinal: int,
    item_ordinal: int,
) -> Step11Rc0030ParsedSemanticAtom:
    terminal_text, family, semantic_key, direction = terminal
    if not value.endswith(terminal_text):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SEMANTIC_PACK_UNPARSEABLE"
        )
    owner_expressions = _step11_rc0030_parse_owner_expression(
        value[: -len(terminal_text)],
        family=family,
        direction=direction,
        morphology=morphology,
    )
    material = {
        "family": family,
        "semantic_key": semantic_key,
        "direction": direction,
        "owner_expression_hashes": [
            hashlib.sha256(row.encode("utf-8")).hexdigest()
            for row in owner_expressions
        ],
        "sentence_group_ordinal": sentence_group_ordinal,
        "grammatical_chunk_ordinal": grammatical_chunk_ordinal,
        "pack_ordinal": pack_ordinal,
        "item_ordinal": item_ordinal,
    }
    return Step11Rc0030ParsedSemanticAtom(
        atom_id="nls3s11rc0030atom_" + artifact_sha256(material)[:16],
        semantic_family=family,
        semantic_key=semantic_key,
        direction=direction,
        owner_expressions=owner_expressions,
        sentence_group_ordinal=sentence_group_ordinal,
        grammatical_chunk_ordinal=grammatical_chunk_ordinal,
        pack_ordinal=pack_ordinal,
        item_ordinal=item_ordinal,
    )


def _step11_rc0030_parse_semantic_pack(
    value: str,
    *,
    catalog: Mapping[str, Any],
    sentence_group_ordinal: int,
    grammatical_chunk_ordinal: int,
    pack_ordinal: int,
    evaluation_budget: list[int],
) -> tuple[tuple[Step11Rc0030ParsedSemanticAtom, ...], int, int]:
    morphology = catalog["clause_morphology"]
    predicate = morphology["semantic_pack_predicate_suffix"]
    if not value.endswith(predicate):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SEMANTIC_PACK_PREDICATE_MISMATCH"
        )
    core = value[: -len(predicate)]
    joiner = morphology["semantic_item_join"]
    terminals = _step11_rc0030_semantic_terminal_index(catalog)
    initial_evaluated = evaluation_budget[0]
    loci: list[tuple[int, tuple[str, str, str, str]]] = []
    for terminal in terminals:
        start = 0
        while True:
            position = core.find(terminal[0], start)
            if position < 0:
                break
            evaluation_budget[0] += 1
            if (
                evaluation_budget[0]
                > _STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX
            ):
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_EVALUATED_DECOMPOSITION_BOUND_EXCEEDED"
                )
            end = position + len(terminal[0])
            if end == len(core) or core.startswith(joiner, end):
                loci.append((end, terminal))
                if len(loci) > _STEP11_RC0030_STORED_DECOMPOSITION_MAX:
                    raise Step11Rc0030ExperimentInverseSurfaceError(
                        "STEP11_RC0030_DECOMPOSITION_AMBIGUOUS"
                    )
            start = position + 1
    loci.sort(key=lambda row: (row[0], row[1]))
    if not loci:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SEMANTIC_PACK_UNPARSEABLE"
        )
    atoms: list[Step11Rc0030ParsedSemanticAtom] = []
    cursor = 0
    for item_ordinal, (end, terminal) in enumerate(loci, 1):
        if item_ordinal > 2 or end <= cursor:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SEMANTIC_PACK_DENSITY_EXCEEDED"
            )
        atoms.append(
            _step11_rc0030_parse_semantic_item(
                core[cursor:end],
                terminal=terminal,
                morphology=morphology,
                sentence_group_ordinal=sentence_group_ordinal,
                grammatical_chunk_ordinal=grammatical_chunk_ordinal,
                pack_ordinal=pack_ordinal,
                item_ordinal=item_ordinal,
            )
        )
        cursor = end
        if cursor < len(core):
            if not core.startswith(joiner, cursor):
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_DECOMPOSITION_AMBIGUOUS"
                )
            cursor += len(joiner)
    if cursor != len(core) or not 1 <= len(atoms) <= 2:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_DECOMPOSITION_AMBIGUOUS"
        )
    return (
        tuple(atoms),
        len(loci),
        evaluation_budget[0] - initial_evaluated,
    )


def _step11_rc0030_parse_observation_tail(
    line: str,
    *,
    catalog: Mapping[str, Any],
    sentence_group_ordinal: int,
    evaluation_budget: list[int],
) -> tuple[
    tuple[Step11Rc0030ParsedSemanticAtom, ...], str, int, int, int
]:
    morphology = catalog["clause_morphology"]
    initial_evaluated = evaluation_budget[0]
    suffix = morphology["sentence_suffix"]
    predicate = morphology["semantic_pack_predicate_suffix"]
    if not line.endswith(suffix):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_OBSERVATION_SUFFIX_INVALID"
        )
    last_predicate = line.rfind(predicate)
    if last_predicate < 0:
        return (
            (),
            hashlib.sha256(line.encode("utf-8")).hexdigest(),
            0,
            0,
            0,
        )
    candidate_starts = [0]
    for index, char in enumerate(line):
        if index >= last_predicate:
            break
        if char in {
            morphology["clause_join"],
            morphology["grammatical_chunk_join"],
        }:
            candidate_starts.append(index + 1)
            if (
                len(candidate_starts)
                > _STEP11_RC0030_DECOMPOSITION_LOCUS_MAX
            ):
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_DECOMPOSITION_LOCUS_BOUND_EXCEEDED"
                )
    chosen: tuple[
        tuple[Step11Rc0030ParsedSemanticAtom, ...], int, int, int
    ] | None = None
    ambiguous_maximal = False
    peak_stored = 0
    for start in candidate_starts:
        evaluation_budget[0] += 1
        if (
            evaluation_budget[0]
            > _STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_EVALUATED_DECOMPOSITION_BOUND_EXCEEDED"
            )
        cursor = start
        pack_ordinal = 0
        # This is an append-relative chunk ordinal.  The first structure pack
        # is 1 when it shares the base tail (clause join), or 2 when the
        # rendered separator opens one new grammatical chunk.  The matcher
        # combines this body-only fact with the independently parsed base tail.
        if start > 0 and line[:start].endswith(morphology["clause_join"]):
            structure_chunk_ordinal = 1
        elif start > 0 and line[:start].endswith(
            morphology["grammatical_chunk_join"]
        ):
            structure_chunk_ordinal = 2
        else:
            structure_chunk_ordinal = 1
        rows: list[Step11Rc0030ParsedSemanticAtom] = []
        local_loci = 0
        local_evaluated = 0
        valid = True
        while valid:
            predicate_start = line.find(predicate, cursor)
            if predicate_start < cursor:
                valid = False
                break
            end = predicate_start + len(predicate)
            pack_ordinal += 1
            try:
                parsed, loci, attempts = _step11_rc0030_parse_semantic_pack(
                    line[cursor:end],
                    catalog=catalog,
                    sentence_group_ordinal=sentence_group_ordinal,
                    grammatical_chunk_ordinal=structure_chunk_ordinal,
                    pack_ordinal=pack_ordinal,
                    evaluation_budget=evaluation_budget,
                )
            except Step11Rc0030ExperimentInverseSurfaceError:
                valid = False
                break
            rows.extend(parsed)
            local_loci += loci
            local_evaluated += attempts
            if end == len(line) - len(suffix):
                cursor = end + len(suffix)
                break
            if end >= len(line) - len(suffix):
                valid = False
                break
            separator = line[end : end + 1]
            if separator not in {
                morphology["clause_join"],
                morphology["grammatical_chunk_join"],
            }:
                valid = False
                break
            if separator == morphology["grammatical_chunk_join"]:
                structure_chunk_ordinal += 1
            cursor = end + 1
        if valid and cursor == len(line) and rows:
            candidate = (tuple(rows), start, local_loci, local_evaluated)
            if chosen is None or start < chosen[1]:
                chosen = candidate
                ambiguous_maximal = False
                peak_stored = max(peak_stored, 1)
            elif start == chosen[1] and candidate != chosen:
                ambiguous_maximal = True
                peak_stored = _STEP11_RC0030_STORED_DECOMPOSITION_MAX
    if chosen is None:
        return (
            (),
            hashlib.sha256(line.encode("utf-8")).hexdigest(),
            len(candidate_starts),
            evaluation_budget[0] - initial_evaluated,
            0,
        )
    # Every proper suffix of a multi-pack tail is syntactically parseable.
    # It is not an alternative witness: the body-only grammar owns the
    # unique maximal contiguous tail, i.e. the earliest successful start.
    if ambiguous_maximal:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_DECOMPOSITION_AMBIGUOUS"
        )
    rows, start, local_loci, local_evaluated = chosen
    prefix = line[:start]
    if not prefix or prefix.endswith(("、", "。")):
        prefix = prefix[:-1]
    if not prefix:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_PREFIX_EMPTY"
        )
    return (
        rows,
        hashlib.sha256(prefix.encode("utf-8")).hexdigest(),
        len(candidate_starts) + local_loci,
        evaluation_budget[0] - initial_evaluated,
        peak_stored,
    )


def _step11_rc0030_parse_reception_line(
    line: str,
    *,
    catalog: Mapping[str, Any],
    line_ordinal: int,
) -> tuple[Step11Rc0030ParsedReceptionBinding, ...]:
    morphology = catalog["clause_morphology"]
    suffix = morphology["sentence_suffix"]
    if not line.endswith(suffix):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_SUFFIX_INVALID"
        )
    moves = tuple(line[: -len(suffix)].split(morphology["grammatical_chunk_join"]))
    if (
        not moves
        or len(moves) > _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX
        or any(not row for row in moves)
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_DENSITY_EXCEEDED"
        )
    inverse_acts = {
        fragment: act
        for act, fragment in catalog["reception_act_predicate_fragments"].items()
    }
    if len(inverse_acts) != len(
        catalog["reception_act_predicate_fragments"]
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_ACT_AMBIGUOUS"
        )
    result: list[Step11Rc0030ParsedReceptionBinding] = []
    support_marker = (
        morphology["support_particle"] + morphology["clause_join"]
    )
    for move_ordinal, move in enumerate(moves, 1):
        act_matches = tuple(
            (fragment, act)
            for fragment, act in inverse_acts.items()
            if move.endswith(fragment)
        )
        if len(act_matches) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_ACT_AMBIGUOUS"
            )
        fragment, act = act_matches[0]
        prefix = move[: -len(fragment)]
        if not prefix.endswith(morphology["object_particle"]):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_TARGET_UNRESOLVED"
            )
        prefix = prefix[: -len(morphology["object_particle"])]
        support_positions = tuple(
            match.start()
            for match in re.finditer(re.escape(support_marker), prefix)
        )
        if len(support_positions) > 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_SUPPORT_AMBIGUOUS"
            )
        support: str | None = None
        target = prefix
        if support_positions:
            position = support_positions[0]
            support = prefix[:position]
            target = prefix[position + len(support_marker) :]
        if (
            not target
            or support == ""
            or any(
                char in value
                for value in (target, support or "")
                for char in ("\r", "\n", "「", "」")
            )
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_OWNER_EXPRESSION_INVALID"
            )
        target_sha256 = hashlib.sha256(target.encode("utf-8")).hexdigest()
        support_sha256 = (
            hashlib.sha256(support.encode("utf-8")).hexdigest()
            if support is not None
            else None
        )
        binding_material = {
            "reception_line_ordinal": line_ordinal,
            "move_ordinal": move_ordinal,
            "reception_act": act,
            "target_expression_sha256": target_sha256,
            "supporting_expression_sha256": support_sha256,
        }
        result.append(
            Step11Rc0030ParsedReceptionBinding(
                binding_id=(
                    "nls3s11rc0030recv_"
                    + artifact_sha256(binding_material)[:16]
                ),
                reception_line_ordinal=line_ordinal,
                move_ordinal=move_ordinal,
                reception_act=act,
                target_expression=target,
                supporting_expression=support,
                target_expression_sha256=target_sha256,
                supporting_expression_sha256=support_sha256,
            )
        )
    return tuple(result)


def parse_step11_rc0030_experiment_surface(
    body: bytes,
) -> Step11Rc0030ExperimentParsedSurfaceWitness:
    """Parse only final bytes and the versioned declarative catalog."""

    if (
        type(body) is not bytes
        or not body
        or len(body) > _STEP11_RC0030_BODY_BYTE_MAX
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BODY_BOUND_INVALID"
        )
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_UTF8_INVALID"
        ) from None
    if (
        text.encode("utf-8", errors="strict") != body
        or unicodedata.normalize("NFC", text) != text
        or "\r" in text
        or text.startswith("\ufeff")
        or text.endswith("\n")
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_CANONICAL_TEXT_INVALID"
        )
    # Pass 1 establishes canonical bytes and the closed two-section frame.
    body_scan_pass_count = 1
    catalog, catalog_sha256 = _step11_rc0030_inverse_catalog()
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SECTION_LAYOUT_INVALID"
        )
    observation_text, reception_text = text[len(prefix) :].split(separator)
    observation_lines = tuple(observation_text.split("\n"))
    reception_lines = tuple(reception_text.split("\n"))
    if (
        not observation_lines
        or not reception_lines
        or any(not row for row in (*observation_lines, *reception_lines))
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SECTION_LAYOUT_INVALID"
        )
    semantic_atoms: list[Step11Rc0030ParsedSemanticAtom] = []
    prefix_commitments: list[str] = []
    locus_count = 0
    evaluated_count = 0
    peak_stored = 0
    evaluation_budget = [0]
    # Pass 2 performs the bounded grammar walk.  All nested decomposition
    # attempts are separately charged by loci/evaluated counters below.
    body_scan_pass_count += 1
    for ordinal, line in enumerate(observation_lines, 1):
        atoms, commitment, loci, evaluated, stored = (
            _step11_rc0030_parse_observation_tail(
                line,
                catalog=catalog,
                sentence_group_ordinal=ordinal,
                evaluation_budget=evaluation_budget,
            )
        )
        semantic_atoms.extend(atoms)
        prefix_commitments.append(commitment)
        locus_count += loci
        evaluated_count += evaluated
        peak_stored = max(peak_stored, stored)
    if locus_count > _STEP11_RC0030_DECOMPOSITION_LOCUS_MAX:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_DECOMPOSITION_LOCUS_BOUND_EXCEEDED"
        )
    if evaluated_count > _STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_EVALUATED_DECOMPOSITION_BOUND_EXCEEDED"
        )
    receptions = tuple(
        binding
        for ordinal, line in enumerate(reception_lines, 1)
        for binding in _step11_rc0030_parse_reception_line(
            line, catalog=catalog, line_ordinal=ordinal
        )
    )
    if len(receptions) > _STEP11_RC0030_RECEPTION_MOVE_MAX:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_DENSITY_EXCEEDED"
        )
    witness = Step11Rc0030ExperimentParsedSurfaceWitness(
        schema_version=STEP11_RC0030_EXPERIMENT_PARSED_WITNESS_SCHEMA,
        body_sha256=hashlib.sha256(body).hexdigest(),
        experiment_catalog_sha256=catalog_sha256,
        semantic_atoms=tuple(semantic_atoms),
        reception_bindings=receptions,
        observation_group_count=len(observation_lines),
        reception_group_count=len(reception_lines),
        base_prefix_commitments=tuple(prefix_commitments),
        decomposition_locus_count=locus_count,
        evaluated_decomposition_count=evaluated_count,
        peak_stored_decomposition_count=peak_stored,
        body_scan_pass_count=body_scan_pass_count,
    )
    _step11_rc0030_register_final_witness(witness)
    step11_rc0030_experiment_parsed_witness_material(witness)
    return witness


def _step11_rc0030_semantic_atom_material(
    value: Step11Rc0030ParsedSemanticAtom,
) -> dict[str, Any]:
    return {
        "atom_id": value.atom_id,
        "semantic_family": value.semantic_family,
        "semantic_key": value.semantic_key,
        "direction": value.direction,
        "owner_expression_count": len(value.owner_expressions),
        "owner_expression_sha256": [
            hashlib.sha256(row.encode("utf-8")).hexdigest()
            for row in value.owner_expressions
        ],
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "grammatical_chunk_ordinal": value.grammatical_chunk_ordinal,
        "pack_ordinal": value.pack_ordinal,
        "item_ordinal": value.item_ordinal,
    }


def step11_rc0030_experiment_parsed_witness_material(
    value: Step11Rc0030ExperimentParsedSurfaceWitness,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentParsedSurfaceWitness:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_PARSED_WITNESS_TYPE_INVALID"
        )
    if not _step11_rc0030_validate_final_witness_origin(value):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_PARSED_WITNESS_ORIGIN_REQUIRED"
        )
    if (
        value.schema_version
        != STEP11_RC0030_EXPERIMENT_PARSED_WITNESS_SCHEMA
        or _STEP11_RC0030_SHA256_RE.fullmatch(value.body_sha256) is None
        or _STEP11_RC0030_SHA256_RE.fullmatch(
            value.experiment_catalog_sha256
        )
        is None
        or not 1 <= value.observation_group_count
        or not 1 <= value.reception_group_count
        or len(value.base_prefix_commitments)
        != value.observation_group_count
        or any(
            _STEP11_RC0030_SHA256_RE.fullmatch(row) is None
            for row in value.base_prefix_commitments
        )
        or not 0
        <= value.decomposition_locus_count
        <= _STEP11_RC0030_DECOMPOSITION_LOCUS_MAX
        or not 0
        <= value.evaluated_decomposition_count
        <= _STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX
        or not 0
        <= value.peak_stored_decomposition_count
        < _STEP11_RC0030_STORED_DECOMPOSITION_MAX
        or value.body_scan_pass_count != _STEP11_RC0030_BODY_SCAN_PASS_MAX
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_PARSED_WITNESS_INVALID"
        )
    atom_ids = tuple(row.atom_id for row in value.semantic_atoms)
    if (
        len(atom_ids) != len(set(atom_ids))
        or any(
            type(row) is not Step11Rc0030ParsedSemanticAtom
            or row.semantic_family
            not in {
                "construction",
                "relation",
                "semantic_link",
                "explicit_unknown",
            }
            or not row.semantic_key
            or not row.owner_expressions
            or len(row.owner_expressions) > _STEP11_RC0030_OWNER_MAX
            or any(not item for item in row.owner_expressions)
            or row.sentence_group_ordinal < 1
            or row.grammatical_chunk_ordinal < 1
            or row.pack_ordinal < 1
            or row.item_ordinal not in {1, 2}
            or row.atom_id
            != (
                "nls3s11rc0030atom_"
                + artifact_sha256(
                    {
                        "family": row.semantic_family,
                        "semantic_key": row.semantic_key,
                        "direction": row.direction,
                        "owner_expression_hashes": [
                            hashlib.sha256(item.encode("utf-8")).hexdigest()
                            for item in row.owner_expressions
                        ],
                        "sentence_group_ordinal": row.sentence_group_ordinal,
                        "grammatical_chunk_ordinal": (
                            row.grammatical_chunk_ordinal
                        ),
                        "pack_ordinal": row.pack_ordinal,
                        "item_ordinal": row.item_ordinal,
                    }
                )[:16]
            )
            for row in value.semantic_atoms
        )
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_PARSED_SEMANTIC_ATOM_SET_INVALID"
        )
    reception_positions = tuple(
        (row.reception_line_ordinal, row.move_ordinal)
        for row in value.reception_bindings
    )
    reception_ids = tuple(row.binding_id for row in value.reception_bindings)
    moves_by_line: dict[int, list[int]] = {}
    for line_ordinal, move_ordinal in reception_positions:
        moves_by_line.setdefault(line_ordinal, []).append(move_ordinal)
    if (
        len(value.reception_bindings) > _STEP11_RC0030_RECEPTION_MOVE_MAX
        or reception_positions != tuple(sorted(reception_positions))
        or len(reception_positions) != len(set(reception_positions))
        or len(reception_ids) != len(set(reception_ids))
        or any(
            tuple(moves) != tuple(range(1, len(moves) + 1))
            or len(moves)
            > _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX
            for moves in moves_by_line.values()
        )
        or any(
        type(row) is not Step11Rc0030ParsedReceptionBinding
        or row.reception_line_ordinal < 1
        or row.reception_line_ordinal > value.reception_group_count
        or row.move_ordinal not in {1, 2}
        or re.fullmatch(r"nls3s11rc0030recv_[0-9a-f]{16}", row.binding_id)
        is None
        or not row.reception_act
        or not row.target_expression
        or row.target_expression_sha256
        != hashlib.sha256(row.target_expression.encode("utf-8")).hexdigest()
        or row.supporting_expression_sha256
        != (
            hashlib.sha256(row.supporting_expression.encode("utf-8")).hexdigest()
            if row.supporting_expression is not None
            else None
        )
        or row.binding_id
        != (
            "nls3s11rc0030recv_"
            + artifact_sha256(
                {
                    "reception_line_ordinal": row.reception_line_ordinal,
                    "move_ordinal": row.move_ordinal,
                    "reception_act": row.reception_act,
                    "target_expression_sha256": row.target_expression_sha256,
                    "supporting_expression_sha256": (
                        row.supporting_expression_sha256
                    ),
                }
            )[:16]
        )
            for row in value.reception_bindings
        )
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_PARSED_RECEPTION_SET_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "semantic_atoms": [
            _step11_rc0030_semantic_atom_material(row)
            for row in value.semantic_atoms
        ],
        "reception_bindings": [
            {
                "binding_id": row.binding_id,
                "reception_line_ordinal": row.reception_line_ordinal,
                "move_ordinal": row.move_ordinal,
                "reception_act": row.reception_act,
                "target_expression_sha256": row.target_expression_sha256,
                "supporting_expression_sha256": (
                    row.supporting_expression_sha256
                ),
            }
            for row in value.reception_bindings
        ],
        "observation_group_count": value.observation_group_count,
        "reception_group_count": value.reception_group_count,
        "base_prefix_commitments": list(value.base_prefix_commitments),
        "decomposition_locus_count": value.decomposition_locus_count,
        "evaluated_decomposition_count": (
            value.evaluated_decomposition_count
        ),
        "peak_stored_decomposition_count": (
            value.peak_stored_decomposition_count
        ),
        "body_scan_pass_count": value.body_scan_pass_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def parse_step11_rc0030_base_body_exact_reuse(
    base_body: bytes,
) -> Step11Rc0030BaseBodyParsedWitness:
    """Parse immutable base bytes without accepting a forward reuse claim."""

    if (
        type(base_body) is not bytes
        or not base_body
        or len(base_body) > _STEP11_RC0030_BODY_BYTE_MAX
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_BOUND_INVALID"
        )
    try:
        text = base_body.decode("utf-8", errors="strict")
        witness = parse_step11_natural_surface(base_body)
    except Step11InverseSurfaceError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_PARSE_FAILED"
        ) from None
    except UnicodeDecodeError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_PARSE_FAILED"
        ) from None
    body_scan_pass_count = 1
    if witness.body_sha256 != hashlib.sha256(base_body).hexdigest():
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_COMMITMENT_MISMATCH"
        )
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_PARSE_FAILED"
        )
    observation, reception = text[len(prefix) :].split(separator, 1)
    observation_lines = tuple(observation.split("\n"))
    reception_lines = tuple(reception.split("\n"))
    body_scan_pass_count += 1
    if (
        not observation_lines
        or not reception_lines
        or any(not row or not row.endswith("。") for row in observation_lines)
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BODY_PARSE_FAILED"
        )
    value = Step11Rc0030BaseBodyParsedWitness(
        schema_version=STEP11_RC0030_BASE_BODY_PARSED_WITNESS_SCHEMA,
        body_sha256=witness.body_sha256,
        base_witness=witness,
        observation_line_sha256=tuple(
            hashlib.sha256(row.encode("utf-8")).hexdigest()
            for row in observation_lines
        ),
        observation_stem_sha256=tuple(
            hashlib.sha256(row[:-1].encode("utf-8")).hexdigest()
            for row in observation_lines
        ),
        observation_group_count=len(observation_lines),
        reception_group_count=len(reception_lines),
        body_scan_pass_count=body_scan_pass_count,
    )
    _step11_rc0030_register_base_witness(value)
    step11_rc0030_base_body_parsed_witness_material(value)
    return value


def step11_rc0030_base_body_parsed_witness_material(
    value: Step11Rc0030BaseBodyParsedWitness,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030BaseBodyParsedWitness:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_WITNESS_TYPE_INVALID"
        )
    if not _step11_rc0030_validate_base_witness_origin(value):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_WITNESS_ORIGIN_REQUIRED"
        )
    if (
        value.schema_version != STEP11_RC0030_BASE_BODY_PARSED_WITNESS_SCHEMA
        or type(value.base_witness) is not Step11ParsedSurfaceWitness
        or value.body_sha256 != value.base_witness.body_sha256
        or _STEP11_RC0030_SHA256_RE.fullmatch(value.body_sha256) is None
        or value.observation_group_count < 1
        or value.reception_group_count < 1
        or value.observation_group_count
        != sum(
            row.section_role == "observation"
            for row in value.base_witness.sentences
        )
        or value.reception_group_count
        != sum(
            row.section_role == "reception"
            for row in value.base_witness.sentences
        )
        or len(value.observation_line_sha256)
        != value.observation_group_count
        or len(value.observation_stem_sha256)
        != value.observation_group_count
        or any(
            _STEP11_RC0030_SHA256_RE.fullmatch(row) is None
            for row in (
                *value.observation_line_sha256,
                *value.observation_stem_sha256,
            )
        )
        or value.body_scan_pass_count != _STEP11_RC0030_BODY_SCAN_PASS_MAX
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_WITNESS_INVALID"
        )
    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "base_witness": _witness_material(value.base_witness),
        "observation_line_sha256": list(value.observation_line_sha256),
        "observation_stem_sha256": list(value.observation_stem_sha256),
        "observation_group_count": value.observation_group_count,
        "reception_group_count": value.reception_group_count,
        "body_scan_pass_count": value.body_scan_pass_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _step11_rc0030_revalidated_base_binding(
    base_witness: Step11ParsedSurfaceWitness,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11VerifiedSurfaceBinding:
    if type(base_witness) is not Step11ParsedSurfaceWitness:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_WITNESS_TYPE_INVALID"
        )
    try:
        binding = match_step11_natural_surface(
            base_witness,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
            current_input=current_input,
        )
    except (Step11InverseSurfaceError, TypeError, ValueError):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BINDING_REVALIDATION_FAILED"
        ) from None
    expected_hash = artifact_sha256(_witness_material(base_witness))
    if (
        type(binding) is not Step11VerifiedSurfaceBinding
        or binding.parsed_witness_sha256 != expected_hash
        or binding.verified is not True
        or binding.issue_codes
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BINDING_REVALIDATION_FAILED"
        )
    return binding


def _step11_rc0030_validated_source_records(
    successor_snapshot: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
) -> tuple[
    tuple[tuple[str, str, str, str, tuple[str, ...]], ...],
    tuple[
        tuple[str, str, str, tuple[str, ...], tuple[str, ...]], ...
    ],
    dict[str, frozenset[str]],
    str,
    str,
    dict[str, frozenset[str]],
]:
    validator_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    try:
        issues = validator_owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            successor_snapshot
        )
    except (AttributeError, TypeError, ValueError):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SOURCE_AUTHORITY_INVALID"
        ) from None
    if issues:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SOURCE_AUTHORITY_INVALID"
        )
    authority = successor_snapshot.relation_construction_authority
    base_snapshot = successor_snapshot.base_snapshot
    if (
        type(inventory_result) is not SemanticObligationInventoryResult
        or base_snapshot != inventory_result.source_snapshot
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_SOURCE_COMMITMENT_MISMATCH"
        )
    aliases: dict[str, frozenset[str]] = {}
    nucleus_aliases: dict[str, frozenset[str]] = {}
    exact_source_aliases: dict[str, frozenset[str]] = {}

    def bind_alias(owner_id: str, values: frozenset[str]) -> None:
        previous = aliases.get(owner_id)
        if previous is not None and previous != values:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SOURCE_OWNER_PARENT_AMBIGUOUS"
            )
        aliases[owner_id] = values

    for nucleus in base_snapshot.nuclei:
        values = frozenset(
            {str(nucleus.source_id), str(nucleus.actual_source_id)}
        )
        for nucleus_id in (
            str(nucleus.source_id),
            str(nucleus.actual_source_id),
        ):
            previous = nucleus_aliases.get(nucleus_id)
            if previous is not None and previous != values:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_SOURCE_OWNER_PARENT_AMBIGUOUS"
                )
            nucleus_aliases[nucleus_id] = values
            bind_alias(nucleus_id, values)
    for participation in authority.source_owner_participations:
        parent = nucleus_aliases.get(str(participation.parent_nucleus_id))
        if parent is None:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SOURCE_OWNER_PARENT_UNRESOLVED"
            )
        bind_alias(str(participation.target_owner_id), parent)
    participation_by_id = {
        str(row.participation_id): row
        for row in authority.source_owner_participations
    }
    records: list[tuple[str, str, str, str, tuple[str, ...]]] = []
    for instance in authority.construction_instances:
        owners = tuple(
            dict.fromkeys(
                str(participation_by_id[row].target_owner_id)
                for row in instance.participation_ids
                if row in participation_by_id
            )
        )
        if len(owners) != 1 or len(instance.participation_ids) != sum(
            row in participation_by_id for row in instance.participation_ids
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_CONSTRUCTION_OWNER_AMBIGUOUS"
            )
        records.append(
            (
                str(instance.construction_instance_id),
                "construction",
                str(instance.construction_code),
                "",
                owners,
            )
        )
    for relation in authority.relation_authorities:
        identity_aliases = {str(relation.source_relation_id)}
        if relation.refines_source_relation_id is not None:
            identity_aliases.add(str(relation.refines_source_relation_id))
        direct_aliases = {
            *identity_aliases,
            *(str(row) for row in relation.source_relation_ids),
        }
        parent_matches: list[frozenset[str]] = []
        for parent in base_snapshot.relations:
            parent_aliases = frozenset(
                {
                    str(parent.source_id),
                    str(parent.actual_source_id),
                    *(str(row) for row in parent.source_relation_ids),
                }
            )
            if identity_aliases & {
                str(parent.source_id),
                str(parent.actual_source_id),
            }:
                parent_matches.append(parent_aliases)
        if not parent_matches:
            for parent in base_snapshot.relations:
                parent_aliases = frozenset(
                    {
                        str(parent.source_id),
                        str(parent.actual_source_id),
                        *(str(row) for row in parent.source_relation_ids),
                    }
                )
                if direct_aliases & parent_aliases:
                    parent_matches.append(parent_aliases)
        if len(parent_matches) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SOURCE_RELATION_PARENT_AMBIGUOUS"
            )
        exact_source_aliases[str(relation.experiment_relation_id)] = (
            frozenset(direct_aliases) | parent_matches[0]
        )
        records.append(
            (
                str(relation.experiment_relation_id),
                "relation",
                str(relation.effective_relation_type),
                str(relation.direction),
                (
                    str(relation.from_source_owner_id),
                    str(relation.to_source_owner_id),
                ),
            )
        )
    for link in authority.semantic_link_bindings:
        records.append(
            (
                str(link.source_semantic_link_id),
                "semantic_link",
                str(link.relation_type),
                str(link.direction),
                (
                    str(link.from_semantic_unit_id),
                    str(link.to_semantic_unit_id),
                ),
            )
        )
    for unknown in authority.explicit_unknown_authorities:
        owner_parent_aliases = tuple(
            aliases.get(str(row.owner_id), frozenset())
            for row in unknown.affected_source_owners
        )
        if not owner_parent_aliases or any(not row for row in owner_parent_aliases):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SOURCE_UNKNOWN_PARENT_UNRESOLVED"
            )
        parent_matches: list[Any] = []
        for parent in base_snapshot.unknowns:
            parent_aliases = {
                str(parent.source_id),
                str(parent.actual_source_id),
            }
            affected = tuple(str(row) for row in parent.affected_nucleus_ids)
            if (
                str(unknown.source_unknown_id) in parent_aliases
                and str(parent.source_dimension) == str(unknown.dimension)
                and len(affected) == len(set(affected))
                and all(
                    any(owner_id in owner_aliases for owner_id in affected)
                    for owner_aliases in owner_parent_aliases
                )
                and all(
                    any(owner_id in owner_aliases for owner_aliases in owner_parent_aliases)
                    for owner_id in affected
                )
            ):
                parent_matches.append(parent)
        if len(parent_matches) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SOURCE_UNKNOWN_PARENT_AMBIGUOUS"
            )
        parent = parent_matches[0]
        exact_source_aliases[str(unknown.source_unknown_id)] = frozenset(
            {
                str(unknown.source_unknown_id),
                str(parent.source_id),
                str(parent.actual_source_id),
            }
        )
        records.append(
            (
                str(unknown.source_unknown_id),
                "explicit_unknown",
                str(unknown.dimension),
                "",
                tuple(str(row.owner_id) for row in unknown.affected_source_owners),
            )
        )
    source_ids = tuple(row[0] for row in records)
    if (
        len(source_ids) != len(set(source_ids))
        or len(set(owner for row in records for owner in row[4]))
        > _STEP11_RC0030_OWNER_MAX
        or any(owner not in aliases for row in records for owner in row[4])
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SOURCE_RECORD_SET_INVALID"
        )
    receptions = tuple(
        (
            str(row.source_id),
            str(row.family),
            str(row.reception_act),
            tuple(str(value) for value in row.target_nucleus_ids),
            tuple(str(value) for value in row.support_nucleus_ids),
        )
        for row in base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not 1 <= len(receptions) <= _STEP11_RC0030_RECEPTION_MOVE_MAX:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_SOURCE_BOUND_INVALID"
        )
    reception_ids = tuple(row[0] for row in receptions)
    all_owner_ids = {
        owner for row in records for owner in row[4]
    } | {
        owner
        for row in receptions
        for owner in (*row[3], *row[4])
    }
    if (
        len(reception_ids) != len(set(reception_ids))
        or len(all_owner_ids) > _STEP11_RC0030_OWNER_MAX
        or any(owner not in aliases for owner in all_owner_ids)
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SOURCE_OWNER_SET_INVALID"
        )
    return (
        tuple(records),
        receptions,
        aliases,
        str(successor_snapshot.experiment_snapshot_sha256),
        str(authority.authority_sha256),
        exact_source_aliases,
    )


def _step11_rc0030_visible_phrase_registry(
    base_witness: Step11ParsedSurfaceWitness,
    base_binding: Step11VerifiedSurfaceBinding,
    *,
    source_owner_aliases: Mapping[str, frozenset[str]],
) -> tuple[dict[str, str], int]:
    phrase_binding_by_key: dict[tuple[str, str, str], list[Any]] = {}
    for row in base_binding.grounded_phrase_bindings:
        phrase_binding_by_key.setdefault(
            (
                str(row.atom_id),
                str(row.visible_feature_fingerprint_sha256),
                str(row.phrase_profile_id),
            ),
            [],
        ).append(row)
    phrase_owner_aliases: dict[str, set[str]] = {}
    for atom in base_witness.atoms:
        for phrase in atom.grounded_phrases:
            key = (
                str(atom.atom_id),
                str(phrase.visible_feature_fingerprint_sha256),
                str(phrase.phrase_profile_id),
            )
            rows = phrase_binding_by_key.get(key, ())
            if len(rows) != 1:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_BASE_PHRASE_BINDING_AMBIGUOUS"
                )
            phrase_owner_aliases.setdefault(str(phrase.phrase_text), set()).update(
                str(value) for value in rows[0].owner_nucleus_ids
            )
    owner_text: dict[str, str] = {}
    comparisons = 0
    for source_owner_id, aliases in source_owner_aliases.items():
        matches: list[str] = []
        for phrase_text, bound_owner_ids in phrase_owner_aliases.items():
            comparisons += 1
            if comparisons > _STEP11_RC0030_OWNER_COMPARISON_MAX:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_OWNER_COMPARISON_BOUND_EXCEEDED"
                )
            if aliases & bound_owner_ids:
                matches.append(phrase_text)
        unique = tuple(dict.fromkeys(matches))
        if len(unique) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_BINDING_AMBIGUOUS"
            )
        owner_text[source_owner_id] = unique[0]
    reverse: dict[str, list[str]] = {}
    for owner_id, phrase_text in owner_text.items():
        reverse.setdefault(phrase_text, []).append(owner_id)
    for rows in reverse.values():
        if len(rows) <= 1:
            continue
        common = source_owner_aliases[rows[0]]
        if not all(
            source_owner_aliases[row] == common and row in common
            for row in rows
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_BINDING_AMBIGUOUS"
            )
    return owner_text, comparisons


def _step11_rc0030_visible_signature(
    *,
    family: str,
    key: str,
    direction: str,
    owner_ids: Sequence[str],
    owner_text: Mapping[str, str],
    catalog: Mapping[str, Any],
) -> tuple[str, str, str, tuple[str, ...]]:
    try:
        texts = tuple(owner_text[row] for row in owner_ids)
    except KeyError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_OWNER_BINDING_UNRESOLVED"
        ) from None
    if family == "explicit_unknown":
        texts = (catalog["clause_morphology"]["symmetric_join"].join(texts),)
    return family, key, direction, texts


def _step11_rc0030_reference_phrase_texts(
    base_witness: Step11ParsedSurfaceWitness,
) -> dict[int, str]:
    result: dict[int, str] = {}
    for atom in base_witness.atoms:
        references = (
            (atom.introduced_reference,)
            if atom.introduced_reference is not None
            else atom.compound_label_references
        )
        phrase_texts = tuple(row.phrase_text for row in atom.grounded_phrases)
        if not references or len(references) != len(phrase_texts):
            continue
        for reference, phrase_text in zip(references, phrase_texts):
            previous = result.get(reference.reference_ordinal)
            if previous is not None and previous != phrase_text:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_BASE_REFERENCE_AMBIGUOUS"
                )
            result[reference.reference_ordinal] = phrase_text
    return result


def _step11_rc0030_reuse_material(
    value: Step11Rc0030VerifiedBaseBodyReuse,
    *,
    include_binding_sha256: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "source_atom_id": value.source_atom_id,
        "semantic_family": value.semantic_family,
        "base_parsed_atom_id": value.base_parsed_atom_id,
        "base_obligation_id": value.base_obligation_id,
        "match_basis": value.match_basis,
        "base_surface_sha256": value.base_surface_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "independent_binding_sha256": value.independent_binding_sha256,
        "body_free": value.body_free,
    }
    if not include_binding_sha256:
        result.pop("independent_binding_sha256")
    return result


def step11_rc0030_verified_base_body_reuse_material(
    value: Step11Rc0030VerifiedBaseBodyReuse,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030VerifiedBaseBodyReuse:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_REUSE_TYPE_INVALID"
        )
    if (
        value.schema_version != STEP11_RC0030_VERIFIED_BASE_REUSE_SCHEMA
        or value.semantic_family
        not in {"construction", "relation", "semantic_link", "explicit_unknown"}
        or re.fullmatch(r"nls3s11atom_[0-9a-f]{16}", value.base_parsed_atom_id)
        is None
        or re.fullmatch(r"obl_[0-9a-f]{16}", value.base_obligation_id) is None
        or _STEP11_RC0030_SHA256_RE.fullmatch(value.base_surface_sha256)
        is None
        or _STEP11_RC0030_SHA256_RE.fullmatch(value.source_authority_sha256)
        is None
        or _STEP11_RC0030_SHA256_RE.fullmatch(
            value.independent_binding_sha256
        )
        is None
        or value.body_free is not True
        or artifact_sha256(
            _step11_rc0030_reuse_material(
                value, include_binding_sha256=False
            )
        )
        != value.independent_binding_sha256
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_REUSE_BINDING_INVALID"
        )
    return _step11_rc0030_reuse_material(value)


def _step11_rc0030_derive_allowed_base_reuse(
    base_witness: Step11ParsedSurfaceWitness,
    base_binding: Step11VerifiedSurfaceBinding,
    *,
    records: Sequence[tuple[str, str, str, str, tuple[str, ...]]],
    owner_text: Mapping[str, str],
    authority_sha: str,
    exact_aliases: Mapping[str, frozenset[str]],
    obligation_by_id: Mapping[str, Mapping[str, Any]],
    catalog: Mapping[str, Any],
) -> tuple[Step11Rc0030VerifiedBaseBodyReuse, ...]:
    """Derive reuse from one already-revalidated base binding."""

    atom_by_id = {row.atom_id: row for row in base_witness.atoms}
    reference_text = _step11_rc0030_reference_phrase_texts(base_witness)
    unknown_dimension = {
        "explicit_cause_unknown": "cause",
        "explicit_unverbalized_unknown": "unverbalized",
        "explicit_choice_decision_unknown": "choice_decision",
        "explicit_temporal_referent_unknown": "temporal_referent",
    }
    result: list[Step11Rc0030VerifiedBaseBodyReuse] = []
    for source_id, family, key, direction, owner_ids in records:
        if family not in {"relation", "explicit_unknown"}:
            continue
        expected_signature = _step11_rc0030_visible_signature(
            family=family,
            key=key,
            direction=direction,
            owner_ids=owner_ids,
            owner_text=owner_text,
            catalog=catalog,
        )
        candidates: list[tuple[str, str, str]] = []
        for binding_row in base_binding.binding_rows:
            basis = str(binding_row.match_basis)
            if family == "relation" and basis != "relation_type_direction_endpoint":
                continue
            if (
                family == "explicit_unknown"
                and basis != "unknown_id_dimension_exact_target"
            ):
                continue
            obligation = obligation_by_id.get(str(binding_row.obligation_id))
            source_field = (
                "relation_ids"
                if family == "relation"
                else "unknown_boundary_ids"
            )
            ledger_source_ids = (
                obligation.get(source_field) if obligation is not None else None
            )
            if (
                type(ledger_source_ids) is not list
                or len(ledger_source_ids) != 1
                or type(ledger_source_ids[0]) is not str
                or ledger_source_ids[0] not in exact_aliases.get(source_id, ())
            ):
                continue
            for atom_id in binding_row.atom_ids:
                atom = atom_by_id.get(atom_id)
                if atom is None:
                    continue
                if family == "relation":
                    texts = tuple(
                        reference_text.get(row.reference_ordinal, "")
                        for row in atom.relation_endpoint_references
                    )
                    actual = (
                        "relation",
                        str(atom.relation_type or ""),
                        str(atom.relation_direction or ""),
                        texts,
                    )
                    match_basis = (
                        "relation_id_endpoint_direction_type_exact"
                    )
                else:
                    target_texts = tuple(
                        reference_text.get(row.reference_ordinal, "")
                        for row in atom.unknown_target_references
                    )
                    if not target_texts:
                        target_texts = tuple(
                            row.phrase_text for row in atom.grounded_phrases
                        )
                    joined = catalog["clause_morphology"][
                        "symmetric_join"
                    ].join(target_texts)
                    actual = (
                        "explicit_unknown",
                        next(
                            (
                                source_dimension
                                for source_dimension, base_dimension
                                in unknown_dimension.items()
                                if base_dimension
                                == atom.unknown_dimension_class
                            ),
                            "",
                        ),
                        "",
                        (joined,),
                    )
                    match_basis = "unknown_id_dimension_exact_target"
                if actual == expected_signature:
                    candidates.append(
                        (
                            str(atom_id),
                            str(binding_row.obligation_id),
                            match_basis,
                        )
                    )
        unique = tuple(dict.fromkeys(candidates))
        if len(unique) > 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_BASE_REUSE_AMBIGUOUS"
            )
        if not unique:
            continue
        atom_id, obligation_id, match_basis = unique[0]
        provisional = Step11Rc0030VerifiedBaseBodyReuse(
            schema_version=STEP11_RC0030_VERIFIED_BASE_REUSE_SCHEMA,
            source_atom_id=source_id,
            semantic_family=family,
            base_parsed_atom_id=atom_id,
            base_obligation_id=obligation_id,
            match_basis=match_basis,
            base_surface_sha256=base_witness.body_sha256,
            source_authority_sha256=authority_sha,
            independent_binding_sha256="0" * 64,
        )
        value = Step11Rc0030VerifiedBaseBodyReuse(
            schema_version=provisional.schema_version,
            source_atom_id=provisional.source_atom_id,
            semantic_family=provisional.semantic_family,
            base_parsed_atom_id=provisional.base_parsed_atom_id,
            base_obligation_id=provisional.base_obligation_id,
            match_basis=provisional.match_basis,
            base_surface_sha256=provisional.base_surface_sha256,
            source_authority_sha256=provisional.source_authority_sha256,
            independent_binding_sha256=artifact_sha256(
                _step11_rc0030_reuse_material(
                    provisional, include_binding_sha256=False
                )
            ),
        )
        step11_rc0030_verified_base_body_reuse_material(value)
        result.append(value)
    return tuple(result)


def match_step11_rc0030_base_body_exact_reuse(
    base_body_witness: Step11Rc0030BaseBodyParsedWitness,
    *,
    successor_snapshot: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[Step11Rc0030VerifiedBaseBodyReuse, ...]:
    """Grant only independently revalidated family-exact base credit."""

    step11_rc0030_base_body_parsed_witness_material(base_body_witness)
    base_witness = base_body_witness.base_witness
    base_binding = _step11_rc0030_revalidated_base_binding(
        base_witness,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
        current_input=current_input,
    )
    records, _receptions, aliases, _snapshot_sha, authority_sha, exact_aliases = (
        _step11_rc0030_validated_source_records(
            successor_snapshot,
            inventory_result=inventory_result,
        )
    )
    try:
        _ledger, obligation_by_id = _validated_parents(
            inventory_result, content_plan, discourse_plan
        )
    except Step11InverseSurfaceError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BINDING_REVALIDATION_FAILED"
        ) from None
    catalog, _catalog_sha = _step11_rc0030_inverse_catalog()
    required_owner_ids = {
        owner_id for row in records for owner_id in row[4]
    }
    owner_text, _comparisons = _step11_rc0030_visible_phrase_registry(
        base_witness,
        base_binding,
        source_owner_aliases={
            owner_id: aliases[owner_id]
            for owner_id in required_owner_ids
        },
    )
    return _step11_rc0030_derive_allowed_base_reuse(
        base_witness,
        base_binding,
        records=records,
        owner_text=owner_text,
        authority_sha=authority_sha,
        exact_aliases=exact_aliases,
        obligation_by_id=obligation_by_id,
        catalog=catalog,
    )


def _step11_rc0030_reception_schedule(
    base_body_witness: Step11Rc0030BaseBodyParsedWitness,
    base_binding: Step11VerifiedSurfaceBinding,
    *,
    inventory_result: SemanticObligationInventoryResult,
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    obligation_by_id: Mapping[str, Mapping[str, Any]],
    receptions: Sequence[
        tuple[str, str, str, tuple[str, ...], tuple[str, ...]]
    ],
) -> tuple[
    tuple[
        str,
        str,
        str,
        tuple[str, ...],
        tuple[str, ...],
        int,
        int,
        str,
    ],
    ...,
]:
    """Rebuild exact base associations, then apply the frozen bounded schedule."""

    try:
        projection = _project_input(current_input)
        contracts = _independent_reception_owner_contract(
            snapshot=inventory_result.source_snapshot,
            by_id=obligation_by_id,
            discourse_plan=discourse_plan,
            projection=projection,
        )
    except (Step11InverseSurfaceError, AttributeError, TypeError, ValueError):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_SOURCE_REVALIDATION_FAILED"
        ) from None
    base_witness = base_body_witness.base_witness
    observation_sentences = tuple(
        row for row in base_witness.sentences if row.section_role == "observation"
    )
    reception_sentences = tuple(
        row for row in base_witness.sentences if row.section_role == "reception"
    )
    if (
        len(observation_sentences) != base_body_witness.observation_group_count
        or len(reception_sentences) != base_body_witness.reception_group_count
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_RECEPTION_LAYOUT_MISMATCH"
        )
    atom_by_id = {row.atom_id: row for row in base_witness.atoms}
    integrated_ids = tuple(base_binding.integrated_reception_binding_ids)
    contract_ids = tuple(str(row["binding_id"]) for row in contracts.values())
    if (
        len(integrated_ids) != len(set(integrated_ids))
        or set(integrated_ids) != set(contract_ids)
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_RECEPTION_CONTRACT_MISMATCH"
        )
    exact_line_by_opportunity: dict[str, int] = {}
    for binding_row in base_binding.binding_rows:
        obligation_id = str(binding_row.obligation_id)
        contract = contracts.get(obligation_id)
        if contract is None:
            continue
        ledger_row = obligation_by_id.get(obligation_id)
        opportunity_ids = tuple(
            str(row) for row in contract["source_reception_opportunity_ids"]
        )
        if (
            ledger_row is None
            or type(ledger_row.get("reception_opportunity_ids")) is not list
            or tuple(ledger_row["reception_opportunity_ids"])
            != opportunity_ids
            or len(binding_row.atom_ids) != 1
            or str(contract["binding_id"]) not in integrated_ids
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_BASE_RECEPTION_CONTRACT_MISMATCH"
            )
        atom = atom_by_id.get(str(binding_row.atom_ids[0]))
        if (
            atom is None
            or atom.section_role != "reception"
            or atom.reception_act not in contract["allowed_response_acts"]
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_BASE_RECEPTION_CONTRACT_MISMATCH"
            )
        line_ordinal = (
            int(atom.sentence_ordinal)
            - base_body_witness.observation_group_count
        )
        if not 1 <= line_ordinal <= base_body_witness.reception_group_count:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_BASE_RECEPTION_LAYOUT_MISMATCH"
            )
        for opportunity_id in opportunity_ids:
            previous = exact_line_by_opportunity.get(opportunity_id)
            if previous is not None:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_RECEPTION_ASSOCIATION_AMBIGUOUS"
                )
            exact_line_by_opportunity[opportunity_id] = line_ordinal

    group_count = base_body_witness.reception_group_count
    loads = {ordinal: 0 for ordinal in range(1, group_count + 1)}
    scheduled: list[
        tuple[
            str,
            str,
            str,
            tuple[str, ...],
            tuple[str, ...],
            int,
            int,
            str,
        ]
    ] = []
    for source_id, scope, act, targets, supports in receptions:
        line_ordinal = exact_line_by_opportunity.get(source_id)
        if line_ordinal is None:
            available = tuple(
                ordinal
                for ordinal in range(1, group_count + 1)
                if loads[ordinal]
                < _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX
            )
            if not available:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_RECEPTION_DENSITY_UNSATISFIABLE"
                )
            line_ordinal = min(
                available, key=lambda row: (loads[row], row)
            )
            basis = "required_opportunity_bounded_schedule"
        else:
            basis = "exact_base_opportunity_id"
        loads[line_ordinal] += 1
        if (
            loads[line_ordinal]
            > _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_DENSITY_UNSATISFIABLE"
            )
        scheduled.append(
            (
                source_id,
                scope,
                act,
                targets,
                supports,
                line_ordinal,
                loads[line_ordinal],
                basis,
            )
        )
    if set(exact_line_by_opportunity) - {row[0] for row in receptions}:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_ASSOCIATION_MISMATCH"
        )
    return tuple(scheduled)


def _step11_rc0030_validate_semantic_placement(
    base_witness: Step11ParsedSurfaceWitness,
    base_binding: Step11VerifiedSurfaceBinding,
    *,
    records: Sequence[tuple[str, str, str, str, tuple[str, ...]]],
    parsed_atoms: Sequence[Step11Rc0030ParsedSemanticAtom],
    parsed_source_ids: Sequence[str],
    reused_source_ids: frozenset[str],
    source_owner_aliases: Mapping[str, frozenset[str]],
    owner_text: Mapping[str, str],
) -> None:
    """Independently reproduce max-two packing and owner-ready deferral."""

    phrase_binding_by_key: dict[tuple[str, str, str], list[Any]] = {}
    for row in base_binding.grounded_phrase_bindings:
        phrase_binding_by_key.setdefault(
            (
                str(row.atom_id),
                str(row.visible_feature_fingerprint_sha256),
                str(row.phrase_profile_id),
            ),
            [],
        ).append(row)
    positions_by_owner: dict[str, set[tuple[int, int]]] = {
        owner_id: set() for owner_id in source_owner_aliases
    }
    for atom in base_witness.atoms:
        if atom.section_role != "observation":
            continue
        for phrase in atom.grounded_phrases:
            rows = phrase_binding_by_key.get(
                (
                    str(atom.atom_id),
                    str(phrase.visible_feature_fingerprint_sha256),
                    str(phrase.phrase_profile_id),
                ),
                (),
            )
            if len(rows) != 1:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_OWNER_BASE_POSITION_AMBIGUOUS"
                )
            bound_ids = {str(row) for row in rows[0].owner_nucleus_ids}
            for owner_id, aliases in source_owner_aliases.items():
                if (
                    phrase.phrase_text == owner_text.get(owner_id)
                    and aliases & bound_ids
                ):
                    positions_by_owner[owner_id].add(
                        (
                            int(atom.sentence_ordinal),
                            int(atom.grammatical_chunk_ordinal),
                        )
                    )
    owner_position: dict[str, tuple[int, int]] = {}
    for owner_id, positions in positions_by_owner.items():
        if len(positions) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_BASE_POSITION_AMBIGUOUS"
            )
        owner_position[owner_id] = next(iter(positions))

    grammar = STEP11_SURFACE_CATALOG["group_grammar"]
    maximum_group_clauses = int(
        grammar["maximum_observation_clauses_per_sentence"]
    )
    maximum_chunk_clauses = int(
        grammar["maximum_visible_clauses_per_grammatical_sentence"]
    )
    maximum_chunk_load = int(
        grammar["maximum_grammatical_complexity_load"]
    )
    maximum_group_joiners = int(
        grammar["maximum_repeated_joiner_per_group"]
    )
    observation_sentences = tuple(
        row for row in base_witness.sentences if row.section_role == "observation"
    )
    if not observation_sentences:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_OBSERVATION_LAYOUT_INVALID"
        )
    chunk_clause_count: dict[tuple[int, int], int] = {}
    chunk_complexity_load: dict[tuple[int, int], int] = {}
    base_unit_count_by_group: dict[int, int] = {}
    for sentence in observation_sentences:
        group_ordinal = int(sentence.sentence_ordinal)
        base_unit_count_by_group[group_ordinal] = len(
            sentence.clause_atom_ids
        )
        for chunk_ordinal, count in enumerate(
            sentence.grammatical_chunk_clause_counts, 1
        ):
            chunk_clause_count[(group_ordinal, chunk_ordinal)] = int(count)
            atoms = tuple(
                row
                for row in base_witness.atoms
                if row.section_role == "observation"
                and row.sentence_ordinal == group_ordinal
                and row.grammatical_chunk_ordinal == chunk_ordinal
            )
            load = 0
            for atom in atoms:
                references = {
                    row.reference_ordinal
                    for row in (
                        *((atom.introduced_reference,)
                          if atom.introduced_reference is not None else ()),
                        *atom.relation_endpoint_references,
                        *atom.unknown_target_references,
                        *atom.compound_label_references,
                        *atom.reception_antecedent_references,
                    )
                }
                load += max(1, len(references))
            chunk_complexity_load[(group_ordinal, chunk_ordinal)] = load
    base_tail_chunk_by_group = {
        group_ordinal: max(
            chunk
            for (group, chunk) in chunk_clause_count
            if group == group_ordinal
        )
        for group_ordinal in base_unit_count_by_group
    }

    pending_by_group: dict[int, list[tuple[Any, ...]]] = {}
    for source_id, family, _key, _direction, owner_ids in records:
        if source_id in reused_source_ids:
            continue
        try:
            positions = tuple(owner_position[row] for row in owner_ids)
        except KeyError:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_BASE_POSITION_UNRESOLVED"
            ) from None
        group_ordinals = tuple(row[0] for row in positions)
        target_group = max(group_ordinals)
        target_chunk = max(
            row[1] for row in positions if row[0] == target_group
        )
        pending_by_group.setdefault(target_group, []).append(
            (source_id, family, owner_ids, target_chunk)
        )

    structure_count_by_group = {
        group_ordinal: 0 for group_ordinal in base_unit_count_by_group
    }
    group_ordinals = tuple(sorted(base_unit_count_by_group))
    if group_ordinals != tuple(range(1, len(group_ordinals) + 1)):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_OBSERVATION_LAYOUT_INVALID"
        )
    last_group_ordinal = group_ordinals[-1]
    planned_packs_by_group: dict[
        int, list[tuple[int, str, tuple[str, ...]]]
    ] = {}
    for ready_group_ordinal in sorted(pending_by_group):
        ordered = sorted(
            pending_by_group[ready_group_ordinal],
            key=lambda row: (row[3], row[1], row[2], row[0]),
        )
        raw_packs: list[list[tuple[Any, ...]]] = []
        for row in ordered:
            for pack in raw_packs:
                owners = {
                    owner_id
                    for item in (*pack, row)
                    for owner_id in item[2]
                }
                if len(pack) < 2 and len(owners) <= maximum_chunk_load:
                    pack.append(row)
                    break
            else:
                raw_packs.append([row])
        for pack in raw_packs:
            owner_count = len(
                {owner_id for item in pack for owner_id in item[2]}
            )
            pack_load = max(owner_count, len(pack))
            preferred_chunk = max(int(item[3]) for item in pack)
            chosen_group: int | None = None
            chosen_chunk: int | None = None
            for destination_group in range(
                ready_group_ordinal, last_group_ordinal + 1
            ):
                tail_chunk = max(
                    chunk
                    for (group, chunk) in chunk_clause_count
                    if group == destination_group
                )
                minimum_chunk = (
                    preferred_chunk
                    if destination_group == ready_group_ordinal
                    else 1
                )
                if tail_chunk < minimum_chunk:
                    raise Step11Rc0030ExperimentInverseSurfaceError(
                        "STEP11_RC0030_OWNER_BASE_POSITION_UNRESOLVED"
                    )
                for candidate_chunk in (tail_chunk, tail_chunk + 1):
                    current_clause_count = chunk_clause_count.get(
                        (destination_group, candidate_chunk), 0
                    )
                    current_complexity_load = chunk_complexity_load.get(
                        (destination_group, candidate_chunk), 0
                    )
                    projected_clause_count = current_clause_count + 1
                    projected_complexity_load = (
                        current_complexity_load + pack_load
                    )
                    projected_joiner_count = sum(
                        max(
                            0,
                            (
                                projected_clause_count
                                if chunk == candidate_chunk
                                else count
                            )
                            - 1,
                        )
                        for (group, chunk), count in chunk_clause_count.items()
                        if group == destination_group
                    )
                    if candidate_chunk not in {
                        chunk
                        for group, chunk in chunk_clause_count
                        if group == destination_group
                    }:
                        projected_joiner_count += max(
                            0, projected_clause_count - 1
                        )
                    if (
                        base_unit_count_by_group[destination_group]
                        + structure_count_by_group[destination_group]
                        + 1
                        <= maximum_group_clauses
                        and projected_clause_count
                        <= maximum_chunk_clauses
                        and projected_complexity_load
                        <= maximum_chunk_load
                        and projected_joiner_count
                        <= maximum_group_joiners
                    ):
                        chosen_group = destination_group
                        chosen_chunk = candidate_chunk
                        break
                if chosen_group is not None:
                    break
            if chosen_group is None or chosen_chunk is None:
                raise Step11Rc0030ExperimentInverseSurfaceError(
                    "STEP11_RC0030_SEMANTIC_PLACEMENT_DENSITY_INVALID"
                )
            chunk_clause_count.setdefault((chosen_group, chosen_chunk), 0)
            chunk_complexity_load.setdefault((chosen_group, chosen_chunk), 0)
            chunk_clause_count[(chosen_group, chosen_chunk)] += 1
            chunk_complexity_load[(chosen_group, chosen_chunk)] += pack_load
            structure_count_by_group[chosen_group] += 1
            source_ids = tuple(sorted(str(item[0]) for item in pack))
            unit_id = "nls3s11rc0030unit_" + artifact_sha256(
                {
                    "source_atom_ids": [str(item[0]) for item in pack],
                    "sentence_group_ordinal": chosen_group,
                    "chunk_ordinal": chosen_chunk,
                }
            )[:16]
            planned_packs_by_group.setdefault(chosen_group, []).append(
                (chosen_chunk, unit_id, source_ids)
            )

    expected_rows: list[tuple[str, int, int, int, int]] = []
    for group_ordinal in sorted(planned_packs_by_group):
        for pack_ordinal, (chunk, _unit_id, source_ids) in enumerate(
            sorted(planned_packs_by_group[group_ordinal]), 1
        ):
            for item_ordinal, source_id in enumerate(source_ids, 1):
                expected_rows.append(
                    (
                        source_id,
                        group_ordinal,
                        (
                            chunk
                            - base_tail_chunk_by_group[group_ordinal]
                            + 1
                        ),
                        pack_ordinal,
                        item_ordinal,
                    )
                )
    actual_rows = tuple(
        (
            source_id,
            atom.sentence_group_ordinal,
            atom.grammatical_chunk_ordinal,
            atom.pack_ordinal,
            atom.item_ordinal,
        )
        for source_id, atom in zip(parsed_source_ids, parsed_atoms)
    )
    if actual_rows != tuple(expected_rows):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SEMANTIC_PLACEMENT_MISMATCH"
        )


def _step11_rc0030_verified_binding_material(
    value: Step11Rc0030ExperimentVerifiedSurfaceBinding,
) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "base_witness_sha256": value.base_witness_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "semantic_bindings": [
            {
                "source_atom_id": row.source_atom_id,
                "semantic_family": row.semantic_family,
                "parsed_atom_id": row.parsed_atom_id,
                "verified_reuse_binding_sha256": (
                    row.verified_reuse_binding_sha256
                ),
                "match_basis": row.match_basis,
            }
            for row in value.semantic_bindings
        ],
        "reception_bindings": [
            {
                "source_reception_opportunity_id": (
                    row.source_reception_opportunity_id
                ),
                "source_scope": row.source_scope,
                "parsed_binding_id": row.parsed_binding_id,
                "reception_line_ordinal": row.reception_line_ordinal,
                "move_ordinal": row.move_ordinal,
                "reception_act": row.reception_act,
                "target_owner_count": row.target_owner_count,
                "supporting_owner_count": row.supporting_owner_count,
                "association_basis": row.association_basis,
            }
            for row in value.reception_bindings
        ],
        "reception_binding_count": value.reception_binding_count,
        "owner_binding_comparison_count": (
            value.owner_binding_comparison_count
        ),
        "unique_solution_count": value.unique_solution_count,
        "semantic_coverage_authorized": value.semantic_coverage_authorized,
        "issue_codes": list(value.issue_codes),
        "hard_verified": value.hard_verified,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def step11_rc0030_experiment_verified_binding_material(
    value: Step11Rc0030ExperimentVerifiedSurfaceBinding,
) -> dict[str, Any]:
    if type(value) is not Step11Rc0030ExperimentVerifiedSurfaceBinding:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_VERIFIED_BINDING_TYPE_INVALID"
        )
    basis_by_family = {
        "construction": "construction_instance_role_layout_exact",
        "relation": "relation_id_endpoint_direction_type_exact",
        "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
        "explicit_unknown": "unknown_id_dimension_exact_target",
    }
    semantic_source_ids = tuple(
        row.source_atom_id
        for row in value.semantic_bindings
        if type(row) is Step11Rc0030VerifiedSemanticBinding
    )
    parsed_ids = tuple(
        row.parsed_atom_id
        for row in value.semantic_bindings
        if type(row) is Step11Rc0030VerifiedSemanticBinding
        and row.parsed_atom_id is not None
    )
    reuse_hashes = tuple(
        row.verified_reuse_binding_sha256
        for row in value.semantic_bindings
        if type(row) is Step11Rc0030VerifiedSemanticBinding
        and row.verified_reuse_binding_sha256 is not None
    )
    reception_source_ids = tuple(
        row.source_reception_opportunity_id
        for row in value.reception_bindings
        if type(row) is Step11Rc0030VerifiedReceptionBinding
    )
    reception_parsed_ids = tuple(
        row.parsed_binding_id
        for row in value.reception_bindings
        if type(row) is Step11Rc0030VerifiedReceptionBinding
    )
    reception_positions = tuple(
        (row.reception_line_ordinal, row.move_ordinal)
        for row in value.reception_bindings
        if type(row) is Step11Rc0030VerifiedReceptionBinding
    )
    if (
        value.schema_version
        != STEP11_RC0030_EXPERIMENT_VERIFIED_BINDING_SCHEMA
        or any(
            type(row) is not str
            or _STEP11_RC0030_SHA256_RE.fullmatch(row) is None
            for row in (
                value.parsed_witness_sha256,
                value.base_witness_sha256,
                value.successor_snapshot_sha256,
                value.source_authority_sha256,
                value.experiment_catalog_sha256,
            )
        )
        or type(value.semantic_bindings) is not tuple
        or not 0
        <= len(value.semantic_bindings)
        <= _STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX
        or len(semantic_source_ids) != len(value.semantic_bindings)
        or any(type(row) is not str or not row for row in semantic_source_ids)
        or len(semantic_source_ids) != len(set(semantic_source_ids))
        or any(type(row) is not str for row in parsed_ids)
        or len(parsed_ids) != len(set(parsed_ids))
        or any(type(row) is not str for row in reuse_hashes)
        or len(reuse_hashes) != len(set(reuse_hashes))
        or any(
            not row.source_atom_id
            or row.semantic_family not in basis_by_family
            or row.match_basis != basis_by_family.get(row.semantic_family)
            or (row.parsed_atom_id is None)
            == (row.verified_reuse_binding_sha256 is None)
            or (
                row.parsed_atom_id is not None
                and (
                    type(row.parsed_atom_id) is not str
                    or re.fullmatch(
                        r"nls3s11rc0030atom_[0-9a-f]{16}",
                        row.parsed_atom_id,
                    )
                    is None
                )
            )
            or (
                row.verified_reuse_binding_sha256 is not None
                and (
                    type(row.verified_reuse_binding_sha256) is not str
                    or _STEP11_RC0030_SHA256_RE.fullmatch(
                        row.verified_reuse_binding_sha256
                    )
                    is None
                )
            )
            for row in value.semantic_bindings
        )
        or type(value.reception_bindings) is not tuple
        or type(value.reception_binding_count) is not int
        or not 1
        <= value.reception_binding_count
        <= _STEP11_RC0030_RECEPTION_MOVE_MAX
        or value.reception_binding_count != len(value.reception_bindings)
        or len(reception_source_ids) != len(value.reception_bindings)
        or any(
            type(row) is not str or not row for row in reception_source_ids
        )
        or len(reception_source_ids) != len(set(reception_source_ids))
        or any(type(row) is not str for row in reception_parsed_ids)
        or len(reception_parsed_ids) != len(set(reception_parsed_ids))
        or any(
            type(line_ordinal) is not int or type(move_ordinal) is not int
            for line_ordinal, move_ordinal in reception_positions
        )
        or len(reception_positions) != len(set(reception_positions))
        or any(
            type(row.source_scope) is not str
            or not row.source_scope
            or type(row.parsed_binding_id) is not str
            or re.fullmatch(
                r"nls3s11rc0030recv_[0-9a-f]{16}",
                row.parsed_binding_id,
            )
            is None
            or type(row.reception_line_ordinal) is not int
            or not 1 <= row.reception_line_ordinal <= 3
            or type(row.move_ordinal) is not int
            or row.move_ordinal not in {1, 2}
            or type(row.reception_act) is not str
            or not row.reception_act
            or type(row.target_owner_count) is not int
            or not 1 <= row.target_owner_count <= _STEP11_RC0030_OWNER_MAX
            or type(row.supporting_owner_count) is not int
            or not 0 <= row.supporting_owner_count <= _STEP11_RC0030_OWNER_MAX
            or row.target_owner_count + row.supporting_owner_count
            > _STEP11_RC0030_OWNER_MAX
            or row.association_basis
            not in {
                "exact_base_opportunity_id",
                "required_opportunity_bounded_schedule",
            }
            for row in value.reception_bindings
        )
        or type(value.owner_binding_comparison_count) is not int
        or not 0
        <= value.owner_binding_comparison_count
        <= _STEP11_RC0030_OWNER_COMPARISON_MAX
        or type(value.unique_solution_count) is not int
        or value.unique_solution_count != 1
        or value.semantic_coverage_authorized is not False
        or type(value.issue_codes) is not tuple
        or value.issue_codes != ()
        or value.hard_verified is not True
        or value.body_free_export_allowed is not False
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_VERIFIED_BINDING_INVALID"
        )
    return _step11_rc0030_verified_binding_material(value)


def _step11_rc0030_expected_base_prefix_commitments(
    base_body_witness: Step11Rc0030BaseBodyParsedWitness,
    witness: Step11Rc0030ExperimentParsedSurfaceWitness,
) -> tuple[str, ...]:
    step11_rc0030_base_body_parsed_witness_material(base_body_witness)
    if base_body_witness.body_sha256 == witness.body_sha256:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_FINAL_EQUALS_BASE_SURFACE"
        )
    if (
        base_body_witness.observation_group_count
        != witness.observation_group_count
        or base_body_witness.reception_group_count
        != witness.reception_group_count
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_FINAL_GROUP_MISMATCH"
        )
    changed_groups = {
        row.sentence_group_ordinal for row in witness.semantic_atoms
    }
    return tuple(
        (
            base_body_witness.observation_stem_sha256[ordinal - 1]
            if ordinal in changed_groups
            else base_body_witness.observation_line_sha256[ordinal - 1]
        )
        for ordinal in range(1, witness.observation_group_count + 1)
    )


def match_step11_rc0030_experiment_surface(
    witness: Step11Rc0030ExperimentParsedSurfaceWitness,
    *,
    base_body_witness: Step11Rc0030BaseBodyParsedWitness,
    successor_snapshot: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
    verified_base_reuse_bindings: Sequence[
        Step11Rc0030VerifiedBaseBodyReuse
    ] = (),
) -> Step11Rc0030ExperimentVerifiedSurfaceBinding:
    """Independently bind final bytes and inverse-owned base reuse."""

    witness_material = step11_rc0030_experiment_parsed_witness_material(
        witness
    )
    catalog, catalog_sha = _step11_rc0030_inverse_catalog()
    if witness.experiment_catalog_sha256 != catalog_sha:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_CATALOG_COMMITMENT_MISMATCH"
        )
    step11_rc0030_base_body_parsed_witness_material(base_body_witness)
    base_witness = base_body_witness.base_witness
    if witness.base_prefix_commitments != (
        _step11_rc0030_expected_base_prefix_commitments(
            base_body_witness, witness
        )
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_PREFIX_COMMITMENT_MISMATCH"
        )
    base_binding = _step11_rc0030_revalidated_base_binding(
        base_witness,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
        current_input=current_input,
    )
    records, receptions, aliases, snapshot_sha, authority_sha, exact_aliases = (
        _step11_rc0030_validated_source_records(
            successor_snapshot,
            inventory_result=inventory_result,
        )
    )
    required_owner_ids = {
        owner_id for row in records for owner_id in row[4]
    } | {
        owner_id
        for row in receptions
        for owner_id in (*row[3], *row[4])
    }
    owner_text, comparison_count = _step11_rc0030_visible_phrase_registry(
        base_witness,
        base_binding,
        source_owner_aliases={
            owner_id: aliases[owner_id] for owner_id in required_owner_ids
        },
    )
    try:
        _ledger, obligation_by_id = _validated_parents(
            inventory_result, content_plan, discourse_plan
        )
    except Step11InverseSurfaceError:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_BINDING_REVALIDATION_FAILED"
        ) from None
    expected_by_signature: dict[
        tuple[str, str, str, tuple[str, ...]], list[str]
    ] = {}
    family_by_source: dict[str, str] = {}
    for source_id, family, key, direction, owner_ids in records:
        signature = _step11_rc0030_visible_signature(
            family=family,
            key=key,
            direction=direction,
            owner_ids=owner_ids,
            owner_text=owner_text,
            catalog=catalog,
        )
        expected_by_signature.setdefault(signature, []).append(source_id)
        family_by_source[source_id] = family
    if any(len(rows) != 1 for rows in expected_by_signature.values()):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SOURCE_SIGNATURE_AMBIGUOUS"
        )
    parsed_bindings: list[Step11Rc0030VerifiedSemanticBinding] = []
    parsed_source_ids: list[str] = []
    basis_by_family = {
        "construction": "construction_instance_role_layout_exact",
        "relation": "relation_id_endpoint_direction_type_exact",
        "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
        "explicit_unknown": "unknown_id_dimension_exact_target",
    }
    for atom in witness.semantic_atoms:
        signature = (
            atom.semantic_family,
            atom.semantic_key,
            atom.direction,
            atom.owner_expressions,
        )
        comparison_count += 1
        if comparison_count > _STEP11_RC0030_OWNER_COMPARISON_MAX:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_COMPARISON_BOUND_EXCEEDED"
            )
        source_ids = expected_by_signature.get(signature, ())
        if len(source_ids) != 1:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_SEMANTIC_BINDING_UNRESOLVED"
            )
        source_id = source_ids[0]
        parsed_source_ids.append(source_id)
        parsed_bindings.append(
            Step11Rc0030VerifiedSemanticBinding(
                source_atom_id=source_id,
                semantic_family=atom.semantic_family,
                parsed_atom_id=atom.atom_id,
                verified_reuse_binding_sha256=None,
                match_basis=basis_by_family[atom.semantic_family],
            )
        )
    reuse_rows = tuple(verified_base_reuse_bindings)
    independently_allowed_reuse = _step11_rc0030_derive_allowed_base_reuse(
        base_witness,
        base_binding,
        records=records,
        owner_text=owner_text,
        authority_sha=authority_sha,
        exact_aliases=exact_aliases,
        obligation_by_id=obligation_by_id,
        catalog=catalog,
    )
    allowed_reuse_by_source = {
        row.source_atom_id: row for row in independently_allowed_reuse
    }
    if len(allowed_reuse_by_source) != len(independently_allowed_reuse):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_BASE_REUSE_AMBIGUOUS"
        )
    reuse_source_ids: list[str] = []
    reuse_bindings: list[Step11Rc0030VerifiedSemanticBinding] = []
    for row in reuse_rows:
        step11_rc0030_verified_base_body_reuse_material(row)
        if (
            allowed_reuse_by_source.get(row.source_atom_id) != row
            or
            row.base_surface_sha256 != base_witness.body_sha256
            or row.source_authority_sha256 != authority_sha
            or family_by_source.get(row.source_atom_id) != row.semantic_family
            or row.match_basis != basis_by_family.get(row.semantic_family)
        ):
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_BASE_REUSE_SOURCE_MISMATCH"
            )
        reuse_source_ids.append(row.source_atom_id)
        reuse_bindings.append(
            Step11Rc0030VerifiedSemanticBinding(
                source_atom_id=row.source_atom_id,
                semantic_family=row.semantic_family,
                parsed_atom_id=None,
                verified_reuse_binding_sha256=(
                    row.independent_binding_sha256
                ),
                match_basis=row.match_basis,
            )
        )
    expected_ids = tuple(row[0] for row in records)
    if (
        len(parsed_source_ids) != len(set(parsed_source_ids))
        or len(reuse_source_ids) != len(set(reuse_source_ids))
        or set(parsed_source_ids) & set(reuse_source_ids)
        or set((*parsed_source_ids, *reuse_source_ids)) != set(expected_ids)
        or len(parsed_source_ids) + len(reuse_source_ids) != len(expected_ids)
    ):
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_SEMANTIC_COVERAGE_XOR_INVALID"
        )
    semantic_owner_ids = {
        owner_id for row in records for owner_id in row[4]
    }
    _step11_rc0030_validate_semantic_placement(
        base_witness,
        base_binding,
        records=records,
        parsed_atoms=witness.semantic_atoms,
        parsed_source_ids=parsed_source_ids,
        reused_source_ids=frozenset(reuse_source_ids),
        source_owner_aliases={
            owner_id: aliases[owner_id] for owner_id in semantic_owner_ids
        },
        owner_text={
            owner_id: owner_text[owner_id] for owner_id in semantic_owner_ids
        },
    )
    joiner = catalog["clause_morphology"]["target_join"]
    scheduled_receptions = _step11_rc0030_reception_schedule(
        base_body_witness,
        base_binding,
        inventory_result=inventory_result,
        discourse_plan=discourse_plan,
        current_input=current_input,
        obligation_by_id=obligation_by_id,
        receptions=receptions,
    )
    parsed_reception_by_signature: dict[
        tuple[int, int, str, str, str | None],
        Step11Rc0030ParsedReceptionBinding,
    ] = {}
    for row in witness.reception_bindings:
        signature = (
            row.reception_line_ordinal,
            row.move_ordinal,
            row.reception_act,
            row.target_expression,
            row.supporting_expression,
        )
        if signature in parsed_reception_by_signature:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_BINDING_AMBIGUOUS"
            )
        parsed_reception_by_signature[signature] = row
    verified_receptions: list[Step11Rc0030VerifiedReceptionBinding] = []
    consumed_parsed_ids: set[str] = set()
    for (
        source_id,
        scope,
        act,
        targets,
        supports,
        line_ordinal,
        move_ordinal,
        association_basis,
    ) in scheduled_receptions:
        signature = (
            line_ordinal,
            move_ordinal,
            act,
            joiner.join(owner_text[row] for row in targets),
            (
                joiner.join(owner_text[row] for row in supports)
                if supports
                else None
            ),
        )
        comparison_count += 1
        if comparison_count > _STEP11_RC0030_OWNER_COMPARISON_MAX:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_OWNER_COMPARISON_BOUND_EXCEEDED"
            )
        parsed = parsed_reception_by_signature.get(signature)
        if parsed is None or parsed.binding_id in consumed_parsed_ids:
            raise Step11Rc0030ExperimentInverseSurfaceError(
                "STEP11_RC0030_RECEPTION_BINDING_MISMATCH"
            )
        consumed_parsed_ids.add(parsed.binding_id)
        verified_receptions.append(
            Step11Rc0030VerifiedReceptionBinding(
                source_reception_opportunity_id=source_id,
                source_scope=scope,
                parsed_binding_id=parsed.binding_id,
                reception_line_ordinal=line_ordinal,
                move_ordinal=move_ordinal,
                reception_act=act,
                target_owner_count=len(targets),
                supporting_owner_count=len(supports),
                association_basis=association_basis,
            )
        )
    if consumed_parsed_ids != {
        row.binding_id for row in witness.reception_bindings
    }:
        raise Step11Rc0030ExperimentInverseSurfaceError(
            "STEP11_RC0030_RECEPTION_BINDING_MISMATCH"
        )
    result = Step11Rc0030ExperimentVerifiedSurfaceBinding(
        schema_version=STEP11_RC0030_EXPERIMENT_VERIFIED_BINDING_SCHEMA,
        parsed_witness_sha256=artifact_sha256(witness_material),
        base_witness_sha256=artifact_sha256(_witness_material(base_witness)),
        successor_snapshot_sha256=snapshot_sha,
        source_authority_sha256=authority_sha,
        experiment_catalog_sha256=catalog_sha,
        semantic_bindings=tuple((*parsed_bindings, *reuse_bindings)),
        reception_bindings=tuple(verified_receptions),
        reception_binding_count=len(verified_receptions),
        owner_binding_comparison_count=comparison_count,
        unique_solution_count=1,
        semantic_coverage_authorized=False,
        issue_codes=(),
        hard_verified=True,
    )
    step11_rc0030_experiment_verified_binding_material(result)
    return result


__all__ += [
    "STEP11_RC0030_BASE_BODY_PARSED_WITNESS_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_PARSED_WITNESS_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_VERIFIED_BINDING_SCHEMA",
    "STEP11_RC0030_VERIFIED_BASE_REUSE_SCHEMA",
    "Step11Rc0030ExperimentInverseSurfaceError",
    "Step11Rc0030BaseBodyParsedWitness",
    "Step11Rc0030ExperimentParsedSurfaceWitness",
    "Step11Rc0030ExperimentVerifiedSurfaceBinding",
    "Step11Rc0030ParsedReceptionBinding",
    "Step11Rc0030ParsedSemanticAtom",
    "Step11Rc0030VerifiedBaseBodyReuse",
    "Step11Rc0030VerifiedReceptionBinding",
    "Step11Rc0030VerifiedSemanticBinding",
    "match_step11_rc0030_base_body_exact_reuse",
    "match_step11_rc0030_experiment_surface",
    "parse_step11_rc0030_base_body_exact_reuse",
    "parse_step11_rc0030_experiment_surface",
    "step11_rc0030_experiment_parsed_witness_material",
    "step11_rc0030_experiment_verified_binding_material",
    "step11_rc0030_base_body_parsed_witness_material",
    "step11_rc0030_verified_base_body_reuse_material",
]
