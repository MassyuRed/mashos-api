# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent inverse parser and semantic matcher for rc0024.

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
from typing import Any, Mapping, Sequence

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
    "cocolon.emlis.nls_v3.step11_parsed_surface_witness.v6"
)
STEP11_VERIFIED_BINDING_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_verified_surface_binding.v6"
)
STEP11_SOURCE_UNKNOWN_ORACLE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_source_unknown_oracle.rc0024.v1"
)
STEP11_HARD_GATE_SCHEMA = "cocolon.emlis.nls_v3.step11_hard_gate_result.v3"
STEP11_SELECTION_SCHEMA = "cocolon.emlis.nls_v3.step11_selection_result.v3"
STEP11_CANDIDATE_VERSION_ID = "nls_v3_rc_0024"

_SLOT_ORDER = {"thought": 0, "action": 1, "emotion": 2, "category": 3}
_SOURCE_FIELD_TO_SLOT = {
    "memo": "thought",
    "memo_action": "action",
    "emotion_details": "emotion",
    "emotions": "emotion",
    "category": "category",
}
_BASE_NUCLEUS_SPAN_RE = re.compile(r"^nucleus:(s[1-9][0-9]*)$")
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


@dataclass(frozen=True, slots=True)
class Step11GateOutcome:
    ordinal: int
    gate_id: str
    passed: bool
    failure_code: str | None


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
    selector_attributes: tuple[int, ...]


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


def _direct_introduction_clause(
    clause: str,
) -> tuple[str, Step11EndpointReference, tuple[str, ...]] | None:
    skeleton, fragments = _scan_quoted(clause)
    if len(fragments) != 1:
        return None
    grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    direct = grammar["direct_introduction"]
    role_labels = grammar["role_labels"]
    ordinal_pattern = str(grammar["ordinal_pattern"])
    matches: list[tuple[str, Step11EndpointReference]] = []
    for role, role_label in role_labels.items():
        token = rf"(?P<ordinal>{ordinal_pattern})つ目の{re.escape(str(role_label))}"
        for index, stem in enumerate(direct["stems"]):
            expected = str(direct["wrapper"]).format(
                reference="__REFERENCE__",
                stem=str(stem).format(quoted_literal="\x00"),
            )
            pattern = re.escape(expected).replace(
                re.escape("__REFERENCE__"), token
            )
            match = re.fullmatch(pattern, skeleton)
            if match is not None:
                matches.append(
                    (
                        f"reference_introduction:{role}:{index}",
                        Step11EndpointReference(
                            reference_ordinal=int(match.group("ordinal")),
                            endpoint_role=str(role),
                        ),
                    )
                )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_REFERENCE_INTRODUCTION_AMBIGUOUS"
        )
    return matches[0][0], matches[0][1], fragments


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
    tuple[Step11EndpointReference, Step11EndpointReference],
    tuple[str, str],
] | None:
    """Parse the current rc0024 positive/negative compound independently."""

    skeleton, fragments = _scan_quoted(clause)
    if len(fragments) != 2:
        return None
    grammar = STEP11_SURFACE_CATALOG.get(
        "mixed_emotion_compound_grammar"
    )
    reference_grammar = STEP11_SURFACE_CATALOG[
        "endpoint_reference_grammar"
    ]
    if type(grammar) is not dict or type(grammar.get("forms")) is not list:
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_COMPOUND_CATALOG_INVALID"
        )
    role_label = str(reference_grammar["role_labels"]["affect"])
    ordinal_pattern = str(reference_grammar["ordinal_pattern"])
    positive_token = (
        rf"(?P<positive_ordinal>{ordinal_pattern})つ目の"
        + re.escape(role_label)
    )
    negative_token = (
        rf"(?P<negative_ordinal>{ordinal_pattern})つ目の"
        + re.escape(role_label)
    )
    matches: list[
        tuple[
            str,
            tuple[Step11EndpointReference, Step11EndpointReference],
        ]
    ] = []
    for index, template in enumerate(grammar["forms"]):
        expected = str(template).format(
            positive_ref="__POSITIVE_REFERENCE__",
            positive_literal="\x00",
            negative_ref="__NEGATIVE_REFERENCE__",
            negative_literal="\x00",
        )
        pattern = re.escape(expected).replace(
            re.escape("__POSITIVE_REFERENCE__"), positive_token
        ).replace(
            re.escape("__NEGATIVE_REFERENCE__"), negative_token
        )
        match = re.fullmatch(pattern, skeleton)
        if match is None:
            continue
        references = (
            Step11EndpointReference(
                int(match.group("positive_ordinal")), "affect"
            ),
            Step11EndpointReference(
                int(match.group("negative_ordinal")), "affect"
            ),
        )
        if references[0].reference_ordinal == references[1].reference_ordinal:
            raise Step11InverseSurfaceError(
                "S11_PARSE_MIXED_EMOTION_COMPOUND_REFERENCE_DUPLICATE"
            )
        matches.append(
            (f"mixed_emotion_compound:{index}", references)
        )
    if not matches:
        return None
    if len(matches) != 1:
        raise Step11InverseSurfaceError(
            "S11_PARSE_MIXED_EMOTION_COMPOUND_AMBIGUOUS"
        )
    return matches[0][0], matches[0][1], (fragments[0], fragments[1])


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
    """Parse a visible rc0024 local-referent reception clause."""

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
                if section == "observation":
                    introduction = _direct_introduction_clause(clause)
                    relation = _reference_relation_clause(clause)
                    mixed_compound = _mixed_emotion_compound_clause(
                        clause
                    )
                    unknown_reference = _unknown_reference_clause(clause)
                    if sum(
                        value is not None
                        for value in (
                            introduction,
                            relation,
                            mixed_compound,
                            unknown_reference,
                        )
                    ) > 1:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_OBSERVATION_FORM_AMBIGUOUS"
                        )
                    if mixed_compound is not None:
                        (
                            form_id,
                            compound_label_references,
                            fragments,
                        ) = mixed_compound
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
                        form_id, introduced_reference, fragments = introduction
                        claims = ("nucleus_notice",)
                        hints: tuple[str, ...] = ()
                        relation_type = direction = unknown = None
                        endpoint_roles = ()
                        denial = False
                        act = scope = explicit_status = None
                        predicate_role = introduced_reference.endpoint_role
                        realization_status = "undetermined"
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
                        (
                            form_id,
                            act,
                            scope,
                            explicit_status,
                            reception_antecedent_references,
                        ) = typed_reception
                        fragments = ()
                        hints = {
                            "thought": ("thought",),
                            "action": ("action",),
                            "thought_action": ("thought", "action"),
                            "relation": (),
                            "relation_action": ("action",),
                        }[scope]
                    else:
                        skeleton, fragments = _scan_quoted(clause)
                        reception = reception_patterns.get(skeleton)
                        if reception is None:
                            raise Step11InverseSurfaceError(
                                "S11_PARSE_RECEPTION_FORM_UNKNOWN"
                            )
                        form_id, act, scope, explicit_status, hints = reception
                    claims = ("bound_reception",)
                    expected_arity = (
                        0
                        if form_id.startswith("reception:typed:")
                        or form_id.startswith("reception:anaphoric:")
                        else 2
                        if scope in {"thought_action", "relation"}
                        else 1
                    )
                    if len(fragments) != expected_arity:
                        raise Step11InverseSurfaceError(
                            "S11_PARSE_RECEPTION_FRAGMENT_ARITY_INVALID"
                        )
                    relation_type = direction = unknown = None
                    endpoint_roles = ()
                    denial = False
                    predicate_role = scope
                    realization_status = explicit_status
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
        if same_event:
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


def _independent_mixed_emotion_compound_issues(
    atoms: Sequence[Step11ParsedAtom],
    *,
    expected_positive_label: str,
    expected_negative_label: str,
    expected_references: tuple[
        Step11EndpointReference, Step11EndpointReference
    ],
) -> tuple[str, ...]:
    """Check compound ownership/order without any forward-plan metadata."""

    issues: set[str] = set()
    matches = tuple(
        row
        for row in atoms
        if type(row) is Step11ParsedAtom
        and row.form_id.startswith("mixed_emotion_compound:")
    )
    if not matches:
        issues.add("S11_MATCH_MIXED_EMOTION_COMPOUND_COVERAGE_MISMATCH")
        return tuple(sorted(issues))
    if len(matches) > 1:
        issues.add("S11_MATCH_MIXED_EMOTION_COMPOUND_DUPLICATE")
        return tuple(sorted(issues))
    atom = matches[0]
    if (
        atom.source_fragments
        != (expected_positive_label, expected_negative_label)
        or atom.compound_label_references != expected_references
        or atom.relation_endpoint_references != expected_references
    ):
        issues.add("S11_MATCH_MIXED_EMOTION_COMPOUND_ORDER_MISMATCH")
    if (
        atom.claim_kinds
        != ("nucleus_notice", "mixed_emotion_relation")
        or atom.source_slot_hints != ("emotion", "emotion")
        or atom.predicate_role != "affect"
        or atom.realization_status != "selected_label"
        or atom.relation_type != "coexists_with"
        or atom.relation_direction != "bidirectional"
        or atom.relation_endpoint_roles != ("affect", "affect")
        or atom.introduced_reference is not None
        or atom.unknown_target_references
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


def _independent_nucleus_source_ranges(
    current_input: Mapping[str, Any],
    *,
    projection: Mapping[str, Any],
    snapshot: Any,
    active_nucleus_ids: frozenset[str],
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
                source_range = (span, 0, len(str(span.raw_text)))
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
    """Rebuild rc0024 reception ownership without trusting the overlay."""

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
        )
    )
    allowed_by_slot = _authorised_fragments_by_slot(
        projection, semantic_overlay
    )
    fragment_slots, fragment_issues = _fragment_slots(
        witness, allowed_by_slot
    )
    issues = set(fragment_issues) | set(anchor_binding_issues)
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
    introduction_by_ordinal: dict[int, Step11ParsedAtom] = {}
    for atom in observation_atoms:
        introduced_rows = (
            atom.compound_label_references
            if atom.compound_label_references
            else (atom.introduced_reference,)
            if atom.introduced_reference is not None
            else ()
        )
        if not introduced_rows:
            continue
        expected_rows = tuple(
            reference_by_ordinal.get(row.reference_ordinal)
            if type(row) is Step11EndpointReference
            else None
            for row in introduced_rows
        )
        compound = bool(atom.compound_label_references)
        invalid = any(row is None for row in expected_rows)
        if not invalid:
            if compound:
                invalid = bool(
                    len(introduced_rows) != 2
                    or atom.introduced_reference is not None
                    or atom.claim_kinds
                    != ("nucleus_notice", "mixed_emotion_relation")
                    or atom.relation_endpoint_references
                    != introduced_rows
                    or atom.unknown_target_references
                    or atom.source_fragments
                    != tuple(row.source_literal for row in expected_rows)
                    or any(row.source_slot != "emotion" for row in expected_rows)
                    or any(
                        introduced.endpoint_role != expected.endpoint_role
                        for introduced, expected in zip(
                            introduced_rows, expected_rows
                        )
                    )
                    or not atom.form_id.startswith(
                        "mixed_emotion_compound:"
                    )
                )
            else:
                introduced = introduced_rows[0]
                expected = expected_rows[0]
                invalid = bool(
                    expected is None
                    or introduced.endpoint_role != expected.endpoint_role
                    or atom.claim_kinds != ("nucleus_notice",)
                    or atom.relation_endpoint_references
                    or atom.unknown_target_references
                    or atom.source_fragments != (expected.source_literal,)
                    or expected.source_slot
                    not in set(fragment_slots.get(atom.atom_id, ()))
                    or not atom.form_id.startswith(
                        f"reference_introduction:{expected.endpoint_role}:"
                    )
                )
        if invalid:
            issues.add("S11_MATCH_REFERENCE_INTRODUCTION_INVALID")
            continue
        for introduced in introduced_rows:
            if introduced.reference_ordinal in introduction_by_ordinal:
                issues.add("S11_MATCH_REFERENCE_INTRODUCTION_DUPLICATE")
                continue
            introduction_by_ordinal[introduced.reference_ordinal] = atom
    if set(introduction_by_ordinal) != set(reference_by_ordinal):
        issues.add("S11_MATCH_REFERENCE_INTRODUCTION_COVERAGE_MISMATCH")
    for atom in witness.atoms:
        if atom.section_role != "observation" and (
            atom.introduced_reference is not None
            or atom.compound_label_references
            or atom.relation_endpoint_references
            or atom.unknown_target_references
        ):
            issues.add("S11_MATCH_REFERENCE_SECTION_INVALID")
        if atom.section_role != "reception" and (
            atom.reception_antecedent_references
        ):
            issues.add("S11_MATCH_REFERENCE_SECTION_INVALID")
        for reference in (
            *atom.relation_endpoint_references,
            *atom.unknown_target_references,
            *atom.reception_antecedent_references,
        ):
            if type(reference) is not Step11EndpointReference:
                issues.add("S11_MATCH_REFERENCE_BEFORE_USE_INVALID")
                continue
            introduction = introduction_by_ordinal.get(
                reference.reference_ordinal
            )
            expected_reference = reference_by_ordinal.get(
                reference.reference_ordinal
            )
            if (
                expected_reference is None
                or reference.endpoint_role
                != expected_reference.endpoint_role
                or introduction is None
                or (
                    introduction.sentence_ordinal,
                    introduction.clause_ordinal,
                )
                > (atom.sentence_ordinal, atom.clause_ordinal)
                or (
                    (
                        introduction.sentence_ordinal,
                        introduction.clause_ordinal,
                    )
                    == (atom.sentence_ordinal, atom.clause_ordinal)
                    and reference not in atom.compound_label_references
                )
            ):
                issues.add("S11_MATCH_REFERENCE_BEFORE_USE_INVALID")
                if atom.relation_type is not None:
                    issues.add(
                        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
                    )
                if atom.form_id.startswith("unknown_anaphora:"):
                    issues.add(
                        "S11_MATCH_UNKNOWN_TARGET_REFERENCE_MISMATCH"
                    )
                if atom.reception_antecedent_references:
                    issues.add(
                        "S11_MATCH_RECEPTION_VISIBLE_REFERENT_UNBOUND"
                    )
    surface_active = frozenset(nucleus_anchor_texts)
    exact_nuclei_by_atom = {
        atom.atom_id: frozenset(
            nucleus_id
            for nucleus_id, texts in nucleus_anchor_texts.items()
            if texts
            and (
                bool(texts & set(atom.source_fragments))
                or atom.self_denial_not_fact
                and bool(
                    {_semantic_core_text(value) for value in texts}
                    & {
                        _semantic_core_text(value)
                        for value in atom.source_fragments
                    }
                )
            )
        )
        for atom in observation_atoms
    }
    for ordinal, introduction in introduction_by_ordinal.items():
        expected = reference_by_ordinal[ordinal]
        exact_nuclei_by_atom[introduction.atom_id] = frozenset(
            set(exact_nuclei_by_atom.get(introduction.atom_id, frozenset()))
            | set(expected.nucleus_ids)
        )
    for atom in observation_atoms:
        if not atom.relation_endpoint_references:
            continue
        resolved_reference_nuclei: set[str] = set()
        for reference in atom.relation_endpoint_references:
            if type(reference) is not Step11EndpointReference:
                continue
            expected = reference_by_ordinal.get(reference.reference_ordinal)
            if expected is not None:
                resolved_reference_nuclei.update(expected.nucleus_ids)
        exact_nuclei_by_atom[atom.atom_id] = frozenset(
            resolved_reference_nuclei
        )
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
        expected_references = (
            Step11EndpointReference(
                from_references[0].reference_ordinal,
                from_references[0].endpoint_role,
            ),
            Step11EndpointReference(
                to_references[0].reference_ordinal,
                to_references[0].endpoint_role,
            ),
        )
        expected_roles = (
            str(relation.from_endpoint_role),
            str(relation.to_endpoint_role),
        )
        expected_prefix = (
            f"relation:{relation.relation_type}:"
            f"{relation.relation_direction}:"
            f"{expected_roles[0]}:{expected_roles[1]}:"
        )
        matches = tuple(
            atom
            for atom in observation_atoms
            if atom.form_id.startswith(expected_prefix)
            and atom.claim_kinds == ("relation_notice",)
            and atom.source_fragments == ()
            and atom.introduced_reference is None
            and atom.relation_endpoint_references == expected_references
            and not atom.unknown_target_references
            and atom.relation_type == relation.relation_type
            and atom.relation_direction == relation.relation_direction
            and atom.relation_endpoint_roles == expected_roles
        )
        if len(matches) != 1:
            issues.add("S11_MATCH_RELATION_UNRESOLVED")
            issues.add("S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH")
            continue
        atom = matches[0]
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
        if len(atom.unknown_target_references) != 1:
            return ()
        typed_reference = atom.unknown_target_references[0]
        expected_reference = reference_by_ordinal.get(
            typed_reference.reference_ordinal
        )
        target_references = tuple(
            row
            for row in reference_registry
            if target_nucleus_ids
            and target_nucleus_ids <= set(row.nucleus_ids)
        )
        if (
            type(typed_reference) is not Step11EndpointReference
            or expected_reference is None
            or typed_reference.endpoint_role
            != expected_reference.endpoint_role
            or len(target_references) != 1
            or target_references[0] != expected_reference
        ):
            return ()
        return tuple(
            preceding
            for preceding in ordered_observation_atoms
            if preceding.byte_start < atom.byte_start
            and introduction_by_ordinal.get(
                typed_reference.reference_ordinal
            )
            is preceding
            and (
                preceding.introduced_reference == typed_reference
                or typed_reference in preceding.compound_label_references
            )
        )

    def relation_unknown_antecedents(
        atom: Step11ParsedAtom,
        *,
        target_nucleus_ids: set[str],
    ) -> tuple[Step11ParsedAtom, ...]:
        if (
            not target_nucleus_ids
            or len(atom.unknown_target_references) != 2
            or len(
                {
                    row.reference_ordinal
                    for row in atom.unknown_target_references
                    if type(row) is Step11EndpointReference
                }
            )
            != 2
        ):
            return ()
        return tuple(
            preceding
            for preceding in ordered_observation_atoms
            if preceding.byte_start < atom.byte_start
            and preceding.atom_id in authorised_relation_atom_ids
            and preceding.relation_type is not None
            and preceding.relation_endpoint_references
            == atom.unknown_target_references
            and set(
                exact_nuclei_by_atom.get(
                    preceding.atom_id, frozenset()
                )
            )
            == target_nucleus_ids
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
            wanted == "relation"
            and source_bound_relation_unknown
            and atom.atom_id in authorised_relation_atom_ids
            and "relation_notice" in atom.claim_kinds
            and target_nucleus_ids
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
            and exact_source_anchor_owns_target
        ):
            return True
        if atom.unknown_dimension_class != wanted:
            return False
        if atom.form_id.startswith("unknown_anaphora:"):
            if not anchor_texts or not atom.unknown_target_references:
                return False
            relation_antecedents = relation_unknown_antecedents(
                atom,
                target_nucleus_ids=target_nucleus_ids,
            )
            if relation_antecedents:
                return bool(
                    len(relation_antecedents) == 1
                    and exact_source_anchor_owns_target
                )
            if wanted == "relation" or source_bound_relation_unknown:
                # A relation-scoped unknown may bind both endpoints.  Keep
                # the existing strict relation antecedent: accepting a
                # nucleus-only or partial endpoint would both reject the
                # canonical relation surface and permit an unsafe partial
                # antecedent.
                return False
            if not exact_source_anchor_owns_target:
                return False
            # Non-relation unknowns may follow an exact source-backed nucleus
            # observation.  Independently recover every eligible antecedent
            # from the parsed body and source binding, then accept only one.
            # Empty-fragment unknown/self-denial atoms cannot become an
            # antecedent merely because they precede this line.
            candidates = nonrelation_unknown_antecedents(
                atom,
                target_nucleus_ids=target_nucleus_ids,
            )
            return len(candidates) == 1
        if not anchor_texts:
            return bool(
                atom.source_fragments
                and target_nucleus_ids
                <= set(
                    exact_nuclei_by_atom.get(atom.atom_id, frozenset())
                )
            )
        if (
            len(atom.source_fragments) == 1
            and atom.source_fragments[0] in anchor_texts
        ):
            return exact_source_anchor_owns_target
        return False

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
    # rc0024 independently reconstructs the first exact positive/negative
    # pair as one typed compound atom.  Additional labels remain independently
    # introduced source owners; no corpus-side semantic contract participates.
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
            compound_issues = _independent_mixed_emotion_compound_issues(
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
                if atom.form_id.startswith("mixed_emotion_compound:")
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
        nuclei = set(row.get("nucleus_ids", []))
        return tuple(
            atom.atom_id
            for atom in observation_atoms
            if nuclei
            and nuclei
            <= set(exact_nuclei_by_atom.get(atom.atom_id, frozenset()))
            and "nucleus_notice" in atom.claim_kinds
        )

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
        owner_valid = True
        for antecedent_id in expected["antecedent_obligation_ids"]:
            owners = obligation_observation_atom_ids(antecedent_id)
            if len(owners) != 1:
                owner_valid = False
                break
            antecedent_owner_ids.append(owners[0])
        for support_id in expected["supporting_obligation_ids"]:
            owners = obligation_observation_atom_ids(support_id)
            if len(owners) != 1:
                owner_valid = False
                break
            support_owner_ids.append(owners[0])
        antecedent_owner_ids = list(dict.fromkeys(antecedent_owner_ids))
        support_owner_ids = list(dict.fromkeys(support_owner_ids))
        owned_nuclei = {
            nucleus_id
            for atom_id in (*antecedent_owner_ids, *support_owner_ids)
            for nucleus_id in terminal_owned_nuclei_by_atom.get(
                atom_id,
                exact_nuclei_by_atom.get(atom_id, frozenset()),
            )
        }
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
            not atom.form_id.startswith("reception:typed:")
            or atom.source_fragments
            or not atom.reception_antecedent_references
        ):
            return None
        semantic_head = (
            atom.reception_act,
            atom.reception_scope,
            _canonical_status(atom.realization_status),
            tuple(
                (row.reference_ordinal, row.endpoint_role)
                for row in atom.reception_antecedent_references
            ),
        )
        candidates = tuple(
            signature
            for signature in allowed_reception_signatures
            if signature[:4] == semantic_head
        )
        if len(candidates) != 1:
            return None
        signature = candidates[0]
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
                claim_authorised = bool(atom.source_fragments) and bool(
                    atom_slots
                ) and atom_slots <= active_source_slots and (
                    claim == "source_context"
                    or bool(exact_nuclei_by_atom.get(atom.atom_id))
                    or atom.atom_id in authorised_unknown_atom_ids
                    or atom.atom_id in authorised_denial_atom_ids
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
                "bound_reception_typed_referent_exact_source_owner"
                if matched_reception_atoms
                and all(
                    atom.form_id.startswith("reception:typed:")
                    and atom.reception_antecedent_references
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
        source_fragment_count=sum(len(row.source_fragments) for row in witness.atoms),
        issue_codes=tuple(sorted(issues)),
        verified=not issues,
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
    "Step11HardGateResult",
    "Step11InverseSurfaceError",
    "Step11ParsedAtom",
    "Step11ParsedSentence",
    "Step11ParsedSurfaceWitness",
    "Step11SelectionResult",
    "Step11VerifiedSurfaceBinding",
    "evaluate_step11_natural_surface_candidate",
    "match_step11_natural_surface",
    "parse_step11_natural_surface",
    "select_step11_natural_surface_candidates",
]
