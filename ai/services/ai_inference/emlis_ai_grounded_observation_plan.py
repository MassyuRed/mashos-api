# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical GroundedObservationPlan contract (I1-I5).

The I1 adapter keeps the existing current-input Evidence Ledger authoritative.
I2 adds structure-first clause semantics and retention without depending on
fixture vocabulary. I3/I4 build SentencePlan/Surface from this plan, and I5
connects that same contract once from ``emlis_ai_reply_service``.
Grounded human reception RR2/RR3 adds a nested body-free opportunity/depth/move
contract while leaving SentencePlan, Surface, Gate, and the public response
shape unchanged.

Every source reference is an existing request-local ``sN`` id. No synthetic or
replacement Evidence id is created here.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Final, Literal

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    EvidenceLedgerResolutionError,
    EvidenceLedgerValidationReport,
    EvidenceSpanResolver,
    build_evidence_ledger,
    build_evidence_span_resolver,
    validate_evidence_ledger,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    EmlisSafetyTriageDecision,
    build_emlis_safety_triage_decision,
    is_bounded_self_denial_text,
)
from emlis_ai_types import (
    EvidenceRef,
    EvidenceSpan,
    InputMeaningBlock,
    MajorMeaningRetentionPlan,
    MeaningCoveragePlan,
    ObservationGraph,
    PerspectiveBoard,
    PerspectiveReport,
    RelationEdge,
    WholeInputMeaningArc,
)

GROUND_OBSERVATION_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_observation_plan.v1"
GROUND_OBSERVATION_PLAN_ADAPTER_VERSION: Final = "cocolon.emlis.grounded_observation_plan_adapter.i1.v1"
GROUND_OBSERVATION_PLAN_GENERATION_PATH: Final = "grounded_observation_plan_canonical_v1"
GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION: Final = "cocolon.emlis.grounded_semantics.i2.v3"
GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_human_reception_plan.v2"
FINAL_STAGE1_GROUNDED_PROJECTION_VERSION: Final = (
    "cocolon.emlis.final_stage1_grounded_projection.v1"
)

EvidenceId = str
NucleusId = str
RelationId = str
NucleusKind = Literal[
    "event",
    "state",
    "reaction",
    "wish",
    "constraint",
    "action",
    "change",
    "self_evaluation",
    "value",
    "uncertainty",
    "conclusion",
    "other_explicit",
]
RelationKind = Literal[
    "temporal_before_after",
    "shift_from_to",
    "contrast",
    "coexistence",
    "user_stated_cause",
    "user_stated_result",
    "attempt_and_block",
    "wish_and_constraint",
    "action_supports_change",
    "evaluation_about_event",
    "self_evaluation_about_state",
    "preserves_despite",
    "uncertain_connection",
    "continuation_or_refusal",
]
Retention = Literal["required", "should", "optional"]
GroundingKind = Literal["explicit", "user_stated_relation", "bounded_structural_inference"]
UnknownSurfacePolicy = Literal["do_not_claim", "hedge_only", "omit"]
GroundedHumanFollowRole = Literal[
    "integrated_current_state",
    "help_seeking_preserved",
    "protective_counterdirection",
    "retained_intention",
    "concrete_effort",
    "valued_change",
    "burden_expression",
]
GroundedHumanFollowDelivery = Literal[
    "separate_distinct_contribution",
    "not_required",
]
GroundedReceptionAct = Literal[
    "stay_with_current_burden",
    "honor_concrete_effort",
    "protect_retained_intention",
    "recognize_lived_change",
    "hold_help_seeking",
    "bounded_counter_self_denial",
    "respect_words_placed",
]
GroundedFollowElement = Literal[
    "intent_affirmation",
    "burden_understanding",
    "effort_receiving",
    "existence_respect",
]
GroundedReceptionStance = Literal[
    "quiet_presence",
    "warm_recognition",
    "gentle_respect",
    "protective_presence",
    "bounded_disagreement",
]
GroundedSpeakerPresence = Literal[
    "implicit_emlis",
    "explicit_emlis",
]
GroundedReferenceMode = Literal[
    "anaphoric_first",
    "short_anchor_if_ambiguous",
    "explicit_emlis_counterposition",
]
GroundedReceptionOpportunityFamily = Literal[
    "current_burden",
    "concrete_effort",
    "retained_intention",
    "lived_change",
    "help_seeking",
    "counterdirection",
    "words_placed",
]
GroundedReceptionDepthLevel = Literal[
    "minimal",
    "focused",
    "layered",
]
GroundedReceptionSafetyMode = Literal[
    "standard",
    "self_denial_bounded",
    "help_seeking_bounded",
]
GroundedReceptionMoveRole = Literal[
    "attention",
    "significance",
    "felt_response",
    "bounded_counterposition",
]
GroundedReceptionSurfaceStrategy = Literal[
    "quiet_referent_first",
    "emlis_attention_first",
    "referent_significance_first",
    "felt_response_first",
    "explicit_emlis_counterposition",
]

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_LABEL_SOURCE_FIELDS: Final = frozenset({"emotion_details", "emotions", "category"})
_EVIDENCE_ID_RE: Final = re.compile(r"^s[1-9][0-9]*$")
_BODY_FREE_CODE_RE: Final = re.compile(r"^[A-Za-z0-9_.:-]+$")
_PUNCT_SPACE_RE: Final = re.compile(r"[\s\u3000、,。．.!！?？「」『』（）()]+")
_PURE_RELATION_MARKERS: Final = frozenset(
    {"でも", "だけど", "けど", "ただ", "とはいえ", "その中で", "一方", "同時に", "なのに", "からこそ", "だからこそ"}
)
_ALLOWED_RELATION_KINDS: Final = frozenset(
    {
        "temporal_before_after",
        "shift_from_to",
        "contrast",
        "coexistence",
        "user_stated_cause",
        "user_stated_result",
        "attempt_and_block",
        "wish_and_constraint",
        "action_supports_change",
        "evaluation_about_event",
        "self_evaluation_about_state",
        "preserves_despite",
        "uncertain_connection",
        "continuation_or_refusal",
    }
)
_RELATION_KIND_BY_EXISTING_TYPE: Final[dict[str, RelationKind]] = {
    "explicit_transition": "contrast",
    "coexistence": "coexistence",
    "tension": "wish_and_constraint",
    "limit_tension": "attempt_and_block",
}
_KIND_BY_DETECTED_TYPE: Final[dict[str, NucleusKind]] = {
    "event": "event",
    "emotion": "reaction",
    "wish": "wish",
    "constraint": "constraint",
    "fear": "reaction",
    "self_awareness": "self_evaluation",
    "limit_signal": "state",
    "value": "value",
    "relation_marker": "other_explicit",
    "safety_risk": "state",
}
_ROLE_KIND_HINTS: Final[tuple[tuple[frozenset[str], NucleusKind], ...]] = (
    (frozenset({"paced_progress"}), "change"),
    (frozenset({"self_view", "self_awareness", "self_suppression"}), "self_evaluation"),
    (frozenset({"wish", "wish_or_hope", "continuation_wish", "own_happiness_wish", "normal_life_wish"}), "wish"),
    (frozenset({"constraint", "restriction_pressure", "reality_gap_or_inconvenience", "collapse_anxiety"}), "constraint"),
    (frozenset({"fear_or_disappointment", "sadness_or_pain", "fatigue_or_limit", "limit_or_exhaustion"}), "reaction"),
    (frozenset({"value", "value_or_strength", "relief_source", "small_change_value"}), "value"),
)
_RETENTION_RANK: Final = {"optional": 0, "should": 1, "required": 2}
_RELATION_GROUP_DELIMITERS: Final[dict[str, str]] = {
    "「": "」",
    "『": "』",
    "“": "”",
    "‘": "’",
    "（": "）",
    "(": ")",
    "［": "］",
    "[": "]",
    "【": "】",
    "｛": "｝",
    "{": "}",
    "＜": "＞",
    "<": ">",
    "〈": "〉",
    "《": "》",
    "〔": "〕",
    "〝": "〟",
    "〖": "〗",
    "〘": "〙",
    "〚": "〛",
    "｟": "｠",
}
_RELATION_SYMMETRIC_DELIMITERS: Final[frozenset[str]] = frozenset({'"'})


_NEGATION_RE: Final = re.compile(
    r"(?:ない|なかった|なく|ません|できず|出来ず|無理|だめ|ダメ)"
)
_NON_NEGATING_UNCERTAINTY_RE: Final = re.compile(r"(?:かも知れない|かもしれない)")
_NON_NEGATING_CONTRAST_RE: Final = re.compile(
    r"(?:だけでなく|わけではなく|のではなく|ではなく|じゃなく)(?:て|、|,)?"
)
_SIMILE_NOT_WISH_RE: Final = re.compile(r"(?<![てで])みたい")
_POSITIVE_CHANGE_RE: Final = re.compile(
    r"(?:できた|出来た|(?:ら|れ)れるようにな|ようになった|くなった|になった|"
    r"増えた|減った|戻った|進んだ|進めた|改善した|楽になった|"
    r"嬉|うれ|喜び|安心|平穏|幸せ|達成|落ち着(?:いた|いてきた))"
)
_FEELING_RE: Final = re.compile(
    r"(?:感じ|気持ち|悲し|不安|だる|しんど|つら|辛|焦|もやもや|怖|寂|苦し|嬉|うれ|落ち着|重い)"
)
_HELP_SEEKING_RE: Final = re.compile(
    r"(?:相談|面談|受診|診察|予約|窓口|連絡先|相談先|支援先|助けを求め|話を聞いてもら)"
)
_SOURCE_METAPHOR_RE: Final = re.compile(
    r"(?:鉛|石|重り|圧力|圧迫|締め付け|押し潰|沈む|霧|棘|刺さる|穴が空|空洞)"
)
_WISH_RE: Final = re.compile(
    r"(?:したい|なりたい|していきたい|過ごしていきたい|ほしい|欲しい|願|つもり|たい(?:って|と|気持ち|と思|です|でした|[、,\s]|$)|たらいい)"
)
_FINITE_WISH_CLAUSE_END_RE: Final = re.compile(
    r"(?:(?:たい|ほしい|欲しい)(?:です|でした)?|"
    r"(?:たい|ほしい|欲しい)(?:気持ち|願い)"
    r"(?:だ|です|だった|でした)|"
    r"(?:たい|ほしい|欲しい)(?:と|とは)?思"
    r"(?:う|っている|っていた|っています|っていました|"
    r"ってき(?:た|ます|ました|ません|ませんでした|"
    r"ている|ていた|ています|ていました)|"
    r"い(?:始め|続け|終え)(?:る|た|ている|ていた|"
    r"てき(?:た|ます|ました|ません|ませんでした|"
    r"ている|ていた|ています|ていました)|"
    r"ます|ました)|"
    r"います|いました)|"
    r"願(?:う|っている)|つもり(?:だ|です))"
    r"(?:(?:の|ん)(?:だ|です|だった|でした))?$"
)
_REFUSAL_RE: Final = re.compile(
    r"(?:(?:し|続け)たく(?:ない|ありません)|やめたい|終わらせたい|投げ出したい|"
    r"つもり(?:は|が)?ない|拒否|拒|嫌だ|このまま(?:では|じゃ)いけない)"
)
_UNCERTAIN_RE: Final = re.compile(
    r"(?:気がする|かもしれ|"
    r"(?:と|とは)思(?:う|った|います|いました|"
    r"って(?:いる|いた|います|いました)|"
    r"ってき(?:た|ます|ました|ません|ませんでした|"
    r"ている|ていた|ています|ていました)|"
    r"い(?:始め|続け|終え)(?:る|た|ている|ていた|"
    r"てき(?:た|ます|ました|ません|ませんでした|"
    r"ている|ていた|ています|ていました)|"
    r"ます|ました))|"
    r"こうかな|かな(?=[、。,.!！?？\s]|$)|憶測|わからない|分からない|不明)"
)
_CONSTRAINT_RE: Final = re.compile(
    r"(?:なければ|ないと|できない|出来ない|"
    r"難し(?:い|かった|く(?:ない|なかった|ありません(?:でした)?))|"
    r"無理|制約|限界|しかない|せざるを得|取れなく|作れない)"
)
_NEGATED_CONSTRAINT_CANCELLATION_INNER_RE: Final = re.compile(
    r"(?:"
    r"難し(?:くない|くなかった|くありません(?:でした)?)|"
    r"(?:無理|制約|限界)(?:は|では|じゃ)?"
    r"(?:ない|なかった|ありません(?:でした)?)"
    r")"
)
_NEGATED_CONSTRAINT_CANCELLATION_RE: Final = re.compile(
    _NEGATED_CONSTRAINT_CANCELLATION_INNER_RE.pattern + r"$"
)
_CHANGE_RE: Final = re.compile(
    r"(?:になった|なって|くなった|変わ|減った|増えた|戻った|進んだ|進めた|"
    r"できるよう|出来るよう|(?:ら|れ)れるよう|改善|進歩)"
)
_BOUNDED_NON_DENIAL_SELF_EVALUATION_RE: Final = re.compile(
    r"(?:(?:自分|私|わたし|僕|ぼく|俺|おれ)(?:自身)?"
    r"(?:には|に|なんか|なんて|など|は|が|も|こそ|だけ)"
    r"[^。！？!?\n]{0,24}(?:弱(?:い|く)|悪(?:い|く)|遅(?:い|く)|"
    r"責任(?:がある|を感じ))|"
    r"(?:自分|私|わたし|僕|ぼく|俺|おれ)(?:自身)?(?:のこと)?を"
    r"[^。！？!?\n]{0,20}比べ(?:て|る))"
)
_VALUE_RE: Final = re.compile(r"(?:大切|大事|価値|意味がある|守りたい|好まし|望まし|良(?:い|く)|いい)")
_ACTION_RE: Final = re.compile(r"(?:行動|記録|メモ|決め|書き|書いた|見て|見た|作った|試した|調べた|残した)")
_ACTION_CHANGE_LINK_RE: Final = re.compile(
    r"(?:たら|だら|てから|でから|た後(?:に)?|たあと(?:に)?)[、,]\s*"
)
# Final Stage-1 alone may expose more than one predicate owner from a single
# EvidenceSpan.  These operators describe grammatical seams which the active
# I5 plan intentionally leaves collapsed.  They are consumed only by
# ``_final_stage1_compound_meaning_projections_for_span`` below.
_FINAL_STAGE1_EVENT_BEFORE_LINK_RE: Final = re.compile(
    r"(?P<perfective>ました|でした|た|だ)(?:後|あと)(?:に)?[、,]\s*"
)
_FINAL_STAGE1_ACTION_RESULT_LINK_RE: Final = re.compile(r"(?:たら|だら)")
_FINAL_STAGE1_OPEN_DELIBERATION_RE: Final = re.compile(
    r"(?:どう|何|どちら|どっち|いつ|どこ|誰)"
    r".{0,24}(?:したら|すれば|すべき|するのが|"
    r"なれば|あれば)(?:いい|よい|良い)?の?か"
)
_FINAL_STAGE1_DELIBERATION_LINK_RE: Final = re.compile(
    r"で[、,]\s*(?=(?:どう|何|どちら|どっち|いつ|どこ|誰))"
)
_FINAL_STAGE1_BURDEN_RE: Final = re.compile(
    r"(?:疲れ|疲労|消耗|負担|限界|引っかか|迷惑|"
    r"不安|だる|しんど|つら|辛|苦し|重い)"
)
_FINAL_STAGE1_INABILITY_RE: Final = re.compile(
    r"(?:でき|出来|[ぁ-んァ-ヶ一-龯々〆ヵヶー]{1,24}"
    r"(?:られ|れ|け|せ))(?:ない|なかった|なく|ません)"
)
_FINAL_STAGE1_WISH_RESIDUE_LINK_RE: Final = re.compile(r"と")
_ACTION_ARGUMENT_STEM_RE: Final = re.compile(
    r"(?:を|に|へ|で|から|と|まで)(?P<predicate>[^、,.!?！？]{1,28})$"
)
_NON_ACTION_CONDITION_END_RE: Final = re.compile(
    r"(?:だっ|であっ|になっ|くなっ|でい|にい|にあっ)$"
)
_OBSERVED_PAST_OUTCOME_RE: Final = re.compile(
    r"(?:た|ました|だった|でした)$"
)
_EXPLICIT_PERFECTIVE_END_RE: Final = re.compile(
    r"(?:た|(?:ん|い)だ|ていた|でいた|ました|だった|でした)$"
)
_PRESENT_RESIDUE_RE: Final = re.compile(
    r"(?:(?:まだ|今も|なお).{0,32}(?:残(?:って|る|り|った)|続(?:いて|く)|消えず)|"
    r"(?:残(?:って|る|り|った)|続(?:いて|く)).{0,12}"
    r"(?:いる|いた|います|いました|ある|あった|あります|ありました))"
)
_OPEN_UNFINISHED_RE: Final = re.compile(
    r"(?:(?:どう|何|どちら|どっち|いつ|どこ|誰).{0,32}"
    r"(?:分からない|わからない|分かりません|わかりません|"
    r"決められない|決められません|決めきれない|決めきれません)|"
    r"(?:まだ|今も).{0,32}(?:分からない|わからない|分かりません|"
    r"わかりません|未定|決められない|決められません|"
    r"決めきれない|決めきれません)|"
    r"(?:未定|途中|決められない|決められません|"
    r"決めきれない|決めきれません|"
    r"結論(?:は|が)出て(?:いない|いなかった|いません(?:でした)?)))"
)
_CONTRAST_RE: Final = re.compile(
    r"(?:それでも|でも|だけど|けれど|けど|"
    r"一方(?:で|(?=[、,\s]|$))|なのに|ただ(?!し)|"
    r"とはいえ(?!な(?:い|かった|く)|ません(?:でした)?))"
)
_COEXISTENCE_RE: Final = re.compile(r"(?:同時に|両方|どっちも|抱えたまま)")
_TOP_LEVEL_CONTRAST_LINK_RE: Final = re.compile(
    r"(?:なのに|のに|けれども?|けども?|"
    r"とはいえ(?!な(?:い|かった|く)|ません(?:でした)?)|"
    r"一方(?:で|(?=[、,\s]|$)))(?:[、,]\s*)?|"
    r"が[、,]\s*|"
    r"(?<=[、,。.!！?？\s])(?:それでも|でも|ただ(?!し))"
    r"(?:[、,]\s*)?"
)
_TOP_LEVEL_BARE_GA_LINK_RE: Final = re.compile(r"が(?![、,])")
_TOP_LEVEL_COORDINATE_LINK_RE: Final = re.compile(r"と[、,]\s*")
_COEXISTENCE_TAIL_RE: Final = re.compile(
    r"(?:が|は|を)?(?:同時に|両方|どっちも)(?:ある|いる|残っている)$"
)
_RELATION_UNCERTAINTY_RE: Final = re.compile(
    r"(?:迷(?:って|い|う)|ためら|自信がな|よいか|いいか|べきか|気がし)"
)
_NEGATED_RELATION_UNCERTAINTY_CANCELLATION_RE: Final = re.compile(
    r"(?:迷|ためら)(?:"
    r"わ(?:ない|なかった|ず|ぬ)|"
    r"って(?:いない|いなかった|いません(?:でした)?)"
    r")$"
)
_CAUSE_RE: Final = re.compile(r"(?:ので(?!す)|ため|ことで|からこそ|だからこそ)")
_RESULT_RE: Final = re.compile(r"(?:その結果|だから|になった|減った|増えた|できた|出来た|ようになった)")
_SHIFT_RE: Final = re.compile(
    r"(?:今までは|これまでは|以前は|前は|今は|現在は|昨日|今日|より|"
    r"になった|くなった|変わ|減った|増えた|戻った|ようになった|進歩)"
)
_CONTINUATION_RE: Final = re.compile(
    r"(?:続(?:け|いて|いた|く)|繰り返|ずっと)"
)

# One shared finite-carrier grammar is used by owner binding, specialized
# endpoint-final checks, and the generic relation fallback.  It deliberately
# describes only inflectional material after an already frozen operator.  It
# does not admit an arbitrary host predicate or a noun/case-particle residue.
_FINITE_ENDPOINT_CARRIER_RE: Final = re.compile(
    r"(?:"
    r"(?:っ|い|し|き|ぎ)?(?:て|で)(?:は|も)?(?:いる|いた|きた|"
    r"いない|いなかった|います|"
    r"いました|いません|いませんでした|ある|あった|ない|なかった|"
    r"あります|ありました|ありません|ありませんでした)|"
    r"(?:で(?:は|も)?|じゃ)(?:ある|あった|ない|なかった|あります|"
    r"ありました|ありません|ありませんでした)|"
    r"(?:だ|です|だった|でした)(?:の|ん)(?:だ|です|だった|でした)|"
    r"(?:な)?(?:の|ん)(?:だ|です|だった|でした)|"
    r"(?:だ|です|だった|でした|である|であった)|"
    r"(?:し|り|き|ぎ|ち|に|び|み|い)?"
    r"(?:始め|続け|終え)(?:る|た|ている|ていた|"
    r"ています|ていました|てしま(?:う|った|っている|っていた)|"
    r"ます|ました)|"
    r"(?:て|で)き(?:た|ている|ていた|ています|ていました)|"
    r"(?:て|で)しま(?:う|った|っている|っていた|"
    r"います|いました)|"
    r"しま(?:う|った|っている|っていた|"
    r"います|いました)|"
    r"でき(?:る|た|ている|ていた|ます|ました|"
    r"ない|なかった|ません|ませんでした)|"
    r"する|"
    r"りする|"
    r"し(?:たい(?:です|でした)?|たかった(?:です)?|たくない|たくなかった|"
    r"たくありません(?:でした)?|ます|ました|ません|ませんでした)|"
    r"(?:し)?(?:い(?:です)?|かった(?:です)?|"
    r"く(?:ない|なかった|ありません(?:でした)?))|"
    r"(?:き|ぎ|し|ち|に|び|み|り|い)?つつ(?:ある|あった|あります|ありました)|"
    r"(?:っ|ん|い|し|き|ぎ)(?:た|だ)|"
    r"(?:か|が|さ|た|な|ば|ま|ら|わ)(?:ない|なかった|なく)|"
    r"(?:き|ぎ|し|ち|に|び|み|り|い)"
    r"(?:ます|ました|ません|ませんでした)|"
    r"(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした)|"
    r"(?:る|う|い|た|だ|ます|ました|ません|ませんでした|ない|なかった)"
    r")"
)
# Attachment classes are intentionally morphological rather than lexical
# continuations.  A carrier is admitted only when the frozen operator that
# precedes it supplies the matching Japanese conjugation class.
_FINITE_TE_AUXILIARY_CARRIER_RE: Final = re.compile(
    r"(?:"
    r"(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした)|"
    r"き(?:た|ます|ました|ません|ませんでした|"
    r"て(?:いる|いた|います|いました))|"
    r"こ(?:ない|なかった)|"
    r"しま(?:う|った|います|いました|"
    r"いません|いませんでした|"
    r"って(?:いる|いた|います|いました))"
    r")"
)
_FINITE_ASPECT_HOST_SOURCE: Final = (
    r"(?:始め|続け|終え)"
    r"(?:る|た|ない|なかった|ます|ました|ません|ませんでした|"
    r"て(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|こない|こなかった|"
    r"き(?:た|ます|ました|ません|ませんでした|"
    r"ている|ていた|ています|ていました)|"
    r"しま(?:う|った|います|いました|"
    r"いません|いませんでした|"
    r"っている|っていた)))"
)
_FINITE_TSUTSU_HOST_SOURCE: Final = (
    r"つつ(?:ある|あった|あります|ありました)"
)
_FINITE_ICHIDAN_CARRIER_RE: Final = re.compile(
    r"(?:る|た|ない|なかった|ます|ました|ません|ませんでした|"
    r"て(?:(?:は|も)?(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした)|こ(?:ない|なかった)|き(?:た|ます|ました|ません|"
    r"ませんでした|ている|ていた|ています|ていました)|"
    r"しま(?:う|った|っている|っていた|います|いました))|"
    + _FINITE_ASPECT_HOST_SOURCE
    + r"|"
    + _FINITE_TSUTSU_HOST_SOURCE
    + r")"
)
_FINITE_SAHEN_CARRIER_RE: Final = re.compile(
    r"(?:"
    r"する|した|しない|しなかった|します|しました|しません|しませんでした|"
    r"したい(?:です|でした)?|したかった(?:です)?|"
    r"したく(?:ない|なかった|ありません(?:でした)?)|"
    r"して(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|こ(?:ない|なかった)|き(?:た|ます|ました|ません|"
    r"ませんでした|ている|ていた|ています|ていました)|"
    r"しま(?:う|った|っている|っていた|います|いました))|"
    r"し" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"し" + _FINITE_TSUTSU_HOST_SOURCE + r"|"
    r"でき(?:る|た|ない|なかった|ます|ました|ません|ませんでした|"
    r"て(?:いる|いた|います|いました))"
    r")"
)
_FINITE_SURU_RENYOKEI_CARRIER_RE: Final = re.compile(
    r"(?:た|ない|なかった|ます|ました|ません|ませんでした|"
    r"て(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|き(?:た|ます|ました)|"
    r"しま(?:う|った|っている|っていた))|"
    + _FINITE_ASPECT_HOST_SOURCE
    + r"|"
    + _FINITE_TSUTSU_HOST_SOURCE
    + r")"
)
_FINITE_GODAN_R_CARRIER_RE: Final = re.compile(
    r"(?:る|った|ら(?:ない|なかった)|り(?:ます|ました|ません|ませんでした)|"
    r"って(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|こ(?:ない|なかった)|き(?:た|ます|ました|ません|"
    r"ませんでした|ている|ていた|ています|ていました)|"
    r"しま(?:う|った|っている|っていた|います|いました))|"
    r"り" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"り" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_GODAN_W_CARRIER_RE: Final = re.compile(
    r"(?:う|った|わ(?:ない|なかった)|い(?:ます|ました|ません|ませんでした)|"
    r"って(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|こ(?:ない|なかった)|き(?:た|ます|ました|ません|"
    r"ませんでした|ている|ていた|ています|ていました)|"
    r"しま(?:う|った|っている|っていた|います|いました))|"
    r"い" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"い" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_GODAN_K_CARRIER_RE: Final = re.compile(
    r"(?:く|いた|か(?:ない|なかった)|き(?:ます|ました|ません|ませんでした)|"
    r"いて(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|こ(?:ない|なかった)|き(?:た|ます|ました|ません|"
    r"ませんでした|ている|ていた|ています|ていました)|"
    r"しま(?:う|った|っている|っていた|います|いました))|"
    r"き" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"き" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_GODAN_B_CARRIER_RE: Final = re.compile(
    r"(?:ぶ|んだ|ば(?:ない|なかった)|"
    r"び(?:ます|ました|ません|ませんでした)|"
    r"んで(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|き(?:た|ます|ました)|"
    r"こ(?:ない|なかった))|"
    r"び" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"び" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_GODAN_S_CARRIER_RE: Final = re.compile(
    r"(?:す|した|さ(?:ない|なかった)|"
    r"し(?:ます|ました|ません|ませんでした)|"
    r"して(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|き(?:た|ます|ました)|"
    r"こ(?:ない|なかった))|"
    r"し" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"し" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_GODAN_M_CARRIER_RE: Final = re.compile(
    r"(?:む|んだ|ま(?:ない|なかった)|"
    r"み(?:ます|ました|ません|ませんでした)|"
    r"んで(?:いる|いた|いない|いなかった|います|いました|"
    r"いません|いませんでした|き(?:た|ます|ました)|"
    r"こ(?:ない|なかった))|"
    r"み" + _FINITE_ASPECT_HOST_SOURCE + r"|"
    r"み" + _FINITE_TSUTSU_HOST_SOURCE + r")"
)
_FINITE_I_ADJECTIVE_CARRIER_RE: Final = re.compile(
    r"(?:い(?:です)?|かった(?:です)?|"
    r"く(?:ない|なかった|ありません(?:でした)?))"
)
_FINITE_SHII_ADJECTIVE_CARRIER_RE: Final = re.compile(
    r"(?:しい(?:です)?|しかった(?:です)?|"
    r"しく(?:ない|なかった|ありません(?:でした)?))"
)
_FINITE_COPULAR_CARRIER_RE: Final = re.compile(
    r"(?:だ|です|だった|でした|である|であった|"
    r"で(?:は|も)?(?:ある|あった|ない|なかった|あります|ありました|"
    r"ありません|ありませんでした)|"
    r"じゃ(?:ある|あった|ない|なかった|ありません|ありませんでした))"
)
_FINITE_ENDPOINT_EXPLANATORY_RE: Final = re.compile(
    r"(?P<base>.*?)(?P<link>の|ん)(?:だ|です|だった|でした|"
    r"である|であった)$"
)
_FINITE_ENDPOINT_EXISTENCE_RE: Final = re.compile(
    r"(?:ある|あった|あります|ありました|"
    r"ない|なかった|ありません|ありませんでした)"
)
_FINITE_ENDPOINT_RESIDUE_HOST_RE: Final = re.compile(
    r"(?P<base>.*?)(?P<link>な|の)?まま"
    r"(?:だ|です|だった|でした|である|であった|"
    r"でいる|でいた|でいます|でいました)$"
)
_FINITE_SEMANTIC_SUBJECT_HOST_RE: Final = re.compile(
    r"(?:(?:まだ|今も|なお)[、,\s]*)?"
    r"(?:(?:少し(?:だけ|ずつ)?|やや|ずっと|強く)[、,\s]*)?"
    r"(?:"
    r"残(?:る|った|って(?:いる|いた|います|いました))|"
    r"続(?:く|いた|いて(?:いる|いた|います|いました))|"
    r"高まって(?:いる|いた|います|いました)|"
    r"強まって(?:いる|いた|います|いました)|"
    r"膨らんで(?:いる|いた|います|いました)|"
    r"募って(?:いる|いた|います|いました)|"
    r"消えず(?:に)?(?:いる|いた|います|いました)"
    r"|ない|なかった|ありません|ありませんでした"
    r")"
)
_FINITE_WISH_EXISTENCE_HOST_RE: Final = re.compile(
    r"(?:(?:少し(?:だけ|ずつ)?|やや|ずっと|強く)[、,\s]*)?"
    r"(?:ある|あった|あります|ありました)"
)
_FINITE_ENDPOINT_TERMINAL_RE: Final = re.compile(
    r"(?:"
    r"(?:て|で)(?:は|も)?(?:いる|いた|いない|いなかった|います|"
    r"いました|いません|いませんでした|ある|あった|ない|なかった|"
    r"あります|ありました|ありません|ありませんでした)|"
    r"(?:で(?:は|も)?|じゃ)(?:ある|あった|ない|なかった|あります|"
    r"ありました|ありません|ありませんでした)|"
    r"(?:な)?(?:の|ん)(?:だ|です|だった|でした)|"
    r"(?:る|う|く|ぐ|す|つ|ぬ|ぶ|む|い|た|だ|ます|ました|"
    r"ません|ませんでした|ない|なかった|だ|です|だった|でした)"
    r")$"
)
_LEADING_CONTRAST_RE: Final = re.compile(
    r"^(?:それでも|けれども?|でも|だけど|"
    r"一方(?:で|(?=[、,\s]|$))|ただ(?!し)|"
    r"とはいえ(?!な(?:い|かった|く)|ません(?:でした)?)|なのに)"
)
_BOUNDARY_CAUSE_RE: Final = re.compile(r"(?:ので|ため|ことで|からこそ|だからこそ)[、,]?$")
_BOUNDARY_RESULT_RE: Final = re.compile(r"^(?:その結果|結果として|そのため|だから)")
_ACHIEVEMENT_RE: Final = re.compile(
    r"(?:できた|出来た|書けた|作れた|見えた|行けた|進めた|伝えられた|残せた|"
    r"整えた|終えた|まとめた|片づけた|片付けた)"
)
_COMPLETED_ACTION_RE: Final = re.compile(
    r"(?:整理した|保存した|記録した|メモした|測定した|確認した|連絡した|相談した|"
    r"準備した|提出した|予約した|縮めて保存した|印を付けた|書き残した|残した|"
    r"書いた|調べた|試した|見た|作った|行った)"
)
_LIMITING_UNKNOWN_RE: Final = re.compile(
    r"(?:まだ(?:不明|分から|わから|遠い)|不明|分からない|わからない|"
    r"遠い(?:と思|気が)|かもしれない|確定できない)"
)
_PROVISIONAL_EVALUATION_RE: Final = re.compile(
    r"(?:失敗|無理|駄目|だめ|ダメ|終わり|価値がない).{0,18}(?:と思|と見|と感じ|"
    r"と片づけ|と片付け|そうにな|かけ)"
)
_EXPLICIT_EVALUATION_RE: Final = re.compile(
    r"(?:私|自分|本人).{0,12}(?:にとって|として).{0,12}(?:良い|いい|大切|大事|価値)|"
    r"(?:良い|いい|大切|大事|価値).{0,8}(?:変化|進歩|結果|部分)"
)
_EXPLICIT_SHIFT_FROM_RE: Final = re.compile(r"(?:今までは|これまでは|以前は|前は|昨日は)")
_EXPLICIT_SHIFT_TO_RE: Final = re.compile(
    r"(?:今は|現在は|これから|今後|次は|ようになった|くなった|になった|減った|増えた)"
)
_SELF_REFERENCE_RE: Final = re.compile(r"(?:自分|私|わたし|僕|ぼく|俺|おれ)")
_OWNER_FOCUS_PARTICLE_SOURCE: Final = (
    r"(?:ぐらい|くらい|ばかり|なんて|なんぞ|だって|"
    r"こそ|しか|だけ|まで|さえ|すら|なんか|など|"
    r"のみ|きり|ほど|とか|なり|だの|やら|自身|本人)"
)
_OWNER_TOPIC_PARTICLE_SOURCE: Final = (
    r"(?:として(?:は)?|なら(?:ば)?|って|"
    r"に関して(?:は)?|において(?:は)?)"
)
_PAST_RE: Final = re.compile(r"(?:昨日|以前|今まで|これまで|過去|先週|前は)")
_PRESENT_RE: Final = re.compile(r"(?:今日|今は|今の|現在|この記録|少しずつ)")
_FUTURE_RE: Final = re.compile(r"(?:これから|今後|次に|していきたい|過ごしていきたい)")
_TRULY_LIMITED_TEXT_RE: Final = re.compile(
    r"^(?:わからない|分からない|不明|特になし|なし|入力なし|未入力|うーん|えっと|それ|これ|あれ)$"
)
_SHORT_STATE_KINDS: Final = frozenset(
    {
        "state",
        "reaction",
        "wish",
        "constraint",
        "self_evaluation",
        "uncertainty",
        "conclusion",
    }
)


class GroundedObservationPlanError(ValueError):
    """Raised when the I1 shadow plan cannot satisfy its internal contract."""


@dataclass(frozen=True)
class GroundedSemanticFrame:
    actor: str
    predicate_kind: str
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"]
    target_anchor_ids: tuple[str, ...] = ()
    time_scope: str = "current_input"
    degree: str = "source_bounded"
    attribute_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedSemanticNucleus:
    nucleus_id: NucleusId
    kind: NucleusKind
    source_span_ids: tuple[EvidenceId, ...]
    source_fields: tuple[str, ...]
    surface_anchor_ids: tuple[str, ...]
    semantic_frame: GroundedSemanticFrame
    grounding_kind: GroundingKind
    certainty: float
    priority: float
    retention: Retention
    allowed_claim_scope: str
    forbidden_inference_codes: tuple[str, ...]
    source_claim_ids: tuple[str, ...] = ()
    source_meaning_block_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedSemanticRelation:
    relation_id: RelationId
    type: RelationKind
    from_nucleus_id: NucleusId
    to_nucleus_id: NucleusId
    source_span_ids: tuple[EvidenceId, ...]
    grounding_kind: GroundingKind
    certainty: float
    retention: Retention
    source_relation_ids: tuple[str, ...] = ()
    source_meaning_arc_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedUnknownBoundary:
    unknown_id: str
    dimension: str
    affected_nucleus_ids: tuple[NucleusId, ...] = ()
    evidence_span_ids: tuple[EvidenceId, ...] = ()
    surface_policy: UnknownSurfacePolicy = "do_not_claim"


@dataclass(frozen=True)
class GroundedInputProfile:
    text_presence: Literal["text_present", "labels_only", "empty"]
    material_quality: Literal[
        "grounded",
        "short_state_sufficient",
        "limited_grounding",
        "labels_only_limited",
        "empty",
        "safety_routed",
    ]
    semantic_complexity: Literal["minimal", "single", "multi", "long_arc"]
    nucleus_count: int
    relation_count: int
    safety_kind: str


@dataclass(frozen=True)
class GroundedQuestionPolicy:
    allowed: bool = False
    reason: str = "p7_base_observation_must_not_be_replaced_by_question"


@dataclass(frozen=True)
class GroundedReceptionQuotePolicy:
    mode: Literal["no_full_quote_replay"]
    max_anchor_count: int
    max_anchor_visible_chars: int


@dataclass(frozen=True)
class GroundedReceptionSentencePolicy:
    min_sentences: int
    max_sentences: int


@dataclass(frozen=True)
class GroundedReceptionDistinctnessPolicy:
    observation_summary_repetition_allowed: bool
    relation_reexplanation_allowed: bool
    all_input_enumeration_allowed: bool
    policy_explanation_allowed: bool
    new_cause_allowed: bool
    new_identity_claim_allowed: bool
    advice_allowed: bool
    question_allowed: bool


@dataclass(frozen=True)
class GroundedReceptionOpportunity:
    """Body-free chance to make one distinct human reception contribution."""

    opportunity_id: str
    family: GroundedReceptionOpportunityFamily
    reception_act: GroundedReceptionAct
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    retention: Retention
    priority: int
    source_field_count: int
    safety_required: bool


@dataclass(frozen=True)
class GroundedReceptionDepthPolicy:
    """Semantic response depth; raw input length is never an input."""

    level: GroundedReceptionDepthLevel
    safety_mode: GroundedReceptionSafetyMode
    opportunity_count: int
    selected_move_count: int
    selection_reason_codes: tuple[str, ...]
    raw_character_count_used: bool
    min_sentences: int
    max_sentences: int
    min_realized_moves: int
    max_moves_per_sentence: int


@dataclass(frozen=True)
class GroundedReceptionMovePlan:
    """One grounded human contribution for the later RR4/RR5 surface owner."""

    move_id: str
    move_role: GroundedReceptionMoveRole
    reception_act: GroundedReceptionAct
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    follow_elements: tuple[GroundedFollowElement, ...]
    speaker_presence: GroundedSpeakerPresence
    reference_mode: GroundedReferenceMode
    surface_strategy: GroundedReceptionSurfaceStrategy
    required: bool
    distinct_from_move_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundedHumanReceptionPlan:
    """Body-free contract for Emlis's distinct human reception contribution."""

    schema_version: str
    required: bool
    opportunities: tuple[GroundedReceptionOpportunity, ...]
    depth_policy: GroundedReceptionDepthPolicy
    moves: tuple[GroundedReceptionMovePlan, ...]
    primary_reception_act: GroundedReceptionAct | None
    secondary_reception_act: GroundedReceptionAct | None
    primary_follow_element: GroundedFollowElement | None
    secondary_follow_elements: tuple[GroundedFollowElement, ...]
    afterglow_follow_element: GroundedFollowElement | None
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    observation_owned_nucleus_ids: tuple[NucleusId, ...]
    stance: GroundedReceptionStance | None
    speaker_presence: GroundedSpeakerPresence | None
    reference_mode: GroundedReferenceMode | None
    quote_policy: GroundedReceptionQuotePolicy
    sentence_policy: GroundedReceptionSentencePolicy
    distinctness_policy: GroundedReceptionDistinctnessPolicy
    safety_modifier_codes: tuple[str, ...]
    forbidden_surface_codes: tuple[str, ...]


@dataclass(frozen=True)
class GroundedResponsePlan:
    response_kind: str
    primary_nucleus_ids: tuple[NucleusId, ...]
    supporting_nucleus_ids: tuple[NucleusId, ...]
    relation_ids: tuple[RelationId, ...]
    fact_boundary_nucleus_ids: tuple[NucleusId, ...]
    human_follow_target_ids: tuple[NucleusId, ...]
    human_reception_plan: GroundedHumanReceptionPlan | None
    required_nucleus_ids: tuple[NucleusId, ...]
    optional_nucleus_ids: tuple[NucleusId, ...]
    question_policy: GroundedQuestionPolicy
    surface_shape: Literal["plain", "two_stage", "multi_paragraph", "separate_safety_surface"]


@dataclass(frozen=True)
class GroundedCoverageRequirements:
    required_nucleus_ids: tuple[NucleusId, ...]
    required_relation_ids: tuple[RelationId, ...]
    all_required_nuclei_must_be_covered: bool = True
    all_required_relations_must_be_covered: bool = True
    all_sentence_evidence_ids_must_resolve: bool = True
    label_only_allowed_only_without_text_nuclei: bool = True
    human_follow_required: bool = False
    fact_boundary_required: bool = False


@dataclass(frozen=True)
class GroundedSurfacePolicy:
    content_source: Literal["grounded_plan_only", "separate_safety_owner"]
    completed_semantic_template_allowed: bool = False
    example_cue_route_allowed: bool = False
    synthetic_evidence_id_allowed: bool = False
    unknown_word_policy: Literal["retain_as_source_anchor", "omit_without_inference"] = "retain_as_source_anchor"
    generic_observation_surface_allowed: bool = True
    tone_family: str = "current_input_bounded"
    hedge_policy: str = "single_input_scope"


@dataclass(frozen=True)
class GroundedSafetyPolicy:
    safety_kind: str
    identity_claim_must_not_be_accepted_as_fact: bool
    emergency_path_must_not_be_overridden: bool = True
    requires_separate_safety_surface: bool = False
    grounded_plan_overlay_allowed: bool = True
    required_boundary_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedObservationPlan:
    schema_version: str
    adapter_version: str
    generation_path: str
    input_profile: GroundedInputProfile
    nuclei: tuple[GroundedSemanticNucleus, ...]
    relations: tuple[GroundedSemanticRelation, ...]
    unknown_boundaries: tuple[GroundedUnknownBoundary, ...]
    response_plan: GroundedResponsePlan
    coverage_requirements: GroundedCoverageRequirements
    surface_policy: GroundedSurfacePolicy
    safety_policy: GroundedSafetyPolicy
    evidence_ledger_validation: EvidenceLedgerValidationReport
    referenced_evidence_span_ids: tuple[EvidenceId, ...]
    source_contracts: tuple[str, ...] = ()

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return ids, codes, counts and policies only; never source/body text."""

        payload = asdict(self)
        payload.update(
            {
                "raw_input_included": False,
                "raw_text_included": False,
                "comment_text_included": False,
                "surface_text_included": False,
                "comment_text_generated": False,
                "surface_connected": True,
                "public_reply_path_connected": True,
                "human_reception_plan_included": self.response_plan.human_reception_plan is not None,
                "human_reception_plan_required": bool(
                    self.response_plan.human_reception_plan
                    and self.response_plan.human_reception_plan.required
                ),
                "public_contract_changed": False,
                "api_route_changed": False,
                "db_physical_name_changed": False,
                "rn_visible_contract_changed": False,
            }
        )
        return payload


@dataclass(frozen=True)
class _MeaningArtifacts:
    meaning_blocks: tuple[InputMeaningBlock, ...] = ()
    coverage_plan: MeaningCoveragePlan | None = None
    whole_input_meaning_arc: WholeInputMeaningArc | None = None
    retention_plan: MajorMeaningRetentionPlan | None = None


@dataclass(frozen=True)
class _RelationSeed:
    type: RelationKind
    from_nucleus_id: NucleusId
    to_nucleus_id: NucleusId
    source_span_ids: tuple[EvidenceId, ...]
    grounding_kind: GroundingKind
    certainty: float
    retention: Retention
    source_relation_ids: tuple[str, ...] = ()
    source_meaning_arc_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class _ClauseSignals:
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"]
    time_scope: str
    operator_codes: tuple[str, ...]


@dataclass(frozen=True)
class _TypedNucleusProjection:
    """One source-bound predicate owner projected from a compound span."""

    nucleus_suffix: str
    kind: NucleusKind
    predicate_kind: str
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"]
    time_scope: str
    scalar_start: int
    scalar_end: int
    attribute_codes: tuple[str, ...]
    relation_kind: RelationKind | None = None
    grounding_kind: GroundingKind = "explicit"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def _top_level_text(text: str) -> str | None:
    """Mask grouped text without changing offsets; malformed nesting fails."""

    expected_closers: list[str] = []
    visible: list[str] = []
    closing_delimiters = set(_RELATION_GROUP_DELIMITERS.values())
    for character in text:
        depth = len(expected_closers)
        delimiter = False
        if character in _RELATION_SYMMETRIC_DELIMITERS:
            delimiter = True
            if expected_closers and expected_closers[-1] == character:
                expected_closers.pop()
            else:
                expected_closers.append(character)
        elif character in _RELATION_GROUP_DELIMITERS:
            delimiter = True
            expected_closers.append(_RELATION_GROUP_DELIMITERS[character])
        elif character in closing_delimiters:
            delimiter = True
            if not expected_closers or expected_closers[-1] != character:
                return None
            expected_closers.pop()
        visible.append(character if depth == 0 and not delimiter else " ")
    return None if expected_closers else "".join(visible)


def _top_level_pattern_matches(
    text: str,
    pattern: re.Pattern[str],
) -> tuple[re.Match[str], ...]:
    """Return matches outside quotes/brackets; malformed nesting fails closed."""

    visible = _top_level_text(text)
    if visible is None:
        return ()
    return tuple(pattern.finditer(visible))


def _finite_endpoint_terminal_shape(fragment: str) -> bool:
    """Prove one balanced, punctuation-free finite clause tail."""

    visible = _top_level_text(fragment)
    if visible is None:
        return False
    value = visible.strip()
    return bool(
        value
        and value == fragment.strip()
        and re.search(r"[、,.!?！？]", value) is None
        and _FINITE_ENDPOINT_TERMINAL_RE.search(value) is not None
    )


def _operator_surface_is_finite(
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Prove that the frozen match itself is a complete finite predicate."""

    if not operator_surface or operator_pattern is None:
        return False
    if operator_pattern is _FEELING_RE:
        return operator_surface == "重い"
    if operator_pattern is _HELP_SEEKING_RE:
        return False
    if operator_pattern is _CHANGE_RE:
        return bool(
            re.fullmatch(
                r"(?:になった|くなった|減った|増えた|戻った|進んだ|進めた)",
                operator_surface,
            )
        )
    if operator_pattern is _RELATION_UNCERTAINTY_RE:
        return bool(
            re.fullmatch(r"(?:迷う|よいか|いいか|べきか)", operator_surface)
        )
    if operator_pattern is _CONSTRAINT_RE:
        return bool(
            re.fullmatch(
                r"(?:できない|出来ない|"
                r"難し(?:い|かった|く(?:ない|なかった|"
                r"ありません(?:でした)?))|"
                r"しかない|作れない)",
                operator_surface,
            )
        )
    if operator_pattern is _UNCERTAIN_RE:
        return bool(
            re.fullmatch(
                r"(?:気がする|(?:と|とは)思(?:う|った|います|いました|"
                r"って(?:いる|いた|います|いました)|"
                r"ってき(?:た|ます|ました|ません|ませんでした|"
                r"ている|ていた|ています|ていました)|"
                r"い(?:始め|続け|終え)(?:る|た|ている|ていた|"
                r"てき(?:た|ます|ました|ません|ませんでした|"
                r"ている|ていた|ています|ていました)|"
                r"ます|ました))|"
                r"こうかな|かな|わからない|分からない)",
                operator_surface,
            )
        )
    if operator_pattern is _VALUE_RE:
        return bool(
            re.fullmatch(
                r"(?:意味がある|守りたい|良い|いい)",
                operator_surface,
            )
        )
    if operator_pattern is _OPEN_UNFINISHED_RE:
        return not operator_surface.endswith(("未定", "途中")) and bool(
            _finite_endpoint_terminal_shape(operator_surface)
        )
    if operator_pattern is _CONTINUATION_RE:
        return operator_surface.endswith(("続いた", "続く"))
    if operator_pattern is _NEGATION_RE:
        return operator_surface.endswith(
            ("ない", "なかった", "ません")
        )
    if operator_pattern is _POSITIVE_CHANGE_RE:
        return bool(_finite_endpoint_terminal_shape(operator_surface))
    return bool(_finite_endpoint_terminal_shape(operator_surface))


def _operator_supports_explanatory_na(
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Admit copular explanatory ``なのだ`` for a frozen nominal."""

    if operator_pattern is _FEELING_RE:
        return operator_surface in {"気持ち", "不安", "もやもや"}
    if operator_pattern is _VALUE_RE:
        return operator_surface in {"大切", "大事", "価値"}
    if operator_pattern is _CONSTRAINT_RE:
        return operator_surface in {"無理", "制約", "限界"}
    if operator_pattern is _RELATION_UNCERTAINTY_RE:
        return operator_surface == "迷い"
    if operator_pattern is _UNCERTAIN_RE:
        return operator_surface in {"憶測", "不明"}
    if operator_pattern is _OPEN_UNFINISHED_RE:
        return operator_surface.endswith(("未定", "途中"))
    if operator_pattern is _WISH_RE:
        return operator_surface.endswith(("気持ち", "願い", "つもり"))
    if operator_pattern is _POSITIVE_CHANGE_RE:
        return operator_surface in {"安心", "平穏", "幸せ", "達成"}
    if operator_pattern is _NEGATION_RE:
        return operator_surface in {"無理", "だめ", "ダメ"}
    return False


def _operator_supports_occurrence_na(
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Admit adnominal ``なこと`` only for na-adjectival operators."""

    if operator_pattern is _FEELING_RE:
        return operator_surface in {"不安", "もやもや"}
    if operator_pattern is _VALUE_RE:
        return operator_surface in {"大切", "大事"}
    if operator_pattern is _CONSTRAINT_RE:
        return operator_surface == "無理"
    if operator_pattern is _OPEN_UNFINISHED_RE:
        return operator_surface.endswith("未定")
    if operator_pattern is _POSITIVE_CHANGE_RE:
        return operator_surface in {"安心", "平穏", "幸せ"}
    if operator_pattern is _NEGATION_RE:
        return operator_surface in {"無理", "だめ", "ダメ"}
    return False


def _operator_supports_residue_link(
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
    link: str,
) -> bool:
    """Prove the operator-specific ``な/のまま`` attachment class."""

    if link == "な":
        return _operator_supports_occurrence_na(
            operator_surface,
            operator_pattern,
        )
    if link != "の":
        return False
    if operator_pattern is _FEELING_RE:
        return operator_surface in {"気持ち", "不安", "もやもや"}
    if operator_pattern is _VALUE_RE:
        return operator_surface in {"価値"}
    if operator_pattern is _CONSTRAINT_RE:
        return operator_surface in {"制約", "限界"}
    if operator_pattern is _RELATION_UNCERTAINTY_RE:
        return operator_surface == "迷い"
    if operator_pattern is _UNCERTAIN_RE:
        return operator_surface in {"憶測", "不明"}
    if operator_pattern is _OPEN_UNFINISHED_RE:
        return operator_surface.endswith(("未定", "途中"))
    if operator_pattern is _WISH_RE:
        return operator_surface.endswith(("気持ち", "願い", "つもり"))
    return False


def _operator_supports_semantic_subject(
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Prove that a frozen surface can head ``が/は/も + finite host``."""

    if operator_pattern is _FEELING_RE:
        return operator_surface in {"気持ち", "不安", "もやもや"}
    if operator_pattern is _VALUE_RE:
        return operator_surface == "価値"
    if operator_pattern is _CONSTRAINT_RE:
        return operator_surface in {"制約", "限界"}
    if operator_pattern is _RELATION_UNCERTAINTY_RE:
        return operator_surface == "迷い"
    if operator_pattern is _UNCERTAIN_RE:
        return operator_surface == "憶測"
    if operator_pattern is _OPEN_UNFINISHED_RE:
        return operator_surface.endswith(("未定", "途中"))
    if operator_pattern is _WISH_RE:
        return operator_surface.endswith(("気持ち", "願い"))
    if operator_pattern is _CHANGE_RE:
        return operator_surface in {"改善", "進歩"}
    if operator_pattern is _HELP_SEEKING_RE:
        return operator_surface in {"相談", "面談", "受診", "診察", "予約"}
    if operator_pattern is _POSITIVE_CHANGE_RE:
        return operator_surface in {"安心", "平穏", "幸せ", "達成"}
    return False


def _direct_finite_carrier_shape(
    carrier: str,
    *,
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Prove a carrier compatible with the matched operator conjugation."""

    if not carrier:
        return False
    operator_is_finite = _operator_surface_is_finite(
        operator_surface,
        operator_pattern,
    )
    if operator_is_finite:
        if operator_surface.endswith(("い", "かった")) and carrier == "です":
            return True
        return bool(
            operator_surface.endswith(("た", "だ"))
            and carrier == "りする"
        )
    if operator_surface.endswith(("て", "で")):
        return _FINITE_TE_AUXILIARY_CARRIER_RE.fullmatch(carrier) is not None
    if _FINITE_COPULAR_CARRIER_RE.fullmatch(carrier) is not None:
        return _operator_supports_explanatory_na(
            operator_surface,
            operator_pattern,
        )
    if operator_pattern is _HELP_SEEKING_RE:
        if operator_surface.endswith("求め"):
            return _FINITE_ICHIDAN_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith("もら"):
            return _FINITE_GODAN_W_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith(("口", "先")):
            return False
        return _FINITE_SAHEN_CARRIER_RE.fullmatch(carrier) is not None
    if operator_pattern is _ACTION_RE:
        if operator_surface == "決め":
            return _FINITE_ICHIDAN_CARRIER_RE.fullmatch(carrier) is not None
        return bool(
            operator_surface in {"行動", "記録", "メモ"}
            and _FINITE_SAHEN_CARRIER_RE.fullmatch(carrier) is not None
        )
    if operator_pattern is _CHANGE_RE:
        if operator_surface.endswith("変わ"):
            return _FINITE_GODAN_R_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface in {"改善", "進歩"}:
            return _FINITE_SAHEN_CARRIER_RE.fullmatch(carrier) is not None
        return False
    if operator_pattern is _FEELING_RE:
        if operator_surface.endswith("感じ"):
            return _FINITE_ICHIDAN_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith("落ち着"):
            return _FINITE_GODAN_K_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith("焦"):
            return _FINITE_GODAN_R_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith(("苦し", "悲し")):
            return bool(
                _FINITE_GODAN_M_CARRIER_RE.fullmatch(carrier)
                or _FINITE_I_ADJECTIVE_CARRIER_RE.fullmatch(carrier)
            )
        if _operator_supports_explanatory_na(
            operator_surface,
            operator_pattern,
        ):
            return False
        if operator_surface in {"寂", "嬉", "うれ"}:
            return (
                _FINITE_SHII_ADJECTIVE_CARRIER_RE.fullmatch(carrier)
                is not None
            )
        return _FINITE_I_ADJECTIVE_CARRIER_RE.fullmatch(carrier) is not None
    if operator_pattern is _RELATION_UNCERTAINTY_RE:
        if operator_surface.endswith("迷い"):
            return re.fullmatch(
                r"(?:ます|ました|ません|ませんでした|"
                + _FINITE_ASPECT_HOST_SOURCE
                + r")",
                carrier,
            ) is not None
        if operator_surface.endswith("ためら"):
            return _FINITE_GODAN_W_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith("気がし"):
            return (
                _FINITE_SURU_RENYOKEI_CARRIER_RE.fullmatch(carrier)
                is not None
            )
        if operator_surface.endswith("自信がな"):
            return _FINITE_I_ADJECTIVE_CARRIER_RE.fullmatch(carrier) is not None
        return False
    if operator_pattern is _UNCERTAIN_RE:
        return bool(
            operator_surface.endswith("かもしれ")
            and re.fullmatch(
                r"(?:ない|なかった|ません|ませんでした)",
                carrier,
            )
            is not None
        )
    if operator_pattern is _WISH_RE:
        return bool(
            operator_surface.endswith("願")
            and _FINITE_GODAN_W_CARRIER_RE.fullmatch(carrier) is not None
        )
    if operator_pattern is _VALUE_RE:
        if operator_surface == "良く":
            return re.fullmatch(
                r"(?:ない|なかった|ありません(?:でした)?)",
                carrier,
            ) is not None
        return bool(
            operator_surface in {"好まし", "望まし"}
            and _FINITE_I_ADJECTIVE_CARRIER_RE.fullmatch(carrier) is not None
        )
    if operator_pattern is _POSITIVE_CHANGE_RE:
        if operator_surface in {"嬉", "うれ"}:
            return (
                _FINITE_SHII_ADJECTIVE_CARRIER_RE.fullmatch(carrier)
                is not None
            )
        if operator_surface in {"安心", "達成"}:
            return _FINITE_SAHEN_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface == "喜び":
            return re.fullmatch(
                r"(?:ます|ました|ません|ませんでした|"
                + _FINITE_ASPECT_HOST_SOURCE
                + r")",
                carrier,
            ) is not None
        if operator_surface.endswith("ようにな"):
            return _FINITE_GODAN_R_CARRIER_RE.fullmatch(carrier) is not None
        return False
    if operator_pattern is _CONTINUATION_RE:
        if operator_surface.endswith("続け"):
            return _FINITE_ICHIDAN_CARRIER_RE.fullmatch(carrier) is not None
        if operator_surface.endswith("繰り返"):
            return _FINITE_GODAN_S_CARRIER_RE.fullmatch(carrier) is not None
        return False
    if operator_pattern is _REFUSAL_RE:
        if operator_surface == "拒否":
            return _FINITE_SAHEN_CARRIER_RE.fullmatch(carrier) is not None
        return bool(
            operator_surface == "拒"
            and _FINITE_GODAN_M_CARRIER_RE.fullmatch(carrier) is not None
        )
    if operator_pattern is _CONSTRAINT_RE:
        return bool(
            operator_surface.endswith("得")
            and _FINITE_ICHIDAN_CARRIER_RE.fullmatch(carrier) is not None
        )
    return False


def _adnominal_finite_carrier_shape(
    carrier: str,
    *,
    operator_surface: str,
    operator_pattern: re.Pattern[str] | None,
) -> bool:
    """Prove a direct carrier that may grammatically precede a wrapper."""

    if re.search(
        r"(?:です|でした|ます|ました|ません|ませんでした)$",
        carrier,
    ) or carrier == "だ":
        return False
    return _direct_finite_carrier_shape(
        carrier,
        operator_surface=operator_surface,
        operator_pattern=operator_pattern,
    )


def _finite_endpoint_carrier_shape(
    carrier: str,
    *,
    operator_surface: str = "",
    operator_pattern: re.Pattern[str] | None = None,
) -> bool:
    """Prove a bounded carrier after an existing frozen operator.

    The proof has fixed depth: direct inflection, optional explanatory
    wrapper, or one grammatical host (occurrence, residue, semantic subject).
    It never recurses and never accepts an arbitrary predicate between the
    frozen operator and the finite endpoint.
    """

    value = carrier.strip()
    if not value or value != carrier or re.search(r"[、,.!?！？]", value):
        return False
    operator_is_finite = _operator_surface_is_finite(
        operator_surface,
        operator_pattern,
    )

    explanatory = _FINITE_ENDPOINT_EXPLANATORY_RE.fullmatch(value)
    if explanatory is not None:
        base = explanatory.group("base")
        if (
            (not base and operator_is_finite)
            or (
                base == "な"
                and _operator_supports_explanatory_na(
                    operator_surface,
                    operator_pattern,
                )
            )
            or _adnominal_finite_carrier_shape(
                base,
                operator_surface=operator_surface,
                operator_pattern=operator_pattern,
            )
        ):
            return True

    if _direct_finite_carrier_shape(
        value,
        operator_surface=operator_surface,
        operator_pattern=operator_pattern,
    ):
        return True

    occurrence = re.fullmatch(
        r"(?P<base>.*?)こと(?:は|が|も)?"
        r"(?P<host>ある|あった|あります|ありました|"
        r"ない|なかった|ありません|ありませんでした)"
        r"(?P<explain>(?:の|ん)(?:だ|です|だった|でした))?",
        value,
    )
    if occurrence is not None:
        base = occurrence.group("base")
        if (
            (not base and operator_is_finite)
            or (
                base == "な"
                and _operator_supports_occurrence_na(
                    operator_surface,
                    operator_pattern,
                )
            )
            or _adnominal_finite_carrier_shape(
                base,
                operator_surface=operator_surface,
                operator_pattern=operator_pattern,
            )
        ):
            return True

    residue = _FINITE_ENDPOINT_RESIDUE_HOST_RE.fullmatch(value)
    if residue is not None:
        base = residue.group("base")
        link = residue.group("link")
        if (
            (not base and not link and operator_is_finite)
            or (
                not base
                and bool(link)
                and _operator_supports_residue_link(
                    operator_surface,
                    operator_pattern,
                    link,
                )
            )
            or (
                bool(base)
                and not link
                and _adnominal_finite_carrier_shape(
                    base,
                    operator_surface=operator_surface,
                    operator_pattern=operator_pattern,
                )
            )
        ):
            return True

    semantic_subject = re.fullmatch(
        r"(?:は|が|も)(?P<host>.+)",
        value,
    )
    subject_capable = _operator_supports_semantic_subject(
        operator_surface,
        operator_pattern,
    )
    if subject_capable and _self_owned_finite_host_shape(value):
        return True
    return bool(
        semantic_subject is not None
        and subject_capable
        and (
            _FINITE_SEMANTIC_SUBJECT_HOST_RE.fullmatch(
                semantic_subject.group("host")
            )
            is not None
            or (
                operator_surface.endswith(("気持ち", "願い"))
                and _FINITE_WISH_EXISTENCE_HOST_RE.fullmatch(
                    semantic_subject.group("host")
                )
                is not None
            )
        )
    )


def _self_owned_finite_host_shape(carrier: str) -> bool:
    """Allow a semantic content topic only when its later owner is self."""

    self_host = re.fullmatch(
        r"(?:は|が|も|の)"
        r"(?:自分|私|わたし|僕|ぼく|俺|おれ)"
        r"(?:"
        r"にとって|には|は|が|も|の|"
        + _OWNER_FOCUS_PARTICLE_SOURCE
        + r"(?:は|が|も)?|"
        + _OWNER_TOPIC_PARTICLE_SOURCE
        + r")(?P<host>.+)",
        carrier,
    )
    if self_host is None:
        return False
    host = self_host.group("host")
    if not _finite_endpoint_terminal_shape(host):
        return False

    # A self marker proves only the owner, not an arbitrary predicate that
    # follows it.  Close the host through one already-frozen operator and its
    # direct inflectional carrier.  Keeping the proof direct also prevents a
    # second, later owner from borrowing the self marker through recursion.
    direct_operator_host = any(
        match.start() == 0
        and (
            (
                match.end() == len(host)
                and _operator_surface_is_finite(match.group(0), pattern)
            )
            or _direct_finite_carrier_shape(
                host[match.end() :],
                operator_surface=match.group(0),
                operator_pattern=pattern,
            )
        )
        for pattern in _FINITE_OPERATOR_PATTERNS
        if pattern is not _OPEN_UNFINISHED_RE
        for match in pattern.finditer(host)
    )
    if direct_operator_host:
        return True

    # Source-local record/memo existence is the one non-predicative host
    # already admitted by the public matrix.  Its noun must itself be a
    # frozen action surface; a free lexical noun or later owner is rejected.
    action_existence = re.fullmatch(
        r"(?P<action>[^\s、,。.!！?？]+?)(?:に|には|にも)"
        r"(?:ある|あった|あります|ありました|"
        r"ない|なかった|ありません|ありませんでした)",
        host,
    )
    return bool(
        action_existence is not None
        and _ACTION_RE.fullmatch(action_existence.group("action"))
        is not None
        and re.fullmatch(
            r"[一-鿿々〆〇ァ-ヶー]+",
            action_existence.group("action"),
        )
        is not None
    )


_FINITE_OPERATOR_PATTERNS: Final = (
    _WISH_RE,
    _CONSTRAINT_RE,
    _RELATION_UNCERTAINTY_RE,
    _UNCERTAIN_RE,
    _REFUSAL_RE,
    _CHANGE_RE,
    _POSITIVE_CHANGE_RE,
    _FEELING_RE,
    _VALUE_RE,
    _HELP_SEEKING_RE,
    _OPEN_UNFINISHED_RE,
    _NEGATION_RE,
    _CONTINUATION_RE,
    _ACTION_RE,
)
_BOUNDED_OPERATOR_PREFIX_RE: Final = re.compile(
    r"^(?:"
    r"(?:自分|私|わたし|僕|ぼく|俺|おれ)"
    r"(?:にとって|には|は|が|も|の)|"
    r"(?:今日|昨日|明日|今|現在|今朝|午前|午後|夕方|"
    r"朝|昼|夜|以前|これまで)(?:は|も|の|には)?|"
    r"この記録では?|"
    r"もう少し|少し(?:だけ|ずつ)?|やや|ずっと|強く|まだ|なお"
    r")[、,\s]*"
)


def _operator_match_has_finite_closure(
    fragment: str,
    operator_pattern: re.Pattern[str],
    match: re.Match[str],
) -> bool:
    """Close a selected operator by its own finite form or typed carrier."""

    tail = fragment[match.end() :]
    if not tail:
        return _operator_surface_is_finite(match.group(0), operator_pattern)
    return _finite_endpoint_carrier_shape(
        tail,
        operator_surface=match.group(0),
        operator_pattern=operator_pattern,
    )


def _strip_bounded_operator_prefix(value: str) -> str:
    """Remove only frozen self/time/intensity prefixes, at fixed depth."""

    remainder = value
    for _index in range(4):
        match = _BOUNDED_OPERATOR_PREFIX_RE.match(remainder)
        if match is None or match.end() == 0:
            break
        remainder = remainder[match.end() :]
    return remainder


def _semantic_content_is_bounded(value: str, *, require_finite: bool) -> bool:
    """Prove one local semantic argument without lending it an opaque owner."""

    visible = _top_level_text(value)
    if visible is None:
        return False
    content = _strip_bounded_operator_prefix(visible.strip())
    if (
        not content
        or re.search(r"[、,.!?！？\s]", content)
        or re.fullmatch(r"[ぁ-んァ-ヶ一-鿿々〆〇ー]+", content)
        is None
    ):
        return False
    matches = tuple(
        (pattern, match)
        for pattern in _FINITE_OPERATOR_PATTERNS
        for match in pattern.finditer(content)
    )
    if not matches:
        return not require_finite
    if not require_finite:
        for pattern, match in matches:
            if not _operator_match_left_context_is_bounded(
                content,
                pattern,
                match,
                depth=1,
            ):
                continue
            if (
                match.end() == len(content)
                or _operator_match_has_finite_closure(
                    content,
                    pattern,
                    match,
                )
            ):
                return True
            nominalizer = re.search(
                r"(?:こと|気持ち|願い|わけ)$",
                content,
            )
            if nominalizer is not None:
                adnominal = content[: nominalizer.start()]
                if (
                    match.end() <= len(adnominal)
                    and _operator_match_has_finite_closure(
                        adnominal,
                        pattern,
                        match,
                    )
                ):
                    return True
        return False
    return any(
        _operator_match_left_context_is_bounded(
            content,
            pattern,
            match,
            depth=1,
        )
        and _operator_match_has_finite_closure(content, pattern, match)
        for pattern, match in matches
    )


def _operator_match_left_context_is_bounded(
    fragment: str,
    operator_pattern: re.Pattern[str],
    match: re.Match[str],
    *,
    depth: int = 0,
) -> bool:
    """Prove the selected endpoint's left context at fixed depth."""

    if match.start() == 0:
        return True
    prefix = fragment[: match.start()]
    unbound_prefix = _strip_bounded_operator_prefix(prefix)
    if not unbound_prefix:
        return True
    if re.fullmatch(
        r"[ぁ-んァ-ヶ一-鿿々〆〇ー]+",
        unbound_prefix,
    ) is None:
        return False
    if (
        operator_pattern is _NEGATION_RE
        and prefix.endswith(("てい", "でい"))
    ):
        positive_candidate = prefix + "る"
        frozen_positive = _last_finite_operator_match(
            positive_candidate,
            *(
                pattern
                for pattern in _FINITE_OPERATOR_PATTERNS
                if pattern is not _NEGATION_RE
            ),
        )
        if frozen_positive is not None:
            return True
        return False
    if match.group(0).startswith(("と", "とは")):
        return _semantic_content_is_bounded(prefix, require_finite=True)
    explicit_self_experiential = re.fullmatch(
        r"(?P<content>.+?)(?:と|とは)"
        r"(?:自分|私|わたし|僕|ぼく|俺|おれ)"
        r"(?:にとって|には|は|が|も|"
        + _OWNER_FOCUS_PARTICLE_SOURCE
        + r"(?:は|が|も)?)",
        prefix,
    )
    if explicit_self_experiential is not None:
        return _semantic_content_is_bounded(
            explicit_self_experiential.group("content"),
            require_finite=True,
        )
    if (
        prefix.endswith(("を", "と"))
        and (
            (
                operator_pattern is _FEELING_RE
                and match.group(0).endswith("感じ")
            )
            or operator_pattern in {_HELP_SEEKING_RE, _ACTION_RE}
        )
    ):
        return _semantic_content_is_bounded(
            prefix[:-1],
            require_finite=False,
        )
    if (
        operator_pattern is _OPEN_UNFINISHED_RE
        and prefix.endswith("かは")
    ):
        question_clause = prefix[:-2]
        return bool(
            _last_finite_operator_match(
                question_clause,
                *_FINITE_OPERATOR_PATTERNS,
            )
            is not None
            or re.fullmatch(
                r"[ぁ-んァ-ヶ一-鿿々〆〇ー]+する",
                question_clause,
            )
            is not None
        )
    if (
        depth == 0
        and operator_pattern in {_UNCERTAIN_RE, _RELATION_UNCERTAINTY_RE}
        and prefix.endswith("か")
    ):
        return any(
            relation_match.end() == len(prefix)
            and _operator_match_left_context_is_bounded(
                prefix,
                _RELATION_UNCERTAINTY_RE,
                relation_match,
                depth=1,
            )
            for relation_match in _RELATION_UNCERTAINTY_RE.finditer(prefix)
        )
    if (
        operator_pattern is _RELATION_UNCERTAINTY_RE
        and prefix.endswith(("て", "で"))
    ):
        action_core = _strip_bounded_operator_prefix(prefix[:-1])
        case_matches = tuple(
            re.finditer(r"を|に|へ|で|から|まで", action_core)
        )
        bounded_case_predicate = False
        if case_matches:
            last_case = case_matches[-1]
            argument = action_core[: last_case.start()]
            predicate_stem = action_core[last_case.end() :]
            bounded_case_predicate = bool(
                argument
                and predicate_stem
                and _semantic_content_is_bounded(
                    argument,
                    require_finite=False,
                )
                and re.search(
                    r"(?:[いきぎしじちぢにびぴみりっん]|"
                    r"[えけげせぜてでねへべぺめれ])$",
                    predicate_stem,
                )
                is not None
            )
        return bool(
            bounded_case_predicate
            or (
                re.fullmatch(
                    r"[一-鿿々〆〇]{1,4}し",
                    action_core,
                )
                is not None
                and not any(
                    embedded.start() != 0
                    for pattern in _FINITE_OPERATOR_PATTERNS
                    for embedded in pattern.finditer(action_core)
                )
            )
        )
    if operator_pattern is _WISH_RE:
        prior_matches = tuple(
            (pattern, prior_match)
            for pattern in _FINITE_OPERATOR_PATTERNS
            if pattern is not _WISH_RE
            for prior_match in pattern.finditer(prefix)
        )
        if match.group(0) == "願" and prefix.endswith("を"):
            return _semantic_content_is_bounded(
                prefix[:-1],
                require_finite=False,
            )
        action_host = _ACTION_ARGUMENT_STEM_RE.search(prefix)
        if action_host is not None:
            predicate_stem = action_host.group("predicate")
            desiderative_surface = match.group(0)
            return bool(
                action_host.start() > 0
                and action_host.end() == len(prefix)
                and _semantic_content_is_bounded(
                    prefix[: action_host.start()],
                    require_finite=False,
                )
                and re.search(
                    r"(?:は|が|も)",
                    predicate_stem,
                )
                is None
                and (
                    (
                        desiderative_surface.startswith("したい")
                        and re.search(r"[一-鿿々〆〇]", predicate_stem)
                    )
                    or (
                        desiderative_surface in {"ほしい", "欲しい"}
                        and predicate_stem.endswith(("て", "で"))
                    )
                    or (
                        not desiderative_surface.startswith("したい")
                        and desiderative_surface not in {"ほしい", "欲しい"}
                        and re.search(
                            r"[いきぎしじちぢにびぴみり"
                            r"えけげせぜてでねへべぺめれ]$",
                            predicate_stem,
                        )
                        is not None
                    )
                )
            )
        if match.group(0) in {"ほしい", "欲しい"}:
            # A registered operator may supply an exact te-form complement
            # to desiderative ``ほしい`` (for example 相談 + して + ほしい).
            # Reuse the operator's own conjugation proof by closing that
            # te-form with ``いる``; no free verb or phrase-family list is
            # introduced here.
            if any(
                _operator_match_left_context_is_bounded(
                    prefix,
                    prior_pattern,
                    prior_match,
                    depth=depth + 1,
                )
                and (
                    (
                        prior_match.end() == len(prefix)
                        and prior_match.group(0).endswith(("て", "で"))
                    )
                    or (
                        prior_match.end() < len(prefix)
                        and prefix[prior_match.end() :].endswith(("て", "で"))
                        and _direct_finite_carrier_shape(
                            prefix[prior_match.end() :] + "いる",
                            operator_surface=prior_match.group(0),
                            operator_pattern=prior_pattern,
                        )
                    )
                )
                for prior_pattern, prior_match in prior_matches
            ):
                return True
        if prior_matches:
            if any(
                prior_match.end() == len(prefix)
                and _operator_match_left_context_is_bounded(
                    prefix,
                    prior_pattern,
                    prior_match,
                    depth=depth + 1,
                )
                and _direct_finite_carrier_shape(
                    match.group(0),
                    operator_surface=prior_match.group(0),
                    operator_pattern=prior_pattern,
                )
                for prior_pattern, prior_match in prior_matches
            ):
                return True
            return False
        return bool(
            re.fullmatch(
                r"(?:[一-鿿々〆〇]|"
                r"[一-鿿々〆〇][ぁ-んァ-ヶー]+)",
                unbound_prefix,
            )
        )
    if (
        operator_pattern in {_CHANGE_RE, _POSITIVE_CHANGE_RE}
        and prefix.endswith("よう")
    ):
        return _semantic_content_is_bounded(
            prefix[:-2],
            require_finite=False,
        )
    return False


def _bounded_nominal_wish_endpoint(fragment: str) -> bool:
    """Prove a desiderative nominal plus one frozen finite subject host."""

    nominal_host = re.search(
        r"(?P<desiderative>.*?(?:したい|なりたい|ほしい|欲しい|たい))"
        r"(?P<nominal>気持ち|願い)"
        r"(?P<carrier>(?:(?:は|が|も|の).+|"
        r"だ|です|だった|でした))$",
        fragment,
    )
    if nominal_host is None:
        return False
    desiderative = nominal_host.group("desiderative")
    operator = desiderative + nominal_host.group("nominal")
    carrier = nominal_host.group("carrier")
    wish_matches = tuple(
        wish_match
        for wish_match in _WISH_RE.finditer(desiderative)
        if wish_match.end() == len(desiderative)
    )
    return bool(
        wish_matches
        and any(
            _operator_match_left_context_is_bounded(
                desiderative,
                _WISH_RE,
                wish_match,
            )
            for wish_match in wish_matches
        )
        and (
            _finite_endpoint_carrier_shape(
                carrier,
                operator_surface=operator,
                operator_pattern=_WISH_RE,
            )
            or _self_owned_finite_host_shape(carrier)
        )
    )


def _bounded_bare_wish_nominal(fragment: str) -> bool:
    """Prove an exact desiderative ``気持ち/願い`` relation endpoint."""

    nominal = re.fullmatch(
        r"(?P<desiderative>.+?(?:したい|なりたい|ほしい|欲しい|たい))"
        r"(?:気持ち|願い)",
        fragment,
    )
    if nominal is None:
        return False
    desiderative = nominal.group("desiderative")
    return any(
        wish_match.end() == len(desiderative)
        and _operator_match_left_context_is_bounded(
            desiderative,
            _WISH_RE,
            wish_match,
        )
        for wish_match in _WISH_RE.finditer(desiderative)
    )


def _bounded_ambiguous_nominal_state(fragment: str) -> bool:
    """Keep the existing m-row/simile ambiguity as a neutral nominal only."""

    core = _strip_bounded_operator_prefix(fragment)
    return bool(
        core
        and re.fullmatch(
            r"[ぁ-んァ-ヶ一-鿿々〆〇ー]+"
            r"(?<![てで])みたい(?:気持ち|願い)",
            core,
        )
        is not None
    )


def _bounded_structural_action_endpoint(fragment: str) -> bool:
    """Prove an owner-local open action by case frame plus perfective tail."""

    visible = _top_level_text(fragment)
    if visible is None:
        return False
    value = _strip_bounded_operator_prefix(visible.strip())
    argument_match = _ACTION_ARGUMENT_STEM_RE.search(value)
    return bool(
        value
        and argument_match is not None
        and argument_match.start() > 0
        and argument_match.end() == len(value)
        and _EXPLICIT_PERFECTIVE_END_RE.search(value) is not None
        and re.search(r"[、,.!?！？\s]", value) is None
        and re.search(r"(?:は|が|も)", argument_match.group("predicate")) is None
    )


def _last_finite_operator_match(
    fragment: str,
    *patterns: re.Pattern[str],
) -> re.Match[str] | None:
    """Return the last frozen operator closed by only finite carriers."""

    visible = _top_level_text(fragment)
    if visible is None:
        return None
    value = visible.strip()
    if not value or value != fragment.strip():
        return None
    matches = tuple(
        match
        for pattern in patterns
        for match in pattern.finditer(value)
        if _operator_match_left_context_is_bounded(value, pattern, match)
        and _operator_match_has_finite_closure(value, pattern, match)
    )
    return max(matches, key=lambda match: (match.end(), match.start())) if matches else None


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or ():
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _span_number(span_id: str) -> tuple[int, str]:
    value = _clean(span_id)
    match = _EVIDENCE_ID_RE.fullmatch(value)
    return (int(value[1:]), value) if match else (10**9, value)


def _ordered_span_ids(values: Iterable[Any]) -> list[str]:
    return sorted(_dedupe(values), key=_span_number)


def _compact(value: Any) -> str:
    return _PUNCT_SPACE_RE.sub("", _clean(value)).lower()


def _is_body_free_code(value: Any) -> bool:
    return bool(_BODY_FREE_CODE_RE.fullmatch(_clean(value)))


def _clamp(value: Any, lower: float = 0.0, upper: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = lower
    return max(lower, min(upper, number))


def _retention_max(left: Retention, right: Retention) -> Retention:
    return left if _RETENTION_RANK[left] >= _RETENTION_RANK[right] else right


def _is_pure_relation_marker(span: EvidenceSpan) -> bool:
    return _clean(getattr(span, "raw_text", "")) in _PURE_RELATION_MARKERS


def _text_spans(spans: Sequence[EvidenceSpan]) -> list[EvidenceSpan]:
    return [span for span in spans if _clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS]


def _sort_spans(spans: Sequence[EvidenceSpan]) -> list[EvidenceSpan]:
    field_order = {"memo": 0, "memo_action": 1, "emotion_details": 2, "emotions": 3, "category": 4}
    return sorted(
        list(spans or ()),
        key=lambda span: (
            field_order.get(_clean(getattr(span, "source_field", "")), 9),
            int(getattr(span, "start_index", -1)) if int(getattr(span, "start_index", -1)) >= 0 else 10**9,
            _span_number(_clean(getattr(span, "span_id", ""))),
        ),
    )


def _time_scope_for_text(text: str) -> str:
    has_past = bool(_PAST_RE.search(text))
    has_present = bool(_PRESENT_RE.search(text))
    has_future = bool(_FUTURE_RE.search(text))
    if has_past and has_present:
        return "past_to_present"
    if has_present and has_future:
        return "present_to_future"
    if has_past:
        return "past"
    if has_future:
        return "future"
    if has_present:
        return "present"
    if _CONTINUATION_RE.search(text):
        return "continuing"
    return "current_input"


def _operator_codes_for_text(text: str, *, source_field: str = "") -> tuple[str, ...]:
    checks: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("operator:positive_change", _POSITIVE_CHANGE_RE),
        ("operator:feeling", _FEELING_RE),
        ("operator:wish", _WISH_RE),
        ("operator:refusal", _REFUSAL_RE),
        ("operator:uncertainty", _UNCERTAIN_RE),
        ("operator:constraint", _CONSTRAINT_RE),
        ("operator:change", _CHANGE_RE),
        ("operator:value", _VALUE_RE),
        ("operator:contrast", _CONTRAST_RE),
        ("operator:coexistence", _COEXISTENCE_RE),
        ("operator:cause", _CAUSE_RE),
        ("operator:result", _RESULT_RE),
        ("operator:shift", _SHIFT_RE),
        ("operator:continuation", _CONTINUATION_RE),
    )
    # ``かもしれない`` carries uncertainty, not negative polarity.  Remove
    # only that neutral uncertainty suffix before evaluating negation; an
    # explicit negative claim such as ``できないかもしれない`` still keeps
    # the preceding ``できない`` operator.
    negation_scope = _NON_NEGATING_UNCERTAINTY_RE.sub("", text)
    negation_scope = _NON_NEGATING_CONTRAST_RE.sub("", negation_scope)
    values = ["operator:negation"] if _NEGATION_RE.search(negation_scope) else []
    # The suffix in a simile such as ``鉛みたい`` is not the desiderative
    # ``たい``.  Let the wish detector see a scope with that exact hiragana
    # form removed; kanji forms such as ``見たい`` remain available.
    wish_scope = _SIMILE_NOT_WISH_RE.sub("", text)
    values.extend(
        code
        for code, pattern in checks
        if pattern.search(wish_scope if code == "operator:wish" else text)
    )
    if is_bounded_self_denial_text(text) or (
        source_field != "memo_action"
        and _BOUNDED_NON_DENIAL_SELF_EVALUATION_RE.search(text)
    ):
        values.append("operator:self_evaluation")
    if source_field == "memo_action" or _ACTION_RE.search(text):
        values.append("operator:action")
    if _HELP_SEEKING_RE.search(text):
        values.append("operator:help_seeking")
    return tuple(_dedupe(values))


def _clause_signals(span: EvidenceSpan, *, kind: NucleusKind) -> _ClauseSignals:
    text = _clean(getattr(span, "raw_text", ""))
    source_field = _clean(getattr(span, "source_field", ""))
    operators = _operator_codes_for_text(text, source_field=source_field)
    operator_set = set(operators)

    negative = "operator:negation" in operator_set or "operator:refusal" in operator_set
    positive = "operator:positive_change" in operator_set or "operator:value" in operator_set
    if negative and positive and "operator:contrast" in operator_set:
        polarity: Literal["positive", "negative", "mixed", "neutral"] = "mixed"
    elif negative:
        polarity = "negative"
    elif positive:
        polarity = "positive"
    elif kind in {"reaction", "constraint", "self_evaluation"}:
        polarity = "negative"
    elif kind in {"value", "wish"}:
        polarity = "positive"
    else:
        polarity = "neutral"

    if "operator:refusal" in operator_set:
        modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"] = "refusal"
    elif "operator:wish" in operator_set:
        modality = "wish"
    elif "operator:uncertainty" in operator_set:
        modality = "uncertain"
    elif kind in {"reaction", "self_evaluation"} or "operator:feeling" in operator_set:
        modality = "feeling"
    elif kind == "constraint" or "operator:constraint" in operator_set:
        modality = "possibility"
    elif source_field == "memo_action" and not re.search(r"(?:した|していった|見た|書いた|記録した|メモした|作った)", text):
        modality = "intention"
    else:
        modality = "fact"

    return _ClauseSignals(
        polarity=polarity,
        modality=modality,
        time_scope=_time_scope_for_text(text),
        operator_codes=operators,
    )


def _nearest_substantive_span(
    spans: Sequence[EvidenceSpan],
    start: int,
    step: int,
) -> EvidenceSpan | None:
    index = start
    while 0 <= index < len(spans):
        span = spans[index]
        if _is_substantive_text_span(span) and not _is_pure_relation_marker(span):
            return span
        index += step
    return None


def _arc_roles_by_span(spans: Sequence[EvidenceSpan]) -> dict[str, tuple[str, ...]]:
    """Classify major semantic turns without using event or fixture nouns.

    Roles are body-free codes attached to existing Evidence spans.  They
    decide which endpoints must survive compression; they do not prescribe a
    completed sentence or create a parallel Evidence system.
    """

    roles: dict[str, list[str]] = {}

    def add(span: EvidenceSpan | None, role: str) -> None:
        if span is None:
            return
        span_id = _clean(getattr(span, "span_id", ""))
        if span_id:
            roles.setdefault(span_id, []).append(role)

    ordered = _sort_spans(_text_spans(spans))
    by_field: dict[str, list[EvidenceSpan]] = {}
    for span in ordered:
        by_field.setdefault(_clean(getattr(span, "source_field", "")), []).append(span)

    for field_name, field_spans in by_field.items():
        substantive = [
            span
            for span in field_spans
            if _is_substantive_text_span(span) and not _is_pure_relation_marker(span)
        ]
        if not substantive:
            continue

        if field_name == "memo_action":
            scored: list[tuple[int, int, EvidenceSpan]] = []
            for order, span in enumerate(substantive):
                text = _clean(getattr(span, "raw_text", ""))
                operators = set(_operator_codes_for_text(text, source_field=field_name))
                score = 1
                if _COMPLETED_ACTION_RE.search(text):
                    score += 5
                if operators & {"operator:positive_change", "operator:change", "operator:result"}:
                    score += 6
                if "operator:action" in operators:
                    score += 3
                if "operator:uncertainty" in operators:
                    score -= 2
                scored.append((score, order, span))
            # A separate action field is supporting evidence, not a replacement
            # for the memo arc.  Select its strongest source-bound action once.
            representative = max(scored, key=lambda item: (item[0], -item[1]))[2]
            add(representative, "semantic_role:concrete_action_evidence")
            continue

        for index, span in enumerate(field_spans):
            text = _clean(getattr(span, "raw_text", ""))
            if _is_pure_relation_marker(span):
                previous = _nearest_substantive_span(field_spans, index - 1, -1)
                following = _nearest_substantive_span(field_spans, index + 1, 1)
                add(previous, "semantic_role:contrast_before")
                add(following, "semantic_role:contrast_after")
                continue
            if not _is_substantive_text_span(span):
                continue

            operators = set(_operator_codes_for_text(text, source_field=field_name))
            if _LEADING_CONTRAST_RE.search(text):
                add(_nearest_substantive_span(field_spans, index - 1, -1), "semantic_role:contrast_before")
                add(span, "semantic_role:contrast_after")
            elif "operator:contrast" in operators:
                # The ledger can keep both sides of a local turn in one span.
                # That source span is mandatory, but it is not split or
                # interpreted through fixture vocabulary.
                add(span, "semantic_role:embedded_turn")

            if operators & {"operator:positive_change", "operator:change"} or _ACHIEVEMENT_RE.search(text):
                add(span, "semantic_role:current_change")
            if "operator:result" in operators:
                add(span, "semantic_role:explicit_result")
            if _EXPLICIT_EVALUATION_RE.search(text):
                add(span, "semantic_role:explicit_evaluation")
            if "operator:wish" in operators:
                add(span, "semantic_role:retained_intention")
            if "operator:refusal" in operators:
                add(span, "semantic_role:protective_or_limiting_refusal")
            if _LIMITING_UNKNOWN_RE.search(text):
                add(span, "semantic_role:limiting_unknown")
            if _PROVISIONAL_EVALUATION_RE.search(text):
                add(span, "semantic_role:provisional_evaluation")
            if _COMPLETED_ACTION_RE.search(text):
                add(span, "semantic_role:concrete_action")

        major_ids = {
            span_id
            for span_id, span_roles in roles.items()
            if any(
                role
                in {
                    "semantic_role:contrast_before",
                    "semantic_role:contrast_after",
                    "semantic_role:embedded_turn",
                    "semantic_role:current_change",
                    "semantic_role:explicit_result",
                    "semantic_role:explicit_evaluation",
                    "semantic_role:retained_intention",
                    "semantic_role:protective_or_limiting_refusal",
                    "semantic_role:limiting_unknown",
                    "semantic_role:provisional_evaluation",
                    "semantic_role:concrete_action",
                }
                for role in span_roles
            )
        }
        if len(substantive) >= 4 and major_ids:
            first = substantive[0]
            add(first, "semantic_role:initial_condition")

    role_sets = {span_id: set(values) for span_id, values in roles.items()}
    for field_spans in by_field.values():
        for index, span in enumerate(field_spans):
            span_id = _clean(getattr(span, "span_id", ""))
            if "semantic_role:contrast_after" not in role_sets.get(span_id, set()):
                continue
            previous = _nearest_substantive_span(field_spans, index - 1, -1)
            previous_id = _clean(getattr(previous, "span_id", "")) if previous else ""
            if "semantic_role:provisional_evaluation" in role_sets.get(previous_id, set()):
                add(span, "semantic_role:counterevidence")

    return {span_id: tuple(_dedupe(values)) for span_id, values in roles.items()}


def _is_substantive_text_span(span: EvidenceSpan) -> bool:
    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    if _is_pure_relation_marker(span):
        return False
    compact = _compact(getattr(span, "raw_text", ""))
    if not compact or _TRULY_LIMITED_TEXT_RE.fullmatch(compact):
        return False
    return len(compact) >= 4 or bool(
        _operator_codes_for_text(
            _clean(getattr(span, "raw_text", "")),
            source_field=_clean(getattr(span, "source_field", "")),
        )
    )


def _is_structural_self_denial_span(span: EvidenceSpan) -> bool:
    """Use the safety owner's bounded case/dependency classification."""

    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    return is_bounded_self_denial_text(getattr(span, "raw_text", ""))


def _is_input_grounded_refusal_span(span: EvidenceSpan) -> bool:
    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    text = _clean(getattr(span, "raw_text", ""))
    operators = set(
        _operator_codes_for_text(
            text,
            source_field=_clean(getattr(span, "source_field", "")),
        )
    )
    return bool(
        "operator:refusal" in operators
        or ({"operator:continuation", "operator:negation"} <= operators)
    )


def _canonicalize_safety_decision(
    base_decision: EmlisSafetyTriageDecision,
    spans: Sequence[EvidenceSpan],
    *,
    authoritative_self_denial: bool,
) -> EmlisSafetyTriageDecision:
    """Keep emergency ownership and derive non-emergency self-denial structurally.

    The public triage remains a separate safety owner.  For this shadow plan,
    a triage hit is not enough by itself: the current Evidence spans must
    contain a self-referential negative evaluation.  This keeps fixture phrases
    and expression-difficulty false positives from deciding the canonical
    family while preserving emergency ownership.
    """

    if base_decision.safety_triage_kind in {
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }:
        return base_decision

    ordered_text = _sort_spans(_text_spans(spans))
    self_denial_spans = [span for span in ordered_text if _is_structural_self_denial_span(span)]
    refusal_spans = [span for span in ordered_text if _is_input_grounded_refusal_span(span)]
    if not self_denial_spans and not (
        authoritative_self_denial
        and base_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    ):
        return EmlisSafetyTriageDecision()

    evidence_ids = _ordered_span_ids(
        [
            *[_clean(getattr(span, "span_id", "")) for span in self_denial_spans],
            *[_clean(getattr(span, "span_id", "")) for span in refusal_spans],
            *(
                list(getattr(base_decision, "evidence_span_ids", ()) or ())
                if authoritative_self_denial
                else []
            ),
        ]
    )
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    source_fields = _dedupe(
        _clean(getattr(span_index[span_id], "source_field", ""))
        for span_id in evidence_ids
        if span_id in span_index
    )
    self_denial_ids = {
        _clean(getattr(span, "span_id", "")) for span in self_denial_spans
    }
    refusal_ids = {
        _clean(getattr(span, "span_id", "")) for span in refusal_spans
    }
    # A limited opposition is only grounded when a distinct source span adds a
    # continuation/refusal statement.  A single self-denial sentence may still
    # receive the fact boundary and evidence-bound follow, but no opposition is
    # invented from the same clause.
    continuation_refusal = bool(refusal_ids - self_denial_ids)
    reason_codes = ["self_denial_structure_non_emergency"]
    if continuation_refusal:
        reason_codes.append("input_grounded_continuation_refusal")
    return EmlisSafetyTriageDecision(
        safety_triage_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        response_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        normal_observation_allowed=False,
        safe_state_answer_allowed=True,
        public_emlis_observation_allowed=True,
        public_input_feedback_allowed=True,
        requires_separate_safety_surface=False,
        blocked_reason=None,
        must_not_accept_identity_claim_as_fact=True,
        continuation_refusal_detected=continuation_refusal,
        reason_codes=reason_codes,
        boundary_types=[],
        evidence_span_ids=evidence_ids,
        source_fields=source_fields,
        source="grounded_structural_overlay",
    )


def _relation_type_for_pair(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    *,
    source_text: str,
    explicit_marker_text: str = "",
) -> RelationKind:
    left_ops = set(left.semantic_frame.attribute_codes)
    right_ops = set(right.semantic_frame.attribute_codes)
    combined_ops = left_ops | right_ops
    marker_text = _clean(explicit_marker_text)
    marker_ops = set(_operator_codes_for_text(marker_text)) if marker_text else set()
    left_roles = {code for code in left_ops if code.startswith("semantic_role:")}
    right_roles = {code for code in right_ops if code.startswith("semantic_role:")}

    if (
        left.kind == "self_evaluation"
        and right.semantic_frame.modality == "refusal"
    ) or (
        right.kind == "self_evaluation"
        and left.semantic_frame.modality == "refusal"
    ):
        return "continuation_or_refusal"
    if "operator:continuation" in combined_ops and (
        right.semantic_frame.modality == "refusal"
        or right.semantic_frame.polarity == "negative"
    ):
        return "continuation_or_refusal"
    if (
        "semantic_role:provisional_evaluation" in left_roles
        and "semantic_role:counterevidence" in right_roles
        and "operator:contrast" in marker_ops
    ):
        return "preserves_despite"
    if right.semantic_frame.modality == "refusal":
        if left.kind in {"wish", "action"}:
            return "attempt_and_block"
        return "coexistence"
    if {left.kind, right.kind} == {"wish", "constraint"}:
        return "wish_and_constraint"
    if (
        "semantic_role:concrete_action_evidence" in right_roles
        and (
            "semantic_role:retained_intention" in left_roles
            or "semantic_role:current_change" in left_roles
        )
    ):
        return "action_supports_change"
    if "operator:cause" in marker_ops:
        return "user_stated_cause"
    if "operator:result" in marker_ops and "operator:shift" not in marker_ops:
        return "user_stated_result"
    if "operator:coexistence" in marker_ops:
        return "coexistence"
    if "operator:contrast" in marker_ops:
        if (
            left.semantic_frame.polarity == "negative"
            and right.semantic_frame.polarity in {"positive", "mixed"}
        ):
            return "preserves_despite"
        return "contrast"
    explicit_shift = bool(
        _EXPLICIT_SHIFT_FROM_RE.search(_clean(source_text))
        and (
            _EXPLICIT_SHIFT_TO_RE.search(_clean(source_text))
            or "semantic_role:current_change" in right_roles
        )
    )
    if explicit_shift or (
        left.semantic_frame.time_scope in {"past", "past_to_present"}
        and right.semantic_frame.time_scope in {"present", "future", "present_to_future"}
    ):
        return "shift_from_to"
    if {left.kind, right.kind} & {"action"} and {left.kind, right.kind} & {"change", "wish"}:
        return "action_supports_change"
    if left.kind == "self_evaluation" and right.kind in {"state", "conclusion", "change", "value"}:
        return "self_evaluation_about_state"
    return "uncertain_connection"


def _relation_grounding_kind_for_pair(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    *,
    relation_type: RelationKind,
    source_text: str,
    explicit_marker_text: str = "",
) -> GroundingKind:
    """Separate source-stated relations from adjacency-only inference.

    The canonical plan may use source order to retain a bounded connection, but
    that alone must not make the relation required.  A relation is promoted to
    ``user_stated_relation`` only when the current clauses contain the matching
    structural operator or endpoint modalities.  No event noun or fixture text
    participates in this decision.
    """

    endpoint_operators = set(left.semantic_frame.attribute_codes) | set(right.semantic_frame.attribute_codes)
    marker_text = _clean(explicit_marker_text)
    marker_operators = set(_operator_codes_for_text(marker_text)) if marker_text else set()
    if relation_type == "continuation_or_refusal" and (
        "operator:continuation" in endpoint_operators
        or (
            "operator:refusal" in endpoint_operators
            and {left.kind, right.kind} & {"self_evaluation", "state", "conclusion"}
        )
    ):
        return "user_stated_relation"
    if relation_type in {"contrast", "preserves_despite"} and "operator:contrast" in marker_operators:
        return "user_stated_relation"
    if relation_type == "coexistence" and "operator:coexistence" in marker_operators:
        return "user_stated_relation"
    if relation_type == "user_stated_cause" and "operator:cause" in marker_operators:
        return "user_stated_relation"
    if relation_type == "user_stated_result" and "operator:result" in marker_operators:
        return "user_stated_relation"
    if relation_type == "shift_from_to" and (
        _EXPLICIT_SHIFT_FROM_RE.search(_clean(source_text))
        or "operator:shift" in marker_operators
    ):
        return "user_stated_relation"
    if relation_type == "wish_and_constraint" and {
        "operator:wish",
        "operator:constraint",
    } <= endpoint_operators:
        return "user_stated_relation"
    if relation_type == "attempt_and_block" and "operator:refusal" in endpoint_operators:
        return "user_stated_relation"
    return "bounded_structural_inference"


def _structural_role_for_span(span: EvidenceSpan) -> str:
    """Return a source-bound role from operators, never from example nouns."""

    text = _clean(getattr(span, "raw_text", ""))
    source_field = _clean(getattr(span, "source_field", ""))
    operators = set(_operator_codes_for_text(text, source_field=source_field))
    if source_field == "memo_action" or "operator:action" in operators:
        return "action"
    if "operator:self_evaluation" in operators:
        return "self_evaluation"
    if {"operator:wish", "operator:constraint"} <= operators:
        return "wish_constraint"
    if "operator:wish" in operators:
        return "wish"
    if "operator:constraint" in operators:
        return "constraint"
    if "operator:change" in operators or "operator:positive_change" in operators:
        return "change"
    if "operator:feeling" in operators:
        return "state"
    if _clean(getattr(span, "detected_type", "")) == "relation_marker":
        return "relation"
    return "current_expression"


def _build_meaning_artifacts(
    normalized_input: Mapping[str, Any],
    spans: Sequence[EvidenceSpan],
) -> _MeaningArtifacts:
    """Build structure/operator based MeaningBlock provenance for the shadow plan.

    The production ``emlis_ai_input_meaning_block_service`` still owns the
    pre-I5 public path.  The canonical shadow path builds directly from the
    authoritative Evidence Ledger so source offsets, real Evidence IDs, and
    relation endpoints remain the single provenance truth without another
    adapter boundary.
    """

    evidence_ref = EvidenceRef(
        kind="current_input",
        ref_id=_clean(normalized_input.get("id")) or "request_local_current_input",
        weight=1.0,
        note="i2_structural_meaning_adapter",
    )
    text_spans = [
        span
        for span in _sort_spans(_text_spans(spans))
        if _is_substantive_text_span(span)
    ]
    blocks: list[InputMeaningBlock] = []
    must_keep_keys: list[str] = []
    should_keep_keys: list[str] = []
    optional_keys: list[str] = []
    arc_roles_by_span = _arc_roles_by_span(spans)

    for order, span in enumerate(text_spans):
        span_id = _clean(getattr(span, "span_id", ""))
        role = _structural_role_for_span(span)
        arc_roles = set(arc_roles_by_span.get(span_id, ()))
        block_key = f"meaning:{order}:{role}"
        priority = 0.92 if arc_roles else 0.72
        blocks.append(
            InputMeaningBlock(
                block_key=block_key,
                role=role,
                title=f"source_bound:{role}",
                summary=_clean(getattr(span, "raw_text", "")),
                user_phrases=[],
                evidence=[evidence_ref],
                priority=priority,
                clarity=_clamp(getattr(span, "confidence", 0.0)),
                include_in_emlis_reply=True,
                include_in_piece_core=False,
            )
        )
        if arc_roles:
            must_keep_keys.append(block_key)
        elif role in {"action", "change", "wish", "constraint", "self_evaluation"}:
            should_keep_keys.append(block_key)
        else:
            optional_keys.append(block_key)

    text_length = sum(len(_compact(getattr(span, "raw_text", ""))) for span in text_spans)
    clear_long_input = text_length >= 180 or len(blocks) >= 6
    input_level = "long" if clear_long_input else "short" if len(blocks) <= 2 else "medium"
    if blocks and not must_keep_keys:
        must_keep_keys.append(blocks[0].block_key)
    selected_keys = [block.block_key for block in blocks]
    required_roles = _dedupe(
        block.role
        for block in blocks
        if block.block_key in set(must_keep_keys)
    )
    coverage = MeaningCoveragePlan(
        input_level=input_level,
        clear_long_input=clear_long_input,
        meaning_block_count=len(blocks),
        required_roles=list(required_roles),
        selected_block_keys=selected_keys,
        min_blocks_to_cover=len(must_keep_keys),
        max_blocks_to_cover=len(blocks),
        coverage_ratio_target=1.0 if clear_long_input else 0.8,
        reason="structure_operator_and_source_anchor_coverage",
    )
    arc = WholeInputMeaningArc(
        arc_key="whole_input:source_order",
        title="source_order_arc",
        summary="",
        ordered_block_keys=selected_keys,
        tension_pairs=[],
        core_wish_keys=[block.block_key for block in blocks if block.role == "wish"],
        fear_keys=[block.block_key for block in blocks if block.role in {"constraint", "state"}],
        present_action_keys=[block.block_key for block in blocks if block.role == "action"],
        clarity=0.86 if blocks else 0.0,
        evidence=[evidence_ref],
    )
    retention = MajorMeaningRetentionPlan(
        clear_long_input=clear_long_input,
        total_block_count=len(blocks),
        must_keep_block_keys=_dedupe(must_keep_keys),
        should_keep_block_keys=_dedupe(should_keep_keys),
        optional_block_keys=_dedupe(optional_keys),
        forbidden_overcompression_targets=_dedupe(must_keep_keys),
        min_must_keep_coverage_ratio=1.0 if must_keep_keys else 0.0,
        reason="structural_retention_without_example_roles",
    )
    return _MeaningArtifacts(tuple(blocks), coverage, arc, retention)


def _block_index(block_key: Any) -> int | None:
    parts = _clean(block_key).split(":")
    return int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None


def _meaning_block_span_ids(
    blocks: Sequence[InputMeaningBlock],
    spans: Sequence[EvidenceSpan],
) -> dict[str, tuple[str, ...]]:
    """Map existing MeaningBlocks back to the current request ledger."""

    ordered_text = _sort_spans(_text_spans(spans))
    result: dict[str, tuple[str, ...]] = {}
    for block in blocks or ():
        key = _clean(getattr(block, "block_key", ""))
        summary = _compact(getattr(block, "summary", ""))
        matched: list[str] = []
        if len(summary) >= 2:
            for span in ordered_text:
                candidate = _compact(getattr(span, "raw_text", ""))
                if candidate and (
                    candidate == summary
                    or (len(candidate) >= 4 and candidate in summary)
                    or (len(summary) >= 4 and summary in candidate)
                ):
                    matched.append(_clean(getattr(span, "span_id", "")))
        if not matched:
            index = _block_index(key)
            if index is not None and 0 <= index < len(ordered_text):
                matched.append(_clean(getattr(ordered_text[index], "span_id", "")))
        result[key] = tuple(_ordered_span_ids(matched))
    return result


def _claim_ids_by_span(board: PerspectiveBoard) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    claims = dict(getattr(board, "claim_index", {}) or getattr(board, "claims_by_id", {}) or {})
    for claim in claims.values():
        for span_id in list(getattr(claim, "evidence_span_ids", ()) or ()):
            index.setdefault(_clean(span_id), []).append(_clean(getattr(claim, "claim_id", "")))
    return {key: tuple(_dedupe(values)) for key, values in index.items()}


def _roles_and_block_keys_by_span(
    blocks: Sequence[InputMeaningBlock],
    block_span_ids: Mapping[str, Sequence[str]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    roles: dict[str, list[str]] = {}
    keys: dict[str, list[str]] = {}
    for block in blocks or ():
        block_key = _clean(getattr(block, "block_key", ""))
        role = _clean(getattr(block, "role", ""))
        for span_id in block_span_ids.get(block_key, ()):
            if role:
                roles.setdefault(span_id, []).append(role)
            if block_key:
                keys.setdefault(span_id, []).append(block_key)
    return (
        {span_id: tuple(_dedupe(values)) for span_id, values in roles.items()},
        {span_id: tuple(_dedupe(values)) for span_id, values in keys.items()},
    )


def _retention_by_span(
    spans: Sequence[EvidenceSpan],
    *,
    block_span_ids: Mapping[str, Sequence[str]],
    meaning_artifacts: _MeaningArtifacts,
    safety_decision: EmlisSafetyTriageDecision,
) -> dict[str, Retention]:
    ordered_text = _sort_spans(_text_spans(spans))
    substantive_text = [span for span in ordered_text if _is_substantive_text_span(span)]
    # The ledger intentionally keeps punctuation-delimited source spans.  A
    # quoted question or quotation suffix can therefore leave a syntactically
    # dependent fragment.  Keep those spans resolvable in the plan, but do not
    # promote them to public-surface mandatory material on their own.
    fragment_ids: set[str] = set()
    for index, span in enumerate(substantive_text):
        text = _clean(getattr(span, "raw_text", "")).strip("「」『』 、,。．.!！?？")
        next_text = ""
        if index + 1 < len(substantive_text):
            next_text = _clean(getattr(substantive_text[index + 1], "raw_text", "")).lstrip()
        if (
            re.search(r"(?:何故|なぜ|どうして)$", text)
            or re.match(r"^(?:何故|なぜ|どうして|とか|という|と考えて(?:いた|しまって))", text)
            or (
                re.match(r"^という", next_text)
                and index + 1 < len(substantive_text)
                and _clean(getattr(span, "source_field", ""))
                == _clean(getattr(substantive_text[index + 1], "source_field", ""))
            )
        ):
            fragment_ids.add(_clean(span.span_id))
    surface_substantive_text = [
        span for span in substantive_text if _clean(span.span_id) not in fragment_ids
    ] or substantive_text
    text_count = len(surface_substantive_text)
    result: dict[str, Retention] = {}
    arc_roles_by_span = _arc_roles_by_span(spans)

    for span in spans:
        span_id = _clean(getattr(span, "span_id", ""))
        field_name = _clean(getattr(span, "source_field", ""))
        if field_name in _TEXT_SOURCE_FIELDS:
            if span_id in fragment_ids:
                result[span_id] = (
                    "required" if arc_roles_by_span.get(span_id) else "optional"
                )
                continue
            if _is_pure_relation_marker(span):
                result[span_id] = "optional"
                continue
            result[span_id] = "required" if text_count <= 3 else "should"
            if arc_roles_by_span.get(span_id):
                result[span_id] = "required"
        else:
            result[span_id] = "required" if text_count == 0 else "optional"

    coverage = meaning_artifacts.coverage_plan
    if coverage is not None:
        for block_key in tuple(getattr(coverage, "selected_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = _retention_max(result.get(span_id, "optional"), "should")

    retention = meaning_artifacts.retention_plan
    if retention is not None:
        for block_key in tuple(getattr(retention, "must_keep_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = "required"
        for block_key in tuple(getattr(retention, "should_keep_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = _retention_max(result.get(span_id, "optional"), "should")

    # Upstream coverage/retention is allowed to keep a dependent fragment in
    # the semantic plan, but it must not reverse the public-surface boundary.
    # A fragment that also owns a major turn is not merely syntactic residue;
    # its arc obligation remains required and is integrated downstream.
    for span_id in fragment_ids:
        if not arc_roles_by_span.get(span_id):
            result[span_id] = "optional"

    for span_id in tuple(getattr(safety_decision, "evidence_span_ids", ()) or ()):
        if span_id in result:
            result[span_id] = "required"

    # Required is a semantic obligation, not a sentence-count budget.  Surface
    # integration may combine endpoints, but it must never demote an arc role
    # merely because more than four required spans exist.
    if surface_substantive_text and not any(result.get(_clean(span.span_id)) == "required" for span in surface_substantive_text):
        result[_clean(surface_substantive_text[0].span_id)] = "required"
    return result


def _kind_for_span(
    span: EvidenceSpan,
    *,
    roles: Sequence[str],
    safety_decision: EmlisSafetyTriageDecision,
    safety_span_order: Mapping[str, int],
) -> NucleusKind:
    field_name = _clean(getattr(span, "source_field", ""))
    span_id = _clean(getattr(span, "span_id", ""))
    text = _clean(getattr(span, "raw_text", ""))
    if (
        safety_decision.safety_triage_kind
        == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and span_id in safety_span_order
        and is_bounded_self_denial_text(text)
    ):
        return "self_evaluation"
    if field_name == "memo_action":
        return "action"
    if (
        safety_decision.safety_triage_kind
        == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and span_id in safety_span_order
    ):
        return "conclusion"
    if _clean(getattr(span, "detected_type", "")) == "relation_marker":
        return "other_explicit"
    if is_bounded_self_denial_text(text) or (
        _BOUNDED_NON_DENIAL_SELF_EVALUATION_RE.search(text)
    ):
        return "self_evaluation"
    if _REFUSAL_RE.search(text):
        return "state"
    if _SIMILE_NOT_WISH_RE.search(text):
        return "reaction"
    if _WISH_RE.search(_SIMILE_NOT_WISH_RE.sub("", text)):
        return "wish"
    if _CHANGE_RE.search(text):
        return "change"
    if _CONSTRAINT_RE.search(text):
        return "constraint"
    if _FEELING_RE.search(text):
        return "reaction"
    if _VALUE_RE.search(text):
        return "value"
    if _ACTION_RE.search(text):
        return "action"

    # Upstream roles remain provenance/fallback only. Canonical semantics above
    # are driven by structural operators and source anchors, not fixture nouns.
    role_set = frozenset(_dedupe(roles))
    if "effort_direction" in role_set:
        return "change" if safety_decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION else "conclusion"
    for candidates, kind in _ROLE_KIND_HINTS:
        if role_set & candidates:
            return kind
    return _KIND_BY_DETECTED_TYPE.get(_clean(getattr(span, "detected_type", "")), "other_explicit")


def _semantic_frame_for_span(
    span: EvidenceSpan,
    *,
    kind: NucleusKind,
    roles: Sequence[str],
    claim_ids: Sequence[str],
    arc_role_codes: Sequence[str] = (),
) -> GroundedSemanticFrame:
    signals = _clause_signals(span, kind=kind)
    detected_type = _clean(getattr(span, "detected_type", "")) or "unknown"
    span_id = _clean(getattr(span, "span_id", ""))
    predicate_kind = (
        "self_evaluation"
        if kind == "self_evaluation"
        and "operator:self_evaluation" in signals.operator_codes
        else next(
            (
                code.split(":", 1)[1]
                for code in signals.operator_codes
                if code
                in {
                    "operator:refusal",
                    "operator:wish",
                    "operator:constraint",
                    "operator:change",
                    "operator:self_evaluation",
                    "operator:feeling",
                    "operator:action",
                }
            ),
            kind,
        )
    )
    return GroundedSemanticFrame(
        actor="current_user",
        predicate_kind=predicate_kind,
        polarity=signals.polarity,
        modality=signals.modality,
        target_anchor_ids=(span_id,),
        time_scope=signals.time_scope,
        attribute_codes=tuple(
            _dedupe(
                [
                    f"semantic_analyzer:{GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION}",
                    f"detected_type:{detected_type}",
                    *signals.operator_codes,
                    *arc_role_codes,
                    f"time_scope:{signals.time_scope}",
                    *[f"source_claim:{claim_id}" for claim_id in claim_ids],
                ]
            )
        ),
    )


def _typed_nucleus_projections_for_span(
    span: EvidenceSpan,
    *,
    base_frame: GroundedSemanticFrame,
) -> tuple[_TypedNucleusProjection, ...]:
    """Project compound Japanese predicate structure without new Evidence.

    The Evidence Ledger deliberately preserves punctuation-sized spans, so a
    single real ``sN`` can contain two separately asserted predicates.  This
    projector creates semantic owners only when Japanese morphology states a
    closed structural link.  It never compares a complete input string and it
    never manufactures a source span or surface sentence.
    """

    source_field = _clean(getattr(span, "source_field", ""))
    if source_field not in _TEXT_SOURCE_FIELDS:
        return ()
    text = _clean(getattr(span, "raw_text", ""))

    def projection_codes(
        scalar_start: int,
        scalar_end: int,
        *codes: str,
    ) -> tuple[str, ...]:
        provenance = tuple(
            code
            for code in base_frame.attribute_codes
            if code.startswith(
                (
                    "semantic_analyzer:",
                    "detected_type:",
                    "source_claim:",
                )
            )
        )
        return tuple(
            _dedupe(
                (
                    *provenance,
                    f"surface_scalar_range:{scalar_start}:{scalar_end}",
                    "surface_scalar_source:normalized_raw_text",
                    *codes,
                )
            )
        )

    def relation_fragment_codes(
        scalar_start: int,
        scalar_end: int,
        *codes: str,
    ) -> tuple[str, ...]:
        return tuple(
            (
                f"source_fragment_scalar_range:{scalar_start}:{scalar_end}"
                if code.startswith("surface_scalar_range:")
                else "source_fragment_scalar_source:normalized_raw_text"
                if code == "surface_scalar_source:normalized_raw_text"
                else code
            )
            for code in projection_codes(scalar_start, scalar_end, *codes)
            if not code.startswith("detected_type:")
        )

    def trimmed_range(start: int, end: int) -> tuple[int, int]:
        while start < end and text[start] in " \t\r\n、,。．.!！?？":
            start += 1
        while start < end and text[end - 1] in " \t\r\n、,。．.!！?？":
            end -= 1
        return start, end

    def owner_scope_is_bound(fragment: str) -> bool:
        top_level_fragment = _top_level_text(fragment)
        if top_level_fragment is None:
            return False
        top_level_fragment = top_level_fragment.strip()
        # A bounded time adverb is not an owner.  Remove it before checking
        # the grammatical subject/possessor so that forms such as
        # ``今日は弟が…`` and ``今の妹の…`` cannot borrow current-user
        # ownership from their temporal prefix.
        temporal_prefix = re.compile(
            r"^(?:(?:今日|昨日|明日|今|現在|午前|午後|夕方|朝|昼|夜|"
            r"以前|これまで)(?:は|も|の|には)?|この記録では?|"
            r"少し(?:だけ|ずつ)?|やや|ずっと|強く|まだ)[、,\s]*"
        )
        owner_marker = re.compile(
            r"^(?P<owner>[^\s、,。.!！?？]+?)"
            r"[ \t\u3000]*"
            r"(?P<marker>にとって|には|は|が|も|の)"
        )
        attribution_prefix = re.compile(
            r"^(?P<owner>[^\s、,。.!！?？]+?)"
            r"[ \t\u3000]*"
            r"(?:(?:に|から)[^\s、,。.!！?？]+?"
            r"(?:ると|れば|ますと)|いわく|曰く)"
        )
        leading_case_owner = re.compile(
            r"^(?P<owner>[^\s、,。.!！?？]+?)"
            r"[ \t\u3000]*"
            r"(?P<marker>から|に|と)(?P<remainder>.+)$"
        )
        leading_focus_owner = re.compile(
            r"^(?P<owner>[^\s、,。.!！?？]+?)"
            r"[ \t\u3000]*"
            r"(?P<marker>"
            + _OWNER_FOCUS_PARTICLE_SOURCE
            + r")"
            r"(?:は|が|も)?(?P<remainder>.+)$"
        )
        leading_topic_owner = re.compile(
            r"^(?P<owner>[^\s、,。.!！?？]+?)"
            r"[ \t\u3000]*"
            r"(?P<marker>"
            + _OWNER_TOPIC_PARTICLE_SOURCE
            + r")"
            r"(?P<remainder>.+)$"
        )
        operator_patterns = _FINITE_OPERATOR_PATTERNS

        def operator_left_context_is_bounded(
            fragment: str,
            operator_pattern: re.Pattern[str],
            match: re.Match[str],
        ) -> bool:
            """Allow only a frozen semantic object before a predicate anchor."""
            return _operator_match_left_context_is_bounded(
                fragment,
                operator_pattern,
                match,
            )

        def finite_owned_operator_matches(
            fragment: str,
        ) -> tuple[tuple[re.Pattern[str], re.Match[str]], ...]:
            return tuple(
                (pattern, match)
                for pattern in operator_patterns
                for match in pattern.finditer(fragment)
                if operator_left_context_is_bounded(
                    fragment,
                    pattern,
                    match,
                )
                and _operator_match_has_finite_closure(
                    fragment,
                    pattern,
                    match,
                )
            )
        explicit_self_content_host = re.compile(
            r"^(?P<content>.+?)(?:とは|と)"
            r"(?P<owner>自分|私|わたし|僕|ぼく|俺|おれ)"
            r"(?:にとって|には|は|が|も|"
            + _OWNER_FOCUS_PARTICLE_SOURCE
            + r"(?:は|が|も)?)"
            r"(?P<host>.+)$"
        )

        def self_experiential_host_is_bounded(host: str) -> bool:
            host_core = re.sub(
                r"^(?:強く|少し|やや|ずっと)[、,\s]*",
                "",
                host,
                count=1,
            )
            feeling_host = _last_finite_operator_match(
                host_core,
                _FEELING_RE,
            )
            epistemic_host = _last_finite_operator_match(
                "と" + host_core,
                _UNCERTAIN_RE,
            )
            return bool(
                (
                    feeling_host is not None
                    and feeling_host.start() == 0
                )
                or (
                    epistemic_host is not None
                    and epistemic_host.start() == 0
                )
            )
        # Whitespace is an owner boundary, not disposable formatting.  Only
        # whitespace immediately consumed with a proven prefix/particle may
        # be removed; an opaque token before an operator fails closed.
        owner_scope = top_level_fragment
        attribution_scope = owner_scope
        # Consume only a chain of explicit self owners and bounded temporal
        # prefixes.  Any subsequent grammatical owner/beneficiary remains a
        # third-party authority and makes the projection ineligible.
        while True:
            owner_scope = owner_scope.lstrip(" \t\u3000")
            previous_owner_scope = owner_scope
            if not any(
                pattern.match(owner_scope) is not None
                for pattern in operator_patterns
            ):
                owner_scope = temporal_prefix.sub("", owner_scope)
            if owner_scope != previous_owner_scope:
                continue
            explicit_content_host = explicit_self_content_host.match(
                owner_scope
            )
            if explicit_content_host is not None:
                content = explicit_content_host.group("content")
                content_is_complete = bool(
                    any(
                        match.end() == len(content)
                        for pattern in operator_patterns
                        for match in pattern.finditer(content)
                    )
                    or _last_finite_operator_match(
                        content,
                        *operator_patterns,
                    )
                    is not None
                )
                if (
                    content_is_complete
                    and self_experiential_host_is_bounded(
                        explicit_content_host.group("host")
                    )
                ):
                    owner_scope = ""
                    continue
            leading_attribution = attribution_prefix.match(owner_scope)
            if leading_attribution is not None:
                if (
                    _SELF_REFERENCE_RE.fullmatch(
                        leading_attribution.group("owner")
                    )
                    is None
                ):
                    return False
                owner_scope = owner_scope[
                    leading_attribution.end() :
                ].lstrip(" \t\u3000")
                continue
            leading_owner = owner_marker.match(owner_scope)
            case_owner = leading_case_owner.match(owner_scope)
            focus_owner = leading_focus_owner.match(owner_scope)
            topic_owner = leading_topic_owner.match(owner_scope)
            for marked_owner in (focus_owner, topic_owner):
                if (
                    marked_owner is not None
                    and any(
                        pattern.search(marked_owner.group("remainder"))
                        is not None
                        for pattern in operator_patterns
                    )
                    and (
                        leading_owner is None
                        or marked_owner.start("marker")
                        < leading_owner.start("marker")
                    )
                ):
                    if (
                        _SELF_REFERENCE_RE.fullmatch(
                            marked_owner.group("owner")
                        )
                        is None
                    ):
                        return False
                    owner_scope = marked_owner.group("remainder").lstrip(
                        " \t\u3000"
                    )
                    break
            else:
                marked_owner = None
            if marked_owner is not None:
                continue
            if (
                case_owner is not None
                and not any(
                    match.start()
                    <= case_owner.start("marker")
                    < match.end()
                    for pattern in operator_patterns
                    for match in pattern.finditer(owner_scope)
                )
                and any(
                    pattern.match(case_owner.group("remainder"))
                    is not None
                    for pattern in operator_patterns
                )
                and (
                    leading_owner is None
                    or case_owner.start("marker")
                    < leading_owner.start("marker")
                )
            ):
                content_owner = case_owner.group("owner")
                content_is_complete = bool(
                    any(
                        match.end() == len(content_owner)
                        for pattern in operator_patterns
                        for match in pattern.finditer(content_owner)
                    )
                    or _last_finite_operator_match(
                        content_owner,
                        *operator_patterns,
                    )
                    is not None
                )
                semantic_content_bridge = bool(
                    case_owner.group("marker") == "と"
                    and content_is_complete
                    and self_experiential_host_is_bounded(
                        case_owner.group("remainder")
                    )
                )
                if semantic_content_bridge:
                    owner_scope = ""
                    continue
                if (
                    _SELF_REFERENCE_RE.fullmatch(case_owner.group("owner"))
                    is None
                ):
                    return False
                owner_scope = case_owner.group("remainder").lstrip(
                    " \t\u3000"
                )
                continue
            if leading_owner is None:
                if (
                    owner_scope
                    and not finite_owned_operator_matches(owner_scope)
                    and not _bounded_nominal_wish_endpoint(owner_scope)
                    and not _bounded_bare_wish_nominal(owner_scope)
                    and not _bounded_ambiguous_nominal_state(owner_scope)
                    and not _bounded_structural_action_endpoint(owner_scope)
                ):
                    return False
                break
            owner = leading_owner.group("owner")
            marker = leading_owner.group("marker")
            if _SELF_REFERENCE_RE.fullmatch(owner) is None:
                marker_start = leading_owner.start("marker")
                marker_is_inside_operator = any(
                    operator_left_context_is_bounded(
                        owner_scope,
                        pattern,
                        match,
                    )
                    and match.start() <= marker_start < match.end()
                    for pattern in operator_patterns
                    for match in pattern.finditer(owner_scope)
                )
                remainder = owner_scope[leading_owner.end() :]
                owned_terminal_matches = finite_owned_operator_matches(
                    owner_scope
                )
                owned_scope_is_complete = any(
                    match.start() == 0 and match.end() == len(owner_scope)
                    for _pattern, match in owned_terminal_matches
                )
                bounded_terminal_carrier = bool(
                    any(
                        match.end() <= marker_start
                        for _pattern, match in owned_terminal_matches
                    )
                )
                semantic_subject_operator = next(
                    (
                        (pattern, match)
                        for pattern in operator_patterns
                        for match in pattern.finditer(owner)
                        if match.end() == len(owner)
                        and operator_left_context_is_bounded(
                            owner,
                            pattern,
                            match,
                        )
                    ),
                    None,
                )
                special_wish_subject = bool(
                    re.search(
                        r"(?:たい|ほしい|欲しい)(?:気持ち|願い)$",
                        owner,
                    )
                )
                semantic_subject_complete = bool(
                    semantic_subject_operator is not None
                    or special_wish_subject
                )
                owner_is_complete_semantic_subject = bool(
                    marker in {"は", "が", "も"}
                    and semantic_subject_complete
                    and (
                        _finite_endpoint_carrier_shape(
                            marker + remainder,
                            operator_surface=(
                                owner
                                if special_wish_subject
                                else semantic_subject_operator[1].group(0)
                                if semantic_subject_operator is not None
                                else ""
                            ),
                            operator_pattern=(
                                _WISH_RE
                                if special_wish_subject
                                else semantic_subject_operator[0]
                                if semantic_subject_operator is not None
                                else None
                            ),
                        )
                        or _self_owned_finite_host_shape(
                            marker + remainder
                        )
                    )
                )
                epistemic_content_topic = bool(
                    marker in {"は", "も"}
                    and (
                        (
                            owner.endswith("か")
                            and any(
                                match.end() == len(remainder)
                                for pattern in (
                                    _RELATION_UNCERTAINTY_RE,
                                    _UNCERTAIN_RE,
                                    _OPEN_UNFINISHED_RE,
                                )
                                for match in pattern.finditer(remainder)
                            )
                        )
                        or (
                            owner.endswith("と")
                            and any(
                                match.end() <= len(owner) - 1
                                for pattern in operator_patterns
                                for match in pattern.finditer(owner[:-1])
                            )
                            and re.fullmatch(
                                r"思(?:う|っている|っていた|っています|"
                                r"っていました|います|いました)"
                                r"(?:の(?:だ|です)|ん(?:だ|です))?",
                                remainder,
                            )
                            is not None
                        )
                    )
                )
                predicate_auxiliary_particle = bool(
                    (
                        marker == "の"
                        and (
                            semantic_subject_complete
                            or (
                                owner.endswith("な")
                                and any(
                                    match.end() == len(owner) - 1
                                    for pattern in operator_patterns
                                    for match in pattern.finditer(owner[:-1])
                                )
                            )
                        )
                        and (
                            semantic_subject_operator is not None
                            or special_wish_subject
                        )
                        and _finite_endpoint_carrier_shape(
                            marker + remainder,
                            operator_surface=(
                                owner
                                if special_wish_subject
                                else semantic_subject_operator[1].group(0)
                            ),
                            operator_pattern=(
                                _WISH_RE
                                if special_wish_subject
                                else semantic_subject_operator[0]
                            ),
                        )
                    )
                    or (
                        marker == "は"
                        and owner.endswith(("て", "で"))
                        and any(
                            match.start() == 0
                            and match.end() == len(owner) - 1
                            and _direct_finite_carrier_shape(
                                remainder,
                                operator_surface=match.group(0),
                                operator_pattern=pattern,
                            )
                            for pattern in operator_patterns
                            for match in pattern.finditer(owner[:-1])
                        )
                    )
                )
                # A marker inside an already-frozen terminal operator (for
                # example 気がする / 意味がある), or a complete semantic
                # content subject followed by an exact finite carrier, is not
                # evidence of a third-party owner.  The operator/end boundary
                # is grammatical; no noun, case or phrase-family list is used.
                if (
                    marker_is_inside_operator
                    or bounded_terminal_carrier
                    or owner_is_complete_semantic_subject
                    or epistemic_content_topic
                    or predicate_auxiliary_particle
                ):
                    # The marker is grammatical, but the remaining predicate
                    # can still introduce an explicit non-self subject or
                    # experiencer.  Consume the protected prefix and continue
                    # scanning to the end; an early break would lend the
                    # current user to a later owner.
                    owner_scope = (
                        ""
                        if (
                            bounded_terminal_carrier
                            or owned_scope_is_complete
                            or owner_is_complete_semantic_subject
                            or epistemic_content_topic
                            or predicate_auxiliary_particle
                        )
                        else remainder
                    )
                    continue
                return False
            owner_scope = owner_scope[leading_owner.end() :].lstrip(
                " \t\u3000、,"
            )
        # A later explicit speaker remains the authority for an attributed
        # predicate even when the fragment begins with an ownerless state.
        for attributed_owner in re.finditer(
            r"(?:と|って)(?P<owner>[^\s、,。.!！?？]+?)"
            r"(?:は|が|も)(?=(?:言|話|語|述べ|書|記録|考|思|感じ|判断|決め))",
            attribution_scope,
        ):
            if (
                _SELF_REFERENCE_RE.fullmatch(attributed_owner.group("owner"))
                is None
            ):
                return False
        return True

    def affirmative_wish_proof(fragment: str) -> tuple[bool, bool]:
        top_level_fragment = _top_level_text(fragment)
        if top_level_fragment is None:
            return False, False
        top_level_fragment = top_level_fragment.strip()
        operators = set(
            _operator_codes_for_text(
                top_level_fragment,
                source_field=source_field,
            )
        )
        # Wish authority is fragment-local.  In particular, one endpoint's
        # real desiderative must never license another endpoint's nominal
        # simile merely because both share one EvidenceSpan.
        wish = "operator:wish" in operators
        nominal_host = re.search(
            r"(?:たい|ほしい|欲しい)(?:気持ち|願い)"
            r"(?P<carrier>(?:は|が|も|の).+)$",
            top_level_fragment,
        )
        explicit_self_wish_host = re.search(
            (
                r"(?:たい|ほしい|欲しい)(?:とは|と)"
                r"(?:自分|私|わたし|僕|ぼく|俺|おれ)"
                r"(?:にとって|には|は|が|も|"
                + _OWNER_FOCUS_PARTICLE_SOURCE
                + r"(?:は|が|も)?)"
                r"(?:(?:強く|少し|やや|ずっと)[、,\s]*)?"
                r"感じ(?:る|た|ている|ていた|ています|ていました)"
                r"(?:こと(?:は|が|も)?"
                r"(?:ある|あった|あります|ありました))?"
                r"(?:(?:の|ん)(?:だ|です))?$"
            ),
            top_level_fragment,
        )
        bounded_nominal_host = bool(
            nominal_host is not None
            and (
                _finite_endpoint_carrier_shape(
                    nominal_host.group("carrier"),
                    operator_surface=top_level_fragment[
                        : nominal_host.start("carrier")
                    ],
                    operator_pattern=_WISH_RE,
                )
                or re.fullmatch(
                    r"(?:は|が|も)"
                    r"(?:(?:少し(?:だけ|ずつ)?|やや|ずっと|強く)[、,\s]*)?"
                    r"(?:ある|あった|あります|ありました)",
                    nominal_host.group("carrier"),
                )
                is not None
                or _self_owned_finite_host_shape(
                    nominal_host.group("carrier")
                )
            )
        )
        shared_finite_wish = bool(
            _last_finite_operator_match(
                top_level_fragment,
                _WISH_RE,
            )
            is not None
        )
        finite_wish = bool(
            shared_finite_wish
            or _FINITE_WISH_CLAUSE_END_RE.search(top_level_fragment)
            or re.search(
                r"(?:たい|ほしい|欲しい)(?:と|とは)?思"
                r"(?:う|っている|っていた|っています|っていました|"
                r"います|いました)(?:の(?:だ|です)|ん(?:だ|です))?$",
                top_level_fragment,
            )
            or re.search(
                r"(?:たい|ほしい|欲しい)(?:と|とは)?感じ"
                r"(?:る|た|ている|ていた|ています|ていました)"
                r"(?:こと(?:は|が|も)?"
                r"(?:ある|あった|あります|ありました))?"
                r"(?:(?:の|ん)(?:だ|です))?$",
                top_level_fragment,
            )
            or bounded_nominal_host
            or explicit_self_wish_host is not None
        )
        nominal_wish = bool(
            re.search(
                r"(?:たい|ほしい|欲しい)(?:気持ち|願い)$",
                top_level_fragment,
            )
        )
        terminal_wish_denial = bool(
            re.search(
                r"(?:たい|ほしい|欲しい)(?:気持ち|願い|わけ)"
                r"(?:は|が|も|では|じゃ)?"
                r"(?:ない|なかった|ありません|ありませんでした)$",
                top_level_fragment,
            )
            or re.search(
                r"(?:たい|ほしい|欲しい)(?:と|とは)?思"
                r"(?:わない|っていない|っていなかった|いません)$",
                top_level_fragment,
            )
        )
        positive = bool(
            wish
            and (finite_wish or nominal_wish)
            and owner_scope_is_bound(top_level_fragment)
            and not terminal_wish_denial
        )
        # A bare 気持ち/願い nominal is a valid endpoint beside an explicit
        # non-ga connective, but it is not a finite left clause that can prove
        # conjunctive が.  The second return value preserves that distinction.
        return positive, bool(positive and finite_wish)

    def affirmative_wish(fragment: str) -> bool:
        return affirmative_wish_proof(fragment)[0]

    def ambiguous_m_row_nominal_state(fragment: str) -> bool:
        """Admit an ambiguous ``…みたい気持ち/願い`` without wish promotion.

        Orthography alone cannot distinguish an m-row desiderative from a
        nominal simile.  The exact nominal source can still be retained as an
        explicit neutral state when a separately proven wish endpoint and an
        explicit coexistence connective establish the relation.
        """

        top_level_fragment = _top_level_text(fragment)
        if top_level_fragment is None:
            return False
        top_level_fragment = top_level_fragment.strip()
        operators = set(
            _operator_codes_for_text(
                top_level_fragment,
                source_field=source_field,
            )
        )
        return bool(
            re.search(r"(?<![てで])みたい(?:気持ち|願い)$", top_level_fragment)
            and owner_scope_is_bound(top_level_fragment)
            and not operators & {"operator:negation", "operator:refusal"}
        )

    def m_row_desiderative_constraint_pair(
        left_fragment: str,
        right_fragment: str,
    ) -> bool:
        """Resolve ambiguous hiragana ``みたい`` from its paired inflection.

        A bare ``Nみたい`` is a simile and remains excluded.  A m-row verb's
        desiderative and potential-negative forms expose the same source stem
        (for example ``休みたい`` / ``休めない``).  Requiring that exact
        cross-clause stem evidence avoids a word list and fails closed when
        the spelling alone is ambiguous.
        """

        if (
            not left_fragment.endswith("みたい")
        ):
            return False
        temporal_prefix = re.compile(
            r"^(?:今日(?:は|も)?|今は|現在は?|この記録では?|少しずつ|まだ)[、,\s]*"
        )
        stem = temporal_prefix.sub(
            "",
            left_fragment[: -len("みたい")],
        )
        right_core = temporal_prefix.sub("", right_fragment)
        if (
            not stem
            or re.fullmatch(r"[ぁ-んァ-ヶ一-龯々〆ヵヶー]+", stem) is None
            or re.search(r"(?:は|が|も|の)", stem) is not None
            or (
                len(stem) == 1
                and re.fullmatch(r"[一-龯々〆ヵヶ]", stem) is None
            )
        ):
            return False
        return bool(
            re.fullmatch(
                rf"{re.escape(stem)}め(?:ない|なかった|なく|ません|ず|ぬ)",
                right_core,
            )
        )

    def structurally_performed_action(fragment: str) -> bool:
        argument_match = _ACTION_ARGUMENT_STEM_RE.search(fragment)
        if argument_match is None or _NON_ACTION_CONDITION_END_RE.search(fragment):
            return False
        predicate = argument_match.group("predicate")
        # These are inflected existential/copular auxiliaries, not a bank of
        # permitted action verbs.  All other verb stems remain open, which is
        # why unseen 座っ/浴び/つけ are admitted by the same rule.
        if re.fullmatch(
            r"(?:い(?:る|た|ました)?|"
            r"あ(?:る|り(?:ました)?|っ(?:た)?)?|"
            r"な(?:る|り(?:ました)?|っ(?:た)?)|した)",
            predicate,
        ):
            return False
        if re.search(r"(?:は|が|も)", predicate):
            return False
        fragment_operators = set(
            _operator_codes_for_text(fragment, source_field=source_field)
        )
        return not bool(
            fragment_operators
            & {
                "operator:constraint",
                "operator:refusal",
                "operator:uncertainty",
                "operator:wish",
            }
        ) and not bool(_FEELING_RE.search(fragment) or _NEGATION_RE.search(fragment))

    action_change_link = _ACTION_CHANGE_LINK_RE.search(text)
    if action_change_link is not None:
        action_start, action_end = trimmed_range(0, action_change_link.start())
        # Keep semantic action detection on the pre-link fragment, while the
        # source-bound surface scalar retains the linker's leading inflection
        # (た/だ/て/で).  This closes the quoted action as a Japanese past/te
        # form without admitting the conditional/sequence connective itself.
        surface_action_end = action_change_link.start() + 1
        if text[action_change_link.start() : surface_action_end] not in {
            "た",
            "だ",
            "て",
            "で",
        }:
            return ()
        change_start, change_end = trimmed_range(action_change_link.end(), len(text))
        action_text = text[action_start:action_end]
        change_text = text[change_start:change_end]
        change_operators = set(
            _operator_codes_for_text(change_text, source_field=source_field)
        )
        performed_action = structurally_performed_action(action_text)
        observed_change = bool(
            (_POSITIVE_CHANGE_RE.search(change_text) or _CHANGE_RE.search(change_text))
            and _OBSERVED_PAST_OUTCOME_RE.search(change_text)
            and "operator:uncertainty" not in change_operators
            and "operator:wish" not in change_operators
            and "operator:refusal" not in change_operators
        )
        if action_text and performed_action and observed_change:
            change_codes = [
                "operator:change",
                "operator:bounded_change",
                "semantic_role:current_change",
                "semantic_role:span_relation_endpoint",
                "semantic_role:compound_reception_coowned_nonprimary",
                "semantic_dependency:action_before_change",
            ]
            if _POSITIVE_CHANGE_RE.search(change_text):
                change_codes.append("operator:positive_change")
            return (
                _TypedNucleusProjection(
                    nucleus_suffix="",
                    kind="action",
                    predicate_kind="action",
                    polarity="neutral",
                    modality="fact",
                    time_scope="past",
                    scalar_start=action_start,
                    scalar_end=surface_action_end,
                    attribute_codes=projection_codes(
                        action_start,
                        surface_action_end,
                        "operator:action",
                        "operator:performed_action",
                        "semantic_role:concrete_action",
                        "semantic_dependency:action_before_change",
                    ),
                ),
                _TypedNucleusProjection(
                    nucleus_suffix=":change",
                    kind="change",
                    predicate_kind="change",
                    polarity="positive" if _POSITIVE_CHANGE_RE.search(change_text) else "neutral",
                    modality=(
                        "feeling"
                        if _FEELING_RE.search(change_text)
                        else "fact"
                    ),
                    time_scope="past",
                    scalar_start=change_start,
                    scalar_end=change_end,
                    attribute_codes=projection_codes(
                        change_start,
                        change_end,
                        *change_codes,
                    ),
                ),
            )

    residue_match = _PRESENT_RESIDUE_RE.search(text)
    unfinished_match = _OPEN_UNFINISHED_RE.search(text)
    if (
        residue_match is not None
        and unfinished_match is not None
        and residue_match.start() <= unfinished_match.start()
    ):
        unfinished_anchor = next(
            (
                match
                for match in re.finditer(
                    r"(?:どう|何|どちら|どっち|いつ|どこ|誰|まだ|今も|未定|途中|結論)",
                    text,
                )
                if match.start() >= residue_match.end()
            ),
            None,
        )
        unfinished_clause_start = (
            unfinished_anchor.start()
            if unfinished_anchor is not None
            else unfinished_match.start()
        )
        separator = max(
            text.rfind("、", residue_match.start(), unfinished_clause_start + 1),
            text.rfind(",", residue_match.start(), unfinished_clause_start + 1),
        )
        residue_end_seed = separator if separator >= 0 else unfinished_clause_start
        unfinished_start_seed = (
            separator + 1 if separator >= 0 else unfinished_clause_start
        )
        residue_start, residue_end = trimmed_range(
            residue_match.start(), residue_end_seed
        )
        unfinished_start, unfinished_end = trimmed_range(
            unfinished_start_seed, len(text)
        )
        if residue_start >= residue_end or unfinished_start >= unfinished_end:
            return ()
        return (
            _TypedNucleusProjection(
                nucleus_suffix="",
                kind="reaction",
                predicate_kind="residue",
                polarity="neutral",
                modality="feeling" if _FEELING_RE.search(text) else "fact",
                time_scope="present",
                scalar_start=residue_start,
                scalar_end=residue_end,
                attribute_codes=projection_codes(
                    residue_start,
                    residue_end,
                    "operator:residue",
                    "semantic_role:present_residue",
                    "semantic_role:span_relation_endpoint",
                    "semantic_dependency:event_before_residue",
                ),
            ),
            _TypedNucleusProjection(
                nucleus_suffix=":unfinished",
                kind="uncertainty",
                predicate_kind="unfinished",
                polarity="neutral",
                modality="uncertain",
                time_scope="present",
                scalar_start=unfinished_start,
                scalar_end=unfinished_end,
                attribute_codes=projection_codes(
                    unfinished_start,
                    unfinished_end,
                    "operator:uncertainty",
                    "operator:unfinished",
                    "semantic_role:present_unfinished",
                    "semantic_role:compound_reception_coowned_nonprimary",
                    "semantic_dependency:residue_before_unfinished",
                ),
            ),
        )

    coordinate_links = _top_level_pattern_matches(
        text,
        _TOP_LEVEL_COORDINATE_LINK_RE,
    )
    contrast_links = _top_level_pattern_matches(
        text,
        _TOP_LEVEL_CONTRAST_LINK_RE,
    )
    bare_ga_links = _top_level_pattern_matches(
        text,
        _TOP_LEVEL_BARE_GA_LINK_RE,
    )
    top_level_relation_link_count = len(coordinate_links) + len(contrast_links)
    coexistence_tails = _top_level_pattern_matches(
        text,
        _COEXISTENCE_TAIL_RE,
    )
    coexistence_tail = (
        coexistence_tails[0] if len(coexistence_tails) == 1 else None
    )
    if (
        top_level_relation_link_count == 1
        and len(coordinate_links) == 1
        and coexistence_tail is not None
    ):
        link = coordinate_links[0]
        left_start, left_end = trimmed_range(0, link.start())
        right_start, right_end = trimmed_range(
            link.end(), coexistence_tail.start()
        )
        left_text = text[left_start:left_end]
        right_text = text[right_start:right_end]
        left_wish = affirmative_wish(left_text)
        right_wish = affirmative_wish(right_text)
        left_state = ambiguous_m_row_nominal_state(left_text)
        right_state = ambiguous_m_row_nominal_state(right_text)
        if (
            left_start < left_end <= link.start()
            and link.end() <= right_start < right_end
            and (left_wish or right_wish)
            and (left_wish or left_state)
            and (right_wish or right_state)
        ):
            dependency = "semantic_dependency:top_level_coexistence"
            common_codes = (
                "operator:coexistence",
                "semantic_role:span_relation_endpoint",
                "semantic_role:generic_relation_fragment",
                dependency,
            )
            left_codes = (
                *(("operator:wish", "semantic_role:retained_intention") if left_wish else ()),
                *common_codes,
                *(
                    ("semantic_role:compound_reception_coowned_nonprimary",)
                    if left_state
                    else ()
                ),
            )
            right_codes = (
                *(("operator:wish", "semantic_role:retained_intention") if right_wish else ()),
                *common_codes,
                *(
                    ("semantic_role:compound_reception_coowned_nonprimary",)
                    if right_state or (left_wish and right_wish)
                    else ()
                ),
            )
            return (
                _TypedNucleusProjection(
                    nucleus_suffix="",
                    kind="wish" if left_wish else "state",
                    predicate_kind="wish" if left_wish else "state",
                    polarity="positive" if left_wish else "neutral",
                    modality="wish" if left_wish else "fact",
                    time_scope=_time_scope_for_text(left_text),
                    scalar_start=left_start,
                    scalar_end=left_end,
                    attribute_codes=relation_fragment_codes(
                        left_start,
                        left_end,
                        *left_codes,
                    ),
                    relation_kind="coexistence",
                ),
                _TypedNucleusProjection(
                    nucleus_suffix=":coexisting",
                    kind="wish" if right_wish else "state",
                    predicate_kind="wish" if right_wish else "state",
                    polarity="positive" if right_wish else "neutral",
                    modality="wish" if right_wish else "fact",
                    time_scope=_time_scope_for_text(right_text),
                    scalar_start=right_start,
                    scalar_end=right_end,
                    attribute_codes=relation_fragment_codes(
                        right_start,
                        right_end,
                        *right_codes,
                    ),
                    relation_kind="coexistence",
                    grounding_kind="user_stated_relation",
                ),
            )

    generic_contrast_links = (
        contrast_links
        if top_level_relation_link_count == 1 and len(contrast_links) == 1
        else bare_ga_links
        if not coordinate_links and not contrast_links and bare_ga_links
        else ()
    )
    if generic_contrast_links:
        link = generic_contrast_links[0]
        left_start, left_end = trimmed_range(0, link.start())
        right_start, right_end = trimmed_range(link.end(), len(text))
        left_text = text[left_start:left_end]
        right_text = text[right_start:right_end]
        # Plain ``のに`` is structurally ambiguous between a concessive and
        # nominalizer+case (purpose/use) construction.  Route A has no
        # argument-selection axis that can prove that distinction, so this
        # generic splitter fails closed.  ``なのに`` remains an unambiguous
        # top-level concessive and is handled by the common exact2 proof.
        if link.group(0).lstrip().startswith("のに"):
            return ()
        paired_m_row_wish = m_row_desiderative_constraint_pair(
            left_text,
            right_text,
        )
        left_wish = affirmative_wish(left_text) or paired_m_row_wish
        # 「が、」 is clause-level only after a finite wish predicate.  A
        # nominal subject such as 「…気持ちが、」 must not become contrast.
        conjunctive_ga_is_finite = bool(
            not link.group(0).startswith("が")
            or _FINITE_WISH_CLAUSE_END_RE.search(left_text)
            or paired_m_row_wish
        )
        right_top_level = _top_level_text(right_text)
        if right_top_level is None:
            return ()
        right_top_level = right_top_level.strip()
        connector_group = link.group(0).lstrip()
        connector_nominal_mode = (
            "na"
            if connector_group.startswith("なのに")
            else "ellipsis"
            if (
                re.search(r"[、,]", text[left_end : link.start()])
                and connector_group.startswith(
                    ("でも", "ただ", "とはいえ", "一方")
                )
            )
            else ""
        )
        right_operators = set(
            _operator_codes_for_text(
                right_top_level,
                source_field=source_field,
            )
        )
        right_uncertain = bool(
            "operator:uncertainty" in right_operators
            or _RELATION_UNCERTAINTY_RE.search(right_top_level)
        )

        def operator_is_endpoint_final(*patterns: re.Pattern[str]) -> bool:
            """Require a frozen operator plus only finite inflectional tail."""

            return (
                _last_finite_operator_match(right_top_level, *patterns)
                is not None
            )

        right_constraint_final = operator_is_endpoint_final(_CONSTRAINT_RE)
        right_uncertainty_final = operator_is_endpoint_final(
            _RELATION_UNCERTAINTY_RE,
            _UNCERTAIN_RE,
        )
        right_negated = "operator:negation" in right_operators
        right_constrained = bool(
            paired_m_row_wish
            or (
                not right_negated
                and (
                    (
                        "operator:constraint" in right_operators
                        and right_constraint_final
                    )
                    or (right_uncertain and right_uncertainty_final)
                )
            )
        )
        # A left-hand wish cannot turn a terminally cancelled burden into a
        # live wish/constraint tension.  Preserve the frozen fail-closed
        # boundary for negated uncertainty and cancelled constraint; the
        # reverse order remains eligible for the neutral generic-state path.
        if (
            left_wish
            and right_negated
            and (
                _NEGATED_CONSTRAINT_CANCELLATION_RE.search(
                    right_top_level
                )
                or _NEGATED_RELATION_UNCERTAINTY_CANCELLATION_RE.search(
                    right_top_level
                )
            )
        ):
            return ()
        if (
            len(generic_contrast_links) == 1
            and left_start < left_end <= link.start()
            and link.end() <= right_start < right_end
            and left_wish
            and conjunctive_ga_is_finite
            and (
                owner_scope_is_bound(right_top_level)
                or (
                    paired_m_row_wish
                    and owner_scope_is_bound(left_text)
                )
            )
            and right_constrained
        ):
            dependency = "semantic_dependency:top_level_wish_constraint"
            left_codes = (
                "operator:wish",
                "semantic_role:retained_intention",
                "semantic_role:span_relation_endpoint",
                "semantic_role:generic_relation_fragment",
                dependency,
            )
            right_codes = [
                "operator:constraint",
                "semantic_role:burden",
                "semantic_role:span_relation_endpoint",
                "semantic_role:generic_relation_fragment",
                "semantic_role:compound_reception_coowned_nonprimary",
                dependency,
            ]
            if right_uncertain:
                right_codes.append("operator:uncertainty")
            if right_negated:
                right_codes.append("operator:negation")
            return (
                _TypedNucleusProjection(
                    nucleus_suffix="",
                    kind="wish",
                    predicate_kind="wish",
                    polarity="positive",
                    modality="wish",
                    time_scope=_time_scope_for_text(left_text),
                    scalar_start=left_start,
                    scalar_end=left_end,
                    attribute_codes=relation_fragment_codes(
                        left_start,
                        left_end,
                        *left_codes,
                    ),
                    relation_kind="wish_and_constraint",
                ),
                _TypedNucleusProjection(
                    nucleus_suffix=":constraint",
                    kind="constraint",
                    predicate_kind="constraint",
                    polarity=(
                        "negative"
                        if right_negated
                        else "neutral"
                    ),
                    modality="uncertain" if right_uncertain else "possibility",
                    time_scope=_time_scope_for_text(right_text),
                    scalar_start=right_start,
                    scalar_end=right_end,
                    attribute_codes=relation_fragment_codes(
                        right_start,
                        right_end,
                        *right_codes,
                    ),
                    relation_kind="wish_and_constraint",
                ),
            )

        def generic_contrast_endpoint_profile(
            fragment: str,
        ) -> tuple[
            NucleusKind,
            str,
            Literal["positive", "negative", "mixed", "neutral"],
            Literal[
                "fact",
                "feeling",
                "wish",
                "possibility",
                "uncertain",
                "refusal",
                "intention",
            ],
            tuple[str, ...],
            bool,
        ] | None:
            """Resolve one contrast endpoint from frozen, fragment-local axes.

            This is deliberately a final generic fallback.  The higher-priority
            action/change, residue/unfinished, coexistence, and finite
            wish/constraint recognizers above retain their existing decisions.
            A fallback endpoint is admitted only when its own source slice has
            current-user ownership and at least one already-frozen grammatical
            operator.  Whole-span operators are never copied into a child.
            """

            top_level_fragment = _top_level_text(fragment)
            if top_level_fragment is None:
                return None
            top_level_fragment = top_level_fragment.strip()
            connector_nominal_endpoint = next(
                (
                    (pattern, match)
                    for pattern in _FINITE_OPERATOR_PATTERNS
                    for match in pattern.finditer(top_level_fragment)
                    if fragment.strip() == left_text.strip()
                    and match.start() == 0
                    and match.end() == len(top_level_fragment)
                    and (
                        (
                            connector_nominal_mode == "na"
                            and _operator_supports_occurrence_na(
                                match.group(0),
                                pattern,
                            )
                        )
                        or (
                            connector_nominal_mode == "ellipsis"
                            and _operator_supports_explanatory_na(
                                match.group(0),
                                pattern,
                            )
                        )
                    )
                ),
                None,
            )
            if (
                not top_level_fragment
                or top_level_fragment != fragment.strip()
                or (
                    connector_nominal_endpoint is None
                    and not owner_scope_is_bound(top_level_fragment)
                )
            ):
                return None
            operators = set(
                _operator_codes_for_text(
                    top_level_fragment,
                    source_field=source_field,
                )
            )
            # Safety-owned self evaluation must keep its existing unsplit
            # priority.  A desiderative that is locally negated/refused is not
            # promoted to a positive wish endpoint.
            if "operator:self_evaluation" in operators:
                return None

            positive_wish, finite_wish_endpoint = affirmative_wish_proof(
                top_level_fragment
            )
            locally_denied_wish = bool(
                re.search(
                    r"(?:たい|ほしい|欲しい)(?:気持ち|願い|わけ)"
                    r"(?:は|が|も|では|じゃ)?"
                    r"(?:ない|なかった|ありません|ありませんでした)$",
                    top_level_fragment,
                )
                or re.search(
                    r"(?:たい|ほしい|欲しい)(?:と|とは)?思"
                    r"(?:わない|っていない|っていなかった|いません)$",
                    top_level_fragment,
                )
            )
            if (
                locally_denied_wish
                or (
                    not positive_wish
                    and "operator:wish" in operators
                    and operators & {"operator:negation", "operator:refusal"}
                )
            ):
                return None

            def endpoint_final_match(
                *patterns: re.Pattern[str],
            ) -> re.Match[str] | None:
                return _last_finite_operator_match(
                    top_level_fragment,
                    *patterns,
                )

            negated = "operator:negation" in operators
            refused = "operator:refusal" in operators
            cancellation_matches = tuple(
                _NEGATED_CONSTRAINT_CANCELLATION_INNER_RE.finditer(
                    top_level_fragment
                )
            )
            constraint_cancelled = any(
                (
                    not top_level_fragment[match.end() :]
                    or _finite_endpoint_carrier_shape(
                        top_level_fragment[match.end() :],
                        operator_surface=match.group(0),
                        operator_pattern=_CONSTRAINT_RE,
                    )
                )
                for match in cancellation_matches
            )
            if not constraint_cancelled:
                wrapped_constraint = _last_finite_operator_match(
                    top_level_fragment,
                    _CONSTRAINT_RE,
                )
                constraint_cancelled = bool(
                    wrapped_constraint is not None
                    and re.fullmatch(
                        r"(?:な)?こと(?:は|が|も)?"
                        r"(?:ない|なかった|ありません|"
                        r"ありませんでした)"
                        r"(?:(?:の|ん)(?:だ|です|だった|でした))?",
                        top_level_fragment[wrapped_constraint.end() :],
                    )
                    is not None
                )
            unfinished_matches = tuple(
                _OPEN_UNFINISHED_RE.finditer(top_level_fragment)
            )
            unfinished = bool(
                len(unfinished_matches) == 1
                and unfinished_matches[0].end() == len(top_level_fragment)
            )
            constraint_occurs = bool(
                "operator:constraint" in operators
                and not constraint_cancelled
            )
            constraint_final = (
                None
                if constraint_cancelled
                else endpoint_final_match(_CONSTRAINT_RE)
            )
            if (
                constraint_final is None
                and connector_nominal_endpoint is not None
                and connector_nominal_endpoint[0] is _CONSTRAINT_RE
            ):
                constraint_final = connector_nominal_endpoint[1]
            uncertainty_occurs = bool(
                "operator:uncertainty" in operators
                or _RELATION_UNCERTAINTY_RE.search(top_level_fragment)
            )
            uncertainty_final = endpoint_final_match(
                _RELATION_UNCERTAINTY_RE,
                _UNCERTAIN_RE,
            )
            if (
                uncertainty_final is None
                and connector_nominal_endpoint is not None
                and connector_nominal_endpoint[0]
                in {_RELATION_UNCERTAINTY_RE, _UNCERTAIN_RE}
            ):
                uncertainty_final = connector_nominal_endpoint[1]
            terminal_uncertainty_primary = uncertainty_final is not None
            refusal_final = endpoint_final_match(_REFUSAL_RE)
            change_final = endpoint_final_match(
                _POSITIVE_CHANGE_RE,
                _CHANGE_RE,
            )
            if (
                change_final is None
                and connector_nominal_endpoint is not None
                and connector_nominal_endpoint[0]
                in {_POSITIVE_CHANGE_RE, _CHANGE_RE}
            ):
                change_final = connector_nominal_endpoint[1]
            positive_change_final = endpoint_final_match(
                _POSITIVE_CHANGE_RE
            )
            feeling_final = endpoint_final_match(_FEELING_RE)
            if (
                feeling_final is None
                and connector_nominal_endpoint is not None
                and connector_nominal_endpoint[0] is _FEELING_RE
            ):
                feeling_final = connector_nominal_endpoint[1]
            if feeling_final is None:
                # A frozen feeling used as the complete semantic subject of
                # an immediately following finite continuation predicate is
                # still the asserted experience endpoint.  Requiring exact
                # ``が`` adjacency avoids promoting a modifier such as
                # ``不安の記録が続いている``.
                feeling_final = next(
                    (
                        match
                        for match in _FEELING_RE.finditer(
                            top_level_fragment
                        )
                        if top_level_fragment[match.end() :].startswith("が")
                        and (
                            continuation_match := _last_finite_operator_match(
                                top_level_fragment[match.end() + 1 :],
                                _CONTINUATION_RE,
                            )
                        )
                        is not None
                        and continuation_match.start() == 0
                    ),
                    None,
                )
            value_final = (
                None if negated else endpoint_final_match(_VALUE_RE)
            )
            if (
                value_final is None
                and not negated
                and connector_nominal_endpoint is not None
                and connector_nominal_endpoint[0] is _VALUE_RE
            ):
                value_final = connector_nominal_endpoint[1]
            passive_perfective = bool(
                re.search(
                    r"[かがさざただなばぱまらわ]れ"
                    r"(?:た|ました|て(?:いた|いました))$",
                    top_level_fragment,
                )
            )
            generic_finite_patterns = (
                *((_POSITIVE_CHANGE_RE,) if "operator:positive_change" in operators else ()),
                *((_FEELING_RE,) if "operator:feeling" in operators else ()),
                *((_WISH_RE,) if "operator:wish" in operators else ()),
                *((_REFUSAL_RE,) if "operator:refusal" in operators else ()),
                *((_UNCERTAIN_RE,) if "operator:uncertainty" in operators else ()),
                *((_RELATION_UNCERTAINTY_RE,) if _RELATION_UNCERTAINTY_RE.search(top_level_fragment) else ()),
                *((_CONSTRAINT_RE,) if constraint_occurs else ()),
                *((_CHANGE_RE,) if "operator:change" in operators else ()),
                *((_VALUE_RE,) if "operator:value" in operators else ()),
                *((_HELP_SEEKING_RE,) if "operator:help_seeking" in operators else ()),
                *((_NEGATION_RE,) if "operator:negation" in operators else ()),
                *((_CONTINUATION_RE,) if "operator:continuation" in operators else ()),
                *((_OPEN_UNFINISHED_RE,) if _OPEN_UNFINISHED_RE.search(top_level_fragment) else ()),
            )
            generic_finite_state_matches = tuple(
                match
                for pattern in generic_finite_patterns
                for match in pattern.finditer(top_level_fragment)
                if (
                    match.start() == 0
                    or (
                        pattern is _NEGATION_RE
                        and top_level_fragment[: match.start()].endswith(
                            ("てい", "でい")
                        )
                    )
                )
                and _operator_match_has_finite_closure(
                    top_level_fragment,
                    pattern,
                    match,
                )
            )
            generic_finite_state_match = (
                max(
                    generic_finite_state_matches,
                    key=lambda match: match.end(),
                )
                if generic_finite_state_matches
                else None
            )
            if generic_finite_state_match is None and constraint_cancelled:
                generic_finite_state_match = next(
                    (
                        match
                        for match in cancellation_matches
                        if match.start() == 0
                        and match.end() == len(top_level_fragment)
                    ),
                    None,
                )
            generic_finite_state_proven = bool(
                generic_finite_state_match is not None
                and not passive_perfective
            )
            # Choose the primary terminal predicate before rejecting earlier
            # semantic material.  A finite affirmative wish may legitimately
            # contain a feeling noun or an epistemic host; those subordinate
            # operators must not veto the wish endpoint.  Non-wish endpoints,
            # and action in particular, retain the strict modifier guards.
            if not positive_wish and not terminal_uncertainty_primary:
                if (
                    constraint_occurs
                    and constraint_final is None
                    and not generic_finite_state_proven
                ):
                    return None
                if (
                    uncertainty_occurs
                    and uncertainty_final is None
                    and not unfinished
                    and not generic_finite_state_proven
                ):
                    return None
                if (
                    "operator:refusal" in operators
                    and refusal_final is None
                    and not generic_finite_state_proven
                ):
                    return None
                if (
                    "operator:change" in operators
                    and change_final is None
                    and not generic_finite_state_proven
                ):
                    return None
                if (
                    "operator:feeling" in operators
                    and feeling_final is None
                    and not generic_finite_state_proven
                ):
                    return None
                if (
                    "operator:value" in operators
                    and value_final is None
                    and not generic_finite_state_proven
                ):
                    return None
            if (
                negated
                and uncertainty_final is not None
                and _NEGATION_RE.search(
                    top_level_fragment[uncertainty_final.end() :]
                )
            ):
                return None
            uncertain = bool(
                uncertainty_final is not None
                or unfinished
            )
            performed_action = structurally_performed_action(
                top_level_fragment
            )

            kind: NucleusKind
            predicate_kind: str
            polarity: Literal["positive", "negative", "mixed", "neutral"]
            modality: Literal[
                "fact",
                "feeling",
                "wish",
                "possibility",
                "uncertain",
                "refusal",
                "intention",
            ]
            role_codes: tuple[str, ...]
            finite_endpoint_proven: bool
            generic_finite_state_selected = False
            finite_clause_proven = bool(
                connector_nominal_endpoint is not None
                or _finite_endpoint_terminal_shape(top_level_fragment)
            )
            terminal_negation = _last_finite_operator_match(
                top_level_fragment,
                _NEGATION_RE,
            )
            terminal_negation_proven = bool(
                terminal_negation is not None
                or constraint_cancelled
                or (negated and generic_finite_state_proven)
            )
            if positive_wish:
                kind = "wish"
                predicate_kind = "wish"
                polarity = "positive"
                modality = "wish"
                role_codes = ("semantic_role:retained_intention",)
                finite_endpoint_proven = finite_wish_endpoint
            elif unfinished:
                kind = "uncertainty"
                predicate_kind = "unfinished"
                polarity = "negative" if negated else "neutral"
                modality = "uncertain"
                role_codes = (
                    "operator:unfinished",
                    "semantic_role:present_unfinished",
                    "semantic_role:burden",
                )
                finite_endpoint_proven = finite_clause_proven
            elif constraint_final is not None:
                kind = "constraint"
                predicate_kind = "constraint"
                polarity = "negative" if negated else "neutral"
                modality = "uncertain" if uncertain else "possibility"
                role_codes = ("semantic_role:burden",)
                finite_endpoint_proven = finite_clause_proven
            elif uncertain:
                kind = "uncertainty"
                predicate_kind = "uncertainty"
                polarity = "negative" if negated else "neutral"
                modality = "uncertain"
                role_codes = ("semantic_role:burden",)
                finite_endpoint_proven = finite_clause_proven
            elif refused and refusal_final is not None:
                kind = "state"
                predicate_kind = "refusal"
                polarity = "negative"
                modality = "refusal"
                role_codes = (
                    "semantic_role:protective_or_limiting_refusal",
                    "semantic_role:burden",
                )
                finite_endpoint_proven = finite_clause_proven
            elif change_final is not None:
                kind = "change"
                predicate_kind = "change"
                polarity = (
                    "negative"
                    if negated
                    else "positive"
                    if positive_change_final is not None
                    else "neutral"
                )
                modality = (
                    "feeling"
                    if "operator:feeling" in operators
                    else "fact"
                )
                role_codes = ("semantic_role:current_change",)
                finite_endpoint_proven = finite_clause_proven
            elif feeling_final is not None:
                kind = "reaction"
                predicate_kind = "feeling"
                polarity = "negative"
                modality = "feeling"
                role_codes = ("semantic_role:burden",)
                finite_endpoint_proven = finite_clause_proven
            elif value_final is not None:
                kind = "value"
                predicate_kind = "value"
                polarity = "positive"
                modality = "fact"
                role_codes = ("semantic_role:explicit_evaluation",)
                finite_endpoint_proven = finite_clause_proven
            elif (
                (performed_action or "operator:action" in operators)
                and _EXPLICIT_PERFECTIVE_END_RE.search(
                    top_level_fragment
                )
                is not None
                and not passive_perfective
            ) and not operators & {
                "operator:wish",
                "operator:constraint",
                "operator:uncertainty",
                "operator:feeling",
                "operator:value",
                "operator:change",
                "operator:positive_change",
                "operator:help_seeking",
                "operator:refusal",
                "operator:negation",
                "operator:self_evaluation",
            }:
                kind = "action"
                predicate_kind = "action"
                polarity = "neutral"
                modality = "fact"
                role_codes = ("semantic_role:concrete_action",)
                finite_endpoint_proven = finite_clause_proven
            elif generic_finite_state_proven:
                kind = "state"
                predicate_kind = "state"
                polarity = (
                    "negative" if terminal_negation_proven else "neutral"
                )
                modality = "fact"
                role_codes = ()
                finite_endpoint_proven = finite_clause_proven
                generic_finite_state_selected = True
            else:
                return None

            if generic_finite_state_selected:
                local_operator_codes = (
                    ("operator:negation",)
                    if terminal_negation_proven
                    else ()
                )
            else:
                local_operator_codes = tuple(
                    code
                    for code in _operator_codes_for_text(
                        top_level_fragment,
                        source_field=source_field,
                    )
                    if code != "operator:contrast"
                    and (code != "operator:wish" or positive_wish)
                    and not (
                        positive_wish
                        and code in {
                            "operator:negation",
                            "operator:refusal",
                            "operator:constraint",
                            "operator:feeling",
                            "operator:uncertainty",
                            "operator:change",
                            "operator:positive_change",
                            "operator:value",
                        }
                    )
                    and not (
                        terminal_uncertainty_primary
                        and code in {
                            "operator:wish",
                            "operator:negation",
                            "operator:refusal",
                            "operator:constraint",
                            "operator:feeling",
                            "operator:change",
                            "operator:positive_change",
                            "operator:value",
                            "operator:continuation",
                        }
                    )
                )
            return (
                kind,
                predicate_kind,
                polarity,
                modality,
                tuple(_dedupe((*local_operator_codes, *role_codes))),
                finite_endpoint_proven,
            )

        def fragment_has_admitted_contrast(fragment: str) -> bool:
            """Reject an outer candidate that would hide another true link."""

            top_level_fragment = _top_level_text(fragment)
            if top_level_fragment is None:
                return False
            nested_links = (
                *_top_level_pattern_matches(
                    top_level_fragment,
                    _TOP_LEVEL_CONTRAST_LINK_RE,
                ),
                *_top_level_pattern_matches(
                    top_level_fragment,
                    _TOP_LEVEL_BARE_GA_LINK_RE,
                ),
            )

            def nested_trimmed_range(start: int, end: int) -> tuple[int, int]:
                while (
                    start < end
                    and top_level_fragment[start] in " \t\r\n、,。．.!！?？"
                ):
                    start += 1
                while (
                    start < end
                    and top_level_fragment[end - 1]
                    in " \t\r\n、,。．.!！?？"
                ):
                    end -= 1
                return start, end

            for nested_link in nested_links:
                nested_left_start, nested_left_end = nested_trimmed_range(
                    0,
                    nested_link.start(),
                )
                nested_right_start, nested_right_end = nested_trimmed_range(
                    nested_link.end(),
                    len(top_level_fragment),
                )
                if not (
                    nested_left_start < nested_left_end <= nested_link.start()
                    and nested_link.end()
                    <= nested_right_start
                    < nested_right_end
                ):
                    continue
                nested_left = top_level_fragment[
                    nested_left_start:nested_left_end
                ]
                nested_right = top_level_fragment[
                    nested_right_start:nested_right_end
                ]
                nested_left_profile = generic_contrast_endpoint_profile(
                    nested_left
                )
                nested_right_profile = generic_contrast_endpoint_profile(
                    nested_right
                )
                if (
                    nested_left_profile is not None
                    and nested_right_profile is not None
                    and (
                        not nested_link.group(0).startswith("が")
                        or nested_left_profile[5]
                    )
                ):
                    return True
            return False

        # The specialized branch above intentionally covers its narrow finite
        # wish/constraint shape first.  For the generic fallback, raw ``が``
        # occurrences are only candidates: exact2 independently proven
        # endpoint profiles plus a finite left-clause proof admit a link.  This
        # keeps a nominative particle out of the relation count while allowing
        # one comma-less conjunctive link even when another raw ``が`` occurs
        # inside an endpoint.
        admitted_contrasts: list[
            tuple[
                int,
                int,
                int,
                int,
                str,
                str,
                tuple[
                    NucleusKind,
                    str,
                    Literal["positive", "negative", "mixed", "neutral"],
                    Literal[
                        "fact",
                        "feeling",
                        "wish",
                        "possibility",
                        "uncertain",
                        "refusal",
                        "intention",
                    ],
                    tuple[str, ...],
                    bool,
                ],
                tuple[
                    NucleusKind,
                    str,
                    Literal["positive", "negative", "mixed", "neutral"],
                    Literal[
                        "fact",
                        "feeling",
                        "wish",
                        "possibility",
                        "uncertain",
                        "refusal",
                        "intention",
                    ],
                    tuple[str, ...],
                    bool,
                ],
            ]
        ] = []
        for candidate_link in generic_contrast_links:
            candidate_left_start, candidate_left_end = trimmed_range(
                0,
                candidate_link.start(),
            )
            candidate_right_start, candidate_right_end = trimmed_range(
                candidate_link.end(),
                len(text),
            )
            if not (
                candidate_left_start
                < candidate_left_end
                <= candidate_link.start()
                and candidate_link.end()
                <= candidate_right_start
                < candidate_right_end
                and text[candidate_link.start() : candidate_link.end()]
                == candidate_link.group(0)
            ):
                continue
            candidate_left_text = text[
                candidate_left_start:candidate_left_end
            ]
            candidate_right_text = text[
                candidate_right_start:candidate_right_end
            ]
            candidate_left_profile = generic_contrast_endpoint_profile(
                candidate_left_text
            )
            candidate_right_profile = generic_contrast_endpoint_profile(
                candidate_right_text
            )
            if (
                candidate_left_profile is None
                or candidate_right_profile is None
                or (
                    candidate_link.group(0).startswith("が")
                    and not candidate_left_profile[5]
                )
            ):
                continue
            if fragment_has_admitted_contrast(
                candidate_left_text
            ) or fragment_has_admitted_contrast(candidate_right_text):
                continue
            admitted_contrasts.append(
                (
                    candidate_left_start,
                    candidate_left_end,
                    candidate_right_start,
                    candidate_right_end,
                    candidate_left_text,
                    candidate_right_text,
                    candidate_left_profile,
                    candidate_right_profile,
                )
            )
        if len(admitted_contrasts) == 1:
            (
                left_start,
                left_end,
                right_start,
                right_end,
                left_text,
                right_text,
                left_profile,
                right_profile,
            ) = admitted_contrasts[0]
            (
                left_kind,
                left_predicate,
                left_polarity,
                left_modality,
                left_codes,
                _left_finite,
            ) = left_profile
            (
                right_kind,
                right_predicate,
                right_polarity,
                right_modality,
                right_codes,
                _right_finite,
            ) = right_profile
            burden_kinds = {
                "constraint",
            }
            if (
                (left_kind == "wish" and right_kind in burden_kinds)
                or (right_kind == "wish" and left_kind in burden_kinds)
            ):
                relation_kind: RelationKind = "wish_and_constraint"
            else:
                relation_kind = "contrast"
            common_codes = (
                "semantic_role:span_relation_endpoint",
                "semantic_role:generic_relation_fragment",
            )
            return (
                _TypedNucleusProjection(
                    nucleus_suffix="",
                    kind=left_kind,
                    predicate_kind=left_predicate,
                    polarity=left_polarity,
                    modality=left_modality,
                    time_scope=_time_scope_for_text(left_text),
                    scalar_start=left_start,
                    scalar_end=left_end,
                    attribute_codes=relation_fragment_codes(
                        left_start,
                        left_end,
                        *left_codes,
                        *common_codes,
                    ),
                    relation_kind=relation_kind,
                ),
                _TypedNucleusProjection(
                    nucleus_suffix=":contrasting",
                    kind=right_kind,
                    predicate_kind=right_predicate,
                    polarity=right_polarity,
                    modality=right_modality,
                    time_scope=_time_scope_for_text(right_text),
                    scalar_start=right_start,
                    scalar_end=right_end,
                    attribute_codes=relation_fragment_codes(
                        right_start,
                        right_end,
                        *right_codes,
                        *common_codes,
                        "semantic_role:compound_reception_coowned_nonprimary",
                    ),
                    relation_kind=relation_kind,
                    grounding_kind="user_stated_relation",
                ),
            )
    return ()


def _priority_for_nucleus(span: EvidenceSpan, retention: Retention, kind: NucleusKind) -> float:
    base = {"required": 0.92, "should": 0.72, "optional": 0.42}[retention]
    if _clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS:
        base += 0.03
    if kind in {"change", "wish", "constraint", "self_evaluation", "action", "value"}:
        base += 0.02
    return _clamp(max(base, float(getattr(span, "confidence", 0.0) or 0.0) * 0.85))


def _build_nuclei(
    *,
    spans: Sequence[EvidenceSpan],
    board: PerspectiveBoard,
    meaning_artifacts: _MeaningArtifacts,
    safety_decision: EmlisSafetyTriageDecision,
) -> tuple[GroundedSemanticNucleus, ...]:
    block_span_ids = _meaning_block_span_ids(meaning_artifacts.meaning_blocks, spans)
    roles_by_span, block_keys_by_span = _roles_and_block_keys_by_span(
        meaning_artifacts.meaning_blocks,
        block_span_ids,
    )
    retention_by_span = _retention_by_span(
        spans,
        block_span_ids=block_span_ids,
        meaning_artifacts=meaning_artifacts,
        safety_decision=safety_decision,
    )
    claim_ids_by_span = _claim_ids_by_span(board)
    safety_ids = _ordered_span_ids(getattr(safety_decision, "evidence_span_ids", ()) or ())
    safety_span_order = {span_id: index for index, span_id in enumerate(safety_ids)}
    arc_roles_by_span = _arc_roles_by_span(spans)

    nuclei: list[GroundedSemanticNucleus] = []
    for span in _sort_spans(spans):
        span_id = _clean(getattr(span, "span_id", ""))
        if not span_id:
            continue
        roles = roles_by_span.get(span_id, ())
        claim_ids = claim_ids_by_span.get(span_id, ())
        retention = retention_by_span.get(span_id, "optional")
        kind = _kind_for_span(
            span,
            roles=roles,
            safety_decision=safety_decision,
            safety_span_order=safety_span_order,
        )
        field_name = _clean(getattr(span, "source_field", ""))
        grounding_kind: GroundingKind = (
            "user_stated_relation"
            if _clean(getattr(span, "detected_type", "")) == "relation_marker"
            else "explicit"
        )
        nuclei.append(
            GroundedSemanticNucleus(
                nucleus_id=f"nucleus:{span_id}",
                kind=kind,
                source_span_ids=(span_id,),
                source_fields=(field_name,),
                surface_anchor_ids=(span_id,),
                semantic_frame=_semantic_frame_for_span(
                    span,
                    kind=kind,
                    roles=roles,
                    claim_ids=claim_ids,
                    arc_role_codes=arc_roles_by_span.get(span_id, ()),
                ),
                grounding_kind=grounding_kind,
                certainty=_clamp(getattr(span, "confidence", 0.0)),
                priority=_priority_for_nucleus(span, retention, kind),
                retention=retention,
                allowed_claim_scope=(
                    "selected_label_only"
                    if field_name in _LABEL_SOURCE_FIELDS
                    else "source_bounded_relation"
                    if grounding_kind == "user_stated_relation"
                    else "explicit_current_input"
                ),
                forbidden_inference_codes=(
                    "unsupported_cause",
                    "unsupported_personality",
                    "diagnosis",
                    "period_tendency_from_single_record",
                    "input_external_fact",
                ),
                source_claim_ids=tuple(claim_ids),
                source_meaning_block_keys=tuple(block_keys_by_span.get(span_id, ())),
            )
        )
    return tuple(nuclei)


def _apply_short_state_lexical_policy(
    nuclei: Sequence[GroundedSemanticNucleus],
    spans: Sequence[EvidenceSpan],
    *,
    material_quality: str,
    relations: Sequence[GroundedSemanticRelation],
) -> tuple[GroundedSemanticNucleus, ...]:
    """Attach source-bound lexical constraints to a true single short state.

    These codes are policy facts, not a completed response.  They tell the
    realizer and Gate that the user's predicate family must remain visible and
    that an unrelated sensation metaphor must not be introduced.
    """

    if material_quality != "short_state_sufficient" or relations:
        return tuple(nuclei)
    candidates = tuple(
        item
        for item in nuclei
        if item.retention == "required"
        and item.kind != "other_explicit"
        and any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
    )
    if len(candidates) != 1:
        return tuple(nuclei)
    target_id = candidates[0].nucleus_id
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    source_text = " ".join(
        _clean(getattr(span_index.get(span_id), "raw_text", ""))
        for span_id in candidates[0].source_span_ids
    )
    policy_codes = [
        "lexical:preserve_source_predicate",
        "lexical:no_new_sensation_family",
    ]
    if _SOURCE_METAPHOR_RE.search(source_text):
        policy_codes.append("lexical:source_metaphor_present")
    output: list[GroundedSemanticNucleus] = []
    for item in nuclei:
        if item.nucleus_id != target_id:
            output.append(item)
            continue
        output.append(
            replace(
                item,
                semantic_frame=replace(
                    item.semantic_frame,
                    attribute_codes=tuple(
                        _dedupe([*item.semantic_frame.attribute_codes, *policy_codes])
                    ),
                ),
            )
        )
    return tuple(output)


def _claim_to_nucleus_id(
    board: PerspectiveBoard,
    claim_id: Any,
    nucleus_by_span: Mapping[str, str],
) -> str | None:
    claims = dict(getattr(board, "claim_index", {}) or getattr(board, "claims_by_id", {}) or {})
    claim = claims.get(_clean(claim_id))
    if claim is None:
        return None
    for span_id in _ordered_span_ids(getattr(claim, "evidence_span_ids", ()) or ()):
        if span_id in nucleus_by_span:
            return nucleus_by_span[span_id]
    return None


def _relation_retention(
    from_id: str,
    to_id: str,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    *,
    relation_type: RelationKind,
    grounding_kind: GroundingKind,
) -> Retention:
    left = nucleus_index[from_id].retention
    right = nucleus_index[to_id].retention
    if "optional" in {left, right}:
        return "optional"
    # Adjacency-only inference is context, not a required claim.  A relation
    # becomes required only after structural operators promote it to a
    # source-stated relation (for example a continuation/refusal sentence).
    if grounding_kind == "bounded_structural_inference":
        left_roles = set(nucleus_index[from_id].semantic_frame.attribute_codes)
        right_roles = set(nucleus_index[to_id].semantic_frame.attribute_codes)
        if (
            relation_type == "action_supports_change"
            and left == right == "required"
            and "semantic_role:concrete_action_evidence" in right_roles
            and bool(
                left_roles
                & {
                    "semantic_role:retained_intention",
                    "semantic_role:current_change",
                }
            )
        ):
            return "required"
        return "should"
    if relation_type == "uncertain_connection":
        return "should"
    if left == right == "required":
        return "required"
    return "should"


def _append_relation_seed(seeds: list[_RelationSeed], seed: _RelationSeed) -> None:
    if not seed.from_nucleus_id or not seed.to_nucleus_id or seed.from_nucleus_id == seed.to_nucleus_id:
        return
    canonical_key = (seed.from_nucleus_id, seed.to_nucleus_id)
    grounding_rank = {
        "bounded_structural_inference": 0,
        "user_stated_relation": 1,
        "explicit": 2,
    }
    type_rank = {
        "uncertain_connection": 0,
        "coexistence": 1,
        "contrast": 2,
        "shift_from_to": 3,
        "evaluation_about_event": 3,
        "self_evaluation_about_state": 3,
        "temporal_before_after": 3,
        "user_stated_cause": 4,
        "user_stated_result": 4,
        "wish_and_constraint": 4,
        "attempt_and_block": 4,
        "action_supports_change": 4,
        "continuation_or_refusal": 5,
        "preserves_despite": 5,
    }

    def candidate_rank(item: _RelationSeed) -> tuple[int, int, int, float]:
        source_rank = 1
        if any(ref.startswith("evidence_relation_marker:") for ref in item.source_relation_ids):
            source_rank = 3
        elif "whole_input_source_order" in item.source_relation_ids:
            source_rank = 2
        elif "source_field_transition:memo_to_memo_action" in item.source_relation_ids:
            source_rank = 2
        elif item.source_relation_ids:
            source_rank = 4
        return (
            grounding_rank.get(item.grounding_kind, -1),
            source_rank,
            type_rank.get(item.type, 0),
            item.certainty,
        )
    for index, item in enumerate(seeds):
        item_key = (item.from_nucleus_id, item.to_nucleus_id)
        if item_key != canonical_key:
            continue
        # Existing graph edges, relation-marker evidence, and source-order
        # analysis can describe the same directed pair with different type
        # guesses.  Keep the strongest/first source-grounded interpretation so
        # the public surface does not repeat one pair under multiple labels.
        item_rank = candidate_rank(item)
        seed_rank = candidate_rank(seed)
        winner = seed if seed_rank > item_rank else item
        stronger_grounding = winner.grounding_kind
        # The strongest/first semantic owner keeps its binding evidence.  This
        # preserves an upstream relation edge's exact provenance instead of
        # silently adding a nearby marker that a later adapter happened to see.
        stronger_source_span_ids = (
            winner.source_span_ids or item.source_span_ids or seed.source_span_ids
        )
        seeds[index] = _RelationSeed(
            type=winner.type,
            from_nucleus_id=item.from_nucleus_id,
            to_nucleus_id=item.to_nucleus_id,
            source_span_ids=stronger_source_span_ids,
            grounding_kind=stronger_grounding,
            certainty=max(item.certainty, seed.certainty),
            retention=_retention_max(item.retention, seed.retention),
            source_relation_ids=tuple(
                _dedupe([*item.source_relation_ids, *seed.source_relation_ids])
            ),
            source_meaning_arc_keys=tuple(
                _dedupe([*item.source_meaning_arc_keys, *seed.source_meaning_arc_keys])
            ),
        )
        return
    seeds.append(seed)


def _build_relations(
    *,
    spans: Sequence[EvidenceSpan],
    board: PerspectiveBoard,
    nuclei: Sequence[GroundedSemanticNucleus],
    meaning_artifacts: _MeaningArtifacts,
) -> tuple[GroundedSemanticRelation, ...]:
    nucleus_index = {item.nucleus_id: item for item in nuclei}
    nucleus_by_span = {
        span_id: item.nucleus_id
        for item in nuclei
        for span_id in item.source_span_ids
    }
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    seeds: list[_RelationSeed] = []

    def source_text_for_ids(span_ids: Sequence[str]) -> str:
        return " ".join(
            _clean(getattr(span_index.get(span_id), "raw_text", ""))
            for span_id in span_ids
            if span_id in span_index
        )

    def boundary_marker_text(left_id: str, right_id: str) -> str:
        left_text = source_text_for_ids(nucleus_index[left_id].source_span_ids)
        right_text = source_text_for_ids(nucleus_index[right_id].source_span_ids)
        if _LEADING_CONTRAST_RE.search(right_text):
            return right_text
        if _BOUNDARY_RESULT_RE.search(right_text):
            return right_text
        if _BOUNDARY_CAUSE_RE.search(left_text):
            return left_text
        return ""

    def syntactically_dependent_pair(left_id: str, right_id: str) -> bool:
        left_text = source_text_for_ids(nucleus_index[left_id].source_span_ids)
        right_text = source_text_for_ids(nucleus_index[right_id].source_span_ids)
        return bool(
            re.search(r"(?:何故|なぜ|どうして)$", left_text)
            or re.match(r"^(?:と考えて(?:いた|しまって)|とか|という)", right_text)
        )

    existing_relations: Sequence[RelationEdge] = tuple(
        dict(getattr(board, "relation_index", {}) or getattr(board, "relations_by_id", {}) or {}).values()
    )
    for edge in existing_relations:
        from_id = _claim_to_nucleus_id(board, getattr(edge, "from_claim_id", ""), nucleus_by_span)
        to_id = _claim_to_nucleus_id(board, getattr(edge, "to_claim_id", ""), nucleus_by_span)
        if not from_id or not to_id:
            continue
        source_ids = tuple(_ordered_span_ids(getattr(edge, "evidence_span_ids", ()) or ()))
        relation_type = _RELATION_KIND_BY_EXISTING_TYPE.get(_clean(getattr(edge, "relation_type", "")))
        if relation_type is None:
            relation_type = _relation_type_for_pair(
                nucleus_index[from_id],
                nucleus_index[to_id],
                source_text=source_text_for_ids(source_ids),
            )
        _append_relation_seed(
            seeds,
            _RelationSeed(
                type=relation_type,
                from_nucleus_id=from_id,
                to_nucleus_id=to_id,
                source_span_ids=source_ids,
                grounding_kind="user_stated_relation",
                certainty=_clamp(getattr(edge, "confidence", 0.0)),
                retention=_relation_retention(
                    from_id,
                    to_id,
                    nucleus_index,
                    relation_type=relation_type,
                    grounding_kind="user_stated_relation",
                ),
                source_relation_ids=(_clean(getattr(edge, "edge_id", "")),),
            ),
        )

    text_spans = _sort_spans(_text_spans(spans))
    by_field: dict[str, list[EvidenceSpan]] = {}
    for span in text_spans:
        by_field.setdefault(_clean(getattr(span, "source_field", "")), []).append(span)
    for field_spans in by_field.values():
        for index, span in enumerate(field_spans):
            if _clean(getattr(span, "detected_type", "")) != "relation_marker":
                continue
            marker_id = _clean(getattr(span, "span_id", ""))
            marker_nucleus = nucleus_by_span.get(marker_id)
            previous = _nearest_substantive_span(field_spans, index - 1, -1)
            following = _nearest_substantive_span(field_spans, index + 1, 1)
            if _is_pure_relation_marker(span):
                left = nucleus_by_span.get(_clean(getattr(previous, "span_id", ""))) if previous else None
                right = nucleus_by_span.get(_clean(getattr(following, "span_id", ""))) if following else None
            else:
                marker_text = _clean(getattr(span, "raw_text", ""))
                # When both sides of an embedded marker remain in one ledger
                # span, the plan cannot truthfully invent an endpoint in the
                # preceding span.  Keep that span as an embedded major turn;
                # only a leading boundary marker may connect it locally to the
                # nearest previous substantive nucleus.
                if not (
                    _LEADING_CONTRAST_RE.search(marker_text)
                    or _BOUNDARY_RESULT_RE.search(marker_text)
                ):
                    continue
                left = nucleus_by_span.get(_clean(getattr(previous, "span_id", ""))) if previous else marker_nucleus
                right = marker_nucleus if previous else (
                    nucleus_by_span.get(_clean(getattr(following, "span_id", ""))) if following else None
                )
            if not left or not right:
                continue
            source_ids = tuple(
                _ordered_span_ids(
                    [marker_id, *nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids]
                )
            )
            relation_type = _relation_type_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                source_text=source_text_for_ids(source_ids),
                explicit_marker_text=_clean(getattr(span, "raw_text", "")),
            )
            _append_relation_seed(
                seeds,
                _RelationSeed(
                    type=relation_type,
                    from_nucleus_id=left,
                    to_nucleus_id=right,
                    source_span_ids=source_ids,
                    grounding_kind="user_stated_relation",
                    certainty=_clamp(getattr(span, "confidence", 0.0)),
                    retention=_relation_retention(
                        left,
                        right,
                        nucleus_index,
                        relation_type=relation_type,
                        grounding_kind="user_stated_relation",
                    ),
                    source_relation_ids=(f"evidence_relation_marker:{marker_id}",),
                ),
            )

    block_span_ids = _meaning_block_span_ids(meaning_artifacts.meaning_blocks, spans)
    arc = meaning_artifacts.whole_input_meaning_arc
    if arc is not None:
        representatives: list[str] = []
        for block_key in tuple(getattr(arc, "ordered_block_keys", ()) or ()):
            nucleus_id = next(
                (nucleus_by_span[span_id] for span_id in block_span_ids.get(_clean(block_key), ()) if span_id in nucleus_by_span),
                None,
            )
            if nucleus_id and (not representatives or representatives[-1] != nucleus_id):
                representatives.append(nucleus_id)
        for left, right in zip(representatives, representatives[1:]):
            if syntactically_dependent_pair(left, right):
                # Both fragments belong to one source clause.  They remain
                # required nuclei and are recombined by SentencePlan; treating
                # their punctuation split as a semantic edge would expose a
                # false from/to direction.
                continue
            source_ids = tuple(
                _ordered_span_ids([*nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids])
            )
            source_text = source_text_for_ids(source_ids)
            marker_text = boundary_marker_text(left, right)
            relation_type = _relation_type_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                source_text=source_text,
                explicit_marker_text=marker_text,
            )
            grounding_kind = _relation_grounding_kind_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                relation_type=relation_type,
                source_text=source_text,
                explicit_marker_text=marker_text,
            )
            # Source-order arcs may bridge ``memo`` and ``memo_action``.  The
            # field boundary alone does not state a semantic relation, so it
            # must not become a required public claim.  The dedicated bounded
            # action-support edge below remains available as context.
            if set(nucleus_index[left].source_fields) != set(nucleus_index[right].source_fields):
                grounding_kind = "bounded_structural_inference"
            _append_relation_seed(
                seeds,
                _RelationSeed(
                    type=relation_type,
                    from_nucleus_id=left,
                    to_nucleus_id=right,
                    source_span_ids=source_ids,
                    grounding_kind=grounding_kind,
                    certainty=_clamp(getattr(arc, "clarity", 0.0) * 0.72),
                    retention=_relation_retention(
                        left,
                        right,
                        nucleus_index,
                        relation_type=relation_type,
                        grounding_kind=grounding_kind,
                    ),
                    source_relation_ids=("whole_input_source_order",),
                    source_meaning_arc_keys=(_clean(getattr(arc, "arc_key", "")),),
                ),
            )

    memo_ids = [
        nucleus_by_span[span.span_id]
        for span in text_spans
        if span.source_field == "memo" and span.span_id in nucleus_by_span
    ]
    action_ids = [
        nucleus_by_span[span.span_id]
        for span in text_spans
        if span.source_field == "memo_action" and span.span_id in nucleus_by_span
    ]
    action_evidence_ids = [
        nucleus_id
        for nucleus_id in action_ids
        if "semantic_role:concrete_action_evidence"
        in nucleus_index[nucleus_id].semantic_frame.attribute_codes
    ]
    intention_or_change_ids = [
        nucleus_id
        for nucleus_id in memo_ids
        if nucleus_index[nucleus_id].retention == "required"
        and bool(
            set(nucleus_index[nucleus_id].semantic_frame.attribute_codes)
            & {
                "semantic_role:retained_intention",
                "semantic_role:current_change",
            }
        )
    ]
    if intention_or_change_ids and action_evidence_ids:
        left, right = intention_or_change_ids[-1], action_evidence_ids[0]
        source_ids = tuple(
            _ordered_span_ids([*nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids])
        )
        _append_relation_seed(
            seeds,
            _RelationSeed(
                type="action_supports_change",
                from_nucleus_id=left,
                to_nucleus_id=right,
                source_span_ids=source_ids,
                grounding_kind="bounded_structural_inference",
                certainty=0.64,
                retention=_relation_retention(
                    left,
                    right,
                    nucleus_index,
                    relation_type="action_supports_change",
                    grounding_kind="bounded_structural_inference",
                ),
                source_relation_ids=("source_field_transition:memo_to_memo_action",),
                source_meaning_arc_keys=(
                    _clean(getattr(arc, "arc_key", "")) if arc is not None else "current_input_source_order",
                ),
            ),
        )

    return tuple(
        GroundedSemanticRelation(
            relation_id=f"relation:r{index}",
            type=seed.type,
            from_nucleus_id=seed.from_nucleus_id,
            to_nucleus_id=seed.to_nucleus_id,
            source_span_ids=seed.source_span_ids,
            grounding_kind=seed.grounding_kind,
            certainty=seed.certainty,
            retention=seed.retention,
            source_relation_ids=tuple(_dedupe(seed.source_relation_ids)),
            source_meaning_arc_keys=tuple(_dedupe(seed.source_meaning_arc_keys)),
        )
        for index, seed in enumerate(seeds, start=1)
    )


def _build_unknown_boundaries(
    *,
    board: PerspectiveBoard,
    graph: ObservationGraph,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[GroundedUnknownBoundary, ...]:
    dimensions = _dedupe(
        [
            *list(getattr(graph, "missing_information", ()) or ()),
            *list(getattr(board, "uncertainty", ()) or ()),
        ]
    )
    affected = tuple(item.nucleus_id for item in nuclei if item.retention == "required")[:4]
    return tuple(
        GroundedUnknownBoundary(
            unknown_id=f"unknown:u{index}",
            dimension=dimension,
            affected_nucleus_ids=affected,
        )
        for index, dimension in enumerate(dimensions, start=1)
    )


def _text_presence(spans: Sequence[EvidenceSpan]) -> Literal["text_present", "labels_only", "empty"]:
    if any(_clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS for span in spans):
        return "text_present"
    if spans:
        return "labels_only"
    return "empty"


def _material_quality(
    *,
    text_presence: str,
    safety_kind: str,
    spans: Sequence[EvidenceSpan],
    nuclei: Sequence[GroundedSemanticNucleus],
) -> Literal[
    "grounded",
    "short_state_sufficient",
    "limited_grounding",
    "labels_only_limited",
    "empty",
    "safety_routed",
]:
    if safety_kind in {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}:
        return "safety_routed"
    if text_presence == "empty":
        return "empty"
    if text_presence == "labels_only":
        return "labels_only_limited"

    substantive = [span for span in _text_spans(spans) if _is_substantive_text_span(span)]
    if not substantive:
        return "limited_grounding"
    total_chars = sum(len(_compact(getattr(span, "raw_text", ""))) for span in substantive)
    text_nuclei = [
        nucleus
        for nucleus in nuclei
        if any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields)
        and nucleus.kind != "other_explicit"
    ]
    if not text_nuclei:
        return "limited_grounding"
    state_like = all(
        nucleus.kind in _SHORT_STATE_KINDS
        or nucleus.semantic_frame.modality in {"feeling", "refusal", "uncertain"}
        for nucleus in text_nuclei
    )
    contains_action_field = any("memo_action" in nucleus.source_fields for nucleus in text_nuclei)
    if total_chars <= 80 and len(substantive) <= 3 and state_like and not contains_action_field:
        return "short_state_sufficient"
    return "grounded"


def _semantic_complexity(
    *,
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    meaning_artifacts: _MeaningArtifacts,
) -> Literal["minimal", "single", "multi", "long_arc"]:
    if meaning_artifacts.coverage_plan is not None and bool(
        getattr(meaning_artifacts.coverage_plan, "clear_long_input", False)
    ):
        return "long_arc"
    text_count = sum(1 for item in nuclei if any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields))
    if text_count == 0:
        return "minimal"
    if text_count == 1 and not relations:
        return "single"
    return "multi"


_NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY: Final[tuple[GroundedHumanFollowRole, ...]] = (
    "help_seeking_preserved",
    "retained_intention",
    "concrete_effort",
    "valued_change",
    "burden_expression",
    "integrated_current_state",
)
_SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY: Final[tuple[GroundedHumanFollowRole, ...]] = (
    "help_seeking_preserved",
    "protective_counterdirection",
    "concrete_effort",
    "retained_intention",
    "burden_expression",
    "integrated_current_state",
)
_RECEPTION_ACT_BY_FOLLOW_ROLE: Final[dict[GroundedHumanFollowRole, GroundedReceptionAct]] = {
    "integrated_current_state": "stay_with_current_burden",
    "burden_expression": "stay_with_current_burden",
    "concrete_effort": "honor_concrete_effort",
    "retained_intention": "protect_retained_intention",
    "valued_change": "recognize_lived_change",
    "help_seeking_preserved": "hold_help_seeking",
    "protective_counterdirection": "bounded_counter_self_denial",
}
_FOLLOW_PROFILE_BY_RECEPTION_ACT: Final[
    dict[
        GroundedReceptionAct,
        tuple[GroundedFollowElement, tuple[GroundedFollowElement, ...], GroundedFollowElement | None],
    ]
] = {
    "stay_with_current_burden": (
        "burden_understanding",
        ("existence_respect",),
        None,
    ),
    "honor_concrete_effort": (
        "effort_receiving",
        ("intent_affirmation",),
        None,
    ),
    "protect_retained_intention": (
        "intent_affirmation",
        ("existence_respect",),
        None,
    ),
    "recognize_lived_change": (
        "effort_receiving",
        ("intent_affirmation",),
        None,
    ),
    "hold_help_seeking": (
        "effort_receiving",
        ("existence_respect",),
        "intent_affirmation",
    ),
    "bounded_counter_self_denial": (
        "existence_respect",
        ("effort_receiving",),
        None,
    ),
    "respect_words_placed": (
        "existence_respect",
        (),
        None,
    ),
}
_STANCE_BY_RECEPTION_ACT: Final[dict[GroundedReceptionAct, GroundedReceptionStance]] = {
    "stay_with_current_burden": "quiet_presence",
    "honor_concrete_effort": "warm_recognition",
    "protect_retained_intention": "gentle_respect",
    "recognize_lived_change": "warm_recognition",
    "hold_help_seeking": "protective_presence",
    "bounded_counter_self_denial": "bounded_disagreement",
    "respect_words_placed": "gentle_respect",
}
_RECEPTION_FORBIDDEN_SURFACE_CODES: Final[tuple[str, ...]] = (
    "generic_empathy_suffix",
    "second_observation_summary",
    "internal_policy_explanation",
    "full_source_quote_replay",
    "all_input_enumeration",
    "duplicate_reception_move",
)
_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY: Final[
    dict[GroundedReceptionOpportunityFamily, GroundedReceptionAct]
] = {
    "current_burden": "stay_with_current_burden",
    "concrete_effort": "honor_concrete_effort",
    "retained_intention": "protect_retained_intention",
    "lived_change": "recognize_lived_change",
    "help_seeking": "hold_help_seeking",
    "counterdirection": "bounded_counter_self_denial",
    "words_placed": "respect_words_placed",
}
_OPPORTUNITY_FAMILY_BY_RECEPTION_ACT: Final[
    dict[GroundedReceptionAct, GroundedReceptionOpportunityFamily]
] = {
    reception_act: family
    for family, reception_act in _RECEPTION_ACT_BY_OPPORTUNITY_FAMILY.items()
}
_OPPORTUNITY_FAMILY_ORDER: Final[tuple[GroundedReceptionOpportunityFamily, ...]] = (
    "help_seeking",
    "counterdirection",
    "concrete_effort",
    "lived_change",
    "retained_intention",
    "current_burden",
    "words_placed",
)
_OPPORTUNITY_ID_RE: Final = re.compile(r"^ro[1-9][0-9]*$")
_MOVE_ID_RE: Final = re.compile(r"^rm[1-9][0-9]*$")


def _grounded_human_follow_role_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    *,
    safety_kind: str,
) -> GroundedHumanFollowRole:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "operator:help_seeking" in attributes:
        return "help_seeking_preserved"
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER and (
        "semantic_role:protective_or_limiting_refusal" in attributes
        or nucleus.semantic_frame.modality == "refusal"
        or (
            "operator:continuation" in attributes
            and nucleus.semantic_frame.polarity == "negative"
        )
    ):
        return "protective_counterdirection"

    # Performed action evidence wins over a wider-arc intention label.  A
    # merely unperformed negative action (for example an inability to move)
    # must remain an intention/burden rather than becoming "effort".
    if _is_explicit_action_nucleus(nucleus):
        return "concrete_effort"

    retained_intention = bool(
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality == "wish"
        or {
            "semantic_role:retained_intention",
            "semantic_role:next_intention",
        }
        & attributes
    )
    if retained_intention:
        return "retained_intention"
    if _is_reception_performed_action_nucleus(nucleus):
        return "concrete_effort"
    if nucleus.kind in {"change", "value"} or {
        "semantic_role:current_change",
        "semantic_role:explicit_evaluation",
        "semantic_role:positive_evaluation",
    } & attributes:
        return "valued_change"
    return "burden_expression"


def classify_grounded_human_follow_role(
    *,
    safety_kind: str,
    material_quality: str,
    required_nucleus_count: int,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> GroundedHumanFollowRole:
    """Classify a body-free follow role from semantic nuclei.

    The classifier deliberately does not inspect case ids, source text, or a
    completed sentence.  Plan target selection and SentencePlan validation can
    therefore share one semantic decision without copying fixture cues.
    """

    candidates = tuple(nuclei)
    if (
        safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and material_quality == "short_state_sufficient"
        and required_nucleus_count == 1
    ):
        return "integrated_current_state"
    if not candidates:
        return "burden_expression"

    roles = {
        _grounded_human_follow_role_for_nucleus(
            nucleus,
            safety_kind=safety_kind,
        )
        for nucleus in candidates
    }
    priority = (
        _SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY
        if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        else _NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY
    )
    return next((role for role in priority if role in roles), "burden_expression")


def map_grounded_human_follow_role_to_reception_act(
    role: GroundedHumanFollowRole,
) -> GroundedReceptionAct:
    """Map the existing target classification to a distinct reception act."""

    try:
        return _RECEPTION_ACT_BY_FOLLOW_ROLE[role]
    except KeyError as exc:
        raise GroundedObservationPlanError(f"unsupported_grounded_human_follow_role:{role}") from exc


def _is_explicit_action_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if (
        "operator:help_seeking" in attributes
        and "operator:action" in attributes
    ):
        return True
    if "operator:wish" in attributes:
        return False
    result_evidence = bool(
        {
            "operator:result",
            "operator:positive_change",
            "operator:shift",
        }
        & attributes
    )
    unperformed_negative_intention = bool(
        nucleus.semantic_frame.modality == "intention"
        and nucleus.semantic_frame.polarity == "negative"
        and "operator:negation" in attributes
        and not result_evidence
    )
    if unperformed_negative_intention:
        return False
    if "semantic_role:concrete_action_evidence" in attributes:
        return True
    return bool(
        nucleus.kind == "action"
        and nucleus.semantic_frame.modality == "fact"
    )


def _is_reception_performed_action_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Accept performed action semantics without treating plans as actions."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_explicit_action_nucleus(nucleus)
        or (
            nucleus.semantic_frame.modality == "fact"
            and "operator:action" in attributes
            and {
                "semantic_role:concrete_action",
                "semantic_role:concrete_action_evidence",
            }
            & attributes
        )
    )


def _is_valued_change_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        nucleus.kind in {"change", "value"}
        or {
            "semantic_role:current_change",
            "semantic_role:explicit_evaluation",
            "semantic_role:positive_evaluation",
        }
        & attributes
    )


def _is_input_grounded_counterposition_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_explicit_action_nucleus(nucleus)
        or nucleus.semantic_frame.modality == "refusal"
        or (
            nucleus.kind == "wish"
            and nucleus.semantic_frame.modality in {"intention", "wish"}
        )
        or "operator:help_seeking" in attributes
        or "operator:continuation" in attributes
        or "operator:refusal" in attributes
        or "semantic_role:protective_or_limiting_refusal" in attributes
    )


def _is_reception_grounded_counterposition_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Recognize grounded action for RR2 without advancing the legacy Surface."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_input_grounded_counterposition_nucleus(nucleus)
        or _is_reception_performed_action_nucleus(nucleus)
    )


def select_grounded_reception_act(
    *,
    human_follow_role: GroundedHumanFollowRole,
    safety_kind: str,
    material_quality: str,
    semantic_complexity: str,
    target_nuclei: Sequence[GroundedSemanticNucleus],
    available_nuclei: Sequence[GroundedSemanticNucleus],
) -> GroundedReceptionAct:
    """Select an act from body-free semantic structure, never fixture identity."""

    candidates = tuple(available_nuclei)
    target_ids = {item.nucleus_id for item in target_nuclei}
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if any(
            _grounded_human_follow_role_for_nucleus(item, safety_kind=safety_kind)
            == "help_seeking_preserved"
            for item in candidates
        ):
            return "hold_help_seeking"
        if any(_is_input_grounded_counterposition_nucleus(item) for item in candidates):
            return "bounded_counter_self_denial"
        # The observation fact boundary still rejects the identity claim.  The
        # reception layer must not manufacture a counterposition without input
        # action, refusal, or intention evidence.
        return "stay_with_current_burden"

    if material_quality == "short_state_sufficient":
        return "stay_with_current_burden"
    if material_quality in {"limited_grounding", "labels_only_limited"} and not any(
        any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
        for item in target_nuclei
    ):
        return "respect_words_placed"

    non_target_candidates = tuple(item for item in candidates if item.nucleus_id not in target_ids)
    if human_follow_role == "retained_intention" and any(
        _is_reception_performed_action_nucleus(item)
        for item in non_target_candidates
    ):
        return "honor_concrete_effort"
    if (
        human_follow_role == "concrete_effort"
        and semantic_complexity == "long_arc"
        and any(_is_valued_change_nucleus(item) for item in non_target_candidates)
    ):
        return "recognize_lived_change"
    return map_grounded_human_follow_role_to_reception_act(human_follow_role)


def _select_reception_support_nucleus_ids(
    *,
    primary_act: GroundedReceptionAct,
    human_follow_role: GroundedHumanFollowRole,
    target_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    observation_owned_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[str, ...]:
    target_ids = set(target_nucleus_ids)
    observation_owned = set(observation_owned_nucleus_ids)
    candidates = tuple(
        item
        for item in nuclei
        if item.nucleus_id not in target_ids and item.nucleus_id in observation_owned
    )

    def first(predicate) -> tuple[str, ...]:
        selected = next((item for item in candidates if predicate(item)), None)
        return (selected.nucleus_id,) if selected is not None else ()

    if primary_act in {"hold_help_seeking", "bounded_counter_self_denial"}:
        fact_boundary = next(
            (
                nucleus_id
                for nucleus_id in fact_boundary_nucleus_ids
                if nucleus_id not in target_ids and nucleus_id in observation_owned
            ),
            None,
        )
        if fact_boundary:
            return (fact_boundary,)
        return first(_is_input_grounded_counterposition_nucleus)
    if primary_act == "honor_concrete_effort" and human_follow_role == "retained_intention":
        return first(_is_explicit_action_nucleus)
    if primary_act == "recognize_lived_change" and human_follow_role == "concrete_effort":
        return first(_is_valued_change_nucleus)
    if primary_act == "recognize_lived_change":
        return first(_is_explicit_action_nucleus)
    return ()


def _is_reception_lived_change_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Require an input-grounded positive/valued change, not a provisional miss."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "semantic_role:provisional_evaluation" in attributes:
        return False
    explicit_positive_evidence = bool(
        {
            "operator:positive_change",
            "semantic_role:explicit_result",
            "semantic_role:explicit_evaluation",
            "semantic_role:positive_evaluation",
        }
        & attributes
    )
    adverse_source_claim_without_positive_evidence = bool(
        any(
            code.startswith(
                (
                    "source_claim:pressure.",
                    "source_claim:conflict.",
                    "source_claim:limit.",
                )
            )
            for code in attributes
        )
        and not explicit_positive_evidence
    )
    if adverse_source_claim_without_positive_evidence:
        # A generic change/feeling parse is not evidence that a repeated
        # burden is a welcome lived change.  Keep adverse-only text in the
        # current-burden reception family unless the semantic layer recorded
        # an explicit positive change/result/evaluation.
        return False
    return bool(
        nucleus.semantic_frame.polarity == "positive"
        and explicit_positive_evidence
    )


def _reception_opportunity_families_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    *,
    safety_kind: str,
) -> tuple[GroundedReceptionOpportunityFamily, ...]:
    """Map body-free nucleus semantics to distinct human contribution families."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    has_text_source = any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields)
    if "semantic_role:compound_reception_coowned_nonprimary" in attributes:
        return ()
    if "operator:help_seeking" in attributes:
        return (
            "help_seeking",
            *(
                ("counterdirection",)
                if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
                else ()
            ),
        )
    if (
        safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and _is_reception_grounded_counterposition_nucleus(nucleus)
        and nucleus.kind != "self_evaluation"
    ):
        return ("counterdirection",)
    if _is_reception_performed_action_nucleus(nucleus):
        return ("concrete_effort",)
    if (
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality == "wish"
        or {
            "semantic_role:retained_intention",
            "semantic_role:next_intention",
        }
        & attributes
    ):
        return ("retained_intention",)
    if _is_reception_lived_change_nucleus(nucleus):
        return ("lived_change",)
    if has_text_source and (
        nucleus.semantic_frame.polarity == "negative"
        or nucleus.semantic_frame.modality in {"feeling", "refusal", "uncertain"}
        or nucleus.kind
        in {
            "state",
            "reaction",
            "constraint",
            "self_evaluation",
            "uncertainty",
        }
    ):
        return ("current_burden",)
    # A text-grounded but otherwise neutral nucleus still gives us something
    # present-tense to stay with.  ``words_placed`` is the deliberately narrow
    # fallback for labels-only / limited material.
    return ("current_burden",) if has_text_source else ("words_placed",)


def _opportunity_nucleus_rank(
    nucleus: GroundedSemanticNucleus,
    *,
    human_follow_target_ids: set[str],
    legacy_support_ids: set[str],
    relation_connected_ids: set[str],
) -> tuple[Any, ...]:
    return (
        0 if nucleus.nucleus_id in human_follow_target_ids else 1,
        0 if nucleus.nucleus_id in legacy_support_ids else 1,
        -_RETENTION_RANK[nucleus.retention],
        0 if nucleus.nucleus_id in relation_connected_ids else 1,
        0 if nucleus.grounding_kind in {"explicit", "user_stated_relation"} else 1,
        -float(nucleus.certainty),
        -float(nucleus.priority),
        _span_number(nucleus.source_span_ids[0] if nucleus.source_span_ids else ""),
    )


def _opportunity_priority(
    nucleus: GroundedSemanticNucleus,
    *,
    family: GroundedReceptionOpportunityFamily,
    human_follow_target_ids: set[str],
    relation_connected_ids: set[str],
    safety_required: bool,
) -> int:
    family_rank = len(_OPPORTUNITY_FAMILY_ORDER) - _OPPORTUNITY_FAMILY_ORDER.index(
        family
    )
    return int(
        _RETENTION_RANK[nucleus.retention] * 100
        + family_rank * 10
        + (40 if nucleus.nucleus_id in human_follow_target_ids else 0)
        + (20 if nucleus.nucleus_id in relation_connected_ids else 0)
        + (200 if safety_required else 0)
        + round(float(nucleus.priority) * 5)
    )


def build_grounded_reception_opportunities(
    *,
    human_follow_target_ids: Sequence[str],
    primary_nucleus_ids: Sequence[str],
    supporting_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    primary_reception_act: GroundedReceptionAct,
    safety_kind: str,
    material_quality: str,
    include_relation_support: bool = False,
) -> tuple[GroundedReceptionOpportunity, ...]:
    """Build a deterministic body-free RR2 opportunity inventory.

    The selector reads only semantic fields, ids, retention, relation
    membership, and Safety.  It never receives a case id, source body,
    expected hash, completed sentence, or raw character count.
    """

    nucleus_index = {item.nucleus_id: item for item in nuclei}
    observation_owned_ids = tuple(
        _dedupe(
            [
                *primary_nucleus_ids,
                *supporting_nucleus_ids,
                *fact_boundary_nucleus_ids,
            ]
        )
    )
    owned_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in observation_owned_ids
        if nucleus_id in nucleus_index
    )
    text_nucleus_present = any(
        any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
        for item in owned_nuclei
    )
    relation_connected_ids = {
        nucleus_id
        for relation in relations
        if relation.retention in {"required", "should"}
        for nucleus_id in (relation.from_nucleus_id, relation.to_nucleus_id)
    }
    follow_ids = set(human_follow_target_ids)
    legacy_support_ids = set(supporting_nucleus_ids)
    candidates_by_family: dict[
        GroundedReceptionOpportunityFamily,
        list[GroundedSemanticNucleus],
    ] = {}
    for nucleus in owned_nuclei:
        has_text_source = any(
            field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields
        )
        if text_nucleus_present and not has_text_source:
            continue
        for family in _reception_opportunity_families_for_nucleus(
            nucleus,
            safety_kind=safety_kind,
        ):
            candidates_by_family.setdefault(family, []).append(nucleus)

    # The established short-state contract is deliberately one quiet burden
    # move.  A terse wish/action must not be inflated merely because its lone
    # nucleus has a richer semantic label; Safety remains the only exception.
    if (
        material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and owned_nuclei
    ):
        candidates_by_family = {"current_burden": list(owned_nuclei)}

    # Preserve the established body-free primary selector as the compatibility
    # anchor.  Its classification can be more specific than the nucleus-kind
    # mapper (for example, an event carrying a valued-change role).  This does
    # not invent a contribution: it binds that already-selected act to the
    # same request-local human-follow target and evidence.
    compatibility_family = _OPPORTUNITY_FAMILY_BY_RECEPTION_ACT[
        primary_reception_act
    ]
    if compatibility_family not in candidates_by_family:
        compatibility_nuclei = [
            nucleus_index[nucleus_id]
            for nucleus_id in human_follow_target_ids
            if nucleus_id in nucleus_index
        ]
        if not compatibility_nuclei:
            compatibility_nuclei = list(owned_nuclei[:1])
        compatibility_family_is_grounded = bool(
            compatibility_family != "lived_change"
            or any(
                _is_reception_lived_change_nucleus(nucleus)
                for nucleus in compatibility_nuclei
            )
        )
        if compatibility_nuclei and compatibility_family_is_grounded:
            candidates_by_family[compatibility_family] = compatibility_nuclei

    concrete_families = set(candidates_by_family) - {"words_placed"}
    if concrete_families and compatibility_family != "words_placed":
        candidates_by_family.pop("words_placed", None)
    richer_families = concrete_families - {"current_burden"}
    if (
        richer_families
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and material_quality != "short_state_sufficient"
        and compatibility_family != "current_burden"
    ):
        candidates_by_family.pop("current_burden", None)

    rows: list[GroundedReceptionOpportunity] = []
    for family in _OPPORTUNITY_FAMILY_ORDER:
        family_candidates = tuple(candidates_by_family.get(family, ()))
        if not family_candidates:
            continue
        representative = min(
            family_candidates,
            key=lambda item: (
                0
                if family == "lived_change"
                and {
                    "semantic_role:explicit_evaluation",
                    "semantic_role:positive_evaluation",
                }
                & set(item.semantic_frame.attribute_codes)
                else 1,
                *_opportunity_nucleus_rank(
                    item,
                    human_follow_target_ids=follow_ids,
                    legacy_support_ids=legacy_support_ids,
                    relation_connected_ids=relation_connected_ids,
                ),
            ),
        )
        target_ids: tuple[str, ...] = (representative.nucleus_id,)
        support_ids: tuple[str, ...] = ()
        if family == "counterdirection" and fact_boundary_nucleus_ids:
            fact_id = next(
                (
                    nucleus_id
                    for nucleus_id in fact_boundary_nucleus_ids
                    if nucleus_id in nucleus_index
                ),
                None,
            )
            if fact_id is not None and fact_id != representative.nucleus_id:
                target_ids = (fact_id,)
                support_ids = (representative.nucleus_id,)
        elif include_relation_support:
            relation_priority = {
                "action_supports_change": 0,
                "preserves_despite": 1,
                "continuation_or_refusal": 1,
                "wish_and_constraint": 2,
                "temporal_before_after": 3,
                "coexistence": 4,
                "contrast": 5,
                "uncertain_connection": 6,
            }
            relation_support_candidates: list[
                tuple[int, int, GroundedSemanticNucleus]
            ] = []
            for relation in relations:
                if relation.retention not in {"required", "should"}:
                    continue
                if relation.from_nucleus_id == representative.nucleus_id:
                    other_id = relation.to_nucleus_id
                elif relation.to_nucleus_id == representative.nucleus_id:
                    other_id = relation.from_nucleus_id
                else:
                    continue
                other = nucleus_index.get(other_id)
                if (
                    other is None
                    or other.nucleus_id not in observation_owned_ids
                    or other.kind == "other_explicit"
                ):
                    continue
                relation_support_candidates.append(
                    (
                        relation_priority.get(relation.type, 99),
                        _span_number(
                            other.source_span_ids[0]
                            if other.source_span_ids
                            else ""
                        ),
                        other,
                    )
                )
            if relation_support_candidates:
                relation_support_candidates.sort(
                    key=lambda row: (row[0], row[1], row[2].nucleus_id)
                )
                support_ids = (
                    relation_support_candidates[0][2].nucleus_id,
                )
        selected_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*target_ids, *support_ids)
            if nucleus_id in nucleus_index
        )
        evidence_ids = tuple(
            _ordered_span_ids(
                span_id
                for item in selected_nuclei
                for span_id in item.source_span_ids
            )
        )
        safety_required = bool(
            safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
            and family in {"help_seeking", "counterdirection"}
        )
        retention = max(
            (item.retention for item in selected_nuclei),
            key=lambda value: _RETENTION_RANK[value],
        )
        rows.append(
            GroundedReceptionOpportunity(
                opportunity_id="",
                family=family,
                reception_act=_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY[family],
                target_nucleus_ids=target_ids,
                support_nucleus_ids=support_ids,
                source_evidence_span_ids=evidence_ids,
                retention=retention,
                priority=_opportunity_priority(
                    representative,
                    family=family,
                    human_follow_target_ids=follow_ids,
                    relation_connected_ids=relation_connected_ids,
                    safety_required=safety_required,
                ),
                source_field_count=len(
                    {
                        field
                        for item in selected_nuclei
                        for field in item.source_fields
                    }
                ),
                safety_required=safety_required,
            )
        )

    rows.sort(
        key=lambda item: (
            -item.priority,
            _OPPORTUNITY_FAMILY_ORDER.index(item.family),
            _span_number(
                item.source_evidence_span_ids[0]
                if item.source_evidence_span_ids
                else ""
            ),
        )
    )
    return tuple(
        replace(item, opportunity_id=f"ro{index}")
        for index, item in enumerate(rows, start=1)
    )


def _opportunities_are_distinct(
    left: GroundedReceptionOpportunity,
    right: GroundedReceptionOpportunity,
) -> bool:
    return bool(
        left.family != right.family
        or left.reception_act != right.reception_act
        or set(left.target_nucleus_ids) != set(right.target_nucleus_ids)
    )


def _select_reception_opportunities(
    opportunities: Sequence[GroundedReceptionOpportunity],
    *,
    legacy_primary_act: GroundedReceptionAct,
    safety_kind: str,
    semantic_complexity: str,
) -> tuple[GroundedReceptionOpportunity, ...]:
    inventory = tuple(opportunities)
    if not inventory:
        raise GroundedObservationPlanError("human_reception_opportunity_missing")
    primary = next(
        (
            item
            for item in inventory
            if item.reception_act == legacy_primary_act
        ),
        inventory[0],
    )
    selected: list[GroundedReceptionOpportunity] = [primary]
    by_family = {item.family: item for item in inventory}

    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if primary.family == "help_seeking":
            support_order = ("counterdirection",)
        elif primary.family == "counterdirection":
            support_order = ("current_burden",)
        else:
            support_order = ("counterdirection",)
    else:
        support_order_by_primary = {
            "concrete_effort": ("lived_change", "retained_intention"),
            "lived_change": ("concrete_effort", "retained_intention"),
            "retained_intention": ("lived_change", "concrete_effort"),
            "current_burden": (
                "concrete_effort",
                "retained_intention",
                "lived_change",
            ),
            "help_seeking": (
                "lived_change",
                "concrete_effort",
                "retained_intention",
            ),
            "counterdirection": ("current_burden",),
            "words_placed": (),
        }
        support_order = support_order_by_primary[primary.family]

    support_limit = 2 if semantic_complexity == "long_arc" else 1
    selected_support_count = 0
    for family in support_order:
        candidate = by_family.get(family)
        if candidate is None or candidate.retention not in {"required", "should"}:
            continue
        if all(_opportunities_are_distinct(candidate, item) for item in selected):
            selected.append(candidate)
            selected_support_count += 1
            if selected_support_count >= support_limit:
                break

    required_safety = tuple(
        item
        for item in inventory
        if item.safety_required and item not in selected
    )
    for item in required_safety:
        if len(selected) >= 3:
            raise GroundedObservationPlanError(
                "human_reception_required_safety_move_exceeds_limit"
            )
        if all(_opportunities_are_distinct(item, other) for other in selected):
            selected.append(item)
    return tuple(selected)


def _move_roles_by_opportunity_family(
    selected: Sequence[GroundedReceptionOpportunity],
) -> dict[str, GroundedReceptionMoveRole]:
    families = {item.family for item in selected}
    result: dict[str, GroundedReceptionMoveRole] = {}
    for item in selected:
        if item.family == "counterdirection":
            role: GroundedReceptionMoveRole = "bounded_counterposition"
        elif item.family in {"current_burden", "help_seeking", "words_placed"}:
            role = "felt_response"
        elif {"concrete_effort", "lived_change"} <= families:
            role = "attention" if item.family == "concrete_effort" else "felt_response"
        elif {"lived_change", "retained_intention"} <= families:
            role = "attention" if item.family == "lived_change" else "felt_response"
        elif {"concrete_effort", "retained_intention"} <= families:
            role = "attention" if item.family == "retained_intention" else "felt_response"
        elif item.family == "concrete_effort":
            role = "attention"
        elif item.family == "retained_intention":
            role = "significance"
        else:
            role = "felt_response"
        result[item.opportunity_id] = role
    return result


def _surface_strategy_for_move(
    opportunity: GroundedReceptionOpportunity,
    role: GroundedReceptionMoveRole,
) -> GroundedReceptionSurfaceStrategy:
    if role == "bounded_counterposition":
        return "explicit_emlis_counterposition"
    if opportunity.family == "current_burden":
        return "quiet_referent_first"
    if role == "attention":
        return "emlis_attention_first"
    if role == "significance":
        return "referent_significance_first"
    return "felt_response_first"


def _build_reception_depth_policy_and_moves(
    opportunities: Sequence[GroundedReceptionOpportunity],
    *,
    legacy_primary_act: GroundedReceptionAct,
    legacy_reference_mode: GroundedReferenceMode,
    safety_kind: str,
    semantic_complexity: str,
) -> tuple[GroundedReceptionDepthPolicy, tuple[GroundedReceptionMovePlan, ...]]:
    selected = _select_reception_opportunities(
        opportunities,
        legacy_primary_act=legacy_primary_act,
        safety_kind=safety_kind,
        semantic_complexity=semantic_complexity,
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        safety_mode: GroundedReceptionSafetyMode = (
            "help_seeking_bounded"
            if any(item.family == "help_seeking" for item in selected)
            else "self_denial_bounded"
        )
        level: GroundedReceptionDepthLevel = "focused"
        min_sentences = 2 if len(selected) >= 2 else 1
        max_sentences = 2
    else:
        safety_mode = "standard"
        if len(selected) >= 2:
            level = "layered"
            min_sentences = 2
            max_sentences = min(3, len(selected))
        elif selected[0].family in {"current_burden", "words_placed"}:
            level = "minimal"
            min_sentences = max_sentences = 1
        else:
            level = "focused"
            min_sentences = max_sentences = 1

    roles = _move_roles_by_opportunity_family(selected)
    moves: list[GroundedReceptionMovePlan] = []
    for index, opportunity in enumerate(selected, start=1):
        role = roles[opportunity.opportunity_id]
        primary_element, secondary_elements, afterglow_element = (
            _FOLLOW_PROFILE_BY_RECEPTION_ACT[opportunity.reception_act]
        )
        follow_elements = tuple(
            _dedupe(
                [
                    primary_element,
                    *secondary_elements,
                    *(
                        (afterglow_element,)
                        if afterglow_element is not None
                        else ()
                    ),
                ]
            )
        )[:3]
        explicit = role == "bounded_counterposition"
        moves.append(
            GroundedReceptionMovePlan(
                move_id=f"rm{index}",
                move_role=role,
                reception_act=opportunity.reception_act,
                target_nucleus_ids=opportunity.target_nucleus_ids,
                support_nucleus_ids=opportunity.support_nucleus_ids,
                source_evidence_span_ids=opportunity.source_evidence_span_ids,
                follow_elements=follow_elements,
                speaker_presence="explicit_emlis" if explicit else "implicit_emlis",
                reference_mode=(
                    "explicit_emlis_counterposition"
                    if explicit
                    else legacy_reference_mode
                    if index == 1
                    else "anaphoric_first"
                ),
                surface_strategy=_surface_strategy_for_move(opportunity, role),
                required=(
                    opportunity.safety_required
                    or opportunity.retention in {"required", "should"}
                ),
                distinct_from_move_ids=tuple(item.move_id for item in moves),
            )
        )

    min_realized_moves = sum(1 for item in moves if item.required)
    policy = GroundedReceptionDepthPolicy(
        level=level,
        safety_mode=safety_mode,
        opportunity_count=len(tuple(opportunities)),
        selected_move_count=len(moves),
        selection_reason_codes=(
            "selection:semantic_opportunity_inventory",
            "selection:distinct_human_contributions",
            "selection:raw_character_count_unused",
            f"depth:{level}",
            f"safety:{safety_mode}",
        ),
        raw_character_count_used=False,
        min_sentences=min_sentences,
        max_sentences=max_sentences,
        min_realized_moves=max(1, min_realized_moves),
        # RR7 may safely integrate one pair only when three selected Moves
        # can still satisfy the layered two-sentence lower bound. Full
        # realization remains one Move per sentence.
        max_moves_per_sentence=2 if len(moves) == 3 else 1,
    )
    return policy, tuple(moves)


def build_grounded_human_reception_plan(
    *,
    required: bool,
    human_follow_target_ids: Sequence[str],
    primary_nucleus_ids: Sequence[str],
    supporting_nucleus_ids: Sequence[str],
    required_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    safety_kind: str,
    material_quality: str,
    semantic_complexity: str,
    include_relation_support: bool = False,
) -> GroundedHumanReceptionPlan | None:
    """Build the request-local body-free RR2/RR3 reception plan."""

    if not required:
        return None
    nucleus_index = {item.nucleus_id: item for item in nuclei}
    target_ids = tuple(_dedupe(human_follow_target_ids))
    target_nuclei = tuple(nucleus_index[item] for item in target_ids if item in nucleus_index)
    if not target_nuclei:
        raise GroundedObservationPlanError("human_reception_target_missing")

    human_follow_role = classify_grounded_human_follow_role(
        safety_kind=safety_kind,
        material_quality=material_quality,
        required_nucleus_count=len(tuple(required_nucleus_ids)),
        nuclei=target_nuclei,
    )
    observation_owned_ids = tuple(
        _dedupe(
            [
                *primary_nucleus_ids,
                *supporting_nucleus_ids,
                *fact_boundary_nucleus_ids,
            ]
        )
    )
    observation_owned_set = set(observation_owned_ids)
    available_nuclei = tuple(
        item for item in nuclei if item.nucleus_id in observation_owned_set
    )
    primary_act = select_grounded_reception_act(
        human_follow_role=human_follow_role,
        safety_kind=safety_kind,
        material_quality=material_quality,
        semantic_complexity=semantic_complexity,
        target_nuclei=target_nuclei,
        available_nuclei=available_nuclei,
    )
    support_ids = _select_reception_support_nucleus_ids(
        primary_act=primary_act,
        human_follow_role=human_follow_role,
        target_nucleus_ids=target_ids,
        fact_boundary_nucleus_ids=fact_boundary_nucleus_ids,
        observation_owned_nucleus_ids=observation_owned_ids,
        nuclei=nuclei,
    )
    selected_nuclei = tuple(
        nucleus_index[item]
        for item in (*target_ids, *support_ids)
        if item in nucleus_index
    )
    grounded_counterposition = any(
        _is_input_grounded_counterposition_nucleus(item) for item in selected_nuclei
    )
    secondary_act: GroundedReceptionAct | None = None
    if (
        safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and primary_act == "hold_help_seeking"
        and grounded_counterposition
    ):
        secondary_act = "bounded_counter_self_denial"

    primary_element, secondary_elements, afterglow_element = _FOLLOW_PROFILE_BY_RECEPTION_ACT[
        primary_act
    ]
    bounded_counterposition = (
        primary_act == "bounded_counter_self_denial"
        or secondary_act == "bounded_counter_self_denial"
    )
    speaker_presence: GroundedSpeakerPresence = (
        "explicit_emlis" if bounded_counterposition else "implicit_emlis"
    )
    reference_mode: GroundedReferenceMode
    if bounded_counterposition:
        reference_mode = "explicit_emlis_counterposition"
    elif material_quality == "short_state_sufficient":
        reference_mode = "anaphoric_first"
    elif semantic_complexity in {"multi", "long_arc"}:
        reference_mode = "short_anchor_if_ambiguous"
    else:
        reference_mode = "anaphoric_first"

    opportunities = build_grounded_reception_opportunities(
        human_follow_target_ids=target_ids,
        primary_nucleus_ids=primary_nucleus_ids,
        supporting_nucleus_ids=supporting_nucleus_ids,
        fact_boundary_nucleus_ids=fact_boundary_nucleus_ids,
        nuclei=nuclei,
        relations=relations,
        primary_reception_act=primary_act,
        safety_kind=safety_kind,
        material_quality=material_quality,
        include_relation_support=include_relation_support,
    )
    depth_policy, moves = _build_reception_depth_policy_and_moves(
        opportunities,
        legacy_primary_act=primary_act,
        legacy_reference_mode=reference_mode,
        safety_kind=safety_kind,
        semantic_complexity=semantic_complexity,
    )
    # RR4 keeps the public follow target stable while expanding the aggregate
    # compatibility grounding to every selected Move.  ClausePlan remains the
    # owner of each individual Move binding; the aggregate fields keep the
    # existing Gate and recovery perimeter evidence-complete.
    move_nucleus_ids = tuple(
        _dedupe(
            nucleus_id
            for move in moves
            for nucleus_id in (
                *move.target_nucleus_ids,
                *move.support_nucleus_ids,
            )
        )
    )
    support_ids = tuple(
        nucleus_id
        for nucleus_id in move_nucleus_ids
        if nucleus_id not in set(target_ids)
    )
    selected_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in (*target_ids, *support_ids)
        if nucleus_id in nucleus_index
    )
    # The compatibility primary remains aligned with the first planned Move.
    primary_act = moves[0].reception_act
    primary_element, secondary_elements, afterglow_element = (
        _FOLLOW_PROFILE_BY_RECEPTION_ACT[primary_act]
    )
    max_sentences = (
        1
        if material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and secondary_act is None
        else 2
    )
    safety_modifier_codes: list[str] = []
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        safety_modifier_codes.extend(
            (
                "felt_state_is_real",
                "identity_claim_is_not_accepted",
            )
        )
        if bounded_counterposition or any(
            move.move_role == "bounded_counterposition" for move in moves
        ):
            safety_modifier_codes.append("counterposition_requires_input_evidence")

    source_evidence_ids = tuple(
        _ordered_span_ids(
            span_id
            for item in selected_nuclei
            for span_id in item.source_span_ids
        )
    )
    return GroundedHumanReceptionPlan(
        schema_version=GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION,
        required=True,
        opportunities=opportunities,
        depth_policy=depth_policy,
        moves=moves,
        primary_reception_act=primary_act,
        secondary_reception_act=secondary_act,
        primary_follow_element=primary_element,
        secondary_follow_elements=secondary_elements,
        afterglow_follow_element=afterglow_element,
        target_nucleus_ids=target_ids,
        support_nucleus_ids=support_ids,
        source_evidence_span_ids=source_evidence_ids,
        observation_owned_nucleus_ids=observation_owned_ids,
        stance=_STANCE_BY_RECEPTION_ACT[primary_act],
        speaker_presence=speaker_presence,
        reference_mode=reference_mode,
        quote_policy=GroundedReceptionQuotePolicy(
            mode="no_full_quote_replay",
            max_anchor_count=1 if reference_mode == "short_anchor_if_ambiguous" else 0,
            max_anchor_visible_chars=16,
        ),
        sentence_policy=GroundedReceptionSentencePolicy(
            min_sentences=1,
            max_sentences=max_sentences,
        ),
        distinctness_policy=GroundedReceptionDistinctnessPolicy(
            observation_summary_repetition_allowed=False,
            relation_reexplanation_allowed=False,
            all_input_enumeration_allowed=False,
            policy_explanation_allowed=False,
            new_cause_allowed=False,
            new_identity_claim_allowed=False,
            advice_allowed=False,
            question_allowed=False,
        ),
        safety_modifier_codes=tuple(safety_modifier_codes),
        forbidden_surface_codes=_RECEPTION_FORBIDDEN_SURFACE_CODES,
    )


def classify_grounded_human_follow_delivery(
    *,
    safety_kind: str,
    material_quality: str,
    required_nucleus_count: int,
    target_nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    required_relation_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str] = (),
) -> GroundedHumanFollowDelivery:
    """Keep the human reception contribution structurally separate.

    ``見えたこと：`` and ``Emlisから：`` are a mandatory public-body
    contract for every generated Emlis observation, including short-state and
    limited-input observations.  A semantic observation line may cover the
    same nucleus, but it must not absorb the human reception contribution.
    Keeping the delivery separate prevents an internal ``human_follow`` atom
    from being mistaken for a visible second section.
    """

    targets = tuple(target_nuclei)
    if not targets:
        return "not_required"

    # Retain the arguments in the contract because callers and tests use this
    # classifier as the single body-free decision point.  They no longer alter
    # the visible section layout.
    _ = (
        safety_kind,
        material_quality,
        required_nucleus_count,
        relations,
        required_relation_ids,
        fact_boundary_nucleus_ids,
    )
    return "separate_distinct_contribution"


def _is_grounded_human_follow_candidate(nucleus: GroundedSemanticNucleus) -> bool:
    if not any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields):
        return False
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if nucleus.kind != "other_explicit":
        return True
    return bool(
        "operator:help_seeking" in attributes
        or "operator:action" in attributes
        or "operator:wish" in attributes
        or any(code.startswith("semantic_role:") for code in attributes)
    )


def _build_response_and_policies(
    *,
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    safety_decision: EmlisSafetyTriageDecision,
    complexity: str,
    material_quality: str,
    include_reception_relation_support: bool = False,
) -> tuple[GroundedResponsePlan, GroundedCoverageRequirements, GroundedSurfacePolicy, GroundedSafetyPolicy]:
    ordered = sorted(
        nuclei,
        key=lambda item: (-_RETENTION_RANK[item.retention], -item.priority, _span_number(item.source_span_ids[0])),
    )
    required_ids = tuple(item.nucleus_id for item in ordered if item.retention == "required")
    optional_ids = tuple(item.nucleus_id for item in ordered if item.retention == "optional")
    required_relation_ids = tuple(item.relation_id for item in relations if item.retention == "required")
    planned_relation_ids = tuple(item.relation_id for item in relations if item.retention in {"required", "should"})

    relation_weight = {
        "preserves_despite": 6,
        "continuation_or_refusal": 6,
        "shift_from_to": 5,
        "user_stated_cause": 5,
        "user_stated_result": 5,
        "wish_and_constraint": 4,
        "action_supports_change": 3,
        "contrast": 3,
    }
    endpoint_weight: dict[str, int] = {}
    for relation in relations:
        if relation.relation_id not in required_relation_ids:
            continue
        weight = relation_weight.get(relation.type, 2)
        endpoint_weight[relation.from_nucleus_id] = max(
            endpoint_weight.get(relation.from_nucleus_id, 0), weight
        )
        endpoint_weight[relation.to_nucleus_id] = max(
            endpoint_weight.get(relation.to_nucleus_id, 0), weight
        )

    def primary_score(item: GroundedSemanticNucleus) -> int:
        roles = set(item.semantic_frame.attribute_codes)
        semantic_weight = 0
        for role, weight in (
            ("semantic_role:counterevidence", 10),
            ("semantic_role:provisional_evaluation", 10),
            ("semantic_role:explicit_evaluation", 9),
            ("semantic_role:embedded_turn", 8),
            ("semantic_role:current_change", 7),
            ("semantic_role:contrast_after", 7),
            ("semantic_role:contrast_before", 6),
            ("semantic_role:initial_condition", 5),
            ("semantic_role:retained_intention", 5),
            ("semantic_role:concrete_action_evidence", 4),
        ):
            if role in roles:
                semantic_weight = max(semantic_weight, weight)
        return semantic_weight + endpoint_weight.get(item.nucleus_id, 0)

    text_required = [
        item
        for item in ordered
        if item.retention == "required"
        and any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
    ]
    if text_required:
        highest_primary_score = max(primary_score(item) for item in text_required)
        selected_primary_ids = tuple(
            item.nucleus_id
            for item in sorted(text_required, key=lambda item: _span_number(item.source_span_ids[0]))
            if primary_score(item) >= max(1, highest_primary_score - 2)
        )
        primary_ids = selected_primary_ids or (text_required[0].nucleus_id,)
    else:
        primary_ids = tuple(required_ids or tuple(item.nucleus_id for item in ordered[:1]))
    supporting_ids = tuple(
        item.nucleus_id
        for item in ordered
        if item.nucleus_id not in primary_ids and item.retention in {"required", "should"}
    )

    safety_evidence_ids = set(getattr(safety_decision, "evidence_span_ids", ()) or ())
    safety_nuclei = tuple(item for item in nuclei if set(item.source_span_ids) & safety_evidence_ids)
    separate_safety = safety_decision.safety_triage_kind in {
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }
    fact_boundary_required = safety_decision.safety_triage_kind in {
        TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }
    if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        self_evaluation_ids = tuple(
            item.nucleus_id
            for item in ordered
            if item.kind == "self_evaluation"
            and item.retention in {"required", "should"}
        )
        safety_self_evaluation_ids = tuple(
            item.nucleus_id for item in safety_nuclei if item.kind == "self_evaluation"
        )
        fact_boundary_ids = (
            safety_self_evaluation_ids
            or self_evaluation_ids[:1]
            or tuple(item.nucleus_id for item in safety_nuclei[:1])
            or primary_ids[:1]
        )
    else:
        fact_boundary_ids = tuple(item.nucleus_id for item in safety_nuclei) if fact_boundary_required else ()

    candidate_ids = tuple(_dedupe([*primary_ids, *supporting_ids, *required_ids]))
    candidate_index = {item.nucleus_id: item for item in nuclei}
    follow_candidates = tuple(
        candidate_index[nucleus_id]
        for nucleus_id in candidate_ids
        if nucleus_id in candidate_index
        and candidate_index[nucleus_id].retention in {"required", "should"}
        and _is_grounded_human_follow_candidate(candidate_index[nucleus_id])
    )
    follow_role_priority = (
        _SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY
        if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        else _NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY
    )
    follow_role_rank = {role: index for index, role in enumerate(follow_role_priority)}
    primary_set = set(primary_ids)
    supporting_set = set(supporting_ids)
    relation_connected_ids = {
        endpoint
        for relation in relations
        if relation.relation_id in required_relation_ids
        or relation.type == "action_supports_change"
        for endpoint in (relation.from_nucleus_id, relation.to_nucleus_id)
    }
    directional_follow_to_ids = (
        {
            relation.to_nucleus_id
            for relation in relations
            if relation.relation_id in required_relation_ids
            and relation.type in {
                "shift_from_to",
                "temporal_before_after",
                "action_supports_change",
                "user_stated_result",
            }
            and relation.from_nucleus_id in candidate_index
            and relation.to_nucleus_id in candidate_index
            and set(
                candidate_index[
                    relation.from_nucleus_id
                ].source_span_ids
            ).isdisjoint(
                candidate_index[
                    relation.to_nucleus_id
                ].source_span_ids
            )
        }
        & {item.nucleus_id for item in follow_candidates}
        if safety_decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION
        else set()
    )

    def follow_rank(item: GroundedSemanticNucleus) -> tuple[Any, ...]:
        role = classify_grounded_human_follow_role(
            safety_kind=safety_decision.safety_triage_kind,
            material_quality=material_quality,
            required_nucleus_count=len(required_ids),
            nuclei=(item,),
        )
        attributes = set(item.semantic_frame.attribute_codes)
        role_explicit = bool(
            (role == "retained_intention" and (
                item.semantic_frame.modality in {"wish", "intention"}
                or {
                    "semantic_role:retained_intention",
                    "semantic_role:next_intention",
                } & attributes
            ))
            or (role == "concrete_effort" and {
                "semantic_role:concrete_action",
                "semantic_role:concrete_action_evidence",
            } & attributes)
            or (role == "valued_change" and {
                "semantic_role:current_change",
                "semantic_role:explicit_evaluation",
                "semantic_role:positive_evaluation",
            } & attributes)
            or (role == "help_seeking_preserved" and "operator:help_seeking" in attributes)
            or (
                role == "protective_counterdirection"
                and "semantic_role:protective_or_limiting_refusal" in attributes
            )
        )
        response_membership_rank = (
            0 if item.nucleus_id in primary_set else 1 if item.nucleus_id in supporting_set else 2
        )
        return (
            0 if item.nucleus_id in directional_follow_to_ids else 1,
            follow_role_rank.get(role, len(follow_role_rank)),
            -_RETENTION_RANK[item.retention],
            0 if role_explicit else 1,
            response_membership_rank,
            0 if item.nucleus_id in relation_connected_ids else 1,
            0 if item.grounding_kind in {"explicit", "user_stated_relation"} else 1,
            -float(item.certainty),
            -float(item.priority),
            _span_number(item.source_span_ids[0] if item.source_span_ids else ""),
        )

    selected_follow = min(follow_candidates, key=follow_rank) if follow_candidates else None
    follow_ids = (selected_follow.nucleus_id,) if selected_follow is not None else primary_ids[:1]

    observable_nucleus_present = bool(nuclei)
    human_follow_required = bool(observable_nucleus_present) and not separate_safety and material_quality != "empty"
    if not human_follow_required:
        follow_ids = ()

    if separate_safety:
        surface_shape: Literal["plain", "two_stage", "multi_paragraph", "separate_safety_surface"] = "separate_safety_surface"
    elif material_quality == "empty":
        surface_shape = "plain"
    else:
        # Long inputs may use multiple paragraphs *inside* the two labelled
        # sections.  They do not change the public body contract.
        surface_shape = "two_stage"

    if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        response_kind = TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    elif separate_safety:
        response_kind = _clean(getattr(safety_decision, "response_kind", "")) or safety_decision.safety_triage_kind
    else:
        response_kind = {
            "short_state_sufficient": "short_state_observation",
            "limited_grounding": "limited_grounding_observation",
            "labels_only_limited": "labels_only_limited_observation",
            "empty": "unavailable",
        }.get(material_quality, "normal_observation")

    human_reception_plan = build_grounded_human_reception_plan(
        required=human_follow_required,
        human_follow_target_ids=follow_ids,
        primary_nucleus_ids=primary_ids,
        supporting_nucleus_ids=supporting_ids,
        required_nucleus_ids=required_ids,
        fact_boundary_nucleus_ids=fact_boundary_ids,
        nuclei=nuclei,
        relations=relations,
        safety_kind=safety_decision.safety_triage_kind,
        material_quality=material_quality,
        semantic_complexity=complexity,
        include_relation_support=include_reception_relation_support,
    )
    response = GroundedResponsePlan(
        response_kind=response_kind,
        primary_nucleus_ids=primary_ids,
        supporting_nucleus_ids=supporting_ids,
        relation_ids=planned_relation_ids,
        fact_boundary_nucleus_ids=tuple(fact_boundary_ids),
        human_follow_target_ids=tuple(follow_ids),
        human_reception_plan=human_reception_plan,
        required_nucleus_ids=required_ids,
        optional_nucleus_ids=optional_ids,
        question_policy=GroundedQuestionPolicy(),
        surface_shape=surface_shape,
    )
    coverage = GroundedCoverageRequirements(
        required_nucleus_ids=required_ids,
        required_relation_ids=required_relation_ids,
        human_follow_required=human_follow_required,
        fact_boundary_required=fact_boundary_required,
    )
    surface = GroundedSurfacePolicy(
        content_source="separate_safety_owner" if separate_safety else "grounded_plan_only",
        generic_observation_surface_allowed=not separate_safety,
        hedge_policy=(
            "limited_single_input_scope"
            if material_quality in {"limited_grounding", "labels_only_limited"}
            else "single_input_scope"
        ),
    )
    safety = GroundedSafetyPolicy(
        safety_kind=_clean(getattr(safety_decision, "safety_triage_kind", "")) or TRIAGE_SAFE_OBSERVATION,
        identity_claim_must_not_be_accepted_as_fact=bool(
            getattr(safety_decision, "must_not_accept_identity_claim_as_fact", False)
        ),
        requires_separate_safety_surface=bool(
            getattr(safety_decision, "requires_separate_safety_surface", False)
        ),
        grounded_plan_overlay_allowed=not separate_safety,
        required_boundary_codes=tuple(
            _dedupe(
                [
                    *list(getattr(safety_decision, "reason_codes", ()) or ()),
                    *list(getattr(safety_decision, "boundary_types", ()) or ()),
                ]
            )
        ),
    )
    return response, coverage, surface, safety


def _all_plan_evidence_ids(
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    unknowns: Sequence[GroundedUnknownBoundary],
) -> tuple[str, ...]:
    return tuple(
        _ordered_span_ids(
            [
                *[span_id for item in nuclei for span_id in item.source_span_ids],
                *[span_id for item in relations for span_id in item.source_span_ids],
                *[span_id for item in unknowns for span_id in item.evidence_span_ids],
            ]
        )
    )


def validate_grounded_human_reception_plan(
    reception_plan: GroundedHumanReceptionPlan,
    *,
    expected_target_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    safety_kind: str,
    material_quality: str,
) -> tuple[str, ...]:
    """Validate the nested plan without inspecting source text or a surface."""

    issues: list[str] = []
    if reception_plan.schema_version != GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION:
        issues.append("human_reception_plan_schema_version_mismatch")
    if not reception_plan.required:
        issues.append("human_reception_plan_present_but_not_required")

    allowed_acts = set(_FOLLOW_PROFILE_BY_RECEPTION_ACT)
    allowed_follow_elements = {
        element
        for primary, secondary, afterglow in _FOLLOW_PROFILE_BY_RECEPTION_ACT.values()
        for element in (primary, *secondary, afterglow)
        if element is not None
    }
    allowed_families = set(_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY)
    observation_owned_set = set(reception_plan.observation_owned_nucleus_ids)
    opportunities = tuple(reception_plan.opportunities)
    if not opportunities:
        issues.append("human_reception_opportunity_missing")
    opportunity_index: dict[str, GroundedReceptionOpportunity] = {}
    opportunity_signatures: set[tuple[Any, ...]] = set()
    for index, opportunity in enumerate(opportunities, start=1):
        expected_id = f"ro{index}"
        if not _OPPORTUNITY_ID_RE.fullmatch(opportunity.opportunity_id):
            issues.append("human_reception_opportunity_id_invalid")
        if opportunity.opportunity_id != expected_id:
            issues.append("human_reception_opportunity_order_invalid")
        if opportunity.opportunity_id in opportunity_index:
            issues.append("human_reception_opportunity_id_duplicate")
        opportunity_index[opportunity.opportunity_id] = opportunity
        if opportunity.family not in allowed_families:
            issues.append("human_reception_opportunity_family_invalid")
        elif (
            opportunity.reception_act
            != _RECEPTION_ACT_BY_OPPORTUNITY_FAMILY[opportunity.family]
        ):
            issues.append("human_reception_opportunity_act_mismatch")

        opportunity_target_ids = tuple(opportunity.target_nucleus_ids)
        opportunity_support_ids = tuple(opportunity.support_nucleus_ids)
        if not opportunity_target_ids:
            issues.append("human_reception_opportunity_target_missing")
        if len(opportunity_target_ids) != len(set(opportunity_target_ids)):
            issues.append("human_reception_opportunity_target_duplicate")
        if len(opportunity_support_ids) != len(set(opportunity_support_ids)):
            issues.append("human_reception_opportunity_support_duplicate")
        if set(opportunity_target_ids) & set(opportunity_support_ids):
            issues.append("human_reception_opportunity_target_support_overlap")
        for nucleus_id in (*opportunity_target_ids, *opportunity_support_ids):
            if nucleus_id not in nucleus_index:
                issues.append(
                    f"human_reception_opportunity_unknown_nucleus:{nucleus_id}"
                )
            elif nucleus_id not in observation_owned_set:
                issues.append(
                    f"human_reception_opportunity_not_observation_owned:{nucleus_id}"
                )

        opportunity_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*opportunity_target_ids, *opportunity_support_ids)
            if nucleus_id in nucleus_index
        )
        expected_opportunity_evidence = tuple(
            _ordered_span_ids(
                span_id
                for nucleus in opportunity_nuclei
                for span_id in nucleus.source_span_ids
            )
        )
        opportunity_evidence = tuple(opportunity.source_evidence_span_ids)
        if not opportunity_evidence:
            issues.append("human_reception_opportunity_evidence_missing")
        if opportunity_evidence != expected_opportunity_evidence:
            issues.append("human_reception_opportunity_evidence_mismatch")
        for span_id in opportunity_evidence:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(
                    f"human_reception_opportunity_invalid_evidence:{span_id}"
                )
        for span_id in resolver.unresolved_ids(opportunity_evidence):
            issues.append(
                f"human_reception_opportunity_unresolved_evidence:{span_id}"
            )

        if opportunity.retention not in _RETENTION_RANK:
            issues.append("human_reception_opportunity_retention_invalid")
        elif opportunity_nuclei:
            expected_retention = max(
                (nucleus.retention for nucleus in opportunity_nuclei),
                key=lambda value: _RETENTION_RANK[value],
            )
            if opportunity.retention != expected_retention:
                issues.append("human_reception_opportunity_retention_mismatch")
        if (
            not isinstance(opportunity.priority, int)
            or isinstance(opportunity.priority, bool)
            or opportunity.priority <= 0
        ):
            issues.append("human_reception_opportunity_priority_invalid")
        expected_source_field_count = len(
            {
                field
                for nucleus in opportunity_nuclei
                for field in nucleus.source_fields
            }
        )
        if opportunity.source_field_count != expected_source_field_count:
            issues.append("human_reception_opportunity_source_field_count_mismatch")
        if not isinstance(opportunity.safety_required, bool):
            issues.append("human_reception_opportunity_safety_required_invalid")
        expected_safety_required = bool(
            safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
            and opportunity.family in {"help_seeking", "counterdirection"}
        )
        if opportunity.safety_required is not expected_safety_required:
            issues.append("human_reception_opportunity_safety_required_mismatch")
        signature = (
            opportunity.family,
            opportunity.reception_act,
            opportunity_target_ids,
            opportunity_support_ids,
        )
        if signature in opportunity_signatures:
            issues.append("human_reception_opportunity_duplicate")
        opportunity_signatures.add(signature)
        if opportunity.family == "counterdirection" and not any(
            _is_reception_grounded_counterposition_nucleus(nucleus)
            for nucleus in opportunity_nuclei
        ):
            issues.append("human_reception_opportunity_ungrounded_counterposition")

    depth_policy = reception_plan.depth_policy
    moves = tuple(reception_plan.moves)
    if depth_policy.level not in {"minimal", "focused", "layered"}:
        issues.append("human_reception_depth_level_invalid")
    if depth_policy.safety_mode not in {
        "standard",
        "self_denial_bounded",
        "help_seeking_bounded",
    }:
        issues.append("human_reception_depth_safety_mode_invalid")
    if depth_policy.opportunity_count != len(opportunities):
        issues.append("human_reception_depth_opportunity_count_mismatch")
    if depth_policy.selected_move_count != len(moves):
        issues.append("human_reception_depth_selected_move_count_mismatch")
    if depth_policy.raw_character_count_used is not False:
        issues.append("human_reception_depth_raw_character_count_forbidden")
    if not depth_policy.selection_reason_codes:
        issues.append("human_reception_depth_selection_reason_missing")
    if len(depth_policy.selection_reason_codes) != len(
        set(depth_policy.selection_reason_codes)
    ):
        issues.append("human_reception_depth_selection_reason_duplicate")
    if any(
        not _is_body_free_code(code)
        for code in depth_policy.selection_reason_codes
    ):
        issues.append("human_reception_depth_selection_reason_non_body_free_code")
    if not 1 <= depth_policy.min_sentences <= depth_policy.max_sentences <= 3:
        issues.append("human_reception_depth_sentence_budget_invalid")
    if not 1 <= depth_policy.max_moves_per_sentence <= 2:
        issues.append("human_reception_depth_moves_per_sentence_invalid")
    if not 1 <= len(moves) <= 3:
        issues.append("human_reception_move_count_invalid")
    if not 1 <= depth_policy.min_realized_moves <= max(1, len(moves)):
        issues.append("human_reception_depth_min_realized_moves_invalid")
    required_move_count = sum(1 for move in moves if move.required)
    if depth_policy.min_realized_moves != max(1, required_move_count):
        issues.append("human_reception_depth_min_realized_moves_mismatch")
    if depth_policy.level == "minimal" and (
        len(moves) != 1
        or depth_policy.min_sentences != 1
        or depth_policy.max_sentences != 1
    ):
        issues.append("human_reception_depth_minimal_contract_invalid")
    if depth_policy.level == "focused":
        if len(moves) not in {1, 2}:
            issues.append("human_reception_depth_focused_contract_invalid")
        if depth_policy.max_sentences > 2:
            issues.append(
                "human_reception_depth_focused_sentence_budget_invalid"
            )
    if depth_policy.level == "layered" and (
        len(moves) < 2 or depth_policy.min_sentences < 2
    ):
        issues.append("human_reception_depth_layered_contract_invalid")

    allowed_move_roles = {
        "attention",
        "significance",
        "felt_response",
        "bounded_counterposition",
    }
    allowed_surface_strategies = {
        "quiet_referent_first",
        "emlis_attention_first",
        "referent_significance_first",
        "felt_response_first",
        "explicit_emlis_counterposition",
    }
    move_index: dict[str, GroundedReceptionMovePlan] = {}
    selected_opportunity_ids: set[str] = set()
    move_signatures: set[tuple[Any, ...]] = set()
    for index, move in enumerate(moves, start=1):
        expected_id = f"rm{index}"
        if not _MOVE_ID_RE.fullmatch(move.move_id):
            issues.append("human_reception_move_id_invalid")
        if move.move_id != expected_id:
            issues.append("human_reception_move_order_invalid")
        if move.move_id in move_index:
            issues.append("human_reception_move_id_duplicate")
        move_index[move.move_id] = move
        if move.move_role not in allowed_move_roles:
            issues.append("human_reception_move_role_invalid")
        if move.reception_act not in allowed_acts:
            issues.append("human_reception_move_act_invalid")
        move_target_ids = tuple(move.target_nucleus_ids)
        move_support_ids = tuple(move.support_nucleus_ids)
        if not move_target_ids:
            issues.append("human_reception_move_target_missing")
        if len(move_target_ids) != len(set(move_target_ids)):
            issues.append("human_reception_move_target_duplicate")
        if len(move_support_ids) != len(set(move_support_ids)):
            issues.append("human_reception_move_support_duplicate")
        if set(move_target_ids) & set(move_support_ids):
            issues.append("human_reception_move_target_support_overlap")
        for nucleus_id in (*move_target_ids, *move_support_ids):
            if nucleus_id not in nucleus_index:
                issues.append(f"human_reception_move_unknown_nucleus:{nucleus_id}")
            elif nucleus_id not in observation_owned_set:
                issues.append(
                    f"human_reception_move_not_observation_owned:{nucleus_id}"
                )
        move_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*move_target_ids, *move_support_ids)
            if nucleus_id in nucleus_index
        )
        expected_move_evidence = tuple(
            _ordered_span_ids(
                span_id
                for nucleus in move_nuclei
                for span_id in nucleus.source_span_ids
            )
        )
        move_evidence = tuple(move.source_evidence_span_ids)
        if not move_evidence:
            issues.append("human_reception_move_evidence_missing")
        if move_evidence != expected_move_evidence:
            issues.append("human_reception_move_evidence_mismatch")
        for span_id in move_evidence:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(f"human_reception_move_invalid_evidence:{span_id}")
        for span_id in resolver.unresolved_ids(move_evidence):
            issues.append(f"human_reception_move_unresolved_evidence:{span_id}")

        matching_opportunities = tuple(
            opportunity
            for opportunity in opportunities
            if (
                opportunity.reception_act == move.reception_act
                and opportunity.target_nucleus_ids == move_target_ids
                and opportunity.support_nucleus_ids == move_support_ids
                and opportunity.source_evidence_span_ids == move_evidence
            )
        )
        if not matching_opportunities:
            issues.append("human_reception_move_without_opportunity")
        else:
            opportunity = matching_opportunities[0]
            if opportunity.opportunity_id in selected_opportunity_ids:
                issues.append("human_reception_move_opportunity_duplicate")
            selected_opportunity_ids.add(opportunity.opportunity_id)
            expected_move_required = bool(
                opportunity.safety_required
                or opportunity.retention in {"required", "should"}
            )
            if move.required is not expected_move_required:
                issues.append("human_reception_move_required_mismatch")
            if move.surface_strategy != _surface_strategy_for_move(
                opportunity,
                move.move_role,
            ):
                issues.append("human_reception_move_surface_strategy_mismatch")
        if not 1 <= len(move.follow_elements) <= 3:
            issues.append("human_reception_move_follow_element_count_invalid")
        if len(move.follow_elements) != len(set(move.follow_elements)):
            issues.append("human_reception_move_follow_element_duplicate")
        if any(
            element not in allowed_follow_elements
            for element in move.follow_elements
        ):
            issues.append("human_reception_move_follow_element_invalid")
        if move.speaker_presence not in {"implicit_emlis", "explicit_emlis"}:
            issues.append("human_reception_move_speaker_presence_invalid")
        if move.reference_mode not in {
            "anaphoric_first",
            "short_anchor_if_ambiguous",
            "explicit_emlis_counterposition",
        }:
            issues.append("human_reception_move_reference_mode_invalid")
        if move.surface_strategy not in allowed_surface_strategies:
            issues.append("human_reception_move_surface_strategy_invalid")
        if not isinstance(move.required, bool):
            issues.append("human_reception_move_required_invalid")
        expected_distinct_ids = tuple(f"rm{item}" for item in range(1, index))
        if tuple(move.distinct_from_move_ids) != expected_distinct_ids:
            issues.append("human_reception_move_distinct_reference_invalid")
        move_signature = (
            move.reception_act,
            move_target_ids,
            move.move_role,
        )
        if move_signature in move_signatures:
            issues.append("human_reception_move_duplicate")
        move_signatures.add(move_signature)
        if move.move_role == "bounded_counterposition":
            if move.reception_act != "bounded_counter_self_denial":
                issues.append("human_reception_counterposition_move_act_invalid")
            if move.speaker_presence != "explicit_emlis":
                issues.append("human_reception_counterposition_move_speaker_invalid")
            if move.reference_mode != "explicit_emlis_counterposition":
                issues.append("human_reception_counterposition_move_reference_invalid")
            if move.surface_strategy != "explicit_emlis_counterposition":
                issues.append("human_reception_counterposition_move_strategy_invalid")
            if not any(
                _is_reception_grounded_counterposition_nucleus(nucleus)
                for nucleus in move_nuclei
            ):
                issues.append("human_reception_move_ungrounded_counterposition")

    if moves and reception_plan.primary_reception_act != moves[0].reception_act:
        issues.append("human_reception_primary_act_move_mismatch")
    # RR4 still owns the compatibility-field cutover.  Until then an internal
    # caller may set the legacy secondary act for the existing renderer; new
    # production plans keep standard-mode secondary acts empty.
    for opportunity in opportunities:
        if (
            opportunity.safety_required
            and opportunity.opportunity_id not in selected_opportunity_ids
        ):
            issues.append("human_reception_required_safety_opportunity_unselected")

    counter_moves = tuple(
        move for move in moves if move.move_role == "bounded_counterposition"
    )
    help_moves = tuple(
        move for move in moves if move.reception_act == "hold_help_seeking"
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        expected_safety_mode = (
            "help_seeking_bounded" if help_moves else "self_denial_bounded"
        )
        if depth_policy.safety_mode != expected_safety_mode:
            issues.append("human_reception_depth_safety_mode_mismatch")
        grounded_counter_opportunity = any(
            opportunity.family == "counterdirection"
            for opportunity in opportunities
        )
        if grounded_counter_opportunity and not counter_moves:
            issues.append("human_reception_required_counterposition_move_missing")
    elif depth_policy.safety_mode != "standard":
        issues.append("human_reception_depth_standard_safety_mode_required")

    if reception_plan.primary_reception_act not in allowed_acts:
        issues.append("human_reception_primary_act_missing_or_invalid")
    if (
        reception_plan.secondary_reception_act is not None
        and reception_plan.secondary_reception_act not in allowed_acts
    ):
        issues.append("human_reception_secondary_act_invalid")
    if reception_plan.secondary_reception_act == reception_plan.primary_reception_act:
        issues.append("human_reception_secondary_act_not_distinct")
    if reception_plan.primary_follow_element not in allowed_follow_elements:
        issues.append("human_reception_primary_follow_element_missing_or_invalid")
    if len(reception_plan.secondary_follow_elements) > 2:
        issues.append("human_reception_secondary_follow_element_limit_exceeded")
    if len(set(reception_plan.secondary_follow_elements)) != len(
        reception_plan.secondary_follow_elements
    ):
        issues.append("human_reception_secondary_follow_element_duplicate")
    if any(
        element not in allowed_follow_elements
        for element in reception_plan.secondary_follow_elements
    ):
        issues.append("human_reception_secondary_follow_element_invalid")
    if reception_plan.primary_follow_element in reception_plan.secondary_follow_elements:
        issues.append("human_reception_primary_follow_element_repeated")
    if (
        reception_plan.afterglow_follow_element is not None
        and reception_plan.afterglow_follow_element not in allowed_follow_elements
    ):
        issues.append("human_reception_afterglow_follow_element_invalid")
    if reception_plan.afterglow_follow_element in {
        reception_plan.primary_follow_element,
        *reception_plan.secondary_follow_elements,
    }:
        issues.append("human_reception_afterglow_follow_element_repeated")
    if reception_plan.primary_reception_act in allowed_acts:
        expected_follow_profile = _FOLLOW_PROFILE_BY_RECEPTION_ACT[
            reception_plan.primary_reception_act
        ]
        if (
            reception_plan.primary_follow_element,
            reception_plan.secondary_follow_elements,
            reception_plan.afterglow_follow_element,
        ) != expected_follow_profile:
            issues.append("human_reception_follow_profile_act_mismatch")

    target_ids = tuple(reception_plan.target_nucleus_ids)
    support_ids = tuple(reception_plan.support_nucleus_ids)
    observation_owned_ids = tuple(reception_plan.observation_owned_nucleus_ids)
    if target_ids != tuple(expected_target_ids):
        issues.append("human_reception_target_mismatch")
    if not target_ids:
        issues.append("human_reception_target_missing")
    for label, ids in (
        ("target", target_ids),
        ("support", support_ids),
        ("observation_owned", observation_owned_ids),
    ):
        if len(ids) != len(set(ids)):
            issues.append(f"human_reception_{label}_duplicate")
        for nucleus_id in ids:
            if nucleus_id not in nucleus_index:
                issues.append(f"human_reception_{label}_unknown_nucleus:{nucleus_id}")
    if set(target_ids) & set(support_ids):
        issues.append("human_reception_target_support_overlap")
    if not observation_owned_ids:
        issues.append("human_reception_observation_owned_missing")
    if not set(target_ids).issubset(observation_owned_ids):
        issues.append("human_reception_target_not_observation_owned")

    selected_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in (*target_ids, *support_ids)
        if nucleus_id in nucleus_index
    )
    expected_evidence_ids = tuple(
        _ordered_span_ids(
            span_id
            for nucleus in selected_nuclei
            for span_id in nucleus.source_span_ids
        )
    )
    if tuple(reception_plan.source_evidence_span_ids) != expected_evidence_ids:
        issues.append("human_reception_source_evidence_mismatch")
    if not reception_plan.source_evidence_span_ids:
        issues.append("human_reception_source_evidence_missing")
    for span_id in reception_plan.source_evidence_span_ids:
        if not _EVIDENCE_ID_RE.fullmatch(span_id):
            issues.append(f"human_reception_invalid_evidence_id:{span_id}")
    for span_id in resolver.unresolved_ids(reception_plan.source_evidence_span_ids):
        issues.append(f"human_reception_unresolved_evidence:{span_id}")

    if reception_plan.stance not in set(_STANCE_BY_RECEPTION_ACT.values()):
        issues.append("human_reception_stance_missing_or_invalid")
    elif (
        reception_plan.primary_reception_act in allowed_acts
        and reception_plan.stance
        != _STANCE_BY_RECEPTION_ACT[reception_plan.primary_reception_act]
    ):
        issues.append("human_reception_stance_act_mismatch")
    if reception_plan.speaker_presence not in {"implicit_emlis", "explicit_emlis"}:
        issues.append("human_reception_speaker_presence_missing_or_invalid")
    if reception_plan.reference_mode not in {
        "anaphoric_first",
        "short_anchor_if_ambiguous",
        "explicit_emlis_counterposition",
    }:
        issues.append("human_reception_reference_mode_missing_or_invalid")

    quote_policy = reception_plan.quote_policy
    if quote_policy.mode != "no_full_quote_replay":
        issues.append("human_reception_quote_policy_mode_invalid")
    if not 0 <= quote_policy.max_anchor_count <= 1:
        issues.append("human_reception_quote_anchor_count_invalid")
    if not 0 <= quote_policy.max_anchor_visible_chars <= 20:
        issues.append("human_reception_quote_anchor_length_invalid")
    sentence_policy = reception_plan.sentence_policy
    if sentence_policy.min_sentences != 1:
        issues.append("human_reception_sentence_min_invalid")
    if not 1 <= sentence_policy.max_sentences <= 2:
        issues.append("human_reception_sentence_max_invalid")
    if sentence_policy.min_sentences > sentence_policy.max_sentences:
        issues.append("human_reception_sentence_budget_invalid")

    distinctness = reception_plan.distinctness_policy
    if any(
        (
            distinctness.observation_summary_repetition_allowed,
            distinctness.relation_reexplanation_allowed,
            distinctness.all_input_enumeration_allowed,
            distinctness.policy_explanation_allowed,
            distinctness.new_cause_allowed,
            distinctness.new_identity_claim_allowed,
            distinctness.advice_allowed,
            distinctness.question_allowed,
        )
    ):
        issues.append("human_reception_distinctness_policy_relaxed")

    for prefix, codes in (
        ("safety_modifier", reception_plan.safety_modifier_codes),
        ("forbidden_surface", reception_plan.forbidden_surface_codes),
    ):
        if len(codes) != len(set(codes)):
            issues.append(f"human_reception_{prefix}_duplicate")
        for code in codes:
            if not _is_body_free_code(code):
                issues.append(f"human_reception_{prefix}_non_body_free_code")
    if not set(_RECEPTION_FORBIDDEN_SURFACE_CODES).issubset(
        reception_plan.forbidden_surface_codes
    ):
        issues.append("human_reception_forbidden_surface_contract_missing")

    bounded_counterposition = (
        reception_plan.primary_reception_act == "bounded_counter_self_denial"
        or reception_plan.secondary_reception_act == "bounded_counter_self_denial"
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not {
            "felt_state_is_real",
            "identity_claim_is_not_accepted",
        }.issubset(reception_plan.safety_modifier_codes):
            issues.append("human_reception_self_denial_safety_modifier_missing")
    if bounded_counterposition:
        if reception_plan.speaker_presence != "explicit_emlis":
            issues.append("human_reception_self_denial_explicit_stance_missing")
        if reception_plan.reference_mode != "explicit_emlis_counterposition":
            issues.append("human_reception_counterposition_reference_invalid")
        if "counterposition_requires_input_evidence" not in reception_plan.safety_modifier_codes:
            issues.append("human_reception_counterposition_evidence_policy_missing")
        if not any(
            _is_reception_grounded_counterposition_nucleus(item)
            for item in selected_nuclei
        ):
            issues.append("human_reception_ungrounded_self_denial_counterposition")
    if (
        material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    ):
        if reception_plan.primary_reception_act != "stay_with_current_burden":
            issues.append("human_reception_short_state_act_invalid")
        if reception_plan.sentence_policy.max_sentences != 1:
            issues.append("human_reception_short_state_sentence_budget_invalid")
        if reception_plan.distinctness_policy.policy_explanation_allowed:
            issues.append("human_reception_short_state_policy_explanation_allowed")
    return tuple(_dedupe(issues))


def validate_grounded_observation_plan(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Validate references and Safety/Surface perimeter without rendering text."""

    issues: list[str] = []
    if plan.schema_version != GROUND_OBSERVATION_PLAN_SCHEMA_VERSION:
        issues.append("plan_schema_version_mismatch")
    if plan.adapter_version != GROUND_OBSERVATION_PLAN_ADAPTER_VERSION:
        issues.append("plan_adapter_version_mismatch")
    if plan.generation_path != GROUND_OBSERVATION_PLAN_GENERATION_PATH:
        issues.append("plan_generation_path_mismatch")

    def append_code_issues(prefix: str, values: Sequence[Any]) -> None:
        for value in values or ():
            cleaned = _clean(value)
            if not cleaned or not _is_body_free_code(cleaned):
                issues.append(f"{prefix}_non_body_free_code")

    def append_evidence_issues(prefix: str, span_ids: Sequence[str]) -> tuple[str, ...]:
        requested = tuple(_dedupe(span_ids))
        for span_id in requested:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(f"{prefix}_invalid_evidence_id:{span_id}")
        unresolved = resolver.unresolved_ids(requested)
        for span_id in unresolved:
            issues.append(f"{prefix}_unresolved_evidence:{span_id}")
        return unresolved

    nucleus_index: dict[str, GroundedSemanticNucleus] = {}
    for item in plan.nuclei:
        if not item.nucleus_id:
            issues.append("nucleus_without_id")
            continue
        if item.nucleus_id in nucleus_index:
            issues.append(f"duplicate_nucleus_id:{item.nucleus_id}")
        nucleus_index[item.nucleus_id] = item
        append_code_issues(
            f"nucleus:{item.nucleus_id}",
            (
                item.nucleus_id,
                *item.surface_anchor_ids,
                *item.semantic_frame.target_anchor_ids,
                *item.semantic_frame.attribute_codes,
                *item.forbidden_inference_codes,
                *item.source_claim_ids,
                *item.source_meaning_block_keys,
            ),
        )
        if not item.source_span_ids:
            issues.append(f"nucleus_without_evidence:{item.nucleus_id}")
        unresolved = append_evidence_issues(f"nucleus:{item.nucleus_id}", item.source_span_ids)
        if not unresolved and tuple(item.source_fields) != resolver.source_fields_for(item.source_span_ids):
            issues.append(f"nucleus_source_field_mismatch:{item.nucleus_id}")

    relation_index: dict[str, GroundedSemanticRelation] = {}
    for item in plan.relations:
        if not item.relation_id:
            issues.append("relation_without_id")
            continue
        if item.relation_id in relation_index:
            issues.append(f"duplicate_relation_id:{item.relation_id}")
        relation_index[item.relation_id] = item
        append_code_issues(
            f"relation:{item.relation_id}",
            (
                item.relation_id,
                item.type,
                item.from_nucleus_id,
                item.to_nucleus_id,
                *item.source_relation_ids,
                *item.source_meaning_arc_keys,
            ),
        )
        if item.type not in _ALLOWED_RELATION_KINDS:
            issues.append(f"unsupported_relation_type:{item.relation_id}:{item.type}")
        if item.from_nucleus_id not in nucleus_index:
            issues.append(f"relation_unknown_from_nucleus:{item.relation_id}:{item.from_nucleus_id}")
        if item.to_nucleus_id not in nucleus_index:
            issues.append(f"relation_unknown_to_nucleus:{item.relation_id}:{item.to_nucleus_id}")
        if item.from_nucleus_id == item.to_nucleus_id:
            issues.append(f"relation_self_loop:{item.relation_id}")
        if not item.source_span_ids:
            issues.append(f"relation_without_evidence:{item.relation_id}")
        append_evidence_issues(f"relation:{item.relation_id}", item.source_span_ids)

    for item in plan.unknown_boundaries:
        append_code_issues(
            f"unknown_boundary:{item.unknown_id}",
            (item.unknown_id, item.dimension, *item.affected_nucleus_ids),
        )
        for nucleus_id in item.affected_nucleus_ids:
            if nucleus_id not in nucleus_index:
                issues.append(f"unknown_boundary_unknown_nucleus:{item.unknown_id}:{nucleus_id}")
        append_evidence_issues(f"unknown_boundary:{item.unknown_id}", item.evidence_span_ids)

    for nucleus_id in (
        *plan.response_plan.primary_nucleus_ids,
        *plan.response_plan.supporting_nucleus_ids,
        *plan.response_plan.fact_boundary_nucleus_ids,
        *plan.response_plan.human_follow_target_ids,
        *plan.response_plan.required_nucleus_ids,
        *plan.response_plan.optional_nucleus_ids,
        *plan.coverage_requirements.required_nucleus_ids,
    ):
        if nucleus_id not in nucleus_index:
            issues.append(f"response_or_coverage_unknown_nucleus:{nucleus_id}")
    for relation_id in (*plan.response_plan.relation_ids, *plan.coverage_requirements.required_relation_ids):
        if relation_id not in relation_index:
            issues.append(f"response_or_coverage_unknown_relation:{relation_id}")

    reception_plan = plan.response_plan.human_reception_plan
    if plan.coverage_requirements.human_follow_required:
        if reception_plan is None:
            issues.append("human_reception_plan_missing")
        else:
            issues.extend(
                validate_grounded_human_reception_plan(
                    reception_plan,
                    expected_target_ids=plan.response_plan.human_follow_target_ids,
                    nucleus_index=nucleus_index,
                    resolver=resolver,
                    safety_kind=plan.safety_policy.safety_kind,
                    material_quality=plan.input_profile.material_quality,
                )
            )
    elif reception_plan is not None:
        issues.append("human_reception_plan_forbidden_when_not_required")

    append_code_issues("source_contract", plan.source_contracts)
    append_code_issues("safety_boundary", plan.safety_policy.required_boundary_codes)
    if plan.response_plan.question_policy.allowed:
        issues.append("p7_question_policy_must_be_false")
    if plan.surface_policy.completed_semantic_template_allowed:
        issues.append("completed_semantic_template_must_be_false")
    if plan.surface_policy.example_cue_route_allowed:
        issues.append("example_cue_route_must_be_false")
    if plan.surface_policy.synthetic_evidence_id_allowed:
        issues.append("synthetic_evidence_id_must_be_false")
    if plan.input_profile.text_presence == "text_present" and not plan.response_plan.required_nucleus_ids:
        issues.append("text_present_without_required_nucleus")

    safety_kind = plan.safety_policy.safety_kind
    separate_expected = safety_kind in {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}
    if separate_expected:
        if plan.response_plan.surface_shape != "separate_safety_surface":
            issues.append("separate_safety_surface_shape_missing")
        if plan.surface_policy.content_source != "separate_safety_owner":
            issues.append("separate_safety_owner_not_preserved")
        if plan.surface_policy.generic_observation_surface_allowed:
            issues.append("generic_surface_allowed_for_separate_safety")
        if plan.safety_policy.grounded_plan_overlay_allowed:
            issues.append("grounded_overlay_allowed_for_separate_safety")
    else:
        if plan.surface_policy.content_source != "grounded_plan_only":
            issues.append("grounded_content_source_missing")
        if plan.input_profile.material_quality == "empty":
            if plan.response_plan.surface_shape != "plain":
                issues.append("empty_input_surface_shape_must_be_plain")
        else:
            # Public Emlis observations always use the same two labelled
            # sections.  Input length controls the number of paragraphs inside
            # a section; it cannot switch the public body back to a plain or
            # observation-only surface.
            if plan.response_plan.surface_shape != "two_stage":
                issues.append("mandatory_two_stage_surface_shape_missing")
            if not plan.coverage_requirements.human_follow_required:
                issues.append("mandatory_two_stage_human_follow_requirement_missing")
            if not plan.response_plan.human_follow_target_ids:
                issues.append("mandatory_two_stage_human_follow_target_missing")
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not plan.safety_policy.identity_claim_must_not_be_accepted_as_fact:
            issues.append("self_denial_identity_fact_boundary_missing")
        if not plan.coverage_requirements.fact_boundary_required:
            issues.append("self_denial_fact_boundary_requirement_missing")
        if any(
            nucleus_id not in nucleus_index
            or nucleus_index[nucleus_id].kind != "self_evaluation"
            or nucleus_index[nucleus_id].semantic_frame.predicate_kind
            != "self_evaluation"
            or "operator:self_evaluation"
            not in nucleus_index[nucleus_id].semantic_frame.attribute_codes
            for nucleus_id in plan.response_plan.fact_boundary_nucleus_ids
        ):
            issues.append("self_denial_fact_boundary_target_kind_invalid")
    if safety_kind == TRIAGE_SAFETY_BLOCKED_EMERGENCY and not plan.safety_policy.emergency_path_must_not_be_overridden:
        issues.append("emergency_override_protection_missing")

    expected_response_kind = {
        "short_state_sufficient": "short_state_observation",
        "limited_grounding": "limited_grounding_observation",
        "labels_only_limited": "labels_only_limited_observation",
        "empty": "unavailable",
    }.get(plan.input_profile.material_quality)
    if (
        expected_response_kind
        and safety_kind == TRIAGE_SAFE_OBSERVATION
        and plan.response_plan.response_kind != expected_response_kind
    ):
        issues.append("material_quality_response_kind_mismatch")
    if plan.input_profile.material_quality == "short_state_sufficient" and plan.response_plan.question_policy.allowed:
        issues.append("short_state_question_escape_forbidden")
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not plan.response_plan.fact_boundary_nucleus_ids:
            issues.append("self_denial_fact_boundary_target_missing")
        if not plan.response_plan.human_follow_target_ids:
            issues.append("self_denial_human_follow_target_missing")
        opposition_required = (
            "input_grounded_continuation_refusal"
            in plan.safety_policy.required_boundary_codes
        )
        if opposition_required and not any(
            item.type == "continuation_or_refusal"
            and item.relation_id in plan.coverage_requirements.required_relation_ids
            for item in plan.relations
        ):
            issues.append("self_denial_limited_opposition_relation_missing")

    computed_references = _all_plan_evidence_ids(plan.nuclei, plan.relations, plan.unknown_boundaries)
    if tuple(plan.referenced_evidence_span_ids) != computed_references:
        issues.append("referenced_evidence_span_ids_mismatch")
    append_evidence_issues("plan", plan.referenced_evidence_span_ids)
    if not plan.evidence_ledger_validation.valid:
        issues.extend(
            f"evidence_ledger_contract:{code}"
            for code in plan.evidence_ledger_validation.issue_codes
        )
    return tuple(_dedupe(issues))


def build_grounded_observation_plan(
    current_input: Mapping[str, Any] | None,
    *,
    evidence_spans: Sequence[EvidenceSpan] | None = None,
    reports: Sequence[PerspectiveReport] | None = None,
    board: PerspectiveBoard | None = None,
    graph: ObservationGraph | None = None,
    meaning_blocks: Sequence[InputMeaningBlock] | None = None,
    coverage_plan: MeaningCoveragePlan | None = None,
    whole_input_meaning_arc: WholeInputMeaningArc | None = None,
    retention_plan: MajorMeaningRetentionPlan | None = None,
    safety_decision: EmlisSafetyTriageDecision | None = None,
) -> GroundedObservationPlan:
    """Build the canonical plan used by the public grounded reply path."""

    normalized = normalize_emlis_current_input(current_input or {})
    span_list = tuple(evidence_spans if evidence_spans is not None else build_evidence_ledger(normalized))
    ledger_validation = validate_evidence_ledger(span_list, current_input=normalized)
    try:
        resolver = build_evidence_span_resolver(span_list, current_input=normalized)
    except EvidenceLedgerResolutionError as exc:
        raise GroundedObservationPlanError(str(exc)) from exc

    report_list = tuple(reports if reports is not None else run_perspective_observers(span_list))
    perspective_board = board or build_perspective_board(evidence_spans=span_list, reports=report_list)
    observation_graph = graph or integrate_perspective_board(board=perspective_board)

    structural_artifacts = _build_meaning_artifacts(normalized, span_list)
    if any(value is not None for value in (meaning_blocks, coverage_plan, whole_input_meaning_arc, retention_plan)):
        blocks = tuple(meaning_blocks) if meaning_blocks is not None else structural_artifacts.meaning_blocks
        block_keys = [_clean(getattr(block, "block_key", "")) for block in blocks]
        coverage = coverage_plan or MeaningCoveragePlan(
            input_level="long" if len(blocks) >= 6 else "short" if len(blocks) <= 2 else "medium",
            clear_long_input=len(blocks) >= 6,
            meaning_block_count=len(blocks),
            required_roles=_dedupe(getattr(block, "role", "") for block in blocks),
            selected_block_keys=block_keys,
            min_blocks_to_cover=len(blocks),
            max_blocks_to_cover=len(blocks),
            coverage_ratio_target=1.0 if blocks else 0.0,
            reason="explicit_upstream_meaning_blocks_adapted_without_role_reclassification",
        )
        arc = whole_input_meaning_arc or WholeInputMeaningArc(
            arc_key="whole_input:provided_source_order",
            title="provided_source_order_arc",
            summary="",
            ordered_block_keys=block_keys,
            clarity=0.8 if blocks else 0.0,
            evidence=[],
        )
        retention = retention_plan or MajorMeaningRetentionPlan(
            clear_long_input=bool(getattr(coverage, "clear_long_input", False)),
            total_block_count=len(blocks),
            must_keep_block_keys=block_keys,
            should_keep_block_keys=[],
            optional_block_keys=[],
            forbidden_overcompression_targets=block_keys,
            min_must_keep_coverage_ratio=1.0 if blocks else 0.0,
            reason="provided_meaning_blocks_are_source_contract",
        )
        meaning_artifacts = _MeaningArtifacts(blocks, coverage, arc, retention)
    else:
        meaning_artifacts = structural_artifacts

    base_triage = safety_decision or build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=observation_graph,
        evidence_spans=span_list,
    )
    triage = _canonicalize_safety_decision(
        base_triage,
        span_list,
        authoritative_self_denial=safety_decision is not None,
    )
    nuclei = _build_nuclei(
        spans=span_list,
        board=perspective_board,
        meaning_artifacts=meaning_artifacts,
        safety_decision=triage,
    )
    relations = _build_relations(
        spans=span_list,
        board=perspective_board,
        nuclei=nuclei,
        meaning_artifacts=meaning_artifacts,
    )
    unknowns = _build_unknown_boundaries(board=perspective_board, graph=observation_graph, nuclei=nuclei)
    presence = _text_presence(span_list)
    material_quality = _material_quality(
        text_presence=presence,
        safety_kind=triage.safety_triage_kind,
        spans=span_list,
        nuclei=nuclei,
    )
    nuclei = _apply_short_state_lexical_policy(
        nuclei,
        span_list,
        material_quality=material_quality,
        relations=relations,
    )
    complexity = _semantic_complexity(nuclei=nuclei, relations=relations, meaning_artifacts=meaning_artifacts)
    response_plan, coverage_requirements, surface_policy, safety_policy = _build_response_and_policies(
        nuclei=nuclei,
        relations=relations,
        safety_decision=triage,
        complexity=complexity,
        material_quality=material_quality,
    )
    referenced_ids = _all_plan_evidence_ids(nuclei, relations, unknowns)
    plan = GroundedObservationPlan(
        schema_version=GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        adapter_version=GROUND_OBSERVATION_PLAN_ADAPTER_VERSION,
        generation_path=GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        input_profile=GroundedInputProfile(
            text_presence=presence,
            material_quality=material_quality,
            semantic_complexity=complexity,
            nucleus_count=len(nuclei),
            relation_count=len(relations),
            safety_kind=triage.safety_triage_kind,
        ),
        nuclei=nuclei,
        relations=relations,
        unknown_boundaries=unknowns,
        response_plan=response_plan,
        coverage_requirements=coverage_requirements,
        surface_policy=surface_policy,
        safety_policy=safety_policy,
        evidence_ledger_validation=ledger_validation,
        referenced_evidence_span_ids=referenced_ids,
        source_contracts=(
            "EmlisCurrentInputBundle",
            "EvidenceSpan:sN",
            "PerspectiveReport",
            "PerspectiveBoard",
            "ObservationGraph",
            "InputMeaningBlock",
            "MeaningCoveragePlan",
            "WholeInputMeaningArc",
            "MajorMeaningRetentionPlan",
            "EmlisSafetyTriageDecision",
        ),
    )
    issues = validate_grounded_observation_plan(plan, resolver)
    if issues:
        raise GroundedObservationPlanError("invalid_grounded_observation_plan:" + ",".join(issues))
    return plan


def _final_stage1_source_text_by_span(
    evidence_spans: Sequence[EvidenceSpan],
) -> dict[str, str]:
    return {
        _clean(getattr(span, "span_id", "")): _clean(
            getattr(span, "raw_text", "")
        )
        for span in evidence_spans
        if _clean(getattr(span, "span_id", ""))
    }


def _final_stage1_relation_source_text(
    relation: GroundedSemanticRelation,
    source_text_by_span: Mapping[str, str],
) -> str:
    return " ".join(
        source_text_by_span.get(span_id, "")
        for span_id in relation.source_span_ids
        if source_text_by_span.get(span_id, "")
    )


def _final_stage1_owner_scope_is_current(
    fragment: str, *, source_field: str, strict_actor: bool = False,
) -> bool:
    top_level = _top_level_text(fragment)
    if top_level is None:
        return False
    scope = top_level.strip()
    if not scope:
        return False
    attributed_owner = re.search(
        r"(?:と|って)(?P<owner>[^\s、,。.!！?？]{1,20}?)"
        r"(?:は|が|も)(?=(?:言|話|語|述|書|記録|考|思|感じ|判断|決め))",
        scope,
    )
    if (
        attributed_owner is not None
        and _SELF_REFERENCE_RE.fullmatch(
            attributed_owner.group("owner")
        )
        is None
    ):
        return False
    temporal_prefix = re.compile(
        r"^(?:(?:今日|昨日|明日|今|現在|今朝|午前|午後|"
        r"夕方|朝|昼|夜|以前|これまで)(?:は|も|の|には)?|"
        r"この記録では?|少し(?:だけ|ずつ)?|やや|ずっと|まだ)"
        r"[、,\s]*"
    )
    owner_marker = re.compile(
        r"^(?P<owner>[^\s、,。.!！?？]{1,32}?)"
        r"(?P<marker>にとって|には|は|が|も)"
        r"(?P<remainder>.*)$"
    )
    while scope:
        stripped = temporal_prefix.sub("", scope, count=1)
        if stripped != scope:
            scope = stripped.lstrip(" \t　")
            continue
        owner_match = owner_marker.match(scope)
        if owner_match is None:
            return True
        owner = owner_match.group("owner")
        remainder = owner_match.group("remainder").lstrip(" \t　、,")
        owner_operators = set(
            _operator_codes_for_text(owner, source_field=source_field)
        )
        semantic_content_owner = bool(
            owner_operators
            or _FINAL_STAGE1_BURDEN_RE.search(owner)
            or owner.endswith(("気持ち", "願い", "わけ", "こと", "の"))
            and bool(
                _operator_codes_for_text(
                    remainder,
                    source_field=source_field,
                )
                or _FINAL_STAGE1_BURDEN_RE.search(remainder)
                or _PRESENT_RESIDUE_RE.search(remainder)
            )
        )
        if (
            _SELF_REFERENCE_RE.fullmatch(owner) is None
            and (strict_actor or not semantic_content_owner)
        ):
            return False
        if not remainder:
            return True
        scope = remainder
    return True



def _final_stage1_compound_meaning_projections_for_span(
    span: EvidenceSpan,
    *,
    base_frame: GroundedSemanticFrame,
) -> tuple[_TypedNucleusProjection, ...]:
    """Recover source-bounded compound meaning only for final Stage-1.

    The active I5 owner deliberately keeps one nucleus per EvidenceSpan.  A
    final-language projection cannot, however, let one punctuation-sized span
    collapse a burden/wish pair, a wish/block pair, an event with present
    residue, or a performed action with its observed change.  This helper
    reuses the canonical nucleus/relation contract and grammatical operators;
    it neither renders text nor creates Evidence.
    """

    source_field = _clean(getattr(span, "source_field", ""))
    if source_field not in _TEXT_SOURCE_FIELDS:
        return ()
    text = _clean(getattr(span, "raw_text", ""))
    if not text or _top_level_text(text) is None:
        return ()

    def trimmed_range(start: int, end: int) -> tuple[int, int]:
        while start < end and text[start] in " \t\r\n、,。．.!！?？":
            start += 1
        while start < end and text[end - 1] in " \t\r\n、,。．.!！?？":
            end -= 1
        return start, end

    def projection_codes(
        scalar_start: int,
        scalar_end: int,
        *codes: str,
    ) -> tuple[str, ...]:
        provenance = tuple(
            code
            for code in base_frame.attribute_codes
            if code.startswith(
                (
                    "semantic_analyzer:",
                    "detected_type:",
                    "source_claim:",
                )
            )
        )
        return tuple(
            _dedupe(
                (
                    *provenance,
                    f"source_fragment_scalar_range:{scalar_start}:{scalar_end}",
                    "source_fragment_scalar_source:normalized_raw_text",
                    "semantic_role:generic_relation_fragment",
                    "semantic_role:final_stage1_compound_meaning",
                    *codes,
                )
            )
        )

    def endpoint_projection(
        scalar_start: int,
        scalar_end: int,
        *,
        nucleus_suffix: str,
        extra_codes: Sequence[str] = (),
    ) -> _TypedNucleusProjection | None:
        fragment = text[scalar_start:scalar_end]
        if not fragment or not _final_stage1_owner_scope_is_current(fragment, source_field=source_field):
            return None
        operators = set(
            _operator_codes_for_text(fragment, source_field=source_field)
        )
        explicit_deliberation = bool(
            _FINAL_STAGE1_OPEN_DELIBERATION_RE.search(fragment)
        )
        negated_wish = bool(
            re.search(
                r"(?:たい|ほしい|欲しい)(?:気持ち|願い|わけ)?"
                r"(?:は|が|も|では|じゃ)?"
                r"(?:ない|なかった|ありません(?:でした)?)$",
                fragment,
            )
        )
        if explicit_deliberation or "operator:uncertainty" in operators:
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="uncertainty",
                predicate_kind="open_deliberation" if explicit_deliberation else "uncertainty",
                polarity="neutral",
                modality="uncertain",
                time_scope=_time_scope_for_text(fragment),
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    "operator:uncertainty",
                    "semantic_role:limiting_unknown",
                    "semantic_role:burden",
                    *extra_codes,
                ),
            )
        if "operator:wish" in operators and not negated_wish:
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="wish",
                predicate_kind="wish",
                polarity="positive",
                modality="wish",
                time_scope=_time_scope_for_text(fragment),
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    "operator:wish",
                    "semantic_role:retained_intention",
                    *extra_codes,
                ),
            )
        if (
            "operator:positive_change" in operators
            or _POSITIVE_CHANGE_RE.search(fragment)
        ):
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="change",
                predicate_kind="change",
                polarity="positive",
                modality=(
                    "feeling"
                    if "operator:feeling" in operators
                    else "fact"
                ),
                time_scope=_time_scope_for_text(fragment),
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    "operator:change",
                    "operator:positive_change",
                    "semantic_role:current_change",
                    "semantic_role:explicit_result",
                    "semantic_role:positive_evaluation",
                    *extra_codes,
                ),
            )
        constrained = bool(
            "operator:constraint" in operators
            or _FINAL_STAGE1_INABILITY_RE.search(fragment)
        )
        if constrained:
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="constraint",
                predicate_kind="constraint",
                polarity=(
                    "negative"
                    if "operator:negation" in operators
                    or _FINAL_STAGE1_INABILITY_RE.search(fragment)
                    else "neutral"
                ),
                modality="possibility",
                time_scope=_time_scope_for_text(fragment),
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    "operator:constraint",
                    "semantic_role:burden",
                    "semantic_role:blocked_direction",
                    *extra_codes,
                ),
            )
        if (
            "operator:feeling" in operators
            or "operator:refusal" in operators
            or _FINAL_STAGE1_BURDEN_RE.search(fragment)
            or _PRESENT_RESIDUE_RE.search(fragment)
        ):
            residue = bool(_PRESENT_RESIDUE_RE.search(fragment))
            refusal = "operator:refusal" in operators
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="reaction" if not refusal else "state",
                predicate_kind="residue" if residue else "feeling",
                polarity="negative",
                modality="refusal" if refusal else "feeling",
                time_scope=(
                    "present" if residue else _time_scope_for_text(fragment)
                ),
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    *(("operator:residue", "semantic_role:present_residue") if residue else ()),
                    "semantic_role:burden",
                    *extra_codes,
                ),
            )
        performed_action = bool(
            _ACTION_ARGUMENT_STEM_RE.search(fragment)
            and not {
                "operator:negation",
                "operator:constraint",
                "operator:refusal",
                "operator:uncertainty",
                "operator:wish",
            }
            & operators
        )
        if performed_action:
            return _TypedNucleusProjection(
                nucleus_suffix=nucleus_suffix,
                kind="action",
                predicate_kind="action",
                polarity="neutral",
                modality="fact",
                time_scope="past",
                scalar_start=scalar_start,
                scalar_end=scalar_end,
                attribute_codes=projection_codes(
                    scalar_start,
                    scalar_end,
                    *operators,
                    "operator:action",
                    "operator:performed_action",
                    "semantic_role:concrete_action",
                    "semantic_role:concrete_action_evidence",
                    *extra_codes,
                ),
            )
        return None

    # Event -> (wish + present residue) is a three-owner structure.  The
    # event is source fact, while wish and residue remain co-present now.
    event_links = tuple(_FINAL_STAGE1_EVENT_BEFORE_LINK_RE.finditer(text))
    if len(event_links) == 1:
        event_link = event_links[0]
        event_start, event_end = trimmed_range(
            0,
            event_link.start() + len(event_link.group("perfective")),
        )
        remainder_start, remainder_end = trimmed_range(
            event_link.end(),
            len(text),
        )
        coordinate_links = tuple(
            match
            for match in _top_level_pattern_matches(
                text[remainder_start:remainder_end],
                _FINAL_STAGE1_WISH_RESIDUE_LINK_RE,
            )
        )
        admitted: list[
            tuple[
                _TypedNucleusProjection,
                _TypedNucleusProjection,
            ]
        ] = []
        for coordinate_link in coordinate_links:
            wish_start, wish_end = trimmed_range(
                remainder_start,
                remainder_start + coordinate_link.start(),
            )
            residue_start, residue_end = trimmed_range(
                remainder_start + coordinate_link.end(),
                remainder_end,
            )
            wish = endpoint_projection(
                wish_start,
                wish_end,
                nucleus_suffix=":wish",
                extra_codes=("semantic_dependency:coexisting_wish_residue",),
            )
            residue = endpoint_projection(
                residue_start,
                residue_end,
                nucleus_suffix=":residue",
                extra_codes=(
                    "semantic_dependency:event_before_residue",
                    "semantic_dependency:coexisting_wish_residue",
                ),
            )
            if (
                wish is not None
                and wish.kind == "wish"
                and residue is not None
                and residue.predicate_kind == "residue"
            ):
                admitted.append((wish, residue))
        event_fragment = text[event_start:event_end]
        if (
            len(admitted) == 1
            and event_start < event_end
            and _final_stage1_owner_scope_is_current(event_fragment, source_field=source_field)
        ):
            wish, residue = admitted[0]
            event = _TypedNucleusProjection(
                nucleus_suffix="",
                kind="event",
                predicate_kind="event",
                polarity="neutral",
                modality="fact",
                time_scope="past",
                scalar_start=event_start,
                scalar_end=event_end,
                attribute_codes=projection_codes(
                    event_start,
                    event_end,
                    "operator:performed_event",
                    "semantic_role:source_event",
                    "semantic_dependency:event_before_residue",
                ),
            )
            return event, wish, residue

    # A present burden followed by an explicitly open deliberation keeps the
    # unresolved question as its own epistemic owner.
    deliberation_links = tuple(
        _top_level_pattern_matches(
            text,
            _FINAL_STAGE1_DELIBERATION_LINK_RE,
        )
    )
    if len(deliberation_links) == 1:
        link = deliberation_links[0]
        left_start, left_end = trimmed_range(0, link.start())
        right_start, right_end = trimmed_range(link.end(), len(text))
        left = endpoint_projection(
            left_start,
            left_end,
            nucleus_suffix="",
            extra_codes=("semantic_dependency:burden_with_open_deliberation",),
        )
        right = endpoint_projection(
            right_start,
            right_end,
            nucleus_suffix=":open-deliberation",
            extra_codes=("semantic_dependency:burden_with_open_deliberation",),
        )
        if (
            left is not None
            and left.kind in {"reaction", "state", "constraint"}
            and right is not None
            and right.kind == "uncertainty"
        ):
            return (
                replace(left, relation_kind="coexistence"),
                replace(
                    right,
                    relation_kind="coexistence",
                    grounding_kind="user_stated_relation",
                ),
            )

    contrast_links = tuple(
        _top_level_pattern_matches(text, _TOP_LEVEL_CONTRAST_LINK_RE)
    )
    if len(contrast_links) != 1:
        return ()
    link = contrast_links[0]
    left_start, left_end = trimmed_range(0, link.start())
    right_start, right_end = trimmed_range(link.end(), len(text))
    left = endpoint_projection(
        left_start,
        left_end,
        nucleus_suffix="",
        extra_codes=("semantic_dependency:top_level_compound_relation",),
    )
    if left is None:
        return ()

    # One contrast endpoint may itself be a performed action -> observed
    # change pair.  Keep all three source meanings instead of assigning the
    # whole span to the terminal feeling alone.
    right_text = text[right_start:right_end]
    action_result_links = tuple(
        _FINAL_STAGE1_ACTION_RESULT_LINK_RE.finditer(right_text)
    )
    if len(action_result_links) == 1:
        action_link = action_result_links[0]
        action_start, action_end = trimmed_range(
            right_start,
            right_start + action_link.start() + 1,
        )
        change_start, change_end = trimmed_range(
            right_start + action_link.end(),
            right_end,
        )
        action = endpoint_projection(
            action_start,
            action_end,
            nucleus_suffix=":action",
            extra_codes=("semantic_dependency:action_before_change",),
        )
        change = endpoint_projection(
            change_start,
            change_end,
            nucleus_suffix=":change",
            extra_codes=(
                "semantic_dependency:action_before_change",
                "semantic_dependency:contrast_before_action_result",
            ),
        )
        if (
            left.kind in {"reaction", "state", "constraint"}
            and action is not None
            and action.kind == "action"
            and change is not None
            and change.kind == "change"
        ):
            left = replace(
                left,
                attribute_codes=tuple(
                    _dedupe(
                        (
                            *left.attribute_codes,
                            "semantic_dependency:contrast_before_action_result",
                        )
                    )
                ),
            )
            return left, action, change

    right = endpoint_projection(
        right_start,
        right_end,
        nucleus_suffix=":counterpart",
        extra_codes=("semantic_dependency:top_level_compound_relation",),
    )
    if right is None:
        return ()
    # In a wish-versus-uncertainty contrast, the uncertain endpoint is the
    # source-explicit limiting burden on that wish. Keep its uncertainty
    # predicate, modality, operators, and scalar evidence intact while giving
    # the endpoint the node kind required by direction-under-burden.
    if left.kind == "wish" and right.kind == "uncertainty":
        right = replace(right, kind="constraint")
    burden_kinds = {"reaction", "state", "constraint", "uncertainty"}
    if left.kind == "wish" and right.kind in burden_kinds:
        relation_kind: RelationKind = "wish_and_constraint"
    elif right.kind == "wish" and left.kind in burden_kinds:
        relation_kind = "preserves_despite"
    else:
        return ()
    return (
        replace(left, relation_kind=relation_kind),
        replace(
            right,
            relation_kind=relation_kind,
            grounding_kind="user_stated_relation",
        ),
    )


def _final_stage1_has_contrast_marker_between(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    evidence_spans: Sequence[EvidenceSpan],
) -> bool:
    endpoint_ids = (*left.source_span_ids, *right.source_span_ids)
    endpoint_numbers = tuple(_span_number(span_id) for span_id in endpoint_ids)
    if not endpoint_numbers:
        return False
    lower = min(endpoint_numbers)
    upper = max(endpoint_numbers)
    endpoint_fields = set((*left.source_fields, *right.source_fields))
    return any(
        lower <= _span_number(_clean(getattr(span, "span_id", ""))) <= upper
        and _clean(getattr(span, "source_field", "")) in endpoint_fields
        and bool(_CONTRAST_RE.search(_clean(getattr(span, "raw_text", ""))))
        for span in evidence_spans
    )


def _final_stage1_direction_under_burden(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
) -> bool:
    left_codes = set(left.semantic_frame.attribute_codes)
    right_codes = set(right.semantic_frame.attribute_codes)
    direction = bool(
        left.kind == "wish"
        or left.semantic_frame.modality in {"wish", "intention"}
        or left_codes
        & {
            "operator:wish",
            "operator:continuation",
            "semantic_role:retained_intention",
        }
    )
    burden = bool(
        right.kind in {"constraint", "reaction", "state", "uncertainty"}
        and (
            right.semantic_frame.polarity == "negative"
            or right.semantic_frame.modality in {"feeling", "refusal", "uncertain"}
            or right_codes
            & {
                "operator:constraint",
                "operator:refusal",
                "operator:feeling",
                "semantic_role:burden",
                "semantic_role:protective_or_limiting_refusal",
            }
        )
    )
    continuation_or_refusal = bool(
        "operator:continuation" in left_codes
        or "operator:refusal" in right_codes
    )
    return direction and burden and continuation_or_refusal


def _final_stage1_completed_or_past_owner(
    nucleus: GroundedSemanticNucleus,
    source_text_by_span: Mapping[str, str],
) -> bool:
    if nucleus.kind not in {"event", "action", "change"}:
        return False
    codes = set(nucleus.semantic_frame.attribute_codes)
    if nucleus.semantic_frame.time_scope in {
        "future",
        "present_to_future",
    } or codes & {
        "operator:wish",
        "operator:continuation",
        "operator:uncertainty",
        "operator:refusal",
    }:
        return False
    source_text = " ".join(
        source_text_by_span.get(span_id, "")
        for span_id in nucleus.source_span_ids
    ).strip(" 、,。．.!！?？")
    return bool(
        nucleus.semantic_frame.time_scope in {"past", "past_to_present"}
        or _EXPLICIT_PERFECTIVE_END_RE.search(source_text)
    )


def _final_stage1_action_change_source_fragment_projections(
    projections: Sequence[_TypedNucleusProjection],
) -> tuple[_TypedNucleusProjection, ...]:
    """Bind canonical action/change children to the final source contract.

    The canonical compound projector retains its ``surface_scalar_*``
    contract.  Final Stage-1 has a stricter typed-fragment contract, so
    translate only the performed-action / observed-change pair at this
    final-only boundary.
    """

    rows = tuple(projections)
    if (
        tuple((row.kind, row.predicate_kind) for row in rows)
        != (("action", "action"), ("change", "change"))
        or not all(
            "semantic_dependency:action_before_change"
            in row.attribute_codes
            for row in rows
        )
    ):
        return rows

    if any(
        sum(
            code.startswith("surface_scalar_range:")
            for code in row.attribute_codes
        )
        != 1
        or row.attribute_codes.count(
            f"surface_scalar_range:{row.scalar_start}:{row.scalar_end}"
        )
        != 1
        or sum(
            code.startswith("surface_scalar_source:")
            for code in row.attribute_codes
        )
        != 1
        or row.attribute_codes.count(
            "surface_scalar_source:normalized_raw_text"
        )
        != 1
        or any(
            code.startswith(
                (
                    "source_fragment_scalar_range:",
                    "source_fragment_scalar_source:",
                )
            )
            or code == "semantic_role:generic_relation_fragment"
            for code in row.attribute_codes
        )
        for row in rows
    ):
        raise GroundedObservationPlanError(
            "final_stage1_action_change_source_fragment_invalid"
        )

    return tuple(
        replace(
            row,
            attribute_codes=tuple(
                _dedupe(
                    (
                        *(
                            "source_fragment_scalar_range:"
                            + code.split(":", 1)[1]
                            if code.startswith("surface_scalar_range:")
                            else (
                                "source_fragment_scalar_source:"
                                "normalized_raw_text"
                            )
                            if code
                            == "surface_scalar_source:normalized_raw_text"
                            else code
                            for code in row.attribute_codes
                        ),
                        "semantic_role:generic_relation_fragment",
                        "semantic_role:final_stage1_compound_meaning",
                    )
                )
            ),
        )
        for row in rows
    )
def _final_stage1_typed_nuclei(
    plan: GroundedObservationPlan,
    evidence_spans: Sequence[EvidenceSpan],
) -> tuple[tuple[GroundedSemanticNucleus, ...], tuple[tuple[str, str, str], ...]]:
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in evidence_spans
        if _clean(getattr(span, "span_id", ""))
    }
    result: list[GroundedSemanticNucleus] = []
    compound_dependencies: list[tuple[str, str, str]] = []
    for nucleus in plan.nuclei:
        span = (
            span_index.get(nucleus.source_span_ids[0])
            if len(nucleus.source_span_ids) == 1
            else None
        )
        canonical_projections = (
            _typed_nucleus_projections_for_span(
                span,
                base_frame=nucleus.semantic_frame,
            )
            if span is not None and nucleus.kind != "self_evaluation"
            else ()
        )
        canonical_projections = (
            _final_stage1_action_change_source_fragment_projections(
                canonical_projections
            )
        )
        projections = canonical_projections or (
            _final_stage1_compound_meaning_projections_for_span(
                span,
                base_frame=nucleus.semantic_frame,
            )
            if span is not None and nucleus.kind != "self_evaluation"
            else ()
        )
        if not projections:
            result.append(nucleus)
            continue
        projected_ids: list[str] = []
        for projection in projections:
            projected_id = f"{nucleus.nucleus_id}{projection.nucleus_suffix}"
            projected_ids.append(projected_id)
            result.append(
                replace(
                    nucleus,
                    nucleus_id=projected_id,
                    kind=projection.kind,
                    semantic_frame=replace(
                        nucleus.semantic_frame,
                        predicate_kind=projection.predicate_kind,
                        polarity=projection.polarity,
                        modality=projection.modality,
                        time_scope=projection.time_scope,
                        attribute_codes=projection.attribute_codes,
                    ),
                    grounding_kind=projection.grounding_kind,
                    priority=_priority_for_nucleus(
                        span,
                        nucleus.retention,
                        projection.kind,
                    ),
                    allowed_claim_scope="explicit_current_input",
                )
            )
        if len(projected_ids) == 2:
            relation_kinds = {
                projection.relation_kind
                for projection in projections
                if projection.relation_kind is not None
            }
            if relation_kinds:
                if len(relation_kinds) != 1:
                    raise GroundedObservationPlanError(
                        "typed_projection_relation_binding_invalid"
                    )
                dependency = next(iter(relation_kinds))
            elif (
                projections[0].kind == "action"
                and projections[1].kind == "change"
            ):
                dependency = "action_supports_change"
            elif (
                projections[0].predicate_kind == "residue"
                and projections[1].predicate_kind == "unfinished"
            ):
                dependency = "residue_and_unfinished"
            else:
                raise GroundedObservationPlanError(
                    "typed_projection_relation_binding_invalid"
                )
            if dependency == "preserves_despite":
                wish_index = next(
                    (
                        index
                        for index, projection in enumerate(projections)
                        if projection.kind == "wish"
                    ),
                    None,
                )
                if wish_index is None:
                    raise GroundedObservationPlanError(
                        "typed_projection_relation_binding_invalid"
                    )
                burden_index = 1 - wish_index
                compound_dependencies.append(
                    (
                        dependency,
                        projected_ids[wish_index],
                        projected_ids[burden_index],
                    )
                )
                continue
            compound_dependencies.append(
                (dependency, projected_ids[0], projected_ids[1])
            )
        elif len(projected_ids) == 3:
            projection_codes = tuple(
                set(projection.attribute_codes) for projection in projections
            )
            if (
                projections[0].kind in {"reaction", "state", "constraint"}
                and projections[1].kind == "action"
                and projections[2].kind == "change"
                and "semantic_dependency:action_before_change"
                in projection_codes[1]
                and "semantic_dependency:contrast_before_action_result"
                in projection_codes[0]
                and "semantic_dependency:contrast_before_action_result"
                in projection_codes[2]
            ):
                compound_dependencies.extend(
                    (
                        (
                            "action_supports_change",
                            projected_ids[1],
                            projected_ids[2],
                        ),
                        (
                            "contrast",
                            projected_ids[0],
                            projected_ids[2],
                        ),
                    )
                )
            elif (
                projections[0].kind == "event"
                and projections[1].kind == "wish"
                and projections[2].predicate_kind == "residue"
                and "semantic_dependency:event_before_residue"
                in projection_codes[0]
                and "semantic_dependency:event_before_residue"
                in projection_codes[2]
                and "semantic_dependency:coexisting_wish_residue"
                in projection_codes[1]
                and "semantic_dependency:coexisting_wish_residue"
                in projection_codes[2]
            ):
                compound_dependencies.extend(
                    (
                        (
                            "temporal_before_after",
                            projected_ids[0],
                            projected_ids[2],
                        ),
                        (
                            "coexistence",
                            projected_ids[1],
                            projected_ids[2],
                        ),
                    )
                )
            else:
                raise GroundedObservationPlanError(
                    "typed_projection_relation_binding_invalid"
                )
        elif projected_ids:
            raise GroundedObservationPlanError(
                "typed_projection_cardinality_invalid"
            )
    return tuple(result), tuple(compound_dependencies)


def _final_stage1_typed_relations(
    plan: GroundedObservationPlan,
    nuclei: Sequence[GroundedSemanticNucleus],
    compound_dependencies: Sequence[tuple[str, str, str]],
    evidence_spans: Sequence[EvidenceSpan],
) -> tuple[
    tuple[GroundedSemanticRelation, ...],
    tuple[GroundedSemanticNucleus, ...],
]:
    nucleus_index = {item.nucleus_id: item for item in nuclei}
    source_text_by_span = _final_stage1_source_text_by_span(evidence_spans)
    material_result_by_compound_action_owner = {
        action_id: change_id
        for dependency, action_id, change_id in compound_dependencies
        if dependency == "action_supports_change"
    }
    rows: list[GroundedSemanticRelation] = []

    for relation in plan.relations:
        # An existing outgoing relation from a compound action+change span was
        # originally owned by the unsplit span.  After the typed split, its
        # material result owner is the change child; the action owner remains
        # reserved for the newly projected action_supports_change dependency.
        relation_from_nucleus_id = (
            material_result_by_compound_action_owner.get(
                relation.from_nucleus_id,
                relation.from_nucleus_id,
            )
            if relation.type != "action_supports_change"
            else relation.from_nucleus_id
        )
        left = nucleus_index.get(relation_from_nucleus_id)
        right = nucleus_index.get(relation.to_nucleus_id)
        if left is None or right is None:
            continue
        source_text = _final_stage1_relation_source_text(
            relation,
            source_text_by_span,
        )
        explicit_contrast = bool(
            _CONTRAST_RE.search(source_text)
            or _final_stage1_has_contrast_marker_between(
                left,
                right,
                evidence_spans,
            )
        )
        direction_under_burden = bool(
            explicit_contrast
            and _final_stage1_direction_under_burden(left, right)
        )
        relation_type: RelationKind = relation.type
        if direction_under_burden:
            relation_type = "continuation_or_refusal"
            left = replace(
                left,
                semantic_frame=replace(
                    left.semantic_frame,
                    attribute_codes=tuple(
                        _dedupe(
                            (
                                *left.semantic_frame.attribute_codes,
                                "semantic_role:direction_under_burden_direction",
                            )
                        )
                    ),
                ),
            )
            right = replace(
                right,
                semantic_frame=replace(
                    right.semantic_frame,
                    attribute_codes=tuple(
                        _dedupe(
                            (
                                *right.semantic_frame.attribute_codes,
                                "semantic_role:direction_under_burden_burden",
                            )
                        )
                    ),
                ),
            )
            nucleus_index[left.nucleus_id] = left
            nucleus_index[right.nucleus_id] = right
        elif relation_type == "continuation_or_refusal":
            relation_type = "contrast" if explicit_contrast else "uncertain_connection"

        right_codes = set(right.semantic_frame.attribute_codes)
        completed_or_past_left = _final_stage1_completed_or_past_owner(
            left,
            source_text_by_span,
        )
        if "operator:residue" in right_codes and completed_or_past_left:
            relation_type = "temporal_before_after"
        elif (
            relation_type == "temporal_before_after"
            and not completed_or_past_left
        ):
            relation_type = (
                "contrast" if explicit_contrast else "uncertain_connection"
            )

        rows.append(
            replace(
                relation,
                type=relation_type,
                from_nucleus_id=relation_from_nucleus_id,
                grounding_kind=(
                    "user_stated_relation"
                    if relation_type
                    in {
                        "continuation_or_refusal",
                        "temporal_before_after",
                    }
                    else relation.grounding_kind
                ),
            )
        )

    for dependency, left_id, right_id in compound_dependencies:
        if dependency == "residue_and_unfinished":
            continue
        left = nucleus_index[left_id]
        right = nucleus_index[right_id]
        relation_type: RelationKind = dependency  # type: ignore[assignment]
        if relation_type not in {
            "action_supports_change",
            "coexistence",
            "contrast",
            "preserves_despite",
            "temporal_before_after",
            "wish_and_constraint",
        }:
            raise GroundedObservationPlanError(
                "typed_projection_relation_binding_invalid"
            )
        source_relation_id = {
            "action_supports_change": (
                "typed_projection:perfective_action_before_bounded_change"
            ),
            "temporal_before_after": (
                "typed_projection:explicit_event_before_present_residue"
            ),
        }.get(relation_type, "typed_projection:top_level_connective")
        source_arc_key = {
            "action_supports_change": "compound_span:action_before_change",
            "temporal_before_after": "compound_span:event_before_present_residue",
        }.get(relation_type, "compound_span:top_level_relation")
        rows.append(
            GroundedSemanticRelation(
                relation_id="",
                type=relation_type,
                from_nucleus_id=left_id,
                to_nucleus_id=right_id,
                source_span_ids=left.source_span_ids,
                grounding_kind="user_stated_relation",
                certainty=min(left.certainty, right.certainty),
                retention=_relation_retention(
                    left_id,
                    right_id,
                    nucleus_index,
                    relation_type=relation_type,
                    grounding_kind="user_stated_relation",
                ),
                source_relation_ids=(source_relation_id,),
                source_meaning_arc_keys=(source_arc_key,),
            )
        )

    return (
        tuple(
            replace(row, relation_id=f"relation:r{index}")
            for index, row in enumerate(rows, start=1)
        ),
        tuple(nucleus_index.get(row.nucleus_id, row) for row in nuclei),
    )


def _final_stage1_normalize_relation_authority(
    relations: Sequence[GroundedSemanticRelation],
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[GroundedSemanticRelation, ...]:
    """Keep structural co-presence distinct from source relation evidence.

    The active production plan remains untouched.  At the registered-disabled
    CMEE final seam, a thought/action field boundary cannot authorize a
    semantic edge, even when either field contains its own connective.  The
    relation remains as bounded context with both endpoint/source references;
    required coverage stays on the explicit endpoint nuclei.
    """

    nucleus_index = {row.nucleus_id: row for row in nuclei}
    normalized: list[GroundedSemanticRelation] = []
    for relation in relations:
        left = nucleus_index.get(relation.from_nucleus_id)
        right = nucleus_index.get(relation.to_nucleus_id)
        if left is None or right is None:
            normalized.append(relation)
            continue
        left_fields = frozenset(left.source_fields)
        right_fields = frozenset(right.source_fields)
        cross_field = bool(
            left_fields
            and right_fields
            and left_fields.isdisjoint(right_fields)
        )
        grounding_kind: GroundingKind = (
            "bounded_structural_inference"
            if cross_field
            else relation.grounding_kind
        )
        retention: Retention = (
            "should"
            if grounding_kind == "bounded_structural_inference"
            and relation.retention == "required"
            else relation.retention
        )
        normalized.append(
            replace(
                relation,
                grounding_kind=grounding_kind,
                retention=retention,
            )
        )
    return tuple(normalized)


def _final_stage1_material_quality(
    plan: GroundedObservationPlan,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> Literal[
    "grounded",
    "short_state_sufficient",
    "limited_grounding",
    "labels_only_limited",
    "empty",
    "safety_routed",
]:
    """Promote only final compound meaning out of the short-state shortcut."""

    original = plan.input_profile.material_quality
    if original != "short_state_sufficient":
        return original
    final_compound = any(
        "semantic_role:final_stage1_compound_meaning"
        in nucleus.semantic_frame.attribute_codes
        for nucleus in nuclei
    )
    direction_under_burden = any(
        {
            "semantic_role:direction_under_burden_direction",
            "semantic_role:direction_under_burden_burden",
        }
        & set(nucleus.semantic_frame.attribute_codes)
        for nucleus in nuclei
    )
    return "grounded" if final_compound or direction_under_burden else original


def _final_stage1_unknown_boundaries(
    plan: GroundedObservationPlan,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[GroundedUnknownBoundary, ...]:
    """Keep old limits attached after split and expose explicit unknowns."""

    old_nucleus_index = {row.nucleus_id: row for row in plan.nuclei}
    expanded: list[GroundedUnknownBoundary] = []
    for boundary in plan.unknown_boundaries:
        affected_source_ids = {
            span_id
            for nucleus_id in boundary.affected_nucleus_ids
            for span_id in (
                old_nucleus_index[nucleus_id].source_span_ids
                if nucleus_id in old_nucleus_index
                else ()
            )
        }
        affected_ids = tuple(
            _dedupe(
                (
                    *(
                        nucleus_id
                        for nucleus_id in boundary.affected_nucleus_ids
                        if any(
                            row.nucleus_id == nucleus_id for row in nuclei
                        )
                    ),
                    *(
                        row.nucleus_id
                        for row in nuclei
                        if affected_source_ids & set(row.source_span_ids)
                    ),
                )
            )
        )
        expanded.append(
            replace(boundary, affected_nucleus_ids=affected_ids)
        )

    explicitly_unknown = tuple(
        row
        for row in nuclei
        if row.semantic_frame.modality == "uncertain"
        or {
            "operator:uncertainty",
            "semantic_role:limiting_unknown",
        }
        & set(row.semantic_frame.attribute_codes)
    )
    next_index = len(expanded) + 1
    for nucleus in explicitly_unknown:
        expanded.append(
            GroundedUnknownBoundary(
                unknown_id=f"unknown:u{next_index}",
                dimension="source_explicit_epistemic_limit",
                affected_nucleus_ids=(nucleus.nucleus_id,),
                evidence_span_ids=nucleus.source_span_ids,
                surface_policy="hedge_only",
            )
        )
        next_index += 1
    return tuple(expanded)


def _final_stage1_align_action_status(
    nuclei: Sequence[GroundedSemanticNucleus],
    evidence_spans: Sequence[EvidenceSpan],
) -> tuple[GroundedSemanticNucleus, ...]:
    """Resolve factual tense once, before the final graph/meaning is sealed.

    The public input adapter deliberately has a conservative action default.
    Final Stage 1 may replace that default only when the same source-bounded
    predicate explicitly realizes a factual past or progressive action.  A
    past suffix in a wish, denial, quotation or condition is not such proof.
    """

    spans = {str(span.span_id): span for span in evidence_spans}
    aligned: list[GroundedSemanticNucleus] = []
    for nucleus in nuclei:
        frame = nucleus.semantic_frame
        codes = tuple(frame.attribute_codes)
        if (
            nucleus.kind != "action"
            or len(nucleus.source_span_ids) != 1
            or frame.actor != "current_user"
            or frame.polarity in {"negative", "mixed"}
            or frame.modality in {"wish", "uncertain", "refusal", "possibility"}
            or set(codes) & {
                "operator:negation", "operator:wish", "operator:uncertainty",
                "operator:refusal",
            }
        ):
            aligned.append(nucleus)
            continue
        span = spans.get(nucleus.source_span_ids[0])
        if span is None:
            raise GroundedObservationPlanError("final_action_status_source_missing")
        text = re.sub(r"\s+", " ", str(span.raw_text).replace("\u3000", " ")).strip()
        ranges = tuple(code for code in codes if code.startswith("source_fragment_scalar_range:"))
        sources = tuple(code for code in codes if code.startswith("source_fragment_scalar_source:"))
        markers = codes.count("semantic_role:generic_relation_fragment")
        legacy = any(code.startswith(("surface_scalar_range:", "surface_scalar_source:")) for code in codes)
        if markers or ranges or sources or legacy:
            if (
                markers != 1 or len(ranges) != 1 or legacy
                or sources != ("source_fragment_scalar_source:normalized_raw_text",)
            ):
                raise GroundedObservationPlanError("final_action_status_fragment_invalid")
            try:
                start, end = map(int, ranges[0].split(":")[1:])
            except (ValueError, TypeError):
                raise GroundedObservationPlanError("final_action_status_fragment_invalid") from None
            if not 0 <= start < end <= len(text):
                raise GroundedObservationPlanError("final_action_status_fragment_invalid")
            text = text[start:end]
            if text != text.strip():
                raise GroundedObservationPlanError("final_action_status_fragment_invalid")
        text = text.strip(" \u3000、,。．.!！?？")
        visible = _top_level_text(text)
        # A quoted or attributed predicate cannot establish this owner's
        # factual action.  Field defaults are not evidence about an actor.
        if (
            not text or visible is None or visible != text
            or not _final_stage1_owner_scope_is_current(text, source_field="", strict_actor=True)
            or re.search(r"(?:ない|なかった|ません|ませんでした|ずに|ぬ)$", text)
        ):
            aligned.append(nucleus)
            continue
        finite = _strip_bounded_operator_prefix(visible.strip())
        argument = _ACTION_ARGUMENT_STEM_RE.search(finite)
        if (
            argument is None or argument.start() == 0
            or argument.end() != len(finite)
            or re.search(r"[、,.!?！？\s]|(?:は|が|も)", argument.group("predicate"))
        ):
            aligned.append(nucleus)
            continue
        predicate = argument.group("predicate")
        if re.search(r"(?:たい|たく|ほしい|つもり|予定|かもしれ|らしい|はず|なら|たら|れば|場合|もし|ようと|ように)", predicate):
            aligned.append(nucleus)
            continue
        progressive = re.search(r"(?:て|で)(?:い|お)(?:る|ます|た|ました)$", predicate)
        past = _bounded_structural_action_endpoint(text)
        if not (progressive or past):
            aligned.append(nucleus)
            continue
        time_scope = "past" if past else "continuing"
        aspect = "progressive" if progressive else "perfective"
        attributes = tuple(
            code for code in codes
            if not code.startswith(("time_scope:", "aspect:", "modality:"))
            and code != "operator:performed_action"
        ) + (f"time_scope:{time_scope}", f"aspect:{aspect}", "operator:performed_action")
        aligned.append(replace(nucleus, semantic_frame=replace(
            frame, modality="fact", time_scope=time_scope,
            attribute_codes=tuple(_dedupe(attributes)),
        )))
    return tuple(aligned)


def project_final_stage1_grounded_observation_plan(
    plan: GroundedObservationPlan,
    *,
    evidence_spans: Sequence[EvidenceSpan],
    safety_decision: EmlisSafetyTriageDecision,
    resolver: EvidenceSpanResolver | None = None,
) -> GroundedObservationPlan:
    """Project final Stage-1 typed owners without changing the active plan.

    This is the sole final-language-core upstream seam.  It projects only
    source-bounded predicate owners and relations; it is not a viability mode,
    does not render text, and is never called by the current public reply path.
    """

    projected_nuclei, compound_dependencies = _final_stage1_typed_nuclei(
        plan,
        evidence_spans,
    )
    projected_nuclei = _final_stage1_align_action_status(
        projected_nuclei,
        evidence_spans,
    )
    relations, nuclei = _final_stage1_typed_relations(
        plan,
        projected_nuclei,
        compound_dependencies,
        evidence_spans,
    )
    relations = _final_stage1_normalize_relation_authority(
        relations,
        nuclei,
    )
    complexity = _semantic_complexity(
        nuclei=nuclei,
        relations=relations,
        meaning_artifacts=_MeaningArtifacts(),
    )
    if plan.input_profile.semantic_complexity == "long_arc":
        complexity = "long_arc"
    material_quality = _final_stage1_material_quality(plan, nuclei)
    unknown_boundaries = _final_stage1_unknown_boundaries(plan, nuclei)
    response_plan, coverage, surface_policy, safety_policy = (
        _build_response_and_policies(
            nuclei=nuclei,
            relations=relations,
            safety_decision=safety_decision,
            complexity=complexity,
            material_quality=material_quality,
            include_reception_relation_support=True,
        )
    )
    projected = replace(
        plan,
        input_profile=replace(
            plan.input_profile,
            material_quality=material_quality,
            semantic_complexity=complexity,
            nucleus_count=len(nuclei),
            relation_count=len(relations),
        ),
        nuclei=nuclei,
        relations=relations,
        unknown_boundaries=unknown_boundaries,
        response_plan=response_plan,
        coverage_requirements=coverage,
        surface_policy=surface_policy,
        safety_policy=safety_policy,
        referenced_evidence_span_ids=_all_plan_evidence_ids(
            nuclei,
            relations,
            unknown_boundaries,
        ),
        source_contracts=tuple(
            _dedupe(
                (
                    *plan.source_contracts,
                    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
                )
            )
        ),
    )
    effective_resolver = resolver or build_evidence_span_resolver(
        evidence_spans
    )
    issues = validate_grounded_observation_plan(projected, effective_resolver)
    if issues:
        raise GroundedObservationPlanError(
            "invalid_final_stage1_grounded_projection:" + ",".join(issues)
        )
    return projected


def build_final_stage1_grounded_observation_plan(
    current_input: Mapping[str, Any] | None,
    *,
    evidence_spans: Sequence[EvidenceSpan] | None = None,
    reports: Sequence[PerspectiveReport] | None = None,
    board: PerspectiveBoard | None = None,
    graph: ObservationGraph | None = None,
    meaning_blocks: Sequence[InputMeaningBlock] | None = None,
    coverage_plan: MeaningCoveragePlan | None = None,
    whole_input_meaning_arc: WholeInputMeaningArc | None = None,
    retention_plan: MajorMeaningRetentionPlan | None = None,
    safety_decision: EmlisSafetyTriageDecision | None = None,
) -> GroundedObservationPlan:
    """Build the registered-disabled final Stage-1 typed grounding plan."""

    normalized = normalize_emlis_current_input(current_input or {})
    span_list = tuple(
        evidence_spans
        if evidence_spans is not None
        else build_evidence_ledger(normalized)
    )
    resolver = build_evidence_span_resolver(
        span_list,
        current_input=normalized,
    )
    report_list = tuple(
        reports if reports is not None else run_perspective_observers(span_list)
    )
    perspective_board = board or build_perspective_board(
        evidence_spans=span_list,
        reports=report_list,
    )
    observation_graph = graph or integrate_perspective_board(
        board=perspective_board
    )
    base_triage = safety_decision or build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=observation_graph,
        evidence_spans=span_list,
    )
    triage = _canonicalize_safety_decision(
        base_triage,
        span_list,
        authoritative_self_denial=safety_decision is not None,
    )
    active_plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=span_list,
        reports=report_list,
        board=perspective_board,
        graph=observation_graph,
        meaning_blocks=meaning_blocks,
        coverage_plan=coverage_plan,
        whole_input_meaning_arc=whole_input_meaning_arc,
        retention_plan=retention_plan,
        safety_decision=safety_decision,
    )
    return project_final_stage1_grounded_observation_plan(
        active_plan,
        evidence_spans=span_list,
        safety_decision=triage,
        resolver=resolver,
    )


# Transitional import compatibility for I1-I4 structural tests and internal
# callers.  Both names resolve to the same canonical builder; there is no
# second generation path or shadow implementation after I5.
build_grounded_observation_plan_shadow = build_grounded_observation_plan


__all__ = [
    "GROUND_OBSERVATION_PLAN_SCHEMA_VERSION",
    "GROUND_OBSERVATION_PLAN_ADAPTER_VERSION",
    "GROUND_OBSERVATION_PLAN_GENERATION_PATH",
    "GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION",
    "GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION",
    "FINAL_STAGE1_GROUNDED_PROJECTION_VERSION",
    "GroundedReceptionAct",
    "GroundedFollowElement",
    "GroundedReceptionStance",
    "GroundedSpeakerPresence",
    "GroundedReferenceMode",
    "GroundedReceptionOpportunityFamily",
    "GroundedReceptionDepthLevel",
    "GroundedReceptionSafetyMode",
    "GroundedReceptionMoveRole",
    "GroundedReceptionSurfaceStrategy",
    "GroundedObservationPlanError",
    "GroundedSemanticFrame",
    "GroundedSemanticNucleus",
    "GroundedSemanticRelation",
    "GroundedUnknownBoundary",
    "GroundedInputProfile",
    "GroundedQuestionPolicy",
    "GroundedReceptionQuotePolicy",
    "GroundedReceptionSentencePolicy",
    "GroundedReceptionDistinctnessPolicy",
    "GroundedReceptionOpportunity",
    "GroundedReceptionDepthPolicy",
    "GroundedReceptionMovePlan",
    "GroundedHumanReceptionPlan",
    "GroundedResponsePlan",
    "GroundedCoverageRequirements",
    "GroundedSurfacePolicy",
    "GroundedSafetyPolicy",
    "GroundedObservationPlan",
    "classify_grounded_human_follow_role",
    "map_grounded_human_follow_role_to_reception_act",
    "select_grounded_reception_act",
    "classify_grounded_human_follow_delivery",
    "build_grounded_reception_opportunities",
    "build_grounded_human_reception_plan",
    "build_grounded_observation_plan",
    "build_grounded_observation_plan_shadow",
    "project_final_stage1_grounded_observation_plan",
    "build_final_stage1_grounded_observation_plan",
    "validate_grounded_human_reception_plan",
    "validate_grounded_observation_plan",
]
