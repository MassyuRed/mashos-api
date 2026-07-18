# -*- coding: utf-8 -*-
from __future__ import annotations

"""Source-bound semantic overlay for the Step 11 rc0023 successor.

The frozen Step 4--6 owners remain the semantic authority.  This module adds a
closed, re-computable view needed by a natural surface successor when an
otherwise active relation was budget-deferred, or when ordinary Japanese
grammar carries an open boundary or a reported self-evaluation that the frozen
inventory did not type explicitly.

Only the four app input fields and independently revalidated Step 4--6
artifacts are accepted.  Corpus annotations, case identities, coverage
families, expected answers, and semantic-contract labels are neither imported
nor accepted by the API.
"""

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Mapping, Sequence

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import build_evidence_ledger
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
from emlis_ai_step11_planning_frontier_v3 import (
    Step11PlanningFrontier,
    build_step11_planning_frontier,
    step11_planning_frontier_material,
)


STEP11_SEMANTIC_OVERLAY_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_semantic_overlay.v6"
)
STEP11_SEMANTIC_OVERLAY_VERSION = "nls_v3_rc_0023"

_INPUT_KEYS = frozenset(
    {"thought_text", "action_text", "emotions", "categories"}
)
_ACTIVE_DECISIONS = frozenset({"selected", "integrated_into"})
_SOURCE_FIELD_SLOT = {
    "memo": "thought",
    "memo_action": "action",
    "emotion_details": "emotion",
    "emotions": "emotion",
    "category": "category",
}
_SLOT_ORDER = {"thought": 0, "action": 1, "emotion": 2, "category": 3}
_UNKNOWN_TYPES = frozenset(
    {
        "cause",
        "future_outcome",
        "omitted_referent",
        "unresolved_intention",
        "decision_state",
        "post_decision_comparative_merit",
        "other_person",
        "relation",
        "unspecified",
    }
)
_ANCHOR_ROLES = frozenset(
    {
        "first",
        "last",
        "nucleus",
        "unknown",
        "self_evaluation",
        "counterposition",
    }
)
_RELATION_TYPE_PRIORITY = {
    "precedes": 0,
    "contrasts_with": 1,
    "coexists_with": 2,
    "supports_without_guarantee": 3,
    "qualifies": 4,
}
_RELATION_TYPES = frozenset(_RELATION_TYPE_PRIORITY)
_RELATION_DIRECTIONS = frozenset(
    {"source_to_target", "target_to_source", "bidirectional"}
)
_RELATION_ENDPOINT_ROLES = frozenset({"action", "affect", "proposition"})
_DECISION_STATES = frozenset({"not_applicable", "open", "completed"})
_EMOTION_VALENCE = {
    "positive": frozenset({"喜び", "平穏"}),
    "negative": frozenset({"悲しみ", "怒り", "不安"}),
    "non_valenced": frozenset({"自己理解"}),
}
_RELATION_DEPTH_CAP = {
    "minimal": 1,
    "focused": 2,
    "layered": 3,
}
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_OVERLAY_ID_RE = re.compile(r"^nls3s11sem_[0-9a-f]{20}$")
_ANCHOR_ID_RE = re.compile(r"^s11anc_[0-9a-f]{16}$")
_LABEL_ANCHOR_ID_RE = re.compile(r"^s11lbl_[0-9a-f]{16}$")
_UNKNOWN_ID_RE = re.compile(r"^s11unk_[0-9a-f]{16}$")
_SELF_EVAL_ID_RE = re.compile(r"^s11self_[0-9a-f]{16}$")
_MIXED_EMOTION_ID_RE = re.compile(r"^s11mix_[0-9a-f]{16}$")
_PURPOSE_NEGATION_PREFIX_RE = re.compile(
    r"(?:ないよう|ぬよう|なく(?:て|、)|ないため|ないまま)[^。！？!?]{0,72}[、,]"
)
_MAIN_ACTION_PROGRESSIVE_RE = re.compile(
    r"(?:て|で)(?:いる|います|おり|いますね)(?:[。！？!?]|$)"
)
_RECEPTION_OWNER_KIND_RANK = {
    "grounded_nucleus_notice": 0,
    "intention_or_next_action": 1,
    # A multi-endpoint source opportunity is structurally owned by its exact
    # relation unless the reception act explicitly prioritises an unknown.
    "grounded_relation_preservation": 2,
    "unknown_boundary_preservation": 3,
}
_RECEPTION_ACT_KIND_RANK = {
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
        # The reported self-evaluation is source-owned; its bounded
        # counterposition is a separate terminal safeguard, not the primary
        # reception antecedent.
        "self_denial_boundary": 0,
        "bounded_counterposition": 1,
        "grounded_nucleus_notice": 2,
    },
}
_RECEPTION_BINDING_ID_RE = re.compile(r"^s11recv_[0-9a-f]{16}$")
_EVIDENCE_ID_RE = re.compile(r"^s[1-9][0-9]*$")
_SURFACE_ANCHOR_ORDINAL_RE = re.compile(r"^[A-Za-z_]*?([0-9]+)$")
_BASE_NUCLEUS_SPAN_RE = re.compile(r"^nucleus:(s[1-9][0-9]*)$")
_TWO_PREDICATE_CONNECTIVE_RE = re.compile(
    r"^(?P<left>.{4,}?(?P<connector>後になると|けれど|だけど|のに|けど|て|で))、"
    r"(?P<right>.{4,})$"
)
_ACTION_INTENTION_RE = re.compile(
    r"(?:たい|つもり|予定|ようと思|ことにした|ことにする|"
    r"してみる|試してみる|しよう|するつもり|する予定|"
    r"決めておく|しておく|伝えるつもり|確認するつもり)"
    r"(?:[。！？!?]|$)|(?:よう|おう)(?:かな)?(?:[。！？!?]|$)"
)
_ACTION_COMPLETED_RE = re.compile(
    r"(?:ました|でした|た|だ)(?=[、,。！？!?]|$)"
)
_ACTION_ONGOING_RE = re.compile(
    r"(?:て|で)(?:いる|います|おる|おります)"
    r"(?:[。！？!?]|$)|"
    r"(?:最中|進行中|作業中|検討中)(?:だ|です)?(?:[。！？!?]|$)"
)
_ACTION_NOT_COMPLETED_RE = re.compile(
    r"(?:まだ[^ 。！？!?]{0,32}(?:ていない|でいない|"
    r"していない|できていない|終わっていない))|"
    r"(?:[^ 。！？!?]{1,24}(?:は|が)まだ)(?:[。！？!?]|$)|"
    r"(?:[^ 。！？!?]{1,32}(?:て|で)いない)(?:[。！？!?]|$)|"
    r"(?:未送信|未提出|未完了|未実施|未着手|未決定)"
)
_PROJECTED_EVALUATION_END_RE = re.compile(
    r"(?:って)?(?:思われ|見られ|言われ)"
    r"(?:そう|るかもしれ|るのでは)"
)
_UNCERTAINTY_RE = re.compile(
    r"(?:分から|わから|判ら|不明|未定|"
    r"迷(?:う|って(?:いる|いて|おり)|い(?:が|を|続け|中))|"
    r"言葉にでき|定まっていな|まとまっていな|見えていな|"
    r"ぼんやり|思われそう|見られそう|言われそう|"
    r"だろう(?:か)?|かな(?:[。！？!?]|$)|…|\.\.\.)"
)
_ANTICIPATED_PASSIVE_OUTCOME_RE = re.compile(
    r"(?P<focus>[^、。！？!?\n]{1,48}"
    r"(?:される|られる|れる)のでは(?:ないか)?)"
)
_CONTENT_REFERENT_OPEN_RE = re.compile(
    r"(?P<focus>(?:出来事|内容|話題|対象|どのこと|どの件|"
    r"何を書く|何を(?:書く|話す|伝える))"
    r"[^、。！？!?\n]{0,24}"
    r"(?:決められない|決まらない|まとまらない|"
    r"分からない|わからない|選べない))"
)
_OPEN_DECISION_MORPHOLOGY_RE = re.compile(
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
_STANDALONE_DEICTIC_RE = re.compile(
    r"(?:これ|それ|あれ|どれ)(?:[、,]?(?:ね|な))?[。！？!?]?"
)
_OTHER_PERSON_AWARENESS_RE = re.compile(
    r"(?P<focus>(?:(?:相手|先方|周り|こちら|私たち|自分たち)"
    r"(?:に|には|の))[^、。！？!?\n]{1,40}"
    r"(?:見えて|伝わって|分かって|わかって|理解されて)"
    r"(?:いない|いる)(?:のか|かもしれない|のだろうか))"
)
_RELATIVE_TEMPORAL_DEICTIC_RE = re.compile(
    r"(?:帰ってから|戻ってから|その後|あの後|そのとき|あのとき)"
)
_CONTEXTUAL_PRECEDING_EVENT_RE = re.compile(
    r"(?:て|で)みたら|(?:て|で)もらえた|"
    r"(?:会|話|相談|訪問|外出|参加|面談|作業|用事)"
    r"[^、。！？!?\n]{0,20}(?:した|して|終えた|終わった)"
)
_OPEN_CANDIDATE_SET_RE = re.compile(
    r"(?P<focus>(?:候補|選択肢|案)(?:を|が)"
    r"[^、。！？!?\n]{0,20}(?:二|三|四|五|複数|いくつか)"
    r"[^、。！？!?\n]{0,24}(?:絞|残|比較|比べ)"
    r"[^。！？!?\n]{0,48})"
)
_FINAL_SELECTION_RE = re.compile(
    r"(?:最終的に|一つに|ひとつに|これに|それに)?"
    r"(?:決めた|選んだ|決定した|確定した)"
)
_OPEN_DECISION_RE = _OPEN_DECISION_MORPHOLOGY_RE
_COMPLETED_DECISION_RE = re.compile(
    r"(?:決めた|選んだ|決定した|確定した|ことにした)"
)
_CLOSED_UNKNOWN_CONNECTIVE_PREFIX_RE = re.compile(
    r"^(?:ただ|でも|一方で|それでも)(?:[、,]\s*)?"
)
_POST_DECISION_COMPARATIVE_RE = re.compile(
    r"(?:別|ほか|他)の(?:選択|選択肢|案|ほう|方)"
    r"[^。！？!?\n]{0,36}(?:よかった|良かった|まし|"
    r"正しかった|正解だった)"
)

_MAX_ANCHOR_CHARS = 96
_LONG_TEXT_THRESHOLD = 120


# This is a closed grammar catalog, not a corpus-derived word list.  Entries
# describe ordinary Japanese grammatical constructions and broad predicate
# classes; no sample text, case identifier, category, or expected cue occurs.
_GRAMMAR_CATALOG: dict[str, Any] = {
    "unknown_patterns": {
        "cause": [
            r"(?:なぜ|どうして|原因|理由|わけ)[^。！？!?\n]{0,48}"
            r"(?:分から|わから|判ら|不明|決められ|言葉にでき)",
            r"(?:分から|わから|判ら)ない[^。！？!?\n]{0,16}"
            r"(?:理由|原因|わけ)",
            r"(?:理由|原因|わけ)(?:は|が|を)?[^。！？!?\n]{0,32}"
            r"(?:説明でき|言え|分から|わから|判ら|特定でき)",
            r"(?:たぶん|おそらく|かもしれ|かも|気がする)"
            r"[^。！？!?\n]{0,24}$",
        ],
        "future_outcome": [
            r"(?:これから|今後|次(?:回|は|に)|明日|来週|将来)"
            r"[^。！？!?\n]{0,56}",
            r"[^。！？!?\n]{0,56}(?:つもり|予定(?=[。！？!?\n]|$)|"
            r"予定(?:です|だ|である)|ようと思う|ことにした|"
            r"たいと思う|してみる|試してから判断)",
        ],
        "omitted_referent": [
            r"^(?:これ|それ|あれ|あの件|この件|その件)(?:は|が|を|に)"
            r"[^。！？!?\n]{1,32}(?:分から|わから|不明|決められ)",
            r"(?:何について|何のこと|どの部分|どれなのか)"
            r"[^。！？!?\n]{0,32}(?:分から|わから|決められ)",
            r"(?:何|どれ|どこ|どの)[^。！？!?\n]{0,36}"
            r"(?:分から|わから|まとまら|見えな)",
            r"(?:点|部分|内容)[^。！？!?\n]{0,24}"
            r"(?:見落としていな|抜けていな|欠けていな)",
            r"(?:^|[、])それだけ[。！？!?]?$",
            r"(?:まだ)?(?:よく)?分からない[。！？!?]?$",
            r"(?:件|こと|もの|部分|対象|内容|話題|出来事|問題)"
            r"[^。！？!?\n]{0,24}(?:分から|わから|不明|ぼんやり|"
            r"まとまっていな|見えていな)",
        ],
        "unresolved_intention": [
            r"(?:決められ(?:ない|なく|ず|ません|ていない|ていません)|"
            r"決めきれ(?:ない|なく|ず|ません|ていない|ていません)|"
            r"決まら(?:ない|なく|ず|ないです|ません)|"
            r"決まってい(?:ない|ません)|決めてい(?:ない|ません)|"
            r"選べ(?:ない|なく|ず|ません|ていない|ていません)|"
            r"選びきれ(?:ない|なく|ず|ません|ていない|ていません)|"
            r"判断でき(?:ない|なく|ず|ません|ていない|ていません)|"
            r"(?:答え|結論)が出(?:ない|なく|ず|ません|ていない|ていません)|"
            r"未決定|保留|迷(?:う|って|い))"
            r"[^。！？!?\n]{0,40}",
            r"[^。！？!?\n]{0,40}(?:未定|保留|決めていない|"
            r"まだ決めない|分からないまま)",
            r"[^。！？!?\n]{0,48}(?:か|かどうか)"
            r"[^。！？!?\n]{0,24}(?:分から|わから|迷|決め|定ま)",
            r"(?:別|ほか|他)の(?:選択|ほう|方)"
            r"[^。！？!?\n]{0,28}(?:よかった|良かった|まし)",
            r"(?:選び方|選択)[^。！？!?\n]{0,32}(?:かな|だろうか)",
        ],
        "other_person": [
            r"[^。！？!?\n]{0,48}(?:思われ|見られ|言われ)"
            r"(?:そう|るかもしれ|るのでは)",
            r"(?:相手|周り|みんな|他の人)[^。！？!?\n]{0,48}"
            r"(?:反応|返事|返信|考え|気持ち)[^。！？!?\n]{0,24}"
            r"(?:分から|わから|未定|不明)",
            r"(?:相手|周り|みんな|他の人|こちら)[^。！？!?\n]{0,56}"
            r"(?:見え|思う|考え|関係|反応|返事|返信)"
            r"[^。！？!?\n]{0,24}(?:分から|わから|未定|不明|かもしれ)",
        ],
        "relation": [
            r"(?:関係|つながり|距離|バランス)[^。！？!?\n]{0,40}"
            r"(?:分から|わから|決められ|不明|まだ|かもしれ)",
            r"(?:折り合い|両立|つながれていな)[^。！？!?\n]{0,32}"
            r"(?:見え|分から|わから|かもしれ|感じ)",
        ],
        "unspecified": [
            r"(?:…|\.\.\.)$",
            r"(?:て|で|けど|けれど|が|のに|ものの)$",
        ],
    },
    # This pattern classifies an open other-person projection only.  It is
    # not authority for a self-denial boundary; required Step 4 obligation
    # pairs exclusively own that decision.
    "projected_other_person_boundary": (
        r"(?:思われ|見られ|言われ)(?:そう|るかもしれ|るのでは)"
    ),
    "unknown_types": sorted(_UNKNOWN_TYPES),
    "anchor_roles": sorted(_ANCHOR_ROLES),
    "max_anchor_chars": _MAX_ANCHOR_CHARS,
    "long_text_threshold": _LONG_TEXT_THRESHOLD,
    "context_resolved_unknown_suppression": {
        "eligible_dimension_token": "TEMPORAL_REFERENT",
        "suppression_reason": "context_resolved_temporal_referent",
        "evidence_grade": "exact_current_input_context_resolution",
        "raw_required_unknown_owned_one_to_one": True,
        "exact_source_and_context_anchors_required": True,
        "visible_unknown_with_same_source_forbidden": True,
    },
    "relation_policy": {
        "backbone_membership": "required_or_content_selected",
        "automatic_spanning_supplement_forbidden": True,
        "required_type_direction_endpoints_immutable": True,
        "text_or_exact_label_endpoint_binding_required": True,
        "optional_uncertain_safe_downgrade": {
            "relation_type": "coexists_with",
            "relation_direction": "bidirectional",
            "same_event_restatement_exception": True,
        },
        "endpoint_roles": sorted(_RELATION_ENDPOINT_ROLES),
    },
    "unknown_policy": {
        "required_source_unknown_unclassifiable": "fail_closed",
        "frozen_explicit_choice_decision": {
            "dimension_tokens": ["CHOICE", "DECISION", "UNKNOWN"],
            "source_uncertainty_required": True,
            "completed_and_open_lifecycle": "fail_closed",
            "dimension_without_source_witness": "fail_closed",
        },
        "canonical_source_ownership_key": [
            "source_slot",
            "source_range",
            "source_text_sha256",
            "target_nucleus_ids",
            "unknown_type",
        ],
        "leading_connective_normalization": {
            "closed_prefixes": ["ただ", "でも", "一方で", "それでも"],
            "exact_unique_active_nucleus_binding_required": True,
        },
        "relation_unknown_endpoint_policy": {
            "exact_source_relation_endpoint_set_required": True,
            "grammar_without_exact_endpoints": "safe_unspecified",
            "required_source_without_exact_endpoints": "fail_closed",
        },
        "decision_states": sorted(_DECISION_STATES),
        "dimension_matrix": {
            "cause": ["not_applicable"],
            "future_outcome": ["not_applicable"],
            "omitted_referent": ["not_applicable"],
            "unresolved_intention": ["not_applicable"],
            "decision_state": ["open"],
            "post_decision_comparative_merit": ["completed"],
            "other_person": ["not_applicable"],
            "relation": ["not_applicable"],
            "unspecified": ["not_applicable"],
        },
        "decision_context_source_bound": True,
    },
    "mixed_emotion_policy": {
        "label_anchor_source": "current_input_and_rebuilt_evidence_ledger",
        "positive_labels": sorted(_EMOTION_VALENCE["positive"]),
        "negative_labels": sorted(_EMOTION_VALENCE["negative"]),
        "non_valenced_labels": sorted(_EMOTION_VALENCE["non_valenced"]),
        "positive_and_negative_requires_coexistence": True,
        "step4_step5_mutation_forbidden": True,
    },
    "reception_antecedent_policy": {
        "source": (
            "source_reception_opportunity_exact_owner_plus_active_discourse"
        ),
        "stance_kind": STANCE_KIND,
        "all_active_targets_required": True,
        "synthetic_target_forbidden": True,
        "legacy_intersection_target_is_lineage_only": True,
        "exact_opportunity_target_nucleus_set_required": True,
        "visible_typed_local_referent_required": True,
        "semantic_head_unique_candidate_injection_forbidden": True,
        "purpose_negation_scope_correction": {
            "concrete_action_evidence_required": True,
            "main_predicate_progressive_required": True,
            "purpose_or_constraint_negation_cannot_override_main_lifecycle": (
                True
            ),
            "zero_or_multiple_action_owners": "fail_closed_or_no_support",
        },
    },
    "body_free": True,
}

STEP11_SEMANTIC_OVERLAY_POLICY_SHA256 = artifact_sha256(_GRAMMAR_CATALOG)
_SUPPRESSION_POLICY = _GRAMMAR_CATALOG[
    "context_resolved_unknown_suppression"
]
_TEMPORAL_SUPPRESSION_REASON = str(_SUPPRESSION_POLICY["suppression_reason"])
_TEMPORAL_SUPPRESSION_GRADE = str(_SUPPRESSION_POLICY["evidence_grade"])

_UNKNOWN_PATTERNS = {
    kind: tuple(re.compile(pattern) for pattern in patterns)
    for kind, patterns in _GRAMMAR_CATALOG["unknown_patterns"].items()
}
_PROJECTED_JUDGMENT_RE = re.compile(
    _GRAMMAR_CATALOG["projected_other_person_boundary"]
)
_SELF_DENIAL_AUTHORITY_RULE = (
    "required_self_denial_bounded_counterposition_pair"
)


class Step11SemanticOverlayError(ValueError):
    """Fail-closed error carrying a body-free machine code only."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11SourceAnchor:
    anchor_id: str
    source_slot: str
    role: str
    start: int
    end: int
    text: str
    text_sha256: str


@dataclass(frozen=True, slots=True)
class Step11ExactLabelAnchor:
    label_anchor_id: str
    source_slot: str
    source_field: str
    source_ordinal: int
    label: str
    strength: str | None
    evidence_span_id: str
    label_sha256: str
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11NucleusAnchorBinding:
    nucleus_id: str
    source_anchor_ids: tuple[str, ...]
    source_label_anchor_ids: tuple[str, ...]
    source_slots: tuple[str, ...]
    source_role: str
    modality: str
    temporal_scope: str
    realization_status: str
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11OverlayRelation:
    source_relation_id: str
    source_relation_ids: tuple[str, ...]
    source_relation_kind: str
    relation_type: str
    relation_direction: str
    from_nucleus_id: str
    to_nucleus_id: str
    from_source_slots: tuple[str, ...]
    to_source_slots: tuple[str, ...]
    from_source_anchor_ids: tuple[str, ...]
    to_source_anchor_ids: tuple[str, ...]
    from_label_anchor_ids: tuple[str, ...]
    to_label_anchor_ids: tuple[str, ...]
    from_endpoint_role: str
    to_endpoint_role: str
    required: bool
    explicit: bool
    cross_field: bool
    source_order: tuple[int, int]
    priority_rank: int
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11TypedUnknown:
    unknown_id: str
    unknown_type: str
    source_slots: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    target_nucleus_ids: tuple[str, ...]
    source_unknown_ids: tuple[str, ...]
    source_rules: tuple[str, ...]
    epistemic_basis: str
    decision_state: str = "not_applicable"
    context_nucleus_ids: tuple[str, ...] = ()
    context_anchor_ids: tuple[str, ...] = ()
    surface_policy: str = "preserve_open"


@dataclass(frozen=True, slots=True)
class Step11SuppressedUnknown:
    source_unknown_id: str
    original_dimension_code: str
    source_slots: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    target_nucleus_ids: tuple[str, ...]
    context_anchor_ids: tuple[str, ...]
    suppression_reason: str
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11ReportedSelfEvaluation:
    self_evaluation_id: str
    source_slot: str
    source_anchor_id: str
    source_rule: str
    identity_fact_denial_required: bool
    bounded_counterposition_required: bool
    source_counterposition_anchor_ids: tuple[str, ...]
    evaluation_target: str


@dataclass(frozen=True, slots=True)
class Step11MixedEmotionRequirement:
    requirement_id: str
    positive_label_anchor_ids: tuple[str, ...]
    negative_label_anchor_ids: tuple[str, ...]
    relation_type: str
    relation_direction: str
    required: bool
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11ReceptionAntecedentBinding:
    binding_id: str
    reception_obligation_id: str
    reception_node_id: str
    source_target_obligation_ids: tuple[str, ...]
    source_target_node_ids: tuple[str, ...]
    source_target_nucleus_ids: tuple[str, ...]
    antecedent_obligation_ids: tuple[str, ...]
    antecedent_node_ids: tuple[str, ...]
    antecedent_nucleus_ids: tuple[str, ...]
    supporting_obligation_ids: tuple[str, ...]
    supporting_node_ids: tuple[str, ...]
    supporting_nucleus_ids: tuple[str, ...]
    support_role: str
    source_reception_opportunity_ids: tuple[str, ...]
    action_lifecycle: str
    allowed_response_acts: tuple[str, ...]
    evidence_grade: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11SemanticOverlay:
    schema_version: str
    candidate_version_id: str
    overlay_id: str
    source_obligation_ledger_sha256: str
    source_content_plan_sha256: str
    source_discourse_plan_sha256: str
    current_input_projection_sha256: str
    overlay_policy_sha256: str
    planning_frontier: Step11PlanningFrontier
    label_anchors: tuple[Step11ExactLabelAnchor, ...]
    anchors: tuple[Step11SourceAnchor, ...]
    nucleus_anchor_bindings: tuple[Step11NucleusAnchorBinding, ...]
    relations: tuple[Step11OverlayRelation, ...]
    unknowns: tuple[Step11TypedUnknown, ...]
    suppressed_unknowns: tuple[Step11SuppressedUnknown, ...]
    reported_self_evaluations: tuple[Step11ReportedSelfEvaluation, ...]
    mixed_emotion_requirements: tuple[Step11MixedEmotionRequirement, ...]
    reception_antecedent_bindings: tuple[
        Step11ReceptionAntecedentBinding, ...
    ]
    body_free: bool = False


def _normalise_text(value: str) -> str:
    return " ".join(
        unicodedata.normalize(
            "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
        ).split()
    )


def _canonical_display_range(
    source_text: str,
    canonical_display: str,
    source_start: int,
    source_end: int,
) -> tuple[int, int]:
    """Map one exact raw-source range into the canonical display space.

    Evidence Ledger offsets belong to the normalized app source with original
    whitespace retained, while the forward surface deliberately NFC-normalises
    and collapses whitespace for display.  Token-coordinate traversal gives a
    deterministic mapping without substring search, clamping, or case-specific
    recovery.  A boundary that bisects an NFC composition fails closed.
    """

    if (
        type(source_text) is not str
        or type(canonical_display) is not str
        or type(source_start) is not int
        or type(source_end) is not int
        or source_start < 0
        or source_end <= source_start
        or source_end > len(source_text)
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )
    if source_text[source_start].isspace() or source_text[
        source_end - 1
    ].isspace():
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )

    # source start/end, display start/end, source token, canonical token
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
        source_token = source_text[token_start:token_end]
        canonical_token = unicodedata.normalize("NFC", source_token)
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
                source_token,
                canonical_token,
            )
        )

    if " ".join(row[5] for row in tokens) != canonical_display:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )
    start_token = next(
        (row for row in tokens if row[0] <= source_start < row[1]), None
    )
    end_token = next(
        (row for row in tokens if row[0] < source_end <= row[1]), None
    )
    if start_token is None or end_token is None:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )

    def display_boundary(
        token: tuple[int, int, int, int, str, str],
        source_boundary: int,
    ) -> int:
        token_start, _, display_start, _, raw_token, canonical_token = token
        relative = source_boundary - token_start
        canonical_prefix = unicodedata.normalize("NFC", raw_token[:relative])
        canonical_suffix = unicodedata.normalize("NFC", raw_token[relative:])
        if canonical_prefix + canonical_suffix != canonical_token:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
            )
        return display_start + len(canonical_prefix)

    display_start = display_boundary(start_token, source_start)
    display_end = display_boundary(end_token, source_end)
    fragment = _normalise_text(source_text[source_start:source_end])
    if (
        not fragment
        or display_start < 0
        or display_end <= display_start
        or display_end > len(canonical_display)
        or canonical_display[display_start:display_end] != fragment
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )
    return display_start, display_end


def _canonical_source_range(
    source_text: str,
    canonical_display: str,
    display_start: int,
    display_end: int,
) -> tuple[int, int]:
    """Invert an exact canonical token range to raw-source coordinates."""

    if (
        type(source_text) is not str
        or type(canonical_display) is not str
        or type(display_start) is not int
        or type(display_end) is not int
        or display_start < 0
        or display_end <= display_start
        or display_end > len(canonical_display)
        or _normalise_text(source_text) != canonical_display
        or canonical_display[display_start].isspace()
        or canonical_display[display_end - 1].isspace()
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )

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
        token_display_start = display_cursor
        display_cursor += len(canonical_token)
        tokens.append(
            (
                token_start,
                token_end,
                token_display_start,
                display_cursor,
                raw_token,
                canonical_token,
            )
        )
    start_token = next(
        (row for row in tokens if row[2] <= display_start < row[3]), None
    )
    end_token = next(
        (row for row in tokens if row[2] < display_end <= row[3]), None
    )
    if start_token is None or end_token is None:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )

    def source_boundary(
        token: tuple[int, int, int, int, str, str],
        display_boundary: int,
    ) -> int:
        token_start, _, token_display_start, _, raw_token, canonical_token = (
            token
        )
        canonical_offset = display_boundary - token_display_start
        candidates = tuple(
            index
            for index in range(len(raw_token) + 1)
            if len(unicodedata.normalize("NFC", raw_token[:index]))
            == canonical_offset
            and unicodedata.normalize("NFC", raw_token[:index])
            + unicodedata.normalize("NFC", raw_token[index:])
            == canonical_token
        )
        if len(candidates) != 1:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
            )
        return token_start + candidates[0]

    source_start = source_boundary(start_token, display_start)
    source_end = source_boundary(end_token, display_end)
    if (
        source_end <= source_start
        or _normalise_text(source_text[source_start:source_end])
        != canonical_display[display_start:display_end]
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )
    return source_start, source_end


def _evidence_source_texts(
    current_input: Mapping[str, Any],
) -> dict[str, str]:
    """Return the exact source texts whose coordinates own ledger spans."""

    try:
        normalized = normalize_emlis_current_input(dict(current_input))
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_EVIDENCE_SOURCE_NORMALIZATION_FAILED"
        ) from exc
    thought = normalized.get("memo")
    action = normalized.get("memo_action")
    if type(thought) is not str or type(action) is not str:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_EVIDENCE_SOURCE_TEXT_INVALID"
        )
    return {"thought": thought, "action": action}


def _input_projection(current_input: Mapping[str, Any]) -> dict[str, Any]:
    if type(current_input) is not dict or set(current_input) != _INPUT_KEYS:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_INPUT_KEYSET_INVALID")
    thought = current_input.get("thought_text")
    action = current_input.get("action_text")
    emotions = current_input.get("emotions")
    categories = current_input.get("categories")
    if type(thought) is not str or type(action) is not str:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_INPUT_TEXT_INVALID")
    thought = _normalise_text(thought)
    action = _normalise_text(action)
    if not thought and not action:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_INPUT_TEXT_REQUIRED")
    if type(categories) is not list or not categories:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_CATEGORIES_INVALID")
    clean_categories: list[str] = []
    for item in categories:
        if type(item) is not str or not _normalise_text(item):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_CATEGORY_ENTRY_INVALID"
            )
        clean_categories.append(_normalise_text(item))
    if len(clean_categories) != len(set(clean_categories)):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_CATEGORY_DUPLICATE"
        )
    if type(emotions) is not list or not emotions:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_EMOTIONS_INVALID")
    clean_emotions: list[dict[str, str]] = []
    for item in emotions:
        if type(item) is not dict or set(item) != {"type", "strength"}:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_EMOTION_ENTRY_INVALID"
            )
        emotion_type = item.get("type")
        strength = item.get("strength")
        if (
            type(emotion_type) is not str
            or not _normalise_text(emotion_type)
            or type(strength) is not str
            or not _normalise_text(strength)
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_EMOTION_ENTRY_INVALID"
            )
        clean_emotions.append(
            {
                "type": _normalise_text(emotion_type),
                "strength": _normalise_text(strength),
            }
        )
    emotion_keys = {(row["type"], row["strength"]) for row in clean_emotions}
    if len(emotion_keys) != len(clean_emotions):
        raise Step11SemanticOverlayError("STEP11_OVERLAY_EMOTION_DUPLICATE")
    return {
        "thought_text": thought,
        "action_text": action,
        "emotions": clean_emotions,
        "categories": clean_categories,
    }


def _exact_label_anchors(
    current_input: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> tuple[Step11ExactLabelAnchor, ...]:
    """Rebind structured labels to the independently rebuilt evidence ledger."""

    try:
        normalized = normalize_emlis_current_input(dict(current_input))
        evidence = tuple(build_evidence_ledger(dict(current_input)))
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_LABEL_EVIDENCE_REBUILD_FAILED"
        ) from exc
    normalized_emotions = normalized.get("emotion_details")
    normalized_categories = normalized.get("category")
    if (
        type(normalized_emotions) is not list
        or type(normalized_categories) is not list
        or normalized_emotions != projection.get("emotions")
        or normalized_categories != projection.get("categories")
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_LABEL_PROJECTION_MISMATCH"
        )
    evidence_by_field_and_label: dict[tuple[str, str], list[Any]] = {}
    for span in evidence:
        if (
            str(span.source_field) in {"emotion_details", "category"}
            and int(span.start_index) == -1
            and int(span.end_index) == -1
        ):
            evidence_by_field_and_label.setdefault(
                (str(span.source_field), _normalise_text(str(span.raw_text))),
                [],
            ).append(span)

    result: list[Step11ExactLabelAnchor] = []

    def add(
        *,
        source_slot: str,
        source_field: str,
        source_ordinal: int,
        label: str,
        strength: str | None,
    ) -> None:
        matches = evidence_by_field_and_label.get((source_field, label), [])
        if len(matches) != 1:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_LABEL_EVIDENCE_UNRESOLVED"
            )
        evidence_span_id = str(matches[0].span_id)
        label_sha256 = hashlib.sha256(label.encode("utf-8")).hexdigest()
        material = {
            "source_slot": source_slot,
            "source_field": source_field,
            "source_ordinal": source_ordinal,
            "label": label,
            "strength": strength,
            "evidence_span_id": evidence_span_id,
            "label_sha256": label_sha256,
            "evidence_grade": "exact_structured_evidence_label",
        }
        result.append(
            Step11ExactLabelAnchor(
                label_anchor_id=(
                    "s11lbl_" + artifact_sha256(material)[:16]
                ),
                source_slot=source_slot,
                source_field=source_field,
                source_ordinal=source_ordinal,
                label=label,
                strength=strength,
                evidence_span_id=evidence_span_id,
                label_sha256=label_sha256,
                evidence_grade="exact_structured_evidence_label",
            )
        )

    for ordinal, emotion in enumerate(projection["emotions"]):
        add(
            source_slot="emotion",
            source_field="emotion_details",
            source_ordinal=ordinal,
            label=str(emotion["type"]),
            strength=str(emotion["strength"]),
        )
    for ordinal, category in enumerate(projection["categories"]):
        add(
            source_slot="category",
            source_field="category",
            source_ordinal=ordinal,
            label=str(category),
            strength=None,
        )
    return tuple(result)


def _trusted_parents(
    inventory_result: Any,
    content_plan: Any,
    discourse_plan: Any,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    frozenset[str],
    frozenset[str],
    Step11PlanningFrontier,
]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_INVENTORY_REQUIRED")
    ledger = inventory_result.ledger
    try:
        if validate_semantic_obligation_inventory(
            ledger, source_snapshot=inventory_result.source_snapshot
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_INVENTORY_REVALIDATION_FAILED"
            )
        if validate_content_selection_policy(
            content_plan, inventory_result=inventory_result
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_CONTENT_REVALIDATION_FAILED"
            )
        if validate_discourse_plan(
            discourse_plan,
            content_plan=content_plan,
            obligation_ledger=ledger,
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_DISCOURSE_REVALIDATION_FAILED"
            )
    except Step11SemanticOverlayError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError) as exc:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_PARENT_REVALIDATION_FAILED"
        ) from exc
    rows = ledger.get("obligations")
    decisions = content_plan.get("decisions")
    nodes = discourse_plan.get("nodes")
    groups = discourse_plan.get("sentence_groups")
    if any(
        type(value) is not list
        for value in (rows, decisions, nodes, groups)
    ):
        raise Step11SemanticOverlayError("STEP11_OVERLAY_PARENT_ROWS_INVALID")
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    if len(by_id) != len(rows):
        raise Step11SemanticOverlayError("STEP11_OVERLAY_LEDGER_IDS_INVALID")
    base_active_decision_ids = {
        row.get("obligation_id")
        for row in decisions
        if type(row) is dict and row.get("status") in _ACTIVE_DECISIONS
    }
    node_by_obligation = {
        row.get("obligation_id"): row.get("node_id")
        for row in nodes
        if type(row) is dict
        and type(row.get("obligation_id")) is str
        and type(row.get("node_id")) is str
    }
    if base_active_decision_ids != set(node_by_obligation):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_ACTIVE_PARENT_MISMATCH"
        )
    group_by_node: dict[str, str] = {}
    for group in groups:
        if type(group) is not dict:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_GROUP_ROW_INVALID"
            )
        group_id = group.get("sentence_group_id")
        node_ids = group.get("node_ids")
        if type(group_id) is not str or type(node_ids) is not list:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_GROUP_ROW_INVALID"
            )
        for node_id in node_ids:
            if type(node_id) is not str or node_id in group_by_node:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_GROUP_NODE_INVALID"
                )
            group_by_node[node_id] = group_id
    if set(group_by_node) != set(node_by_obligation.values()):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_GROUP_COVERAGE_INVALID"
        )
    planning_frontier = build_step11_planning_frontier(
        inventory_result,
        content_plan,
        discourse_plan,
        _trusted_rows=(
            ledger,
            by_id,
            frozenset(base_active_decision_ids),
            node_by_obligation,
            group_by_node,
        ),
    )
    active_ids = frozenset(planning_frontier.participating_obligation_ids)
    active_nucleus_ids = frozenset(planning_frontier.active_nucleus_ids)
    return (
        ledger,
        by_id,
        active_ids,
        active_nucleus_ids,
        planning_frontier,
    )


def _clause_spans(text: str) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"[^。！？!?…]+(?:[。！？!?]+|…+|$)", text):
        start, end = match.span()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            spans.append((start, end))
    if not spans and text:
        spans.append((0, len(text)))
    return tuple(spans)


def _bounded_span(
    start: int,
    end: int,
    *,
    from_end: bool = False,
) -> tuple[int, int]:
    # Never cut a source anchor through a word, scalar, or sentence.  The
    # generated app corpus has source clauses below the policy target, but an
    # unexpectedly longer clause is still safer as one exact source span than
    # as a misleading head/tail slice.
    del from_end
    return start, end


def _anchor(
    *, source_slot: str, role: str, text: str, start: int, end: int
) -> Step11SourceAnchor:
    if source_slot not in {"thought", "action"} or role not in _ANCHOR_ROLES:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_ANCHOR_ENUM_INVALID")
    if start < 0 or end <= start or end > len(text):
        raise Step11SemanticOverlayError("STEP11_OVERLAY_ANCHOR_RANGE_INVALID")
    value = text[start:end]
    text_sha256 = hashlib.sha256(value.encode("utf-8")).hexdigest()
    material = {
        "source_slot": source_slot,
        "role": role,
        "start": start,
        "end": end,
        "text_sha256": text_sha256,
    }
    return Step11SourceAnchor(
        anchor_id="s11anc_" + artifact_sha256(material)[:16],
        source_slot=source_slot,
        role=role,
        start=start,
        end=end,
        text=value,
        text_sha256=text_sha256,
    )


def _append_anchor(
    anchors: list[Step11SourceAnchor],
    *,
    source_slot: str,
    role: str,
    text: str,
    start: int,
    end: int,
    from_end: bool = False,
) -> str:
    start, end = _bounded_span(start, end, from_end=from_end)
    row = _anchor(
        source_slot=source_slot,
        role=role,
        text=text,
        start=start,
        end=end,
    )
    if row not in anchors:
        anchors.append(row)
    return row.anchor_id


def _base_anchors(projection: Mapping[str, Any]) -> list[Step11SourceAnchor]:
    anchors: list[Step11SourceAnchor] = []
    for slot, field in (("thought", "thought_text"), ("action", "action_text")):
        text = str(projection[field])
        if not text:
            continue
        spans = _clause_spans(text)
        _append_anchor(
            anchors,
            source_slot=slot,
            role="first",
            text=text,
            start=spans[0][0],
            end=spans[0][1],
        )
        if len(text) >= _LONG_TEXT_THRESHOLD or len(spans) >= 3:
            last = spans[-1]
            _append_anchor(
                anchors,
                source_slot=slot,
                role="last",
                text=text,
                start=last[0],
                end=last[1],
                from_end=True,
            )
    return anchors


def _semantic_unit_id(
    *,
    parent_nucleus_id: str,
    source_span_id: str,
    start: int,
    end: int,
    fragment: str,
    role: str,
) -> str:
    """Recompute the frozen body-free unit identity from its source slice."""

    digest = artifact_sha256(
        {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "parent_nucleus_id": parent_nucleus_id,
            "source_span_id": source_span_id,
            "start_index": start,
            "end_index": end,
            "source_fragment_sha256": artifact_sha256(
                {"source_fragment": fragment}
            ),
            "unit_role": role,
        }
    )[:24]
    return f"semantic_unit:u{digest}"


def _text_evidence_spans(
    current_input: Mapping[str, Any],
) -> tuple[Any, ...]:
    try:
        rows = tuple(build_evidence_ledger(dict(current_input)))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_EVIDENCE_REBUILD_FAILED"
        ) from exc
    return tuple(
        row
        for row in rows
        if row.source_field in {"memo", "memo_action"}
    )


def _semantic_unit_source_range(
    actual_source_id: str,
    spans: Sequence[Any],
) -> tuple[Any, int, int] | None:
    """Resolve an opaque semantic-unit id to its exact frozen source range."""

    for span in spans:
        raw = str(span.raw_text)
        match = _TWO_PREDICATE_CONNECTIVE_RE.fullmatch(raw)
        if match is None:
            continue
        separator_index = match.start("right") - 1
        fragments = (
            ("antecedent", match.group("left"), 0, separator_index),
            (
                "consequent",
                match.group("right"),
                match.start("right"),
                len(raw),
            ),
        )
        for role, fragment, start, end in fragments:
            candidate = _semantic_unit_id(
                parent_nucleus_id=f"nucleus:{span.span_id}",
                source_span_id=str(span.span_id),
                start=start,
                end=end,
                fragment=fragment,
                role=role,
            )
            if candidate == actual_source_id:
                return span, start, end
    return None


def _span_display_range(
    evidence_sources: Mapping[str, str],
    projection: Mapping[str, Any],
    span: Any,
    relative_start: int,
    relative_end: int,
) -> tuple[str, str, int, int]:
    """Resolve a ledger/span-local range into one display field exactly."""

    source_keys = {
        "memo": ("thought", "thought_text"),
        "memo_action": ("action", "action_text"),
    }
    source = source_keys.get(str(span.source_field))
    if source is None:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_NUCLEUS_SOURCE_SPAN_UNRESOLVED"
        )
    source_slot, field = source
    raw_text = evidence_sources.get(source_slot)
    display_text = projection.get(field)
    if type(raw_text) is not str or type(display_text) is not str:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_DISPLAY_MAPPING_INVALID"
        )
    span_source = str(span.raw_text)
    span_start = int(span.start_index)
    span_end = int(span.end_index)
    source_span_text = raw_text[span_start:span_end]
    canonical_span = _normalise_text(span_source)
    if _normalise_text(source_span_text) != canonical_span:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SOURCE_SPAN_MISMATCH"
        )
    canonical_relative_start, canonical_relative_end = (
        _canonical_display_range(
            span_source,
            canonical_span,
            relative_start,
            relative_end,
        )
    )
    raw_relative_start, raw_relative_end = _canonical_source_range(
        source_span_text,
        canonical_span,
        canonical_relative_start,
        canonical_relative_end,
    )
    absolute_start = span_start + raw_relative_start
    absolute_end = span_start + raw_relative_end
    display_start, display_end = _canonical_display_range(
        raw_text,
        display_text,
        absolute_start,
        absolute_end,
    )
    return (
        source_slot,
        display_text,
        display_start,
        display_end,
    )


def _nucleus_realization_status(
    nucleus: Any,
    source_texts: Sequence[str],
) -> str:
    slots = _slots_for_nucleus(nucleus)
    if "action" not in slots:
        return "reported_content"

    def classify(source_text: str) -> str:
        if _ACTION_NOT_COMPLETED_RE.search(source_text) is not None:
            return "reported_not_completed"
        if _ACTION_ONGOING_RE.search(source_text) is not None:
            return "reported_ongoing"
        intended = _ACTION_INTENTION_RE.search(source_text) is not None
        completed = _ACTION_COMPLETED_RE.search(source_text) is not None
        if intended:
            return "intended"
        if completed:
            return "reported_completed"
        if nucleus.modality == "intended":
            return "intended"
        return "undetermined"

    statuses = {classify(text) for text in source_texts if text}
    if not statuses:
        return "undetermined"
    if len(statuses) == 1:
        return next(iter(statuses))
    # Mixed exact anchors must never be upcast to completion merely because
    # another clause in the same app field reports a completed act.
    return "undetermined"


def _nucleus_anchor_bindings(
    current_input: Mapping[str, Any],
    projection: Mapping[str, Any],
    anchors: list[Step11SourceAnchor],
    label_anchors: Sequence[Step11ExactLabelAnchor],
    *,
    inventory_result: SemanticObligationInventoryResult,
    active_nucleus_ids: frozenset[str],
) -> tuple[
    tuple[Step11NucleusAnchorBinding, ...],
    dict[str, tuple[str, ...]],
    dict[str, tuple[str, ...]],
]:
    """Bind every active text nucleus to an exact, recomputable source span."""

    spans = _text_evidence_spans(current_input)
    evidence_sources = _evidence_source_texts(current_input)
    span_by_id = {str(row.span_id): row for row in spans}
    nucleus_by_id = {
        row.source_id: row for row in inventory_result.source_snapshot.nuclei
    }
    label_anchor_ids_by_evidence: dict[str, list[str]] = {}
    for label_anchor in label_anchors:
        label_anchor_ids_by_evidence.setdefault(
            label_anchor.evidence_span_id, []
        ).append(label_anchor.label_anchor_id)
    actual_evidence_ids_by_alias: dict[str, list[str]] = {}
    for alias in inventory_result.source_snapshot.source_id_alias_bindings:
        if alias.source_kind == "evidence":
            actual_evidence_ids_by_alias.setdefault(
                alias.alias_source_id, []
            ).append(alias.actual_source_id)
    anchor_ids_by_nucleus: dict[str, tuple[str, ...]] = {}
    label_anchor_ids_by_nucleus: dict[str, tuple[str, ...]] = {}
    for nucleus_id in sorted(active_nucleus_ids):
        nucleus = nucleus_by_id[nucleus_id]
        slots = _slots_for_nucleus(nucleus)
        label_anchor_ids_by_nucleus[nucleus_id] = tuple(
            dict.fromkeys(
                label_anchor_id
                for evidence_id in nucleus.evidence_ids
                for actual_evidence_id in (
                    *actual_evidence_ids_by_alias.get(
                        str(evidence_id), ()
                    ),
                    str(evidence_id),
                )
                for label_anchor_id in label_anchor_ids_by_evidence.get(
                    actual_evidence_id, ()
                )
            )
        )
        if (
            {"emotion", "category"} & set(slots)
            and not label_anchor_ids_by_nucleus[nucleus_id]
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_NUCLEUS_LABEL_ANCHOR_UNRESOLVED"
            )
        text_slots = tuple(
            slot for slot in slots if slot in {"thought", "action"}
        )
        if not text_slots:
            anchor_ids_by_nucleus[nucleus_id] = ()
            continue
        source_range: tuple[Any, int, int] | None = None
        base_match = _BASE_NUCLEUS_SPAN_RE.fullmatch(
            str(nucleus.actual_source_id)
        )
        if base_match is not None:
            span = span_by_id.get(base_match.group(1))
            if span is not None:
                source_range = (span, 0, len(str(span.raw_text)))
        elif str(nucleus.actual_source_id).startswith("semantic_unit:"):
            source_range = _semantic_unit_source_range(
                str(nucleus.actual_source_id), spans
            )
        if source_range is None:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_NUCLEUS_SOURCE_SPAN_UNRESOLVED"
            )
        span, relative_start, relative_end = source_range
        source_slot, text, absolute_start, absolute_end = (
            _span_display_range(
                evidence_sources,
                projection,
                span,
                relative_start,
                relative_end,
            )
        )
        anchor_id = _append_anchor(
            anchors,
            source_slot=source_slot,
            role="nucleus",
            text=text,
            start=absolute_start,
            end=absolute_end,
        )
        anchor_ids_by_nucleus[nucleus_id] = (anchor_id,)
    bindings = tuple(
        Step11NucleusAnchorBinding(
            nucleus_id=nucleus_id,
            source_anchor_ids=anchor_ids_by_nucleus[nucleus_id],
            source_label_anchor_ids=(
                label_anchor_ids_by_nucleus[nucleus_id]
            ),
            source_slots=_slots_for_nucleus(nucleus_by_id[nucleus_id]),
            source_role=(
                "action"
                if "action" in _slots_for_nucleus(nucleus_by_id[nucleus_id])
                else "thought"
                if "thought" in _slots_for_nucleus(nucleus_by_id[nucleus_id])
                else "label"
            ),
            modality=str(nucleus_by_id[nucleus_id].modality),
            temporal_scope=str(nucleus_by_id[nucleus_id].temporal_scope),
            realization_status=_nucleus_realization_status(
                nucleus_by_id[nucleus_id],
                tuple(
                    row.text
                    for row in anchors
                    if row.anchor_id in anchor_ids_by_nucleus[nucleus_id]
                ),
            ),
            evidence_grade=(
                "exact_source_span"
                if anchor_ids_by_nucleus[nucleus_id]
                else "exact_structured_evidence_label"
            ),
        )
        for nucleus_id in sorted(anchor_ids_by_nucleus)
    )
    return bindings, anchor_ids_by_nucleus, label_anchor_ids_by_nucleus


def _slots_for_nucleus(nucleus: Any) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _SOURCE_FIELD_SLOT[field]
                for field in nucleus.source_fields
                if field in _SOURCE_FIELD_SLOT
            },
            key=_SLOT_ORDER.__getitem__,
        )
    )


def _source_ordinal(nucleus: Any) -> int:
    ordinals: list[int] = []
    for value in nucleus.surface_anchor_ids:
        match = _SURFACE_ANCHOR_ORDINAL_RE.fullmatch(str(value))
        if match is not None:
            ordinals.append(int(match.group(1)))
    return min(ordinals) if ordinals else 10**9


def _relation_sort_key(
    relation: Any,
    *,
    nucleus_by_id: Mapping[str, Any],
) -> tuple[Any, ...]:
    source = nucleus_by_id[relation.from_nucleus_id]
    target = nucleus_by_id[relation.to_nucleus_id]
    source_slots = _slots_for_nucleus(source)
    target_slots = _slots_for_nucleus(target)
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
        _RELATION_TYPE_PRIORITY.get(relation.relation_type, 99),
        _source_ordinal(source),
        _source_ordinal(target),
        relation.source_relation_kind,
        relation.source_id,
    )


_EVENT_SPLIT_RE = re.compile(
    r"(?:から|まで|だけ|は|が|を|に|へ|で|と|も|の|"
    r"[、。！？!?\s]+)"
)
_EVENT_GENERIC_LEXEMES = frozenset(
    {"これ", "それ", "あれ", "こと", "もの", "ため", "よう"}
)


def _event_lexemes(value: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in _EVENT_SPLIT_RE.split(_normalise_text(value))
        if token and token not in _EVENT_GENERIC_LEXEMES
    )


def _same_event_restatement(left: str, right: str) -> bool:
    """Recognise a cross-field restatement without inventing causality.

    A shared predicate alone is too weak (many unrelated actions end in
    ``した``), and a shared noun alone is equally unsafe.  The two source
    spans must independently expose both the same predicate-role lexeme and a
    non-generic participant lexeme.  This keeps a same-event ``qualifies``
    relation while ordinary thought/action co-presence remains conservative.
    """

    left_lexemes = _event_lexemes(left)
    right_lexemes = _event_lexemes(right)
    if len(left_lexemes) < 2 or len(right_lexemes) < 2:
        return False
    if left_lexemes[-1] != right_lexemes[-1]:
        return False
    left_participants = set(left_lexemes[:-1])
    right_participants = set(right_lexemes[:-1])
    return bool(left_participants & right_participants)


def _relation_semantic_signature(relation: Any) -> tuple[str, ...]:
    return (
        str(relation.from_nucleus_id),
        str(relation.to_nucleus_id),
        str(relation.source_relation_kind),
        str(relation.relation_type),
        str(relation.relation_direction),
        "required" if relation.required else "optional",
    )


def _relation_endpoint_role(nucleus: Any) -> str:
    """Return one closed semantic endpoint role from frozen source fields."""

    slots = _slots_for_nucleus(nucleus)
    kind = str(nucleus.kind)
    predicate_kind = str(nucleus.source_predicate_kind)
    modality = str(nucleus.modality)
    if "action" in slots or kind in {"action", "wish"} or predicate_kind == "action":
        return "action"
    if (
        "emotion" in slots
        or modality == "feeling"
        or predicate_kind == "feeling"
        or kind in {"state", "reaction", "change", "self_evaluation"}
    ):
        return "affect"
    return "proposition"


def _overlay_relations(
    inventory_result: SemanticObligationInventoryResult,
    active_nucleus_ids: frozenset[str],
    *,
    active_relation_ids: frozenset[str],
    selected_relation_ids: frozenset[str],
    content_depth: str,
    projection: Mapping[str, Any],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
    label_anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
    anchor_by_id: Mapping[str, Step11SourceAnchor],
) -> tuple[Step11OverlayRelation, ...]:
    del projection
    snapshot = inventory_result.source_snapshot
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    source_rows = [
        relation
        for relation in snapshot.relations
        if relation.source_id in active_relation_ids
        if {
            relation.from_nucleus_id,
            relation.to_nucleus_id,
        }
        <= active_nucleus_ids
    ]
    source_rows.sort(
        key=lambda row: _relation_sort_key(row, nucleus_by_id=nucleus_by_id)
    )
    # Alias only genuinely identical semantic rows.  An endpoint pair is not
    # a semantic identity: contrast, qualification and ordered support may all
    # legitimately coexist over the same nuclei and require separate atoms.
    deduplicated_rows: list[Any] = []
    aliases_by_primary_id: dict[str, list[str]] = {}
    primary_by_signature: dict[tuple[str, ...], Any] = {}
    for relation in source_rows:
        signature = _relation_semantic_signature(relation)
        primary = primary_by_signature.get(signature)
        if primary is not None:
            aliases_by_primary_id[primary.source_id].append(
                relation.source_id
            )
            continue
        primary_by_signature[signature] = relation
        aliases_by_primary_id[relation.source_id] = [relation.source_id]
        deduplicated_rows.append(relation)

    # Required and explicitly selected relations are the complete backbone.
    # No deferred edge may be manufactured as a spanning supplement.
    if content_depth not in _RELATION_DEPTH_CAP:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_CONTENT_DEPTH_INVALID"
        )
    selected_rows = [
        relation
        for relation in deduplicated_rows
        if relation.required
        or bool(
            set(aliases_by_primary_id[relation.source_id])
            & selected_relation_ids
        )
    ]
    selected_rows.sort(
        key=lambda row: _relation_sort_key(row, nucleus_by_id=nucleus_by_id)
    )
    result: list[Step11OverlayRelation] = []
    for rank, relation in enumerate(selected_rows):
        if relation.relation_type not in _RELATION_TYPES:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RELATION_TYPE_UNSUPPORTED"
            )
        if relation.relation_direction not in _RELATION_DIRECTIONS:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RELATION_DIRECTION_UNSUPPORTED"
            )
        source = nucleus_by_id[relation.from_nucleus_id]
        target = nucleus_by_id[relation.to_nucleus_id]
        source_slots = _slots_for_nucleus(source)
        target_slots = _slots_for_nucleus(target)
        source_anchor_ids = anchor_ids_by_nucleus.get(
            relation.from_nucleus_id, ()
        )
        target_anchor_ids = anchor_ids_by_nucleus.get(
            relation.to_nucleus_id, ()
        )
        source_texts = tuple(
            anchor_by_id[anchor_id].text for anchor_id in source_anchor_ids
        )
        target_texts = tuple(
            anchor_by_id[anchor_id].text for anchor_id in target_anchor_ids
        )
        if source_texts and source_texts == target_texts:
            # A non-reflexive source relation cannot be rendered as the same
            # quotation twice.  Fail closed instead of manufacturing endpoint
            # distinctness in the public surface.
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RELATION_ENDPOINT_TEXT_EQUAL"
            )
        explicit = (
            relation.source_relation_kind != "uncertain_connection"
            and relation.relation_type != "qualifies"
        )
        surface_relation_type = relation.relation_type
        surface_relation_direction = relation.relation_direction
        evidence_grade = (
            "exact_cross_field_source_relation"
            if source_slots != target_slots
            else "exact_same_field_relation"
        )
        same_event_restatement = (
            source_slots != target_slots
            and not relation.required
            and relation.source_relation_kind == "uncertain_connection"
            and relation.relation_type == "qualifies"
            and any(
                _same_event_restatement(left, right)
                for left in source_texts
                for right in target_texts
            )
        )
        optional_uncertain = (
            not relation.required
            and relation.source_relation_kind == "uncertain_connection"
        )
        if same_event_restatement:
            evidence_grade = "cross_field_same_event_restatement"
        elif optional_uncertain:
            # Optional uncertain connections are useful for spanning the
            # display frontier, but a thought/action endpoint shape alone does
            # not license a visible directional or causal claim.  The
            # source-grounded same-event restatement above remains the sole
            # optional exception; all other uncertain connections collapse to
            # symmetric co-presence.  Required relations remain owned by the
            # frozen inventory and retain their type/direction across fields.
            surface_relation_type = "coexists_with"
            evidence_grade = (
                "cross_field_copresence_only"
                if source_slots != target_slots
                else "source_order_copresence_only"
            )
        if optional_uncertain and not same_event_restatement:
            surface_relation_direction = "bidirectional"
        result.append(
            Step11OverlayRelation(
                source_relation_id=relation.source_id,
                source_relation_ids=tuple(
                    aliases_by_primary_id[relation.source_id]
                ),
                source_relation_kind=relation.source_relation_kind,
                relation_type=surface_relation_type,
                relation_direction=surface_relation_direction,
                from_nucleus_id=relation.from_nucleus_id,
                to_nucleus_id=relation.to_nucleus_id,
                from_source_slots=source_slots,
                to_source_slots=target_slots,
                from_source_anchor_ids=source_anchor_ids,
                to_source_anchor_ids=target_anchor_ids,
                from_label_anchor_ids=label_anchor_ids_by_nucleus.get(
                    relation.from_nucleus_id, ()
                ),
                to_label_anchor_ids=label_anchor_ids_by_nucleus.get(
                    relation.to_nucleus_id, ()
                ),
                from_endpoint_role=_relation_endpoint_role(source),
                to_endpoint_role=_relation_endpoint_role(target),
                required=relation.required,
                explicit=explicit,
                cross_field=(
                    source_slots != target_slots
                    and bool(
                        ({"thought", "action"} & set(source_slots))
                        and ({"thought", "action"} & set(target_slots))
                    )
                ),
                source_order=(
                    _source_ordinal(source),
                    _source_ordinal(target),
                ),
                priority_rank=rank,
                evidence_grade=evidence_grade,
            )
        )
    return tuple(result)


def _first_anchor_ids(
    anchors: Sequence[Step11SourceAnchor], slots: Sequence[str]
) -> tuple[str, ...]:
    result: list[str] = []
    for slot in slots:
        row = next(
            (
                item
                for item in anchors
                if item.source_slot == slot and item.role == "first"
            ),
            None,
        )
        if row is not None:
            result.append(row.anchor_id)
    return tuple(result)


def _unknown_material(
    *,
    unknown_type: str,
    source_slots: Sequence[str],
    source_anchor_ids: Sequence[str],
    target_nucleus_ids: Sequence[str],
    source_unknown_ids: Sequence[str],
    source_rules: Sequence[str],
    epistemic_basis: str,
    decision_state: str,
    context_nucleus_ids: Sequence[str],
    context_anchor_ids: Sequence[str],
) -> dict[str, Any]:
    return {
        "unknown_type": unknown_type,
        "source_slots": list(source_slots),
        "source_anchor_ids": list(source_anchor_ids),
        "target_nucleus_ids": list(target_nucleus_ids),
        "source_unknown_ids": list(source_unknown_ids),
        "source_rules": list(source_rules),
        "epistemic_basis": epistemic_basis,
        "decision_state": decision_state,
        "context_nucleus_ids": list(context_nucleus_ids),
        "context_anchor_ids": list(context_anchor_ids),
        "surface_policy": "preserve_open",
    }


def _add_unknown(
    unknowns: list[Step11TypedUnknown],
    *,
    unknown_type: str,
    source_slots: Sequence[str],
    source_anchor_ids: Sequence[str],
    target_nucleus_ids: Sequence[str],
    source_rule: str,
    source_unknown_ids: Sequence[str] = (),
    epistemic_basis: str = "explicit_unknown",
    decision_state: str = "not_applicable",
    context_nucleus_ids: Sequence[str] = (),
    context_anchor_ids: Sequence[str] = (),
) -> None:
    if unknown_type not in _UNKNOWN_TYPES:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_UNKNOWN_TYPE_INVALID")
    slots = tuple(sorted(set(source_slots), key=_SLOT_ORDER.__getitem__))
    anchor_ids = tuple(dict.fromkeys(source_anchor_ids))
    nuclei = tuple(sorted(set(target_nucleus_ids)))
    frozen_ids = tuple(sorted(set(source_unknown_ids)))
    context_nuclei = tuple(sorted(set(context_nucleus_ids)))
    context_anchors = tuple(dict.fromkeys(context_anchor_ids))
    rules = (source_rule,)
    allowed_decision_states = set(
        _GRAMMAR_CATALOG["unknown_policy"]["dimension_matrix"].get(
            unknown_type, ()
        )
    )
    if decision_state not in allowed_decision_states:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_UNKNOWN_DECISION_STATE_INVALID"
        )
    if unknown_type in {"decision_state", "post_decision_comparative_merit"}:
        if not context_nuclei or not context_anchors:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_DECISION_CONTEXT_REQUIRED"
            )
    elif context_nuclei or context_anchors:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_UNKNOWN_DECISION_CONTEXT_FORBIDDEN"
        )
    material = _unknown_material(
        unknown_type=unknown_type,
        source_slots=slots,
        source_anchor_ids=anchor_ids,
        target_nucleus_ids=nuclei,
        source_unknown_ids=frozen_ids,
        source_rules=rules,
        epistemic_basis=epistemic_basis,
        decision_state=decision_state,
        context_nucleus_ids=context_nuclei,
        context_anchor_ids=context_anchors,
    )
    row = Step11TypedUnknown(
        unknown_id="s11unk_" + artifact_sha256(material)[:16],
        unknown_type=unknown_type,
        source_slots=slots,
        source_anchor_ids=anchor_ids,
        target_nucleus_ids=nuclei,
        source_unknown_ids=frozen_ids,
        source_rules=rules,
        epistemic_basis=epistemic_basis,
        decision_state=decision_state,
        context_nucleus_ids=context_nuclei,
        context_anchor_ids=context_anchors,
    )
    if row not in unknowns:
        unknowns.append(row)


def _explicit_unknown_types(clause: str) -> tuple[str, ...]:
    """Classify one clause with mutually exclusive semantic precedence."""

    normal = _normalise_text(clause)
    # A bare deictic is meaningful precisely because its referent is absent.
    # Restrict this rule to a complete short clause; ordinary demonstratives
    # inside a larger proposition are not unknowns by themselves.
    if _STANDALONE_DEICTIC_RE.fullmatch(normal) is not None:
        return ("omitted_referent",)
    open_decision = _OPEN_DECISION_MORPHOLOGY_RE.search(normal) is not None
    uncertain = _UNCERTAINTY_RE.search(normal) is not None or open_decision
    cause_marker = re.search(
        r"(?:なぜ|どうして|なんで|理由|原因|わけ)", normal
    )
    cause_open = re.search(
        r"(?:分から|わから|判ら|不明|言葉にでき|"
        r"説明でき|特定でき|だろう|かな(?:[。！？!?]|$))",
        normal,
    )
    if cause_marker is not None and cause_open is not None:
        return ("cause",)
    # ``置かれるのでは`` and the equivalent passive construction report an
    # anticipated outcome whose truth remains open.  It is a future boundary,
    # not an assertion about the other person's actual state.
    if _ANTICIPATED_PASSIVE_OUTCOME_RE.search(normal) is not None:
        return ("future_outcome",)
    # Projected judgments carry an other-person boundary even without a
    # separate ``分からない`` predicate.
    if _PROJECTED_JUDGMENT_RE.search(normal) is not None:
        return ("other_person",)
    if _OTHER_PERSON_AWARENESS_RE.search(normal) is not None:
        return ("other_person",)
    # A decision predicate can govern an omitted event/content argument.  The
    # missing argument owns the boundary, so classify it before the generic
    # choice-state rule below.
    if _CONTENT_REFERENT_OPEN_RE.search(normal) is not None:
        return ("omitted_referent",)
    if _POST_DECISION_COMPARATIVE_RE.search(normal) is not None:
        return ("post_decision_comparative_merit",)
    if open_decision:
        return ("decision_state",)
    # Resolve the grammatical focus before considering a surrounding choice
    # word.  For example, ``この選び方で大事な点を見落としていないかな``
    # owns an omitted-point boundary, not a choice-decision boundary.
    if (
        re.search(
            r"(?:あの件|この件|その件|あのこと|このこと|そのこと)",
            normal,
        )
        or uncertain
        and re.search(
            r"(?:何について|何のこと|どの部分|どのこと|"
            r"どれ|どこ|何が|何を|何から|"
            r"見落としていな|抜けていな|欠けていな)",
            normal,
        )
        or uncertain
        and re.fullmatch(
            r"(?:まだ)?(?:よく)?分からない[。！？!?]?", normal
        )
    ):
        return ("omitted_referent",)
    if uncertain and re.search(
        r"(?:決め|選(?:ぶ|べ)|選択|どちら|どうする|"
        r"続けるか|意図|つもり|したいのか|"
        r"ほうがよかった|方がよかった)",
        normal,
    ):
        return ("decision_state",)
    if uncertain and re.search(
        r"(?:思われ|見られ|言われ|相手|周り|みんな|他の人)",
        normal,
    ):
        return ("other_person",)
    if uncertain and re.search(
        r"(?:関係|つながり|距離|バランス|折り合い|両立)",
        normal,
    ):
        return ("relation",)
    if uncertain and re.search(
        r"(?:これから|今後|次(?:回|は|に)|明日|来週|将来|この先|先の)",
        normal,
    ):
        return ("future_outcome",)
    if uncertain:
        return ("unspecified",)
    return ()


def _unknown_focus_range(
    clause: str,
    unknown_type: str,
) -> tuple[int, int]:
    """Return the smallest safe contiguous span that owns an unknown."""

    end = len(clause.rstrip("。！？!?"))
    start = 0
    if unknown_type == "cause":
        marker = re.search(r"(?:なぜ|どうして|なんで|理由|原因|わけ)", clause[:end])
        if marker is not None:
            start = marker.start()
    elif unknown_type == "other_person":
        projected = _PROJECTED_EVALUATION_END_RE.search(clause[:end])
        if projected is not None:
            end = projected.end()
            delimiter = max(
                clause.rfind("。", 0, projected.start()),
                clause.rfind("！", 0, projected.start()),
                clause.rfind("？", 0, projected.start()),
                clause.rfind("、", 0, projected.start()),
            )
            start = delimiter + 1
        else:
            awareness = _OTHER_PERSON_AWARENESS_RE.search(clause[:end])
            if awareness is not None:
                start, end = awareness.span("focus")
    elif unknown_type == "omitted_referent":
        marker = re.search(
            r"(?:何について|何のこと|どの部分|どのこと|"
            r"どれ|どこ|何が|何を|何から|どの点|"
            r"出来事|内容|話題|対象|どの件)",
            clause[:end],
        )
        if marker is not None:
            start = marker.start()
            content_open = _CONTENT_REFERENT_OPEN_RE.search(
                clause, marker.start(), end
            )
            if content_open is not None:
                end = content_open.end("focus")
        else:
            deictic = _STANDALONE_DEICTIC_RE.fullmatch(clause.strip())
            if deictic is not None:
                start = clause.find(deictic.group(0))
                end = start + len(deictic.group(0).rstrip("。！？!?"))
    elif unknown_type == "future_outcome":
        anticipated = _ANTICIPATED_PASSIVE_OUTCOME_RE.search(clause[:end])
        if anticipated is not None:
            start, end = anticipated.span("focus")
    elif unknown_type in {
        "unresolved_intention",
        "decision_state",
        "post_decision_comparative_merit",
    }:
        marker = (
            _POST_DECISION_COMPARATIVE_RE.search(clause[:end])
            if unknown_type == "post_decision_comparative_merit"
            else _OPEN_DECISION_RE.search(clause[:end])
        )
        if marker is not None:
            delimiter = clause.rfind("、", 0, marker.start())
            start = delimiter + 1
            next_delimiter = clause.find("、", marker.end(), end)
            if next_delimiter >= 0:
                end = next_delimiter
    while start < end and clause[start].isspace():
        start += 1
    while end > start and clause[end - 1].isspace():
        end -= 1
    return start, end


def _decision_context(
    unknown_type: str,
    *,
    source_anchor_ids: Sequence[str],
    target_nucleus_ids: Sequence[str],
    anchors: Sequence[Step11SourceAnchor],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Derive decision state and context only from exact current anchors."""

    if unknown_type not in {
        "decision_state",
        "post_decision_comparative_merit",
    }:
        return "not_applicable", (), ()
    anchor_by_id = {row.anchor_id: row for row in anchors}
    nucleus_by_anchor = {
        anchor_id: nucleus_id
        for nucleus_id, anchor_ids in anchor_ids_by_nucleus.items()
        for anchor_id in anchor_ids
    }
    source_ids = tuple(
        anchor_id
        for anchor_id in dict.fromkeys(source_anchor_ids)
        if anchor_id in anchor_by_id
    )
    if unknown_type == "decision_state":
        context_anchor_ids = source_ids
        context_nucleus_ids = tuple(
            sorted(
                set(target_nucleus_ids)
                | {
                    nucleus_by_anchor[anchor_id]
                    for anchor_id in context_anchor_ids
                    if anchor_id in nucleus_by_anchor
                }
            )
        )
        return "open", context_nucleus_ids, context_anchor_ids

    completed_anchor_ids = tuple(
        row.anchor_id
        for row in anchors
        if row.role == "nucleus"
        and _COMPLETED_DECISION_RE.search(row.text) is not None
    )
    # A post-decision comparative itself grammatically presupposes the
    # completed selection.  Use that exact span when no separate completed
    # decision clause exists; never invent a context or bind another case.
    context_anchor_ids = completed_anchor_ids or source_ids
    context_nucleus_ids = tuple(
        sorted(
            {
                nucleus_by_anchor[anchor_id]
                for anchor_id in context_anchor_ids
                if anchor_id in nucleus_by_anchor
            }
            or set(target_nucleus_ids)
        )
    )
    return "completed", context_nucleus_ids, context_anchor_ids


def _temporal_referent_is_open(
    source_text: str,
    *,
    contextual_text: str,
) -> bool:
    """Distinguish a missing temporal anchor from an ordinary connective."""

    marker = _RELATIVE_TEMPORAL_DEICTIC_RE.search(source_text)
    if marker is None:
        return False
    if _CONTEXTUAL_PRECEDING_EVENT_RE.search(source_text[: marker.start()]):
        return False
    # A preceding app-field proposition may supply the event that the action's
    # relative-time connective follows.  Remove the affected source span before
    # checking so the connective cannot count as its own antecedent.
    surrounding = contextual_text.replace(source_text, "", 1)
    if _CONTEXTUAL_PRECEDING_EVENT_RE.search(surrounding) is not None:
        return False
    return True


def _frozen_unknown_type(
    dimension_code: str,
    source_text: str,
    *,
    contextual_text: str = "",
) -> str | None:
    code = dimension_code.upper()
    if "CAUSE" in code or "REASON" in code or "MOTIVE" in code:
        return (
            "cause"
            if code.startswith("EXPLICIT_")
            or "cause" in _explicit_unknown_types(source_text)
            or re.search(r"(?:なんとなく|理由もなく|わけもなく)", source_text)
            else None
        )
    if any(token in code for token in ("CHOICE", "DECISION", "INTENTION")):
        classified = _explicit_unknown_types(source_text)
        post_decision_comparative = (
            _POST_DECISION_COMPARATIVE_RE.search(source_text) is not None
        )
        open_decision = (
            _OPEN_DECISION_MORPHOLOGY_RE.search(source_text) is not None
        )
        completed_decision = (
            _COMPLETED_DECISION_RE.search(source_text) is not None
        )
        # The frozen choice/decision dimension supplies provenance.  Resolve
        # its lifecycle before the grammar-only content-referent rule: a
        # decision predicate can mention an event/content object and still
        # state that the decision itself remains open.  Keep the grammar-only
        # classifier unchanged for unknowns that lack this frozen dimension.
        # A source span that independently says both "completed" and "open"
        # cannot be collapsed into either lifecycle.  The source must instead
        # be decomposed upstream, so the overlay fails closed here.
        if open_decision and (
            completed_decision or post_decision_comparative
        ):
            return None
        if post_decision_comparative:
            return "post_decision_comparative_merit"
        if open_decision:
            return "decision_state"
        # The frozen upstream witness classifies ordinary hesitation (for
        # example a non-terminal ``迷う`` construction) as an explicit
        # choice/decision unknown.  Reuse that exact contract only when all
        # dimension tokens are present, the target-owned source range itself
        # contains uncertainty, and no completed decision conflicts with it.
        # This does not widen grammar-only discovery or trust the dimension
        # code without an independent source witness.
        code_tokens = frozenset(code.split("_"))
        if (
            code.startswith("EXPLICIT_")
            and {"CHOICE", "DECISION", "UNKNOWN"} <= code_tokens
            and _UNCERTAINTY_RE.search(source_text) is not None
            and not completed_decision
        ):
            return "decision_state"
        if "omitted_referent" in classified:
            return "omitted_referent"
        if "unresolved_intention" in classified:
            return "unresolved_intention"
        return None
    if "OTHER_PERSON" in code or "OTHER_REACTION" in code:
        classified = _explicit_unknown_types(source_text)
        return (
            "other_person"
            if "other_person" in classified
            or code.startswith("EXPLICIT_")
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
            and _UNCERTAINTY_RE.search(source_text) is not None
            else None
        )
    if "RELATION" in code or "CONNECTION" in code:
        return (
            "relation"
            if code.startswith("EXPLICIT_")
            or "relation" in _explicit_unknown_types(source_text)
            else None
        )
    if "TEMPORAL_REFERENT" in code:
        return (
            "omitted_referent"
            if _temporal_referent_is_open(
                source_text,
                contextual_text=contextual_text or source_text,
            )
            else None
        )
    if any(token in code for token in ("REFERENT", "OBJECT", "TARGET", "SUBJECT")):
        classified = _explicit_unknown_types(source_text)
        if "omitted_referent" in classified:
            return "omitted_referent"
        return "unspecified" if code.startswith("EXPLICIT_") else None
    classified = _explicit_unknown_types(source_text)
    if classified:
        return classified[0]
    return "unspecified" if code.startswith("EXPLICIT_") else None


def _exact_relation_unknown_endpoint_set(
    target_nucleus_ids: Sequence[str],
    relations: Sequence[Any],
) -> bool:
    """Require one source-backed relation with exactly the same endpoints."""

    targets = tuple(sorted(set(target_nucleus_ids)))
    if len(targets) != 2 or len(targets) != len(target_nucleus_ids):
        return False
    return any(
        tuple(
            sorted(
                {
                    str(relation.from_nucleus_id),
                    str(relation.to_nucleus_id),
                }
            )
        )
        == targets
        and relation.from_nucleus_id != relation.to_nucleus_id
        for relation in relations
    )


def _closed_prefix_exact_nucleus_binding(
    *,
    source_text: str,
    source_slot: str,
    start: int,
    end: int,
    target_nucleus_ids: Sequence[str],
    anchors: Sequence[Step11SourceAnchor],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
) -> tuple[str, str] | None:
    """Resolve a closed leading connective to one exact active nucleus.

    No prefix is removed from an ownership range by text similarity.  The
    suffix must itself be the exact range of one and only one active nucleus
    anchor; otherwise the wider grammar range remains authoritative.
    """

    fragment = source_text[start:end]
    prefix = _CLOSED_UNKNOWN_CONNECTIVE_PREFIX_RE.match(fragment)
    if prefix is None:
        return None
    owned_start = start + prefix.end()
    while owned_start < end and source_text[owned_start].isspace():
        owned_start += 1
    if owned_start >= end:
        return None
    anchor_by_id = {row.anchor_id: row for row in anchors}
    candidates: set[tuple[str, str]] = set()
    for nucleus_id in tuple(sorted(set(target_nucleus_ids))):
        for anchor_id in anchor_ids_by_nucleus.get(nucleus_id, ()):
            anchor = anchor_by_id.get(anchor_id)
            if (
                anchor is not None
                and anchor.role == "nucleus"
                and anchor.source_slot == source_slot
                and anchor.start == owned_start
                and anchor.end == end
                and anchor.text == source_text[owned_start:end]
            ):
                candidates.add((nucleus_id, anchor_id))
    if len(candidates) != 1:
        return None
    return next(iter(candidates))


def _grammar_unknowns(
    projection: Mapping[str, Any],
    anchors: list[Step11SourceAnchor],
    *,
    active_slots: frozenset[str],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
    relations: Sequence[Step11OverlayRelation],
) -> list[Step11TypedUnknown]:
    unknowns: list[Step11TypedUnknown] = []
    for slot, field in (("thought", "thought_text"), ("action", "action_text")):
        if slot not in active_slots:
            continue
        text = str(projection[field])
        for start, end in _clause_spans(text):
            clause = text[start:end]
            for detected_type in _explicit_unknown_types(clause):
                focus_start, focus_end = _unknown_focus_range(
                    clause, detected_type
                )
                absolute_start = start + focus_start
                absolute_end = start + focus_end
                anchor_by_id = {row.anchor_id: row for row in anchors}
                target_nuclei = tuple(
                    sorted(
                        nucleus_id
                        for nucleus_id, nucleus_anchor_ids
                        in anchor_ids_by_nucleus.items()
                        if any(
                            (
                                anchor_by_id[nucleus_anchor_id].source_slot
                                == slot
                                and anchor_by_id[nucleus_anchor_id].start
                                < absolute_end
                                and absolute_start
                                < anchor_by_id[nucleus_anchor_id].end
                            )
                            for nucleus_anchor_id in nucleus_anchor_ids
                        )
                    )
                )
                if not target_nuclei:
                    target_nuclei = tuple(
                        sorted(
                            nucleus_id
                            for nucleus_id, nucleus_anchor_ids
                            in anchor_ids_by_nucleus.items()
                            if any(
                                (
                                    anchor_by_id[nucleus_anchor_id].source_slot
                                    == slot
                                    and anchor_by_id[nucleus_anchor_id].start < end
                                    and start
                                    < anchor_by_id[nucleus_anchor_id].end
                                )
                                for nucleus_anchor_id in nucleus_anchor_ids
                            )
                        )
                    )
                unknown_type = detected_type
                source_rule = f"grammar_{unknown_type}"
                if (
                    unknown_type == "relation"
                    and not _exact_relation_unknown_endpoint_set(
                        target_nuclei, relations
                    )
                ):
                    # A one-ended or otherwise unowned grammatical relation
                    # marker may preserve openness, but cannot assert typed
                    # relation semantics.  Required source-owned relation
                    # unknowns are handled separately and fail closed.
                    unknown_type = "unspecified"
                    source_rule = (
                        "grammar_relation_without_exact_endpoints_as_unspecified"
                    )
                prefix_binding = _closed_prefix_exact_nucleus_binding(
                    source_text=text,
                    source_slot=slot,
                    start=absolute_start,
                    end=absolute_end,
                    target_nucleus_ids=target_nuclei,
                    anchors=anchors,
                    anchor_ids_by_nucleus=anchor_ids_by_nucleus,
                )
                if prefix_binding is not None:
                    target_nuclei = (prefix_binding[0],)
                    bound_source_anchor_ids = (prefix_binding[1],)
                else:
                    clause_core = _normalise_text(
                        text[absolute_start:absolute_end]
                    ).rstrip("。！？!?")
                    exact_target_anchor_ids = tuple(
                        dict.fromkeys(
                            target_anchor_id
                            for nucleus_id in target_nuclei
                            for target_anchor_id in anchor_ids_by_nucleus.get(
                                nucleus_id, ()
                            )
                            if _normalise_text(
                                anchor_by_id[target_anchor_id].text
                            ).rstrip("。！？!?")
                            == clause_core
                        )
                    )
                    if len(exact_target_anchor_ids) == 1:
                        bound_source_anchor_ids = exact_target_anchor_ids
                    else:
                        anchor_id = _append_anchor(
                            anchors,
                            source_slot=slot,
                            role="unknown",
                            text=text,
                            start=absolute_start,
                            end=absolute_end,
                        )
                        bound_source_anchor_ids = (anchor_id,)
                (
                    decision_state,
                    context_nucleus_ids,
                    context_anchor_ids,
                ) = _decision_context(
                    unknown_type,
                    source_anchor_ids=bound_source_anchor_ids,
                    target_nucleus_ids=target_nuclei,
                    anchors=anchors,
                    anchor_ids_by_nucleus=anchor_ids_by_nucleus,
                )
                _add_unknown(
                    unknowns,
                    unknown_type=unknown_type,
                    source_slots=(slot,),
                    source_anchor_ids=bound_source_anchor_ids,
                    target_nucleus_ids=target_nuclei,
                    source_rule=source_rule,
                    epistemic_basis="explicit_unknown",
                    decision_state=decision_state,
                    context_nucleus_ids=context_nucleus_ids,
                    context_anchor_ids=context_anchor_ids,
                )

    # A plural candidate set that is only narrowed/compared does not establish
    # a final selection.  When the thought side independently exposes an open
    # selection criterion or referent, retain that second, bounded boundary on
    # the action span.  This is intentionally structural: neither a case id nor
    # a corpus label participates in the decision.
    thought_has_open_selection_scope = any(
        row.unknown_type == "omitted_referent"
        and "thought" in row.source_slots
        for row in unknowns
    ) and re.search(
        r"(?:選び方|選択|候補|どれ|何を選|決め)",
        str(projection["thought_text"]),
    ) is not None
    action_text = str(projection["action_text"])
    candidate_set = _OPEN_CANDIDATE_SET_RE.search(action_text)
    if (
        "action" in active_slots
        and thought_has_open_selection_scope
        and candidate_set is not None
        and _FINAL_SELECTION_RE.search(action_text) is None
    ):
        candidate_start, candidate_end = candidate_set.span("focus")
        anchor_id = _append_anchor(
            anchors,
            source_slot="action",
            role="unknown",
            text=action_text,
            start=candidate_start,
            end=candidate_end,
        )
        anchor_by_id = {row.anchor_id: row for row in anchors}
        target_nuclei = tuple(
            sorted(
                nucleus_id
                for nucleus_id, nucleus_anchor_ids
                in anchor_ids_by_nucleus.items()
                if any(
                    anchor_by_id[nucleus_anchor_id].source_slot == "action"
                    and anchor_by_id[nucleus_anchor_id].start < candidate_end
                    and candidate_start < anchor_by_id[nucleus_anchor_id].end
                    for nucleus_anchor_id in nucleus_anchor_ids
                )
            )
        )
        if not target_nuclei:
            target_nuclei = tuple(
                sorted(
                    nucleus_id
                    for nucleus_id, nucleus_anchor_ids
                    in anchor_ids_by_nucleus.items()
                    if any(
                        anchor_by_id[nucleus_anchor_id].source_slot
                        == "action"
                        for nucleus_anchor_id in nucleus_anchor_ids
                    )
                )
            )
        _add_unknown(
            unknowns,
            unknown_type="unresolved_intention",
            source_slots=("action",),
            source_anchor_ids=(anchor_id,),
            target_nucleus_ids=target_nuclei,
            source_rule="bounded_open_candidate_set",
            epistemic_basis="bounded_inference",
        )
    return unknowns


def _source_unknowns(
    inventory_result: SemanticObligationInventoryResult,
    anchors: list[Step11SourceAnchor],
    *,
    active_nucleus_ids: frozenset[str],
    projection: Mapping[str, Any],
    relations: Sequence[Step11OverlayRelation],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
) -> list[Step11TypedUnknown]:
    snapshot = inventory_result.source_snapshot
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    unknowns: list[Step11TypedUnknown] = []
    for source in snapshot.unknowns:
        affected = tuple(
            sorted(set(source.affected_nucleus_ids) & active_nucleus_ids)
        )
        if not source.required or not affected:
            continue
        slots = tuple(
            sorted(
                {
                    slot
                    for nucleus_id in affected
                    for slot in _slots_for_nucleus(nucleus_by_id[nucleus_id])
                },
                key=_SLOT_ORDER.__getitem__,
            )
        )
        candidate_anchor_ids = tuple(
            dict.fromkeys(
                anchor_id
                for nucleus_id in affected
                for anchor_id in anchor_ids_by_nucleus.get(nucleus_id, ())
            )
        ) or _first_anchor_ids(anchors, slots)
        anchor_by_id = {row.anchor_id: row for row in anchors}
        candidate_text = " ".join(
            anchor_by_id[anchor_id].text
            for anchor_id in candidate_anchor_ids
            if anchor_id in anchor_by_id
        )
        unknown_type = _frozen_unknown_type(
            source.dimension_code,
            candidate_text,
            contextual_text=(
                str(projection["thought_text"])
                + "\n"
                + str(projection["action_text"])
            ),
        )
        if unknown_type == "relation" and not (
            _exact_relation_unknown_endpoint_set(
                affected, snapshot.relations
            )
            and _exact_relation_unknown_endpoint_set(affected, relations)
        ):
            independently_classified = _explicit_unknown_types(
                candidate_text
            )
            if (
                independently_classified
                and independently_classified[0] != "relation"
            ):
                unknown_type = independently_classified[0]
            else:
                unknown_type = None
        if unknown_type is None:
            if "TEMPORAL_REFERENT" in str(source.dimension_code).upper():
                continue
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_REQUIRED_UNKNOWN_UNCLASSIFIED"
            )
        matching_anchor_ids = tuple(
            anchor_id
            for anchor_id in candidate_anchor_ids
            if unknown_type
            in _explicit_unknown_types(anchor_by_id[anchor_id].text)
        )
        target_ranges = tuple(
            anchor_by_id[anchor_id]
            for anchor_id in candidate_anchor_ids
            if anchor_id in anchor_by_id
        )
        grammar_anchor_ids = tuple(
            row.anchor_id
            for row in anchors
            if row.role == "unknown"
            and row.source_slot in slots
            and unknown_type in _explicit_unknown_types(row.text)
            and (
                not target_ranges
                or any(
                    row.source_slot == target.source_slot
                    and row.start < target.end
                    and target.start < row.end
                    for target in target_ranges
                )
            )
        )
        bound_source_anchor_ids = (
            grammar_anchor_ids[:1]
            or matching_anchor_ids[:1]
            or candidate_anchor_ids[:1]
        )
        (
            decision_state,
            context_nucleus_ids,
            context_anchor_ids,
        ) = _decision_context(
            unknown_type,
            source_anchor_ids=bound_source_anchor_ids,
            target_nucleus_ids=affected,
            anchors=anchors,
            anchor_ids_by_nucleus=anchor_ids_by_nucleus,
        )
        _add_unknown(
            unknowns,
            unknown_type=unknown_type,
            source_slots=slots,
            source_anchor_ids=bound_source_anchor_ids,
            target_nucleus_ids=affected,
            source_rule="frozen_required_unknown",
            source_unknown_ids=(source.source_id,),
            epistemic_basis="frozen_required",
            decision_state=decision_state,
            context_nucleus_ids=context_nucleus_ids,
            context_anchor_ids=context_anchor_ids,
        )
    del projection
    return unknowns


def _suppressed_source_unknowns(
    inventory_result: SemanticObligationInventoryResult,
    anchors: Sequence[Step11SourceAnchor],
    *,
    active_nucleus_ids: frozenset[str],
    projection: Mapping[str, Any],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
) -> tuple[Step11SuppressedUnknown, ...]:
    """Materialise exact provenance for context-resolved temporal unknowns."""

    snapshot = inventory_result.source_snapshot
    nucleus_by_id = {row.source_id: row for row in snapshot.nuclei}
    anchor_by_id = {row.anchor_id: row for row in anchors}
    bound_anchor_ids = tuple(
        dict.fromkeys(
            anchor_id
            for nucleus_id in sorted(active_nucleus_ids)
            for anchor_id in anchor_ids_by_nucleus.get(nucleus_id, ())
        )
    )
    contextual_text = (
        str(projection["thought_text"])
        + "\n"
        + str(projection["action_text"])
    )
    result: list[Step11SuppressedUnknown] = []
    for source in sorted(snapshot.unknowns, key=lambda row: row.source_id):
        affected = tuple(
            sorted(set(source.affected_nucleus_ids) & active_nucleus_ids)
        )
        if (
            source.required is not True
            or not affected
            or "TEMPORAL_REFERENT"
            not in str(source.dimension_code).upper()
        ):
            continue
        target_anchor_ids = tuple(
            dict.fromkeys(
                anchor_id
                for nucleus_id in affected
                for anchor_id in anchor_ids_by_nucleus.get(nucleus_id, ())
            )
        )
        source_anchor_ids = tuple(
            anchor_id
            for anchor_id in target_anchor_ids
            if anchor_id in anchor_by_id
            and _RELATIVE_TEMPORAL_DEICTIC_RE.search(
                anchor_by_id[anchor_id].text
            )
            is not None
        )
        if not source_anchor_ids:
            continue
        source_text = " ".join(
            anchor_by_id[anchor_id].text
            for anchor_id in source_anchor_ids
        )
        if _temporal_referent_is_open(
            source_text, contextual_text=contextual_text
        ):
            continue
        context_anchor_ids: list[str] = []
        for anchor_id in bound_anchor_ids:
            anchor = anchor_by_id.get(anchor_id)
            if anchor is None:
                continue
            if anchor_id in source_anchor_ids:
                marker = _RELATIVE_TEMPORAL_DEICTIC_RE.search(anchor.text)
                if (
                    marker is not None
                    and _CONTEXTUAL_PRECEDING_EVENT_RE.search(
                        anchor.text[: marker.start()]
                    )
                    is not None
                ):
                    context_anchor_ids.append(anchor_id)
                continue
            if _CONTEXTUAL_PRECEDING_EVENT_RE.search(anchor.text) is not None:
                context_anchor_ids.append(anchor_id)
        if not context_anchor_ids:
            # Absence of an exact source-bound antecedent is not evidence of
            # resolution.  Leave the raw required unknown visible to fail
            # closed in the inverse coverage check.
            continue
        slots = tuple(
            sorted(
                {
                    slot
                    for nucleus_id in affected
                    for slot in _slots_for_nucleus(nucleus_by_id[nucleus_id])
                },
                key=_SLOT_ORDER.__getitem__,
            )
        )
        result.append(
            Step11SuppressedUnknown(
                source_unknown_id=str(source.source_id),
                original_dimension_code=str(source.dimension_code),
                source_slots=slots,
                source_anchor_ids=source_anchor_ids,
                target_nucleus_ids=affected,
                context_anchor_ids=tuple(dict.fromkeys(context_anchor_ids)),
                suppression_reason=_TEMPORAL_SUPPRESSION_REASON,
                evidence_grade=_TEMPORAL_SUPPRESSION_GRADE,
            )
        )
    return tuple(result)


def _canonical_unknowns(
    rows: Sequence[Step11TypedUnknown],
    anchors: Sequence[Step11SourceAnchor],
) -> tuple[Step11TypedUnknown, ...]:
    """Merge only unknowns with identical source ownership and targets."""

    anchor_by_id = {row.anchor_id: row for row in anchors}
    basis_rank = {
        "bounded_inference": 0,
        "explicit_unknown": 1,
        "frozen_required": 2,
    }
    role_rank = {"unknown": 0, "nucleus": 1}
    grouped: dict[
        tuple[
            str,
            tuple[tuple[str, int, int, str], ...],
        ],
        dict[str, Any],
    ] = {}
    for row in rows:
        source_anchors = tuple(
            anchor_by_id.get(anchor_id) for anchor_id in row.source_anchor_ids
        )
        if not source_anchors or any(anchor is None for anchor in source_anchors):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_SOURCE_OWNERSHIP_INVALID"
            )
        ownership_key = tuple(
            sorted(
                {
                    (
                        str(anchor.source_slot),
                        int(anchor.start),
                        int(anchor.end),
                        str(anchor.text_sha256),
                    )
                    for anchor in source_anchors
                    if anchor is not None
                }
            )
        )
        if not ownership_key:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_SOURCE_OWNERSHIP_INVALID"
            )
        context_source_anchors = tuple(
            anchor_by_id.get(anchor_id) for anchor_id in row.context_anchor_ids
        )
        if any(anchor is None for anchor in context_source_anchors):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_CONTEXT_OWNERSHIP_INVALID"
            )
        context_ownership_key = tuple(
            sorted(
                {
                    (
                        str(anchor.source_slot),
                        int(anchor.start),
                        int(anchor.end),
                        str(anchor.text_sha256),
                    )
                    for anchor in context_source_anchors
                    if anchor is not None
                }
            )
        )
        target_nuclei = tuple(sorted(row.target_nucleus_ids))
        key = (row.unknown_type, ownership_key)
        state = grouped.setdefault(
            key,
            {
                "target_nuclei": set(),
                "source_slots": row.source_slots,
                "source_ids": set(),
                "rules": set(),
                "basis": row.epistemic_basis,
                "decision_state": row.decision_state,
                "context_nucleus_ids": row.context_nucleus_ids,
                "context_ownership_key": context_ownership_key,
                "anchor_candidates": {},
                "context_anchor_candidates": {},
            },
        )
        state["target_nuclei"].update(target_nuclei)  # type: ignore[union-attr]
        if (
            state["decision_state"] != row.decision_state
            or state["context_nucleus_ids"] != row.context_nucleus_ids
            or state["context_ownership_key"] != context_ownership_key
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_CANONICAL_CONTEXT_CONFLICT"
            )
        state["source_ids"].update(row.source_unknown_ids)  # type: ignore[union-attr]
        state["rules"].update(row.source_rules)  # type: ignore[union-attr]
        existing_basis_rank = basis_rank[str(state["basis"])]
        current_basis_rank = basis_rank[row.epistemic_basis]
        if current_basis_rank > existing_basis_rank:
            state["basis"] = row.epistemic_basis
            state["source_slots"] = row.source_slots
        elif (
            current_basis_rank == existing_basis_rank
            and state["source_slots"] != row.source_slots
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_UNKNOWN_CANONICAL_SLOT_CONFLICT"
            )
        anchor_candidates = state["anchor_candidates"]
        for anchor_id, anchor in zip(row.source_anchor_ids, source_anchors):
            if anchor is None:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_UNKNOWN_SOURCE_OWNERSHIP_INVALID"
                )
            signature = (
                anchor.source_slot,
                anchor.start,
                anchor.end,
                anchor.text_sha256,
            )
            anchor_candidates.setdefault(signature, []).append(  # type: ignore[union-attr]
                (
                    basis_rank[row.epistemic_basis],
                    role_rank.get(anchor.role, -1),
                    anchor_id,
                )
            )
        context_anchor_candidates = state["context_anchor_candidates"]
        for anchor_id, anchor in zip(
            row.context_anchor_ids, context_source_anchors
        ):
            if anchor is None:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_UNKNOWN_CONTEXT_OWNERSHIP_INVALID"
                )
            signature = (
                anchor.source_slot,
                anchor.start,
                anchor.end,
                anchor.text_sha256,
            )
            context_anchor_candidates.setdefault(signature, []).append(  # type: ignore[union-attr]
                (
                    basis_rank[row.epistemic_basis],
                    role_rank.get(anchor.role, -1),
                    anchor_id,
                )
            )

    specific_anchor_sets = {
        ownership_key
        for (unknown_type, ownership_key) in grouped
        if unknown_type != "unspecified"
    }
    result: list[Step11TypedUnknown] = []
    for (unknown_type, ownership_key), state in sorted(
        grouped.items()
    ):
        if (
            unknown_type == "unspecified"
            and ownership_key in specific_anchor_sets
            and not state["source_ids"]
        ):
            continue
        targets = tuple(sorted(state["target_nuclei"]))
        anchor_candidates = state["anchor_candidates"]
        anchor_ids = tuple(
            max(anchor_candidates[signature])[2]  # type: ignore[index]
            for signature in ownership_key
        )
        slots = tuple(
            sorted(
                set(state["source_slots"]),  # type: ignore[arg-type]
                key=_SLOT_ORDER.__getitem__,
            )
        )
        source_ids = tuple(sorted(state["source_ids"]))  # type: ignore[arg-type]
        rules = tuple(sorted(state["rules"]))  # type: ignore[arg-type]
        basis = str(state["basis"])
        decision_state = str(state["decision_state"])
        context_nuclei = tuple(state["context_nucleus_ids"])
        context_anchor_candidates = state["context_anchor_candidates"]
        context_anchors = tuple(
            max(context_anchor_candidates[signature])[2]  # type: ignore[index]
            for signature in state["context_ownership_key"]
        )
        material = _unknown_material(
            unknown_type=unknown_type,
            source_slots=slots,
            source_anchor_ids=anchor_ids,
            target_nucleus_ids=targets,
            source_unknown_ids=source_ids,
            source_rules=rules,
            epistemic_basis=basis,
            decision_state=decision_state,
            context_nucleus_ids=context_nuclei,
            context_anchor_ids=context_anchors,
        )
        result.append(
            Step11TypedUnknown(
                unknown_id="s11unk_" + artifact_sha256(material)[:16],
                unknown_type=unknown_type,
                source_slots=slots,
                source_anchor_ids=anchor_ids,
                target_nucleus_ids=targets,
                source_unknown_ids=source_ids,
                source_rules=rules,
                epistemic_basis=basis,
                decision_state=decision_state,
                context_nucleus_ids=context_nuclei,
                context_anchor_ids=context_anchors,
            )
        )
    return tuple(result)


def _require_complete_source_unknown_coverage(
    inventory_result: SemanticObligationInventoryResult,
    *,
    active_nucleus_ids: frozenset[str],
    unknowns: Sequence[Step11TypedUnknown],
    suppressed_unknowns: Sequence[Step11SuppressedUnknown],
) -> None:
    required_ids = {
        str(row.source_id)
        for row in inventory_result.source_snapshot.unknowns
        if row.required is True
        and set(row.affected_nucleus_ids) & active_nucleus_ids
    }
    visible_ids = [
        source_id
        for row in unknowns
        for source_id in row.source_unknown_ids
    ]
    suppressed_ids = [row.source_unknown_id for row in suppressed_unknowns]
    represented = visible_ids + suppressed_ids
    if (
        set(represented) != required_ids
        or len(represented) != len(set(represented))
    ):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_REQUIRED_UNKNOWN_UNCLASSIFIED"
        )


def _required_self_denial_pairs(
    obligations_by_id: Mapping[str, Mapping[str, Any]],
    active_obligation_ids: frozenset[str],
) -> tuple[tuple[Mapping[str, Any], Mapping[str, Any]], ...]:
    """Resolve exact Step 4 required boundary pairs, or fail closed."""

    self_rows = tuple(
        row
        for obligation_id, row in obligations_by_id.items()
        if obligation_id in active_obligation_ids
        and row.get("required") is True
        and row.get("kind") == "self_denial_boundary"
    )
    counter_rows = tuple(
        row
        for obligation_id, row in obligations_by_id.items()
        if obligation_id in active_obligation_ids
        and row.get("required") is True
        and row.get("kind") == "bounded_counterposition"
    )
    counter_by_id = {
        str(row.get("obligation_id")): row for row in counter_rows
    }
    pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    consumed_counter_ids: set[str] = set()
    for self_row in sorted(
        self_rows, key=lambda row: str(row.get("obligation_id"))
    ):
        self_id = str(self_row.get("obligation_id"))
        self_nuclei = tuple(self_row.get("nucleus_ids", []))
        candidates = tuple(
            counter
            for counter_id, counter in counter_by_id.items()
            if counter_id in set(self_row.get("must_not_merge_with", []))
            and self_id in set(counter.get("must_not_merge_with", []))
            and self_nuclei
            and tuple(counter.get("nucleus_ids", [])) == self_nuclei
        )
        if len(candidates) != 1:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
            )
        counter = candidates[0]
        counter_id = str(counter.get("obligation_id"))
        if counter_id in consumed_counter_ids:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
            )
        consumed_counter_ids.add(counter_id)
        pairs.append((self_row, counter))
    if consumed_counter_ids != set(counter_by_id):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
        )
    return tuple(pairs)


def _reported_self_evaluations(
    projection: Mapping[str, Any],
    anchors: list[Step11SourceAnchor],
    *,
    obligations_by_id: Mapping[str, Mapping[str, Any]],
    active_obligation_ids: frozenset[str],
    anchor_ids_by_nucleus: Mapping[str, tuple[str, ...]],
) -> tuple[Step11ReportedSelfEvaluation, ...]:
    """Project only Step 4 required boundary authority into exact anchors."""

    anchor_by_id = {row.anchor_id: row for row in anchors}
    result: list[Step11ReportedSelfEvaluation] = []
    for self_row, _counter_row in _required_self_denial_pairs(
        obligations_by_id, active_obligation_ids
    ):
        for nucleus_id in tuple(self_row.get("nucleus_ids", [])):
            nucleus_anchor_ids = anchor_ids_by_nucleus.get(str(nucleus_id), ())
            if len(nucleus_anchor_ids) != 1:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
                )
            nucleus_anchor = anchor_by_id.get(nucleus_anchor_ids[0])
            if nucleus_anchor is None or nucleus_anchor.role != "nucleus":
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
                )
            projection_key = f"{nucleus_anchor.source_slot}_text"
            text = projection.get(projection_key)
            if type(text) is not str:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
                )
            anchor_id = _append_anchor(
                anchors,
                source_slot=nucleus_anchor.source_slot,
                role="self_evaluation",
                text=text,
                start=nucleus_anchor.start,
                end=nucleus_anchor.end,
            )
            material = {
                "source_slot": nucleus_anchor.source_slot,
                "source_anchor_id": anchor_id,
                "source_rule": _SELF_DENIAL_AUTHORITY_RULE,
                "identity_fact_denial_required": True,
                "bounded_counterposition_required": True,
                "source_counterposition_anchor_ids": [],
                "evaluation_target": "speaker_identity_or_trait",
            }
            result.append(
                Step11ReportedSelfEvaluation(
                    self_evaluation_id=(
                        "s11self_" + artifact_sha256(material)[:16]
                    ),
                    source_slot=nucleus_anchor.source_slot,
                    source_anchor_id=anchor_id,
                    source_rule=_SELF_DENIAL_AUTHORITY_RULE,
                    identity_fact_denial_required=True,
                    bounded_counterposition_required=True,
                    source_counterposition_anchor_ids=(),
                    evaluation_target="speaker_identity_or_trait",
                )
            )
    anchor_by_id = {row.anchor_id: row for row in anchors}
    return tuple(
        sorted(
            result,
            key=lambda row: (
                _SLOT_ORDER[row.source_slot],
                anchor_by_id[row.source_anchor_id].start,
                anchor_by_id[row.source_anchor_id].end,
                row.self_evaluation_id,
            ),
        )
    )


def _mixed_emotion_requirements(
    label_anchors: Sequence[Step11ExactLabelAnchor],
) -> tuple[Step11MixedEmotionRequirement, ...]:
    positive = tuple(
        row.label_anchor_id
        for row in label_anchors
        if row.source_slot == "emotion"
        and row.label in _EMOTION_VALENCE["positive"]
    )
    negative = tuple(
        row.label_anchor_id
        for row in label_anchors
        if row.source_slot == "emotion"
        and row.label in _EMOTION_VALENCE["negative"]
    )
    if not positive or not negative:
        return ()
    material = {
        "positive_label_anchor_ids": list(positive),
        "negative_label_anchor_ids": list(negative),
        "relation_type": "coexists_with",
        "relation_direction": "bidirectional",
        "required": True,
        "evidence_grade": "exact_current_input_mixed_valence",
    }
    return (
        Step11MixedEmotionRequirement(
            requirement_id="s11mix_" + artifact_sha256(material)[:16],
            positive_label_anchor_ids=positive,
            negative_label_anchor_ids=negative,
            relation_type="coexists_with",
            relation_direction="bidirectional",
            required=True,
            evidence_grade="exact_current_input_mixed_valence",
        ),
    )


def _reception_antecedent_bindings(
    *,
    obligations_by_id: Mapping[str, Mapping[str, Any]],
    active_obligation_ids: frozenset[str],
    discourse_plan: Mapping[str, Any],
    source_snapshot: Any,
    projection: Mapping[str, Any],
) -> tuple[Step11ReceptionAntecedentBinding, ...]:
    """Resolve visible reception owners from source authority, not proximity.

    rc0021 trusted the obligation selected by the legacy inventory even when
    that obligation merely intersected an opportunity target.  rc0022 keeps
    the legacy target as lineage, independently resolves the exact opportunity
    owner, and records every local referent that must be visible in the body.
    A narrowly bounded adapter also recovers a concrete, progressive main
    action when an upstream purpose-clause negation was allowed to overwrite
    the main predicate lifecycle.
    """

    nodes = discourse_plan.get("nodes")
    if type(nodes) is not list:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_RECEPTION_NODE_ROWS_INVALID"
        )
    nodes_by_obligation: dict[str, Mapping[str, Any]] = {}
    for node in nodes:
        obligation_id = node.get("obligation_id") if type(node) is dict else None
        if type(obligation_id) is not str or obligation_id in nodes_by_obligation:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_NODE_BINDING_INVALID"
            )
        nodes_by_obligation[obligation_id] = node

    opportunities = getattr(source_snapshot, "reception_opportunities", None)
    nuclei = getattr(source_snapshot, "nuclei", None)
    if type(opportunities) is not tuple or type(nuclei) is not tuple:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_RECEPTION_SOURCE_AUTHORITY_INVALID"
        )
    opportunity_by_id = {
        row.source_id: row
        for row in opportunities
        if type(getattr(row, "source_id", None)) is str
    }
    if len(opportunity_by_id) != len(opportunities):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_RECEPTION_SOURCE_AUTHORITY_INVALID"
        )
    nucleus_by_id = {
        row.source_id: row
        for row in nuclei
        if type(getattr(row, "source_id", None)) is str
    }
    if len(nucleus_by_id) != len(nuclei):
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_RECEPTION_SOURCE_AUTHORITY_INVALID"
        )

    def exact_owner_ids(
        nucleus_ids: Sequence[str],
        *,
        reception_act: str,
        preferred_obligation_ids: Sequence[str] = (),
    ) -> tuple[str, ...]:
        wanted = frozenset(nucleus_ids)
        if not wanted:
            return ()
        candidates = tuple(
            obligation_id
            for obligation_id in sorted(active_obligation_ids)
            if obligations_by_id[obligation_id].get("kind") != STANCE_KIND
            and frozenset(
                obligations_by_id[obligation_id].get("nucleus_ids", [])
            )
            == wanted
        )
        if not candidates:
            return ()
        preferred = tuple(
            row for row in preferred_obligation_ids if row in candidates
        )
        pool = preferred or candidates
        act_ranks = _RECEPTION_ACT_KIND_RANK.get(reception_act, {})

        def rank(obligation_id: str) -> tuple[int, int, str]:
            kind = str(obligations_by_id[obligation_id].get("kind"))
            return (
                int(act_ranks.get(kind, 20)),
                int(_RECEPTION_OWNER_KIND_RANK.get(kind, 20)),
                obligation_id,
            )

        ordered = tuple(sorted(pool, key=rank))
        best_rank = rank(ordered[0])[:2]
        best = tuple(row for row in ordered if rank(row)[:2] == best_rank)
        if len(best) != 1:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_EXACT_OWNER_AMBIGUOUS"
            )
        return best

    action_text = projection.get("action_text")
    if type(action_text) is not str:
        raise Step11SemanticOverlayError(
            "STEP11_OVERLAY_RECEPTION_ACTION_SOURCE_INVALID"
        )
    progressive_main_action = bool(
        action_text
        and _MAIN_ACTION_PROGRESSIVE_RE.search(action_text) is not None
    )
    purpose_negation_scope_correction = bool(
        progressive_main_action
        and _PURPOSE_NEGATION_PREFIX_RE.search(action_text) is not None
    )
    eligible_action_nucleus_ids = frozenset(
        nucleus_id
        for nucleus_id, nucleus in nucleus_by_id.items()
        if getattr(nucleus, "kind", None) == "action"
        and "memo_action" in getattr(nucleus, "source_fields", ())
        and "semantic_role:concrete_action_evidence"
        in getattr(nucleus, "source_attribute_codes", ())
        and progressive_main_action
    )

    def action_lifecycle_for(
        nucleus_ids: Sequence[str],
    ) -> str:
        statuses = {
            _nucleus_realization_status(
                nucleus_by_id[nucleus_id], (action_text,)
            )
            for nucleus_id in nucleus_ids
            if nucleus_id in nucleus_by_id
            and getattr(nucleus_by_id[nucleus_id], "kind", None)
            == "action"
        }
        if not statuses:
            return "not_applicable"
        return next(iter(statuses)) if len(statuses) == 1 else "undetermined"

    def corrected_action_support(
        primary_nucleus_ids: Sequence[str],
    ) -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
        if not eligible_action_nucleus_ids:
            return (), (), "none", "not_applicable"
        candidates = tuple(
            obligation_id
            for obligation_id in sorted(active_obligation_ids)
            if obligations_by_id[obligation_id].get("kind")
            == "intention_or_next_action"
            and frozenset(
                obligations_by_id[obligation_id].get("nucleus_ids", [])
            )
            and frozenset(
                obligations_by_id[obligation_id].get("nucleus_ids", [])
            )
            <= eligible_action_nucleus_ids
        )
        if len(candidates) > 1:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_ACTION_OWNER_AMBIGUOUS"
            )
        if not candidates:
            return (), (), "none", "not_applicable"
        obligation_id = candidates[0]
        action_nucleus_ids = tuple(
            obligations_by_id[obligation_id].get("nucleus_ids", [])
        )
        if set(action_nucleus_ids) <= set(primary_nucleus_ids):
            return (), (), "none", "reported_ongoing"
        support_role = (
            "legacy_purpose_negation_scope_corrected_action"
            if purpose_negation_scope_correction
            else "source_progressive_concrete_action"
        )
        return (
            (obligation_id,),
            action_nucleus_ids,
            support_role,
            "reported_ongoing",
        )

    result: list[Step11ReceptionAntecedentBinding] = []
    for reception_id in sorted(active_obligation_ids):
        reception = obligations_by_id[reception_id]
        if reception.get("kind") != STANCE_KIND:
            continue
        source_target_ids = tuple(reception.get("target_obligation_ids", []))
        if (
            not source_target_ids
            or len(source_target_ids) != len(set(source_target_ids))
            or not set(source_target_ids) <= active_obligation_ids
            or any(
                obligations_by_id[target_id].get("kind") == STANCE_KIND
                for target_id in source_target_ids
            )
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_ANTECEDENT_INVALID"
            )
        reception_node = nodes_by_obligation.get(reception_id)
        source_target_nodes = tuple(
            nodes_by_obligation.get(target_id) for target_id in source_target_ids
        )
        if reception_node is None or any(
            row is None for row in source_target_nodes
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_NODE_BINDING_INVALID"
            )
        source_target_node_ids = tuple(
            str(row.get("node_id"))
            for row in source_target_nodes
            if row is not None
        )
        if (
            tuple(reception_node.get("antecedent_node_ids", []))
            != tuple(sorted(source_target_node_ids))
            or reception_node.get("section_role") != "reception"
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_NODE_BINDING_INVALID"
            )
        allowed_acts = tuple(reception.get("allowed_response_acts", []))
        if not allowed_acts or len(allowed_acts) != len(set(allowed_acts)):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_ACT_INVALID"
            )
        source_opportunity_ids = tuple(
            reception.get("reception_opportunity_ids", [])
        )
        if (
            len(source_opportunity_ids) != len(set(source_opportunity_ids))
            or any(
                type(row) is not str or row not in opportunity_by_id
                for row in source_opportunity_ids
            )
            or len(source_opportunity_ids) > 1
        ):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_OPPORTUNITY_BINDING_INVALID"
            )
        source_target_nucleus_ids = tuple(
            sorted(
                {
                    str(nucleus_id)
                    for target_id in source_target_ids
                    for nucleus_id in obligations_by_id[target_id].get(
                        "nucleus_ids", []
                    )
                }
            )
        )
        opportunity = (
            opportunity_by_id[source_opportunity_ids[0]]
            if source_opportunity_ids
            else None
        )
        exact_target_nucleus_ids = (
            tuple(opportunity.target_nucleus_ids)
            if opportunity is not None
            else source_target_nucleus_ids
        )
        antecedent_ids = exact_owner_ids(
            exact_target_nucleus_ids,
            reception_act=str(allowed_acts[0]),
            preferred_obligation_ids=source_target_ids,
        )
        if not antecedent_ids:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_EXACT_OWNER_UNRESOLVED"
            )
        antecedent_nodes = tuple(
            nodes_by_obligation.get(target_id) for target_id in antecedent_ids
        )
        if any(row is None for row in antecedent_nodes):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_EXACT_OWNER_UNRESOLVED"
            )
        antecedent_node_ids = tuple(
            str(row.get("node_id"))
            for row in antecedent_nodes
            if row is not None
        )
        antecedent_nucleus_ids = tuple(
            sorted(
                {
                    str(nucleus_id)
                    for target_id in antecedent_ids
                    for nucleus_id in obligations_by_id[target_id].get(
                        "nucleus_ids", []
                    )
                }
            )
        )
        if tuple(sorted(exact_target_nucleus_ids)) != antecedent_nucleus_ids:
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_EXACT_OWNER_MISMATCH"
            )
        support_ids: tuple[str, ...] = ()
        support_nucleus_ids: tuple[str, ...] = ()
        support_role = "none"
        action_lifecycle = "not_applicable"
        if opportunity is not None and opportunity.support_nucleus_ids:
            support_ids = exact_owner_ids(
                opportunity.support_nucleus_ids,
                reception_act=str(allowed_acts[0]),
            )
            if not support_ids:
                raise Step11SemanticOverlayError(
                    "STEP11_OVERLAY_RECEPTION_SUPPORT_OWNER_UNRESOLVED"
                )
            support_nucleus_ids = tuple(
                sorted(
                    {
                        str(nucleus_id)
                        for obligation_id in support_ids
                        for nucleus_id in obligations_by_id[obligation_id].get(
                            "nucleus_ids", []
                        )
                    }
                )
            )
            support_role = "source_opportunity_support"
        else:
            (
                support_ids,
                support_nucleus_ids,
                support_role,
                action_lifecycle,
            ) = corrected_action_support(antecedent_nucleus_ids)
        if action_lifecycle == "not_applicable":
            action_lifecycle = action_lifecycle_for(
                (*antecedent_nucleus_ids, *support_nucleus_ids)
            )
        support_nodes = tuple(
            nodes_by_obligation.get(obligation_id)
            for obligation_id in support_ids
        )
        if any(row is None for row in support_nodes):
            raise Step11SemanticOverlayError(
                "STEP11_OVERLAY_RECEPTION_SUPPORT_OWNER_UNRESOLVED"
            )
        support_node_ids = tuple(
            str(row.get("node_id"))
            for row in support_nodes
            if row is not None
        )
        material = {
            "reception_obligation_id": reception_id,
            "reception_node_id": str(reception_node.get("node_id")),
            "source_target_obligation_ids": list(source_target_ids),
            "source_target_node_ids": list(source_target_node_ids),
            "source_target_nucleus_ids": list(source_target_nucleus_ids),
            "antecedent_obligation_ids": list(antecedent_ids),
            "antecedent_node_ids": list(antecedent_node_ids),
            "antecedent_nucleus_ids": list(antecedent_nucleus_ids),
            "supporting_obligation_ids": list(support_ids),
            "supporting_node_ids": list(support_node_ids),
            "supporting_nucleus_ids": list(support_nucleus_ids),
            "support_role": support_role,
            "source_reception_opportunity_ids": list(
                source_opportunity_ids
            ),
            "action_lifecycle": action_lifecycle,
            "allowed_response_acts": list(allowed_acts),
            "evidence_grade": (
                "visible_typed_antecedent_exact_source_owner"
            ),
        }
        result.append(
            Step11ReceptionAntecedentBinding(
                binding_id="s11recv_" + artifact_sha256(material)[:16],
                reception_obligation_id=reception_id,
                reception_node_id=str(reception_node.get("node_id")),
                source_target_obligation_ids=source_target_ids,
                source_target_node_ids=source_target_node_ids,
                source_target_nucleus_ids=source_target_nucleus_ids,
                antecedent_obligation_ids=antecedent_ids,
                antecedent_node_ids=antecedent_node_ids,
                antecedent_nucleus_ids=antecedent_nucleus_ids,
                supporting_obligation_ids=support_ids,
                supporting_node_ids=support_node_ids,
                supporting_nucleus_ids=support_nucleus_ids,
                support_role=support_role,
                source_reception_opportunity_ids=(
                    source_opportunity_ids
                ),
                action_lifecycle=action_lifecycle,
                allowed_response_acts=allowed_acts,
                evidence_grade=(
                    "visible_typed_antecedent_exact_source_owner"
                ),
            )
        )
    return tuple(result)


def _anchor_material(value: Step11SourceAnchor) -> dict[str, Any]:
    return {
        "anchor_id": value.anchor_id,
        "source_slot": value.source_slot,
        "role": value.role,
        "start": value.start,
        "end": value.end,
        "text": value.text,
        "text_sha256": value.text_sha256,
    }


def _label_anchor_material(value: Step11ExactLabelAnchor) -> dict[str, Any]:
    return {
        "label_anchor_id": value.label_anchor_id,
        "source_slot": value.source_slot,
        "source_field": value.source_field,
        "source_ordinal": value.source_ordinal,
        "label": value.label,
        "strength": value.strength,
        "evidence_span_id": value.evidence_span_id,
        "label_sha256": value.label_sha256,
        "evidence_grade": value.evidence_grade,
    }


def _nucleus_anchor_binding_material(
    value: Step11NucleusAnchorBinding,
) -> dict[str, Any]:
    return {
        "nucleus_id": value.nucleus_id,
        "source_anchor_ids": list(value.source_anchor_ids),
        "source_label_anchor_ids": list(value.source_label_anchor_ids),
        "source_slots": list(value.source_slots),
        "source_role": value.source_role,
        "modality": value.modality,
        "temporal_scope": value.temporal_scope,
        "realization_status": value.realization_status,
        "evidence_grade": value.evidence_grade,
    }


def _relation_material(value: Step11OverlayRelation) -> dict[str, Any]:
    return {
        "source_relation_id": value.source_relation_id,
        "source_relation_ids": list(value.source_relation_ids),
        "source_relation_kind": value.source_relation_kind,
        "relation_type": value.relation_type,
        "relation_direction": value.relation_direction,
        "from_nucleus_id": value.from_nucleus_id,
        "to_nucleus_id": value.to_nucleus_id,
        "from_source_slots": list(value.from_source_slots),
        "to_source_slots": list(value.to_source_slots),
        "from_source_anchor_ids": list(value.from_source_anchor_ids),
        "to_source_anchor_ids": list(value.to_source_anchor_ids),
        "from_label_anchor_ids": list(value.from_label_anchor_ids),
        "to_label_anchor_ids": list(value.to_label_anchor_ids),
        "from_endpoint_role": value.from_endpoint_role,
        "to_endpoint_role": value.to_endpoint_role,
        "required": value.required,
        "explicit": value.explicit,
        "cross_field": value.cross_field,
        "source_order": list(value.source_order),
        "priority_rank": value.priority_rank,
        "evidence_grade": value.evidence_grade,
    }


def _typed_unknown_material(value: Step11TypedUnknown) -> dict[str, Any]:
    return {
        "unknown_id": value.unknown_id,
        **_unknown_material(
            unknown_type=value.unknown_type,
            source_slots=value.source_slots,
            source_anchor_ids=value.source_anchor_ids,
            target_nucleus_ids=value.target_nucleus_ids,
            source_unknown_ids=value.source_unknown_ids,
            source_rules=value.source_rules,
            epistemic_basis=value.epistemic_basis,
            decision_state=value.decision_state,
            context_nucleus_ids=value.context_nucleus_ids,
            context_anchor_ids=value.context_anchor_ids,
        ),
    }


def _suppressed_unknown_material(
    value: Step11SuppressedUnknown,
) -> dict[str, Any]:
    return {
        "source_unknown_id": value.source_unknown_id,
        "original_dimension_code": value.original_dimension_code,
        "source_slots": list(value.source_slots),
        "source_anchor_ids": list(value.source_anchor_ids),
        "target_nucleus_ids": list(value.target_nucleus_ids),
        "context_anchor_ids": list(value.context_anchor_ids),
        "suppression_reason": value.suppression_reason,
        "evidence_grade": value.evidence_grade,
    }


def _self_evaluation_material(
    value: Step11ReportedSelfEvaluation,
) -> dict[str, Any]:
    return {
        "self_evaluation_id": value.self_evaluation_id,
        "source_slot": value.source_slot,
        "source_anchor_id": value.source_anchor_id,
        "source_rule": value.source_rule,
        "identity_fact_denial_required": value.identity_fact_denial_required,
        "bounded_counterposition_required": (
            value.bounded_counterposition_required
        ),
        "source_counterposition_anchor_ids": list(
            value.source_counterposition_anchor_ids
        ),
        "evaluation_target": value.evaluation_target,
    }


def _mixed_emotion_material(
    value: Step11MixedEmotionRequirement,
) -> dict[str, Any]:
    return {
        "requirement_id": value.requirement_id,
        "positive_label_anchor_ids": list(value.positive_label_anchor_ids),
        "negative_label_anchor_ids": list(value.negative_label_anchor_ids),
        "relation_type": value.relation_type,
        "relation_direction": value.relation_direction,
        "required": value.required,
        "evidence_grade": value.evidence_grade,
    }


def _reception_binding_material(
    value: Step11ReceptionAntecedentBinding,
) -> dict[str, Any]:
    return {
        "binding_id": value.binding_id,
        "reception_obligation_id": value.reception_obligation_id,
        "reception_node_id": value.reception_node_id,
        "source_target_obligation_ids": list(
            value.source_target_obligation_ids
        ),
        "source_target_node_ids": list(value.source_target_node_ids),
        "source_target_nucleus_ids": list(
            value.source_target_nucleus_ids
        ),
        "antecedent_obligation_ids": list(value.antecedent_obligation_ids),
        "antecedent_node_ids": list(value.antecedent_node_ids),
        "antecedent_nucleus_ids": list(value.antecedent_nucleus_ids),
        "supporting_obligation_ids": list(
            value.supporting_obligation_ids
        ),
        "supporting_node_ids": list(
            value.supporting_node_ids
        ),
        "supporting_nucleus_ids": list(
            value.supporting_nucleus_ids
        ),
        "support_role": value.support_role,
        "source_reception_opportunity_ids": list(
            value.source_reception_opportunity_ids
        ),
        "action_lifecycle": value.action_lifecycle,
        "allowed_response_acts": list(value.allowed_response_acts),
        "evidence_grade": value.evidence_grade,
    }


def step11_semantic_overlay_material(
    value: Step11SemanticOverlay,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    """Return the canonical private material used for overlay identity."""

    if type(value) is not Step11SemanticOverlay:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_TYPE_INVALID")
    result = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "overlay_id": value.overlay_id,
        "source_obligation_ledger_sha256": (
            value.source_obligation_ledger_sha256
        ),
        "source_content_plan_sha256": value.source_content_plan_sha256,
        "source_discourse_plan_sha256": value.source_discourse_plan_sha256,
        "current_input_projection_sha256": (
            value.current_input_projection_sha256
        ),
        "overlay_policy_sha256": value.overlay_policy_sha256,
        "planning_frontier": step11_planning_frontier_material(
            value.planning_frontier
        ),
        "label_anchors": [
            _label_anchor_material(row) for row in value.label_anchors
        ],
        "anchors": [_anchor_material(row) for row in value.anchors],
        "nucleus_anchor_bindings": [
            _nucleus_anchor_binding_material(row)
            for row in value.nucleus_anchor_bindings
        ],
        "relations": [_relation_material(row) for row in value.relations],
        "unknowns": [_typed_unknown_material(row) for row in value.unknowns],
        "suppressed_unknowns": [
            _suppressed_unknown_material(row)
            for row in value.suppressed_unknowns
        ],
        "reported_self_evaluations": [
            _self_evaluation_material(row)
            for row in value.reported_self_evaluations
        ],
        "mixed_emotion_requirements": [
            _mixed_emotion_material(row)
            for row in value.mixed_emotion_requirements
        ],
        "reception_antecedent_bindings": [
            _reception_binding_material(row)
            for row in value.reception_antecedent_bindings
        ],
        "body_free": value.body_free,
    }
    if not include_id:
        result.pop("overlay_id")
    return result


def _build_overlay(
    current_input: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
) -> Step11SemanticOverlay:
    projection = _input_projection(current_input)
    label_anchors = _exact_label_anchors(current_input, projection)
    (
        ledger,
        by_id,
        active_ids,
        active_nucleus_ids,
        planning_frontier,
    ) = _trusted_parents(
        inventory_result, content_plan, discourse_plan
    )
    nucleus_by_id = {
        row.source_id: row for row in inventory_result.source_snapshot.nuclei
    }
    # rc0022 has one authoritative frontier: only obligations selected by the
    # validated Content Plan (including required mixed-emotion rows now owned
    # by Step 4/5) may reach the surface.  Retention metadata is not a second,
    # renderer-local selection channel.
    display_nucleus_ids = active_nucleus_ids
    selected_relation_ids = frozenset(
        relation_id
        for obligation_id in active_ids
        for relation_id in by_id[obligation_id].get("relation_ids", [])
    )
    display_relation_ids = selected_relation_ids
    selected_unknown_ids = frozenset(
        unknown_id
        for obligation_id in active_ids
        for unknown_id in by_id[obligation_id].get(
            "unknown_boundary_ids", []
        )
    )
    active_slots = frozenset(
        slot
        for nucleus_id in display_nucleus_ids
        for slot in _slots_for_nucleus(nucleus_by_id[nucleus_id])
    )
    anchors = _base_anchors(projection)
    (
        nucleus_anchor_bindings,
        anchor_ids_by_nucleus,
        label_anchor_ids_by_nucleus,
    ) = (
        _nucleus_anchor_bindings(
            current_input,
            projection,
            anchors,
            label_anchors,
            inventory_result=inventory_result,
            active_nucleus_ids=display_nucleus_ids,
        )
    )
    self_evaluations = _reported_self_evaluations(
        projection,
        anchors,
        obligations_by_id=by_id,
        active_obligation_ids=active_ids,
        anchor_ids_by_nucleus=anchor_ids_by_nucleus,
    )
    mixed_label_anchor_ids = {
        anchor_id
        for nucleus_id in planning_frontier.mixed_emotion_nucleus_ids
        for anchor_id in label_anchor_ids_by_nucleus.get(nucleus_id, ())
    }
    mixed_emotion_requirements = _mixed_emotion_requirements(
        tuple(
            row
            for row in label_anchors
            if row.label_anchor_id in mixed_label_anchor_ids
        )
    )
    reception_antecedent_bindings = _reception_antecedent_bindings(
        obligations_by_id=by_id,
        active_obligation_ids=active_ids,
        discourse_plan=discourse_plan,
        source_snapshot=inventory_result.source_snapshot,
        projection=projection,
    )
    relations = _overlay_relations(
        inventory_result,
        display_nucleus_ids,
        projection=projection,
        active_relation_ids=display_relation_ids,
        selected_relation_ids=selected_relation_ids,
        content_depth=str(content_plan.get("depth")),
        anchor_ids_by_nucleus=anchor_ids_by_nucleus,
        label_anchor_ids_by_nucleus=label_anchor_ids_by_nucleus,
        anchor_by_id={row.anchor_id: row for row in anchors},
    )
    # Grammar anchors are discovered first so frozen required dimensions can
    # bind to their exact visible scope instead of falling back to an arbitrary
    # first nucleus in the same app field.
    unknowns = _grammar_unknowns(
        projection,
        anchors,
        active_slots=active_slots,
        anchor_ids_by_nucleus=anchor_ids_by_nucleus,
        relations=relations,
    )
    unknowns.extend(
        _source_unknowns(
            inventory_result,
            anchors,
            active_nucleus_ids=display_nucleus_ids,
            projection=projection,
            relations=relations,
            anchor_ids_by_nucleus=anchor_ids_by_nucleus,
        )
    )
    unknowns = [
        row
        for row in _canonical_unknowns(unknowns, anchors)
        if set(row.source_unknown_ids) & selected_unknown_ids
    ]
    suppressed_unknowns = tuple(
        row
        for row in _suppressed_source_unknowns(
            inventory_result,
            anchors,
            active_nucleus_ids=display_nucleus_ids,
            projection=projection,
            anchor_ids_by_nucleus=anchor_ids_by_nucleus,
        )
        if row.source_unknown_id in selected_unknown_ids
    )
    _require_complete_source_unknown_coverage(
        inventory_result,
        active_nucleus_ids=display_nucleus_ids,
        unknowns=unknowns,
        suppressed_unknowns=suppressed_unknowns,
    )
    anchors.sort(
        key=lambda row: (
            _SLOT_ORDER[row.source_slot],
            row.start,
            row.end,
            row.role,
            row.anchor_id,
        )
    )
    overlay = Step11SemanticOverlay(
        schema_version=STEP11_SEMANTIC_OVERLAY_SCHEMA,
        candidate_version_id=STEP11_SEMANTIC_OVERLAY_VERSION,
        overlay_id="nls3s11sem_00000000000000000000",
        source_obligation_ledger_sha256=artifact_sha256(ledger),
        source_content_plan_sha256=artifact_sha256(content_plan),
        source_discourse_plan_sha256=artifact_sha256(discourse_plan),
        current_input_projection_sha256=artifact_sha256(projection),
        overlay_policy_sha256=STEP11_SEMANTIC_OVERLAY_POLICY_SHA256,
        planning_frontier=planning_frontier,
        label_anchors=label_anchors,
        anchors=tuple(anchors),
        nucleus_anchor_bindings=nucleus_anchor_bindings,
        relations=relations,
        unknowns=tuple(unknowns),
        suppressed_unknowns=suppressed_unknowns,
        reported_self_evaluations=self_evaluations,
        mixed_emotion_requirements=mixed_emotion_requirements,
        reception_antecedent_bindings=reception_antecedent_bindings,
        body_free=False,
    )
    overlay_id = "nls3s11sem_" + artifact_sha256(
        step11_semantic_overlay_material(overlay, include_id=False)
    )[:20]
    return Step11SemanticOverlay(
        schema_version=overlay.schema_version,
        candidate_version_id=overlay.candidate_version_id,
        overlay_id=overlay_id,
        source_obligation_ledger_sha256=(
            overlay.source_obligation_ledger_sha256
        ),
        source_content_plan_sha256=overlay.source_content_plan_sha256,
        source_discourse_plan_sha256=overlay.source_discourse_plan_sha256,
        current_input_projection_sha256=(
            overlay.current_input_projection_sha256
        ),
        overlay_policy_sha256=overlay.overlay_policy_sha256,
        planning_frontier=overlay.planning_frontier,
        label_anchors=overlay.label_anchors,
        anchors=overlay.anchors,
        nucleus_anchor_bindings=overlay.nucleus_anchor_bindings,
        relations=overlay.relations,
        unknowns=overlay.unknowns,
        suppressed_unknowns=overlay.suppressed_unknowns,
        reported_self_evaluations=overlay.reported_self_evaluations,
        mixed_emotion_requirements=overlay.mixed_emotion_requirements,
        reception_antecedent_bindings=(
            overlay.reception_antecedent_bindings
        ),
        body_free=False,
    )


def build_step11_semantic_overlay(
    current_input: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
) -> Step11SemanticOverlay:
    """Build the exact rc0023 overlay from app input and Step 4--6 parents."""

    result = _build_overlay(
        current_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
    )
    issues = validate_step11_semantic_overlay(
        result,
        current_input=current_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
    )
    if issues:
        raise Step11SemanticOverlayError(issues[0])
    return result


def validate_step11_semantic_overlay(
    value: Any,
    *,
    current_input: Mapping[str, Any],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    discourse_plan: Mapping[str, Any],
) -> tuple[str, ...]:
    """Recompute the complete private overlay; caller declarations are ignored."""

    if type(value) is not Step11SemanticOverlay:
        return ("STEP11_OVERLAY_TYPE_INVALID",)
    issues: set[str] = set()
    if value.schema_version != STEP11_SEMANTIC_OVERLAY_SCHEMA:
        issues.add("STEP11_OVERLAY_SCHEMA_INVALID")
    if value.candidate_version_id != STEP11_SEMANTIC_OVERLAY_VERSION:
        issues.add("STEP11_OVERLAY_VERSION_INVALID")
    if _OVERLAY_ID_RE.fullmatch(value.overlay_id) is None:
        issues.add("STEP11_OVERLAY_ID_INVALID")
    if value.overlay_policy_sha256 != STEP11_SEMANTIC_OVERLAY_POLICY_SHA256:
        issues.add("STEP11_OVERLAY_POLICY_MISMATCH")
    if type(value.planning_frontier) is not Step11PlanningFrontier:
        issues.add("STEP11_OVERLAY_PLANNING_FRONTIER_INVALID")
    if value.body_free is not False:
        issues.add("STEP11_OVERLAY_PRIVATE_BODY_DECLARATION_INVALID")
    if type(value.label_anchors) is not tuple:
        issues.add("STEP11_OVERLAY_LABEL_ANCHORS_INVALID")
        label_anchor_rows: tuple[Any, ...] = ()
    else:
        label_anchor_rows = value.label_anchors
        label_anchor_ids: list[str] = []
        label_positions: list[tuple[str, int]] = []
        for row in label_anchor_rows:
            if type(row) is Step11ExactLabelAnchor:
                label_anchor_ids.append(row.label_anchor_id)
                label_positions.append((row.source_slot, row.source_ordinal))
            if (
                type(row) is not Step11ExactLabelAnchor
                or _LABEL_ANCHOR_ID_RE.fullmatch(row.label_anchor_id) is None
                or (row.source_slot, row.source_field)
                not in {
                    ("emotion", "emotion_details"),
                    ("category", "category"),
                }
                or type(row.source_ordinal) is not int
                or row.source_ordinal < 0
                or type(row.label) is not str
                or not row.label
                or (
                    row.source_slot == "emotion"
                    and (type(row.strength) is not str or not row.strength)
                )
                or (row.source_slot == "category" and row.strength is not None)
                or _EVIDENCE_ID_RE.fullmatch(row.evidence_span_id) is None
                or _SHA_RE.fullmatch(row.label_sha256) is None
                or hashlib.sha256(row.label.encode("utf-8")).hexdigest()
                != row.label_sha256
                or row.evidence_grade != "exact_structured_evidence_label"
            ):
                issues.add("STEP11_OVERLAY_LABEL_ANCHOR_INVALID")
        if (
            len(label_anchor_ids) != len(set(label_anchor_ids))
            or len(label_positions) != len(set(label_positions))
        ):
            issues.add("STEP11_OVERLAY_LABEL_ANCHOR_IDENTITY_INVALID")
    exact_label_anchor_ids = {
        row.label_anchor_id
        for row in label_anchor_rows
        if type(row) is Step11ExactLabelAnchor
    }
    if type(value.anchors) is not tuple:
        issues.add("STEP11_OVERLAY_ANCHORS_INVALID")
        anchor_rows: tuple[Any, ...] = ()
    else:
        anchor_rows = value.anchors
        for row in anchor_rows:
            if (
                type(row) is not Step11SourceAnchor
                or _ANCHOR_ID_RE.fullmatch(row.anchor_id) is None
                or row.source_slot not in {"thought", "action"}
                or row.role not in _ANCHOR_ROLES
                or not _SHA_RE.fullmatch(row.text_sha256)
                or hashlib.sha256(row.text.encode("utf-8")).hexdigest()
                != row.text_sha256
            ):
                issues.add("STEP11_OVERLAY_ANCHOR_INVALID")
    anchor_ids = {
        row.anchor_id
        for row in anchor_rows
        if type(row) is Step11SourceAnchor
    }
    if type(value.nucleus_anchor_bindings) is not tuple:
        issues.add("STEP11_OVERLAY_NUCLEUS_BINDINGS_INVALID")
    else:
        binding_ids = [
            row.nucleus_id
            for row in value.nucleus_anchor_bindings
            if type(row) is Step11NucleusAnchorBinding
        ]
        if (
            len(binding_ids) != len(value.nucleus_anchor_bindings)
            or len(binding_ids) != len(set(binding_ids))
            or any(
                type(row.source_anchor_ids) is not tuple
                or not set(row.source_anchor_ids) <= anchor_ids
                or type(row.source_label_anchor_ids) is not tuple
                or not set(row.source_label_anchor_ids)
                <= exact_label_anchor_ids
                or not (
                    row.source_anchor_ids or row.source_label_anchor_ids
                )
                or row.source_role not in {"thought", "action", "label"}
                or row.realization_status
                not in {
                    "reported_content",
                    "reported_completed",
                    "reported_ongoing",
                    "reported_not_completed",
                    "intended",
                    "undetermined",
                }
                or row.evidence_grade
                not in {
                    "exact_source_span",
                    "exact_structured_evidence_label",
                }
                for row in value.nucleus_anchor_bindings
                if type(row) is Step11NucleusAnchorBinding
            )
        ):
            issues.add("STEP11_OVERLAY_NUCLEUS_BINDING_INVALID")
    if type(value.relations) is not tuple:
        issues.add("STEP11_OVERLAY_RELATIONS_INVALID")
    else:
        for rank, row in enumerate(value.relations):
            if (
                type(row) is not Step11OverlayRelation
                or not row.source_relation_ids
                or row.source_relation_id not in row.source_relation_ids
                or len(row.source_relation_ids)
                != len(set(row.source_relation_ids))
                or row.relation_type not in _RELATION_TYPES
                or row.relation_direction not in _RELATION_DIRECTIONS
                or row.from_endpoint_role not in _RELATION_ENDPOINT_ROLES
                or row.to_endpoint_role not in _RELATION_ENDPOINT_ROLES
                or row.priority_rank != rank
                or type(row.from_source_anchor_ids) is not tuple
                or type(row.to_source_anchor_ids) is not tuple
                or type(row.from_label_anchor_ids) is not tuple
                or type(row.to_label_anchor_ids) is not tuple
                or not set(row.from_source_anchor_ids) <= anchor_ids
                or not set(row.to_source_anchor_ids) <= anchor_ids
                or not set(row.from_label_anchor_ids)
                <= exact_label_anchor_ids
                or not set(row.to_label_anchor_ids)
                <= exact_label_anchor_ids
                or not (
                    row.from_source_anchor_ids or row.from_label_anchor_ids
                )
                or not (
                    row.to_source_anchor_ids or row.to_label_anchor_ids
                )
                or row.evidence_grade
                not in {
                    "exact_same_field_relation",
                    "exact_cross_field_source_relation",
                    "cross_field_copresence_only",
                    "cross_field_same_event_restatement",
                    "source_order_copresence_only",
                }
            ):
                issues.add("STEP11_OVERLAY_RELATION_INVALID")
    if type(value.unknowns) is not tuple:
        issues.add("STEP11_OVERLAY_UNKNOWNS_INVALID")
    else:
        for row in value.unknowns:
            if (
                type(row) is not Step11TypedUnknown
                or _UNKNOWN_ID_RE.fullmatch(row.unknown_id) is None
                or row.unknown_type not in _UNKNOWN_TYPES
                or row.epistemic_basis
                not in {
                    "frozen_required",
                    "explicit_unknown",
                    "bounded_inference",
                }
                or row.surface_policy != "preserve_open"
                or row.decision_state not in _DECISION_STATES
                or row.decision_state
                not in _GRAMMAR_CATALOG["unknown_policy"][
                    "dimension_matrix"
                ].get(row.unknown_type, ())
                or type(row.context_nucleus_ids) is not tuple
                or type(row.context_anchor_ids) is not tuple
                or type(row.source_anchor_ids) is not tuple
                or not set(row.source_anchor_ids) <= anchor_ids
                or not set(row.context_anchor_ids) <= anchor_ids
                or (
                    row.unknown_type
                    in {"decision_state", "post_decision_comparative_merit"}
                    and (
                        not row.context_nucleus_ids
                        or not row.context_anchor_ids
                    )
                )
                or (
                    row.unknown_type
                    not in {"decision_state", "post_decision_comparative_merit"}
                    and (row.context_nucleus_ids or row.context_anchor_ids)
                )
            ):
                issues.add("STEP11_OVERLAY_UNKNOWN_INVALID")
    if type(value.suppressed_unknowns) is not tuple:
        issues.add("STEP11_OVERLAY_SUPPRESSED_UNKNOWNS_INVALID")
    else:
        snapshot_unknown_by_id = {
            row.source_id: row
            for row in inventory_result.source_snapshot.unknowns
        }
        snapshot_nucleus_by_id = {
            row.source_id: row
            for row in inventory_result.source_snapshot.nuclei
        }
        binding_by_nucleus = {
            row.nucleus_id: row
            for row in value.nucleus_anchor_bindings
            if type(row) is Step11NucleusAnchorBinding
        }
        anchor_by_id_for_suppression = {
            row.anchor_id: row
            for row in value.anchors
            if type(row) is Step11SourceAnchor
        }
        visible_source_unknown_ids = {
            source_id
            for row in value.unknowns
            if type(row) is Step11TypedUnknown
            for source_id in row.source_unknown_ids
        }
        suppression_source_ids = [
            row.source_unknown_id
            for row in value.suppressed_unknowns
            if type(row) is Step11SuppressedUnknown
        ]
        if (
            len(suppression_source_ids) != len(value.suppressed_unknowns)
            or len(suppression_source_ids) != len(set(suppression_source_ids))
        ):
            issues.add("STEP11_OVERLAY_SUPPRESSED_UNKNOWN_IDENTITY_INVALID")
        for row in value.suppressed_unknowns:
            source = (
                snapshot_unknown_by_id.get(row.source_unknown_id)
                if type(row) is Step11SuppressedUnknown
                else None
            )
            target_ids = (
                set(row.target_nucleus_ids)
                if type(row) is Step11SuppressedUnknown
                else set()
            )
            expected_target_ids = (
                set(source.affected_nucleus_ids) & set(binding_by_nucleus)
                if source is not None
                else set()
            )
            target_anchor_ids = {
                anchor_id
                for nucleus_id in target_ids
                if nucleus_id in binding_by_nucleus
                for anchor_id in binding_by_nucleus[
                    nucleus_id
                ].source_anchor_ids
            }
            expected_slots = {
                slot
                for nucleus_id in target_ids
                if nucleus_id in snapshot_nucleus_by_id
                for slot in _slots_for_nucleus(
                    snapshot_nucleus_by_id[nucleus_id]
                )
            }
            source_anchors = tuple(
                anchor_by_id_for_suppression.get(anchor_id)
                for anchor_id in getattr(row, "source_anchor_ids", ())
            )
            context_anchors = tuple(
                anchor_by_id_for_suppression.get(anchor_id)
                for anchor_id in getattr(row, "context_anchor_ids", ())
            )
            exact_context = False
            if all(anchor is not None for anchor in source_anchors):
                for context_anchor in context_anchors:
                    if context_anchor is None:
                        continue
                    if context_anchor.anchor_id not in row.source_anchor_ids:
                        if (
                            _CONTEXTUAL_PRECEDING_EVENT_RE.search(
                                context_anchor.text
                            )
                            is not None
                        ):
                            exact_context = True
                        continue
                    marker = _RELATIVE_TEMPORAL_DEICTIC_RE.search(
                        context_anchor.text
                    )
                    if (
                        marker is not None
                        and _CONTEXTUAL_PRECEDING_EVENT_RE.search(
                            context_anchor.text[: marker.start()]
                        )
                        is not None
                    ):
                        exact_context = True
            if (
                type(row) is not Step11SuppressedUnknown
                or source is None
                or source.required is not True
                or str(source.source_role) != "original_input"
                or str(source.surface_policy) != "do_not_claim"
                or row.original_dimension_code
                != str(source.dimension_code)
                or "TEMPORAL_REFERENT"
                not in row.original_dimension_code.upper()
                or row.source_unknown_id in visible_source_unknown_ids
                or type(row.source_slots) is not tuple
                or set(row.source_slots) != expected_slots
                or type(row.source_anchor_ids) is not tuple
                or not row.source_anchor_ids
                or not set(row.source_anchor_ids) <= target_anchor_ids
                or any(
                    anchor is None
                    or _RELATIVE_TEMPORAL_DEICTIC_RE.search(anchor.text)
                    is None
                    for anchor in source_anchors
                )
                or type(row.target_nucleus_ids) is not tuple
                or not target_ids
                or target_ids != expected_target_ids
                or type(row.context_anchor_ids) is not tuple
                or not row.context_anchor_ids
                or not set(row.context_anchor_ids) <= anchor_ids
                or not exact_context
                or row.suppression_reason
                != _TEMPORAL_SUPPRESSION_REASON
                or row.evidence_grade
                != _TEMPORAL_SUPPRESSION_GRADE
            ):
                issues.add("STEP11_OVERLAY_SUPPRESSED_UNKNOWN_INVALID")
    if type(value.mixed_emotion_requirements) is not tuple:
        issues.add("STEP11_OVERLAY_MIXED_EMOTION_REQUIREMENTS_INVALID")
    else:
        label_by_id = {
            row.label_anchor_id: row
            for row in label_anchor_rows
            if type(row) is Step11ExactLabelAnchor
        }
        if len(value.mixed_emotion_requirements) > 1:
            issues.add("STEP11_OVERLAY_MIXED_EMOTION_REQUIREMENTS_INVALID")
        for row in value.mixed_emotion_requirements:
            positive_ids = (
                set(row.positive_label_anchor_ids)
                if type(row) is Step11MixedEmotionRequirement
                else set()
            )
            negative_ids = (
                set(row.negative_label_anchor_ids)
                if type(row) is Step11MixedEmotionRequirement
                else set()
            )
            if (
                type(row) is not Step11MixedEmotionRequirement
                or _MIXED_EMOTION_ID_RE.fullmatch(row.requirement_id) is None
                or type(row.positive_label_anchor_ids) is not tuple
                or type(row.negative_label_anchor_ids) is not tuple
                or not positive_ids
                or not negative_ids
                or bool(positive_ids & negative_ids)
                or not (positive_ids | negative_ids)
                <= exact_label_anchor_ids
                or any(
                    label_by_id[label_id].label
                    not in _EMOTION_VALENCE["positive"]
                    for label_id in positive_ids
                )
                or any(
                    label_by_id[label_id].label
                    not in _EMOTION_VALENCE["negative"]
                    for label_id in negative_ids
                )
                or row.relation_type != "coexists_with"
                or row.relation_direction != "bidirectional"
                or row.required is not True
                or row.evidence_grade != "exact_current_input_mixed_valence"
            ):
                issues.add("STEP11_OVERLAY_MIXED_EMOTION_REQUIREMENT_INVALID")
    if type(value.reception_antecedent_bindings) is not tuple:
        issues.add("STEP11_OVERLAY_RECEPTION_BINDINGS_INVALID")
    else:
        binding_ids: list[str] = []
        reception_ids: list[str] = []
        for row in value.reception_antecedent_bindings:
            if type(row) is Step11ReceptionAntecedentBinding:
                binding_ids.append(row.binding_id)
                reception_ids.append(row.reception_obligation_id)
            if (
                type(row) is not Step11ReceptionAntecedentBinding
                or _RECEPTION_BINDING_ID_RE.fullmatch(row.binding_id) is None
                or not row.reception_obligation_id
                or not row.reception_node_id
                or type(row.source_target_obligation_ids) is not tuple
                or not row.source_target_obligation_ids
                or len(row.source_target_obligation_ids)
                != len(set(row.source_target_obligation_ids))
                or type(row.source_target_node_ids) is not tuple
                or not row.source_target_node_ids
                or len(row.source_target_node_ids)
                != len(set(row.source_target_node_ids))
                or type(row.source_target_nucleus_ids) is not tuple
                or not row.source_target_nucleus_ids
                or type(row.antecedent_obligation_ids) is not tuple
                or not row.antecedent_obligation_ids
                or len(row.antecedent_obligation_ids)
                != len(set(row.antecedent_obligation_ids))
                or type(row.antecedent_node_ids) is not tuple
                or not row.antecedent_node_ids
                or len(row.antecedent_node_ids)
                != len(set(row.antecedent_node_ids))
                or type(row.antecedent_nucleus_ids) is not tuple
                or not row.antecedent_nucleus_ids
                or type(row.supporting_obligation_ids) is not tuple
                or len(row.supporting_obligation_ids)
                != len(set(row.supporting_obligation_ids))
                or type(row.supporting_node_ids) is not tuple
                or len(row.supporting_node_ids)
                != len(set(row.supporting_node_ids))
                or type(row.supporting_nucleus_ids) is not tuple
                or bool(row.supporting_obligation_ids)
                != bool(row.supporting_node_ids)
                or bool(row.supporting_obligation_ids)
                != bool(row.supporting_nucleus_ids)
                or row.support_role
                not in {
                    "none",
                    "source_opportunity_support",
                    "source_progressive_concrete_action",
                    "legacy_purpose_negation_scope_corrected_action",
                }
                or (row.support_role == "none")
                != (not row.supporting_obligation_ids)
                or type(row.source_reception_opportunity_ids) is not tuple
                or len(row.source_reception_opportunity_ids)
                != len(set(row.source_reception_opportunity_ids))
                or len(row.source_reception_opportunity_ids) > 1
                or row.action_lifecycle
                not in {
                    "not_applicable",
                    "undetermined",
                    "intended",
                    "reported_ongoing",
                    "reported_not_completed",
                    "reported_completed",
                }
                or type(row.allowed_response_acts) is not tuple
                or not row.allowed_response_acts
                or row.evidence_grade
                != "visible_typed_antecedent_exact_source_owner"
                or row.binding_id
                != "s11recv_"
                + artifact_sha256(
                    {
                        key: value
                        for key, value in _reception_binding_material(row).items()
                        if key != "binding_id"
                    }
                )[:16]
            ):
                issues.add("STEP11_OVERLAY_RECEPTION_BINDING_INVALID")
        if (
            len(binding_ids) != len(set(binding_ids))
            or len(reception_ids) != len(set(reception_ids))
        ):
            issues.add("STEP11_OVERLAY_RECEPTION_BINDING_IDENTITY_INVALID")
    if type(value.reported_self_evaluations) is not tuple:
        issues.add("STEP11_OVERLAY_SELF_EVALUATIONS_INVALID")
    else:
        anchor_by_id = {
            row.anchor_id: row
            for row in value.anchors
            if type(row) is Step11SourceAnchor
        }
        for row in value.reported_self_evaluations:
            source_anchor = (
                anchor_by_id.get(row.source_anchor_id)
                if type(row) is Step11ReportedSelfEvaluation
                else None
            )
            if (
                type(row) is not Step11ReportedSelfEvaluation
                or _SELF_EVAL_ID_RE.fullmatch(row.self_evaluation_id) is None
                or row.source_slot not in {"thought", "action"}
                or row.identity_fact_denial_required is not True
                or row.bounded_counterposition_required is not True
                or row.evaluation_target != "speaker_identity_or_trait"
                or source_anchor is None
                or source_anchor.source_slot != row.source_slot
                or source_anchor.role != "self_evaluation"
                or row.source_rule != _SELF_DENIAL_AUTHORITY_RULE
                or row.source_counterposition_anchor_ids != ()
                or not set(row.source_counterposition_anchor_ids) <= anchor_ids
            ):
                issues.add("STEP11_OVERLAY_SELF_EVALUATION_INVALID")
        try:
            (
                _authority_ledger,
                authority_by_id,
                authority_active_ids,
                _authority_nucleus_ids,
                _authority_planning_frontier,
            ) = _trusted_parents(
                inventory_result, content_plan, discourse_plan
            )
            authority_pairs = _required_self_denial_pairs(
                authority_by_id, authority_active_ids
            )
        except Step11SemanticOverlayError:
            issues.add("STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID")
            authority_pairs = ()
        binding_by_nucleus = {
            row.nucleus_id: row
            for row in value.nucleus_anchor_bindings
            if type(row) is Step11NucleusAnchorBinding
        }
        expected_authority_signatures: list[
            tuple[str, int, int, str]
        ] = []
        for self_row, _counter_row in authority_pairs:
            for nucleus_id in tuple(self_row.get("nucleus_ids", [])):
                binding = binding_by_nucleus.get(str(nucleus_id))
                nucleus_anchor = (
                    anchor_by_id.get(binding.source_anchor_ids[0])
                    if binding is not None
                    and len(binding.source_anchor_ids) == 1
                    else None
                )
                if nucleus_anchor is None or nucleus_anchor.role != "nucleus":
                    issues.add(
                        "STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_INVALID"
                    )
                    continue
                expected_authority_signatures.append(
                    (
                        nucleus_anchor.source_slot,
                        nucleus_anchor.start,
                        nucleus_anchor.end,
                        nucleus_anchor.text_sha256,
                    )
                )
        actual_authority_signatures = [
            (
                row.source_slot,
                anchor_by_id[row.source_anchor_id].start,
                anchor_by_id[row.source_anchor_id].end,
                anchor_by_id[row.source_anchor_id].text_sha256,
            )
            for row in value.reported_self_evaluations
            if type(row) is Step11ReportedSelfEvaluation
            and row.source_anchor_id in anchor_by_id
        ]
        if sorted(actual_authority_signatures) != sorted(
            expected_authority_signatures
        ):
            issues.add("STEP11_OVERLAY_SELF_DENIAL_AUTHORITY_MISMATCH")
    try:
        expected = _build_overlay(
            current_input,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
        )
    except Step11SemanticOverlayError:
        issues.add("STEP11_OVERLAY_PARENT_RECOMPUTATION_FAILED")
    else:
        if value != expected:
            issues.add("STEP11_OVERLAY_RECOMPUTATION_MISMATCH")
    return tuple(sorted(issues))


def primary_overlay_relation(
    value: Step11SemanticOverlay,
) -> Step11OverlayRelation | None:
    """Return the semantically ranked primary active-endpoint relation."""

    if type(value) is not Step11SemanticOverlay:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_TYPE_INVALID")
    return value.relations[0] if value.relations else None


def overlay_anchor_by_id(
    value: Step11SemanticOverlay,
    anchor_id: str,
) -> Step11SourceAnchor:
    """Resolve a source-bearing anchor without exposing a mutable index."""

    if type(value) is not Step11SemanticOverlay:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_TYPE_INVALID")
    result = next(
        (row for row in value.anchors if row.anchor_id == anchor_id), None
    )
    if result is None:
        raise Step11SemanticOverlayError("STEP11_OVERLAY_ANCHOR_UNRESOLVED")
    return result


__all__ = [
    "STEP11_SEMANTIC_OVERLAY_POLICY_SHA256",
    "STEP11_SEMANTIC_OVERLAY_SCHEMA",
    "STEP11_SEMANTIC_OVERLAY_VERSION",
    "Step11OverlayRelation",
    "Step11ExactLabelAnchor",
    "Step11MixedEmotionRequirement",
    "Step11NucleusAnchorBinding",
    "Step11ReceptionAntecedentBinding",
    "Step11ReportedSelfEvaluation",
    "Step11SemanticOverlay",
    "Step11SemanticOverlayError",
    "Step11SourceAnchor",
    "Step11SuppressedUnknown",
    "Step11TypedUnknown",
    "build_step11_semantic_overlay",
    "overlay_anchor_by_id",
    "primary_overlay_relation",
    "step11_semantic_overlay_material",
    "validate_step11_semantic_overlay",
]
