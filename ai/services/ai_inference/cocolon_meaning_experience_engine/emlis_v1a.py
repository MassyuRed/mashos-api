# -*- coding: utf-8 -*-
from __future__ import annotations

"""Emlis V1-A text-grounded graph, plan, realization and trace sealer."""

import copy
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re
from typing import Any, Iterable, Sequence

from emlis_ai_conversation_composer_service import compose_emlis_conversation_candidate
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_human_reception import (
    realize_grounded_human_reception,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_plan import (
    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
    build_final_stage1_grounded_observation_plan,
    build_grounded_human_reception_plan,
    build_grounded_observation_plan,
    validate_grounded_human_reception_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    DIRECTIONAL_GROUNDED_RELATION_TYPES,
    build_grounded_sentence_plan,
)
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import (
    AddresseeNotes,
    GraphClaim,
    LimitedObservationScope,
    ObservationGraph,
    RelationEdge,
)
from cocolon_text_generation_core.guards.base import split_sentences
from cocolon_text_generation_core.adapters.emlis_observation_composer import (
    attach_core_evaluation_meta,
    core_rejection_reason,
    evaluate_emlis_observation_candidate,
)

from .contracts import (
    AttachmentAdmission,
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CMEE_STAGE1_EMLIS_OWNER_REF_V1,
    CMEE_STAGE1_EMLIS_OWNER_REF_V2,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V1,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2,
    CMEEStage1ContractError,
    CommonGuardProof,
    CommonGuardResultProof,
    EmlisStage1PositiveTraceExtension,
    EmlisStage1Projection,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    MeaningEdge,
    MeaningNode,
    OwnerClass,
    OwnerDisposition,
    ResolverResolution,
    SourceOwnerDisposition,
    Stage1V2UnitSeal,
    RealizedSentenceUnit,
    VisibleAuthority,
    VisibleUnknownUnit,
    VisibleUnitTrace,
    stage1_projection_artifact_ref,
    validate_stage1_sentence_unit,
    validate_stage1_trace_spine,
    validate_stage1_projection_artifact_ref,
)
from .emlis_stage1_response import (
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE,
    compile_stage1_response,
    stage1_required_projection_nucleus_ids,
)
from .source_kernel import (
    AdmittedTextSource,
    build_source_owner_universe,
    normalize_evidence_literal,
)


OBSERVATION_DUTY_ID = "OBSERVE_SOURCE_EXPLICIT_CURRENT_MEANING"
UNKNOWN_DUTY_ID = "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
RECEPTION_DUTY_ID = "BOUND_HUMAN_RECEPTION_TO_VISIBLE_OBSERVATION"
STRUCTURED_ATTACHMENT_UNKNOWN_TEXT = (
    "書かれた内容と、選択された気持ち・カテゴリのあいだに、"
    "どのような関係があるかまでは、この入力だけでは決められません。"
)
REALIZER_CONTRACT_IDS = (
    "cocolon.cmee.emlis.plan_bound_grounded_surface_adapter.v2",
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
)
_STAGE1_REALIZER_ADAPTER_CONTRACT_ID = REALIZER_CONTRACT_IDS[0]
_STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY = (
    "cocolon.cmee.emlis.typed_derivation_echo_admission.v1"
)


def _stage1_runtime_contract(
    schema_version: str,
) -> tuple[str, str, tuple[str, str]]:
    """Resolve one exact private runtime contract without version fallback."""

    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        return (
            CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V1,
            CMEE_STAGE1_EMLIS_OWNER_REF_V1,
            (
                _STAGE1_REALIZER_ADAPTER_CONTRACT_ID,
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
            ),
        )
    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
        return (
            CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2,
            CMEE_STAGE1_EMLIS_OWNER_REF_V2,
            (
                _STAGE1_REALIZER_ADAPTER_CONTRACT_ID,
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
            ),
        )
    raise CMEEVerticalError("stage1_response_schema_version_invalid")


def _stage1_trust_policy_ids(schema_version: str) -> tuple[str, ...]:
    """Bind the artifact policy registry to the selected trace generation."""

    trace_schema_version, _owner_ref, _realizer_ids = (
        _stage1_runtime_contract(schema_version)
    )
    common_ids = (
        *tuple(sorted(EXPECTED_COMMON_GUARDS)),
        "cocolon.cmee.source_owner.positive_realization_trace.v2",
    )
    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        return (*common_ids, trace_schema_version)
    return (
        *common_ids,
        _STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY,
        trace_schema_version,
    )


def _stage1_schema_from_projection_artifact_ref(value: str) -> str:
    """Read only the exact registered schema suffix from one private ref."""

    if type(value) is not str or value.count("@") != 1:
        raise CMEEVerticalError("stage1_projection_artifact_ref_invalid")
    schema_version = value.rsplit("@", 1)[1]
    _stage1_runtime_contract(schema_version)
    return schema_version


def _build_stage1_grounded_observation_plan_for_schema(
    source: AdmittedTextSource,
    *,
    schema_version: str,
) -> Any:
    """Build the one grounded-plan generation selected by the schema tag."""

    _stage1_runtime_contract(schema_version)
    builder = (
        build_grounded_observation_plan
        if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
        else build_final_stage1_grounded_observation_plan
    )
    grounded_plan = builder(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    contracts = tuple(getattr(grounded_plan, "source_contracts", ()))
    has_final_projection = FINAL_STAGE1_GROUNDED_PROJECTION_VERSION in contracts
    if has_final_projection is not (
        schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    ):
        raise CMEEVerticalError("stage1_grounded_plan_schema_mismatch")
    return grounded_plan
ADMISSIBLE_NUCLEUS_GROUNDING = frozenset({"explicit", "user_stated_relation"})
ADMISSIBLE_RELATION_GROUNDING = frozenset({"user_stated_relation"})
NEGATIVE_RECEPTION_RE = re.compile(r"(?:負荷|苦しさ|つらさ|負担|痛み|しんどさ)")
SOURCE_BURDEN_CUE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|嫌|限界|痛|しんど|迷惑|ダメ|悪化|不便|動けない|できない|何もしたくない)"
)
NONCURRENT_BURDEN_RE = re.compile(
    r"(?:(?:疲れ|不安|限界|痛み|苦しさ|つらさ|しんどさ|"
    r"つらい|苦しい|しんどい|だるい|重い)(?:という)?(?:わけ|の)?"
    r"(?:では?|じゃ)(?:ない|なく|ありません)|"
    r"疲(?:れ)?て(?:(?:い)?な(?:い|く|かった)|(?:い)?ません(?:でした)?)|"
    r"(?:つら|苦し|しんど|だる|重)くな(?:い|く|かった)|"
    r"(?:つら|苦し|しんど|だる|重)く(?:は)?ありません(?:でした)?|"
    r"(?:不安|限界|痛み|苦しさ|つらさ|しんどさ|疲れ)"
    r"(?:(?:は|が)?な(?:い|く|かった)|(?:は|が)?ありません(?:でした)?|"
    r"(?:では?|じゃ)(?:な(?:い|く|かった)|ありません(?:でした)?))|"
    r"(?:疲れ|不安|痛み|苦しさ|つらさ|しんどさ)(?:が|は)?"
    r"(?:取れ|抜け|消え|なくな))"
)
SOURCE_BURDEN_EXTRA_RE = re.compile(r"(?:だる|重い)")
NEGATED_DESIRE_ADVERB_PATTERN = (
    r"(?:全く|まったく|全然|決して|特に|別に|今は|あまり|そこまで|一切)?"
)
NEGATED_DESIRE_SUFFIX_PATTERN = (
    rf"(?:(?:という)?(?:わけ|の)?(?:では?|でも)"
    rf"(?:な(?:い|く|かった)|ありません(?:でした)?|ございません)|"
    rf"じゃ(?:な(?:い|く|かった)|ありません)|"
    rf"気(?:持ち)?(?:は|が){NEGATED_DESIRE_ADVERB_PATTERN}(?:ない|ありません)|"
    rf"気持ち(?:では?|じゃ)(?:な(?:い|く|かった)|ありません)|"
    rf"気分(?:は{NEGATED_DESIRE_ADVERB_PATTERN}(?:ない|ありません)|"
    rf"(?:では?|じゃ)(?:な(?:い|く|かった)|ありません))|"
    rf"(?:と|とは|なんて|などとは?){NEGATED_DESIRE_ADVERB_PATTERN}"
    rf"(?:思わない|思いません|思ってない|思っていない|思っていません|"
    rf"考えない|考えてない|考えていない|考えていません|"
    rf"感じない|感じません)|"
    rf"(?:と)?思っている(?:という)?(?:わけ|の)?(?:では?|でも)"
    rf"(?:な(?:い|く|かった)|ありません))"
)
NEGATED_DESIRE_RE = re.compile(
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい" + NEGATED_DESIRE_SUFFIX_PATTERN
)
NEGATED_DESIRE_SUFFIX_RE = re.compile(NEGATED_DESIRE_SUFFIX_PATTERN)
OTHER_EXPERIENCER_SUBJECT_PATTERN = (
    r"(?:友達|友人|同僚|家族|相手|上司|部下|彼女?|母|父|夫|妻|旦那|"
    r"主人|奥さん|娘|息子|子ども|子供|祖母|祖父|兄|姉|弟|妹|先輩|後輩|"
    r"先生|顧客|お客(?:さん)?|医師|医者|看護師|担当者|パートナー|"
    r"[ぁ-んァ-ン一-龥ー]{1,12}(?:さん|氏|ちゃん|くん))"
)
OTHER_EXPERIENCER_BURDEN_REPORT_RE = re.compile(
    rf"{OTHER_EXPERIENCER_SUBJECT_PATTERN}(?:が|は)"
    r"[^。！？!?]{0,48}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,24}(?:と|って)(?:言|話|述)"
)
OTHER_EXPERIENCER_BURDEN_RE = re.compile(
    rf"{OTHER_EXPERIENCER_SUBJECT_PATTERN}(?:が|は)"
    r"[^。！？!?]{0,48}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
)
OTHER_EXPERIENCER_DESIRE_RE = re.compile(
    rf"{OTHER_EXPERIENCER_SUBJECT_PATTERN}(?:が|は)"
    r"[^。！？!?]{0,56}たい"
)
GENERIC_EXPERIENCER_SUBJECT_PATTERN = (
    r"[^\s、。！？!?「」『』]{1,24}?"
)
GENERIC_EXPERIENCER_PARTICLE_PATTERN = (
    r"(?:が|は|こそ|(?<!で)も)"
)
GENERIC_EXPERIENCER_APPEARANCE_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    rf"{GENERIC_EXPERIENCER_PARTICLE_PATTERN}"
    r"[^。！？!?]{0,48}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,20}(?:そう|よう|らしい)"
)
GENERIC_EXPERIENCER_REPORTED_DESIRE_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    rf"{GENERIC_EXPERIENCER_PARTICLE_PATTERN}"
    r"[^。！？!?]{0,48}たい[^。！？!?]{0,12}"
    r"(?:と|って)(?:言|話|述)"
)
REPORTED_EXTERNAL_APPEARANCE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,24}(?:そうに見える|そうだ|ようだ|らしい)"
    r"[^。！？!?]{0,16}(?:と|って)(?:言われ|見られ|思われ)"
)
GENERIC_OTHER_THEN_FIRST_PERSON_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    rf"{GENERIC_EXPERIENCER_PARTICLE_PATTERN}"
    r"[^。！？!?]{0,64}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,64}。[^。！？!?]{0,20}"
    r"(?:私|わたし|僕|ぼく|俺|おれ|自分)(?:が|は)"
)
GENERIC_EXPERIENCER_STATE_OR_DESIRE_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    rf"{GENERIC_EXPERIENCER_PARTICLE_PATTERN}"
    r"[^。！？!?]{0,56}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
)
GENERIC_EXPERIENCER_ATTRIBUTION_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    r"(?:によると|によれば|によりますと|の話では|の話だと|の話によると|"
    r"の話を(?:聞|聴)くと|曰く|いわく|から(?:聞|聴)いたところ|"
    r"から(?:聞|聴)くと)"
    r"[^。！？!?]{0,64}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
)
GENERIC_OTHER_SOURCE_BEFORE_CUE_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
    r"(?:から|に|について|に関して)"
    r"[^。！？!?]{0,64}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:(?:と|って)?(?:聞|聴|教え|伝え|言われ|話))"
)
GENERIC_POSSESSIVE_EXPERIENCER_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})の"
    r"(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み|しんどさ)"
)
GENERIC_AFFECTED_OBJECT_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})を"
    r"[^。！？!?]{0,32}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,16}(?:に)?(?:させ|した)"
)
GENERIC_AFFECTED_DATIVE_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})に"
    r"[^。！？!?]{0,32}(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み)"
    r"[^。！？!?]{0,16}(?:を)?(?:与え|抱かせ|感じさせ)"
)
GENERIC_BARE_OTHER_EXPERIENCER_RE = re.compile(
    r"(?P<subject>(?:みんな|皆|全員|人々|誰も|彼ら|彼女ら))"
    r"[^。！？!?]{0,12}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
)
ATTRIBUTIVE_OTHER_EXPERIENCER_RE = re.compile(
    r"(?:不安な|疲れた|疲れている|つらい|苦しい|悲しい|怒った|怖い|"
    r"限界の|痛みの|しんどい)"
    rf"(?P<subject>(?:{OTHER_EXPERIENCER_SUBJECT_PATTERN}|人(?:たち)?|人々))"
    r"(?:が|は|を|に|の)"
)
UNBOUND_EPISTEMIC_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:らしい(?:です)?|みたい(?:だ|です)?|"
    r"そう(?:だ|です)?|よう(?:だ|です)?|とのこと|っぽい)"
)
UNBOUND_REPORTED_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:(?:だ|です)?(?:と|って)(?:聞|聴|言っていた|"
    r"言っていました|伝えられ|教えられ)|(?:と)?いう話を(?:聞|聴)|"
    r"との話(?:だ|です))"
)
UNBOUND_REPORT_OR_EPISTEMIC_WINDOW_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,28}(?:耳にし|伝え聞|(?:との)?報告|(?:との)?連絡|"
    r"との話|ということ|だって(?:[。！？!?]|$)|って(?:[。！？!?]|$)|"
    r"との噂|とされている)"
)
DIRECT_UNCERTAIN_STATE_OR_DESIRE_RE = re.compile(
    r"(?:(?:不安|限界|痛み|疲れ|つらい|苦しい|悲しい|怖い|しんどい)"
    r"(?:なの|の)?かもしれない|"
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい(?:の)?かもしれない|"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)(?:っぽ(?:い|かった)|"
    r"げ(?:だ|です)?))"
)
POSTPOSED_EXPERIENCER_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,16}(?:なの|の)(?:は|が)"
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})(?:だ|です)?"
)
QUOTED_OR_MARKED_OTHER_OWNERSHIP_RE = re.compile(
    r"(?:「[^」]{0,24}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^」]{0,24}」|\"[^\"]{0,24}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|"
    r"しんど|たい)[^\"]{0,24}\"|【[^】]{0,24}(?:不安|疲|つら|苦|悲|怒|"
    r"怖|限界|痛|しんど|たい)[^】]{0,24}】|"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい))"
    r"(?:は|が)"
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})の"
    r"(?:言葉|発言|話|気持ち|状態|もの)"
)
QUOTED_OTHER_AUTHOR_RE = re.compile(
    r"(?:「[^」]{0,80}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^」]{0,80}」|\"[^\"]{0,80}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|"
    r"しんど|たい)[^\"]{0,80}\"|【[^】]{0,80}(?:不安|疲|つら|苦|悲|怒|"
    r"怖|限界|痛|しんど|たい)[^】]{0,80}】|"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい))"
    r"(?:は|と)[、,]?"
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})(?:が|は)"
    r"[^。！？!?]{0,24}(?:言|話|述|書|投稿|送)"
)
OTHER_SOURCE_LABEL_PREFIX_RE = re.compile(
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})の"
    r"(?:メモ|記録|投稿|発言|診断|評価)[：:]"
    r"[^。！？!?]{0,16}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
)
PARENTHETICAL_OTHER_SOURCE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,8}[（(]"
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})の"
    r"(?:話|言葉|発言|記録|メモ)[）)]"
)
PARENTHETICAL_SOURCE_LABEL_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,8}[（(](?:出典|引用元|情報源)[：:]"
    rf"(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})[）)]"
)
EXTERNAL_ASCRIPTION_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:決めつけられ|思われ|評価を受け|診断され|"
    r"ラベルを付けられ)"
)
CONDITIONAL_STATE_OR_DESIRE_RE = re.compile(
    r"(?:(?:もし|仮に)[^。！？!?]{0,48}"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)|"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,16}(?:なら|な場合|だとしても|としても|"
    r"になったら|になれば|であれば|(?:ている|の)?とき(?:は|だけ)?))"
)
UNKNOWN_OR_INTERROGATIVE_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:か(?:どうか|否か)?(?:は|自分でも)?分から|"
    r"なのか分から|だろうか|のかな|(?:な)?気(?:が|も|は)する)"
)
FUTURE_OR_POTENTIAL_STATE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,16}(?:になる)?(?:可能性がある|予定(?:だ|です))"
)
RETRACTED_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,28}(?:というより|かと思った(?:が|けど|けれど)"
    r"[^。！？!?]{0,12}(?:違った|勘違い)|だと思っていた(?:が|けど|けれど)"
    r"[^。！？!?]{0,12}(?:違った|勘違い))"
)
SEMANTIC_NEGATION_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,20}(?:とは(?:言えない|限らない|無縁)|"
    r"かと言えば[^。！？!?]{0,8}(?:違う|違います)|どころか|とは反対に)"
)
NOMINALIZED_PAST_STATE_RE = re.compile(
    r"(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み|しんどさ)"
    r"の(?:記憶|思い出|過去|記録|体験)"
)
METALINGUISTIC_STATE_OR_DESIRE_MENTION_RE = re.compile(
    r"(?:(?:不安|疲れ|つらい|苦しい|悲しい|怒り|怖い|限界|痛み|しんどい|"
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい)(?:」|』|\"|】)?(?:という)?"
    r"(?:単語|表現|文|言葉)[^。！？!?]{0,24}(?:書|読|使|調べ|入力)|"
    r"(?:例|例文|サンプル)[：:][^。！？!?]{0,16}"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)|"
    r"(?:テスト|確認|練習)用に[^。！？!?]{0,24}"
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい))"
)
GENERIC_PROPOSITION_RE = re.compile(
    r"(?:(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み|しんどさ)"
    r"(?:は|が)[^。！？!?]{0,24}(?:自然な反応|普通の反応|一般的|誰にでも|"
    r"休息で和らぐ|睡眠で和らぐ|時間で和らぐ|回復する)|"
    r"(?:不安|疲れ)(?:とは|というのは)[^。！？!?]{0,24}(?:反応|状態|感情))"
)
DIRECTIVE_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,28}(?:説明|感じ|書|言|入力|回答|答え|考え|想像)"
    r"(?:して|いて|って|んで|て)?ください"
)
DIRECT_QUESTION_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲れている|つらい|苦しい|悲しい|怖い|しんどい|"
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい)[^。！？!?]{0,6}[？?]"
)
NONFACTIVE_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:なふりを|と嘘を|だと仮定|と仮定|"
    r"という設定)"
)
DEONTIC_STATE_OR_DESIRE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
    r"[^。！？!?]{0,24}(?:べき(?:だ|です)?|になる必要はない|"
    r"である必要はない)"
)
EMPTY_CLASS_DESIRE_RE = re.compile(
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい(?:人|者)(?:は|が)"
    r"(?:いない|いません|存在しない)"
)
LEXICAL_FALSE_CUE_RE = re.compile(r"(?:不安定|不安定性|だいたい)")
NEGATED_DESIDERATIVE_BURDEN_RE = re.compile(
    r"(?:不安|疲れ|つらく|苦しく|悲しく|怖く|しんどく)"
    r"[^。！？!?]{0,8}(?:になり|を感じ)たくない"
)
COMPLETED_FACTUAL_CHANGE_RESULT_RE = re.compile(
    r"^(?:(?:少し|だいぶ|徐々に|少しずつ|前より)?"
    r"(?:落ち着いた|ほっとした|安心した|楽になった|軽くなった|"
    r"和らいだ|回復した|癒えた|元気になった|前向きになった))$"
)
HABITUAL_OR_DISPOSITIONAL_STATE_RE = re.compile(
    r"(?:(?:疲れ|不安|つらく|苦しく|悲しく|怖く|しんどく)"
    r"[^。！？!?]{0,12}(?:やすい|がち(?:だ|です)?)|"
    r"(?:時々|ときどき|いつも|よく|しばしば|普段)"
    r"[^。！？!?]{0,24}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど))"
)
RELATIVE_CLAUSE_OTHER_EXPERIENCER_RE = re.compile(
    r"(?:不安を感じている|疲れている|つらがっている|苦しんでいる|"
    r"悲しんでいる|怖がっている|帰りたいという|"
    r"[ぁ-んァ-ン一-龥ー]{1,24}たいという)"
    rf"(?P<subject>(?:人(?:たち)?|者|{OTHER_EXPERIENCER_SUBJECT_PATTERN}))"
    r"(?:が|は|を|に|の)"
)
NONEXPERIENTIAL_STATE_THEME_RE = re.compile(
    r"(?:(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み|しんどさ)"
    r"(?:を|への|について)[^。！？!?]{0,20}(?:研究|調査|分析|対処法|"
    r"説明|教育)|"
    r"(?:不安|疲れ|つらさ|苦しさ|悲しさ|怒り|怖さ|限界|痛み|しんどさ)"
    r"[^。！？!?]{0,12}を表す(?:演技|表現))"
)
UNRESOLVED_DESIRE_NEGATION_WINDOW_RE = re.compile(
    r"たい(?:とは?|なんて|などとは?|気(?:持ち|分)?(?:は|が|では?)|"
    r"(?:という)?わけ(?:では?|でも))[^。！？!?]{0,20}"
    r"(?:な(?:い|く|かった)|ません(?:でした)?|ございません)"
)
NEGATED_OR_RESOLVED_BURDEN_WINDOW_RE = re.compile(
    r"(?:(?:不安(?:感)?|疲れ|つらさ|苦しさ|しんどさ|悲しさ|怒り|怖さ|"
    r"限界|痛み)(?:なんか|など|は|が)?"
    r"(?:少しも|全く|まったく|全然|一切)?"
    r"(?:ない|なく|なかった|ありません(?:でした)?|解消(?:した|しました)|"
    r"なくな(?:った|りました)|消え(?:た|ました)|取れ(?:た|ました)|"
    r"抜け(?:た|ました)|収ま(?:った|りました)|和らいだ|癒えた|"
    r"から回復(?:した|しました)|とは無縁(?:だ|です)|"
    r"を感じずに済んだ|治った|おさまった|感じていない)|"
    r"疲れて(?:(?:い)?ない|いません))"
)
EXPLICIT_WHOLE_STATE_NEGATION_RE = re.compile(
    r"(?:(?:不安|心配|疲れ|つらさ|苦しさ|しんどさ|悲しさ|怒り|怖さ|"
    r"限界|痛み)[^。！？!?]{0,20}"
    r"(?:ではな(?:い|かった)|じゃな(?:い|かった)|"
    r"(?:は|が|も)な(?:い|かった)|"
    r"してい(?:ない|なかった|ません(?:でした)?)|"
    r"感じてい(?:ない|なかった|ません(?:でした)?)|"
    r"てい(?:ない|なかった|ません(?:でした)?)|"
    r"ではありません(?:でした)?|ありません(?:でした)?)|"
    r"(?:つら|苦し|しんど|悲し|怖|痛)く(?:は|も)?"
    r"(?:ない|なかった|ありません(?:でした)?)|"
    r"(?:疲れ|怒っ|心配し)て(?:い(?:ない|なかった|ません(?:でした)?)|"
    r"ない|なかった|ません(?:でした)?))$"
)
RESOLVED_DESIRE_RE = re.compile(
    r"[ぁ-んァ-ン一-龥ー]{1,24}たい(?:気持ち|願い)"
    r"(?:は|が)?(?:消えた|なくなった|薄れた|解消した|皆無(?:だ|です)|"
    r"ゼロ(?:だ|です)|消滅した)"
)
FIRST_PERSON_SUBJECTS = frozenset(
    {"私", "わたし", "僕", "ぼく", "俺", "おれ", "自分"}
)
SAFE_NONPERSON_TOPIC_EXACT = frozenset(
    {
        "今",
        "今日",
        "今回",
        "昨日",
        "一昨日",
        "昨夜",
        "昨晩",
        "今朝",
        "さっき",
        "先ほど",
        "先程",
        "先日",
        "この前",
        "先週",
        "先月",
        "去年",
        "以前",
        "昔",
        "かつて",
        "過去",
        "当時",
        "前",
        "このまま",
        "このままなの",
        "体",
        "身体",
        "こと",
        "状態",
        "状況",
        "仕事",
        "環境",
        "職場",
        "生活",
        "気持ち",
        "形",
    }
)
SAFE_NONPERSON_TOPIC_PATTERNS = (
    re.compile(r"^(?:ずっと)?このままなの?$"),
    re.compile(
        r"^(?:この|その|あの)?(?:仕事|環境|職場|生活|状態|状況|気持ち|体|身体)$"
    ),
    re.compile(r"^[^\s、。！？!?「」『』]{1,20}たい気持ち$"),
    re.compile(r"^[^\s、。！？!?「」『』]{1,20}(?:られる|れる|できる)形$"),
)
QUOTED_OTHER_REPORT_RE = re.compile(
    r"(?:「[^」]{1,80}」|『[^』]{1,80}』)(?:と|って)"
    r"[^。！？!?]{0,32}(?:が|は)?[^。！？!?]{0,16}(?:言|話|述|聞|聴|伝|教)"
)
FUTURE_HYPOTHETICAL_BURDEN_RE = re.compile(
    r"(?:今夜|今晩|明日|明後日|週末|来週|来月|来年|今後|将来|これから)"
    r"[^。！？!?]{0,64}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど)"
    r"[^。！？!?]{0,40}(?:かもしれない|だろう|でしょう|はず|予定|そう|よう|らしい)"
)
FUTURE_HYPOTHETICAL_DESIRE_RE = re.compile(
    r"(?:今夜|今晩|明日|明後日|週末|来週|来月|来年|今後|将来|これから)"
    r"[^。！？!?]{0,72}たい[^。！？!?]{0,24}"
    r"(?:と思う|と考える|つもり|予定|かもしれない|だろう)"
)
PAST_SCOPE_MARKER_PATTERN = (
    r"(?:昨日|一昨日|昨夜|昨晩|今朝|さっき|先ほど|先程|先日|この前|"
    r"先週|先々週|先月|先々月|去年|昨年|一昨年|おととい|数日前|"
    r"[一二三四五六七八九十0-9]+日前|その頃|以前|昔|かつて|過去|当時|前は)"
)
PAST_TO_CURRENT_SCOPE_RE = re.compile(
    rf"{PAST_SCOPE_MARKER_PATTERN}(?:は|に)?"
    r"[^！？!?]{1,80}(?:。(?:でも)?|が|けれども?|けど|でも|一方で)"
    r"[^。！？!?]{0,24}(?:今日|今)(?:は|も|の)"
)
PAST_DESIRE_WITH_CURRENT_SCOPE_RE = re.compile(
    rf"{PAST_SCOPE_MARKER_PATTERN}(?:は|に)?"
    r"[^！？!?]{0,80}たい[^！？!?]{0,48}"
    r"(?:。|が|けれども?|けど|でも|一方で)"
    r"[^。！？!?]{0,24}(?:今日|今)(?:は|も|の)"
)
PAST_BURDEN_OR_DESIRE_RE = re.compile(
    rf"{PAST_SCOPE_MARKER_PATTERN}(?:は|に)?"
    r"[^。！？!?]{0,80}(?:不安|疲|つら|苦|悲|怒|怖|限界|痛|しんど|たい)"
)
PAST_STATE_OR_DESIRE_MORPHOLOGY_RE = re.compile(
    r"(?:(?:不安(?:感)?|限界|痛み|疲れ|つらさ|苦しさ|しんどさ|悲しさ|怖さ)"
    r"(?:だった|でした|であった|でありました|でございました|"
    r"になった|になりました|"
    r"があった|がありました|を感じて(?:いた|いました)|"
    r"を感じた|を抱えて(?:いた|いました)|を抱いて(?:いた|いました)|"
    r"を抱えた|を覚えた|が残って(?:いた|いました))|"
    r"疲れ(?:切って(?:いた|いました)|て(?:いた|いました|た|おりました)|ました)|"
    r"(?:怒って|悲しんで)(?:いた|いました)|"
    r"(?:つら|苦し|しんど|だる|重|悲し|怖)かった|しんどく感じた|"
    r"[^。！？!?]{1,32}たかった|"
    r"[^。！？!?]{1,32}たい[^。！？!?]{0,16}"
    r"(?:と思った|と思いました|と考えた|と考えました|"
    r"と思って(?:いた|いました|た|おりました)|"
    r"と考えて(?:いた|いました|た|おりました))|"
    r"[^。！？!?]{1,32}たい(?:気持ち|願い)(?:だった|でした|があった|がありました))"
)
CMEE_SOURCE_ANCHOR_LIMIT = 10
CMEE_FROZEN_ROLE_MAX = int(
    dict(dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)["role_anchor_policy"])[
        "max_graphemes"
    ]
)
_CMEE_FINITE_NEGATIVE_CARRIER_RE = re.compile(
    r"(?:ではありませんでした|じゃありませんでした|ありませんでした|"
    r"ございませんでした|ませんでした|ではありません|じゃありません|"
    r"ありません|ございません|ません|ではなかった|じゃなかった|"
    r"なかった|ではない|じゃない|ない)"
)
_CMEE_EXCLUSIVE_FOCUS_GROUP_RE = re.compile(
    r"[「」『』\"“”【】〔〕［］\[\]（）()]"
)
_CMEE_EXCLUSIVE_FOCUS_METALINGUISTIC_RE = re.compile(
    r"(?:単語|表現|文|言葉|例文?|サンプル|テスト|練習|引用|出典)"
    r"[^。！？!?]{0,24}しか|"
    r"しか[^。！？!?]{0,24}(?:単語|表現|文|言葉|例文?|引用)"
)
_CMEE_EXCLUSIVE_FOCUS_SCOPE_NEGATION_RE = re.compile(
    r"しか[^。！？!?]{0,24}(?:わけ|ということ|のでは|とは)"
    r"[^。！？!?]{0,12}(?:ない|なかった|ありません|"
    r"限らない|言えない)"
)
_CMEE_EXCLUSIVE_FOCUS_OTHER_EXPERIENCER_RE = re.compile(
    rf"^(?:{OTHER_EXPERIENCER_SUBJECT_PATTERN}|"
    r"みんな|皆|全員|人々|誰か|誰も|彼ら|彼女ら|"
    r"[^、。！？!?「」『』]{1,12}(?:さん|氏|ちゃん|くん))"
    r"(?:が|は|には|にしか)"
)
_CMEE_EXCLUSIVE_FOCUS_OTHER_CONTEXT_RE = re.compile(
    rf"(?:{OTHER_EXPERIENCER_SUBJECT_PATTERN}|みんな|皆|全員|"
    r"人々|彼ら|彼女ら)"
    r"(?:によると|によれば|の話では|の話だと|"
    r"が言うには|から聞くと)"
    r"[^。！？!?]{0,32}しか"
)
_CMEE_SOURCE_SHAPE_RECOGNIZERS = dict(
    dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)["source_shape_recognizers"]
)
_CMEE_SOURCE_SHAPE_INFLECTIONS = dict(
    dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)["source_shape_inflections"]
)
_CMEE_SOURCE_FRAGMENT_MAX = int(
    dict(dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)["quote_policy"])[
        "l1_max_graphemes"
    ]
)
_CMEE_DIRECT_CONTRAST_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["direct_contrast"]
)
_CMEE_CONTEXT_DIRECTION_RESIDUE_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["context_direction_residue"]
)
_CMEE_OPEN_QUESTION_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["open_question"]
)
_CMEE_COMPOUND_BURDEN_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["compound_burden"]
)
_CMEE_ACTION_CHANGE_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["action_change"]
)
_CMEE_SIMPLE_CHANGE_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["simple_positive_change"]
)
_CMEE_POSITIVE_DESIRE_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["positive_desire"]
)
_CMEE_HESITATION_SHAPE_RE = re.compile(
    _CMEE_SOURCE_SHAPE_RECOGNIZERS["hesitation"]
)
CMEE_RECEPTION_MATERIAL_MODE = "limited_grounding"
CMEE_POSITIVE_RECEPTION_ACTS = frozenset(
    {
        "honor_concrete_effort",
        "protect_retained_intention",
        "recognize_lived_change",
        "hold_help_seeking",
    }
)
CMEE_BURDEN_RECEPTION_ACTS = frozenset(
    {"stay_with_current_burden", "bounded_counter_self_denial"}
)
CMEE_RELATION_SURFACE_LABELS = {
    "temporal_before_after": "時間の順序",
    "shift_from_to": "変化の方向",
    "contrast": "異なる向きの対比",
    "coexistence": "並存する関係",
    "user_stated_cause": "入力内で明示された理由の関係",
    "user_stated_result": "入力内で明示された結果の関係",
    "attempt_and_block": "試みと制約の関係",
    "wish_and_constraint": "願いと制約の関係",
    "action_supports_change": "行動と変化の関係",
    "evaluation_about_event": "出来事と評価の関係",
    "self_evaluation_about_state": "状態と自己評価の関係",
    "preserves_despite": "負荷の中に残る方向",
    "uncertain_connection": "入力内の順序上の関係",
    "continuation_or_refusal": "継続と拒否の関係",
}
EXPECTED_COMMON_GUARD_IDS = (
    "cocolon_text_generation_core.guards.japanese_coherence.v1",
    "cocolon_text_generation_core.guards.template_echo.v1",
    "cocolon_text_generation_core.guards.overclaim_diagnosis.v1",
    "cocolon_text_generation_core.guards.grounding.v1",
    "cocolon_text_generation_core.guards.must_keep_coverage.v1",
)
EXPECTED_COMMON_GUARDS = frozenset(EXPECTED_COMMON_GUARD_IDS)
EXPECTED_COMMON_SHAPE_PART_IDS = (
    "SourceAnchor",
    "EvidenceSpanLike",
    "PhraseUnit",
    "SentencePlan",
    "TextGenerationResult",
    "GuardResult",
    "used_evidence_span_ids",
    "quality_flags",
)
COMMON_GUARD_STABILIZATION_REPORT_NAME = (
    "cocolon_text_generation_core.step15_stabilization.v1"
)
COMMON_GUARD_STABILIZATION_PHASE = "step15_common_core_stabilization"
COMMON_GUARD_STABILIZATION_CORE_ID = "emlis"
TRUST_POLICY_IDS = _stage1_trust_policy_ids(
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
)
SOURCE_OWNER_REASON_CODES = frozenset(
    {
        "RESOLVER_IDENTITY_MISMATCH",
        "RESOURCE_LOCK_MISMATCH",
        "RESOLVER_OUTPUT_INVALID",
        "REQUIRED_OWNER_MISSING",
        "ATTACHMENT_AMBIGUOUS",
        "ATTACHMENT_UNRESOLVED",
        "OOV_UNRESOLVED",
        "NO_MEANINGFUL_GROUNDED_CLAIM",
        "CLARIFICATION_BUDGET_CONSUMED",
        "SUPPLEMENTAL_LINEAGE_MISMATCH",
        "PRIVATE_BOUNDARY_VIOLATION",
    }
)


class CMEEVerticalError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = str(reason_code or "cmee_vertical_failed")
        super().__init__(self.reason_code)


@dataclass(frozen=True, slots=True)
class _CMEEVisibleBinding:
    line_role: str
    nucleus_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    constrained_owner_ids: tuple[str, ...] = ()
    claim_scope: str = "cmee_source_explicit_plan"
    contains_question: bool = False
    required: bool = True


@dataclass(frozen=True, slots=True)
class _CMEEVisibleLine:
    sentence_id: str
    text: str
    binding: _CMEEVisibleBinding


@dataclass(frozen=True, slots=True)
class _CMEECorePhraseUnit:
    phrase_unit_id: str
    evidence_span_id: str
    raw_text: str
    compressed_text: str
    role: str = "source_grounded_observation"
    polarity: str = "neutral"
    must_keep: bool = False
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _CMEECoreSentencePlan:
    sentence_plan_id: str
    line_role: str
    phrase_unit_ids: tuple[str, ...]
    relation_type: str
    max_chars: int = 240
    must_include: bool = True


@dataclass(frozen=True, slots=True)
class _CommonGuardSealMaterial:
    guard_results: tuple[CommonGuardResultProof, ...]
    stabilization_report_name: str
    stabilization_phase: str
    stabilization_core_id: str
    stabilization_passed: bool
    common_shapes_ready: bool
    stabilization_guard_names: tuple[str, ...]
    issue_codes: tuple[str, ...]
    typed_admission_refs: tuple[str, ...] = ()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}-{_sha256_text('|'.join(values))[:24]}"


def _stage1_v2_typed_admission_ref_from_core_meta(
    core_meta: Mapping[str, Any],
) -> str | None:
    """Validate the body-free admission digest retained in private core meta."""

    key = "stage1_v2_typed_derivation_admission"
    detail = core_meta.get(key)
    if detail is None:
        return None
    preimage = detail.get("digest_preimage") if type(detail) is dict else None
    typed_admission_ref = (
        detail.get("typed_admission_ref") if type(detail) is dict else None
    )
    expected_preimage_keys = {
        "policy_id",
        "typed_derivation_ref",
        "original_rejection_reasons",
        "original_quality_flags",
        "raw_echo_ratio",
        "raw_quote_ratio",
        "raw_quote_hit_digests",
        "evidence_digest",
        "surface_digest",
    }
    if (
        type(detail) is not dict
        or set(detail) != {"typed_admission_ref", "digest_preimage"}
        or type(preimage) is not dict
        or set(preimage) != expected_preimage_keys
        or preimage.get("policy_id")
        != _STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY
        or re.fullmatch(
            r"stage1-v2-typed-derivation-[0-9a-f]{64}",
            str(preimage.get("typed_derivation_ref") or ""),
        )
        is None
        or type(preimage.get("original_rejection_reasons")) is not list
        or not preimage.get("original_rejection_reasons")
        or len(preimage.get("original_rejection_reasons"))
        != len(set(preimage.get("original_rejection_reasons")))
        or not set(preimage.get("original_rejection_reasons")).issubset(
            {"raw_input_echo", "excessive_raw_quote"}
        )
        or tuple(preimage.get("original_quality_flags") or ())
        != (
            "template_echo_failed",
            "core_text_composer_rejected",
            "guard_rejected",
        )
        or type(preimage.get("raw_echo_ratio")) not in {int, float}
        or type(preimage.get("raw_quote_ratio")) not in {int, float}
        or type(preimage.get("raw_quote_hit_digests")) is not list
        or any(
            re.fullmatch(r"[0-9a-f]{64}", str(value or "")) is None
            for value in preimage.get("raw_quote_hit_digests")
        )
        or re.fullmatch(
            r"[0-9a-f]{64}", str(preimage.get("evidence_digest") or "")
        )
        is None
        or re.fullmatch(
            r"[0-9a-f]{64}", str(preimage.get("surface_digest") or "")
        )
        is None
    ):
        raise CMEEVerticalError("stage1_v2_typed_admission_invalid")
    digest = _sha256_text(
        json.dumps(
            preimage,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    expected_ref = (
        f"typed-source-quotation:{digest}"
        f"@{_STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY}"
    )
    if typed_admission_ref != expected_ref:
        raise CMEEVerticalError("stage1_v2_typed_admission_invalid")
    return expected_ref


def _extract_common_guard_seal(
    core_meta: dict[str, Any],
) -> _CommonGuardSealMaterial:
    """Validate and project the actual one-shot common-core guard result."""

    result = core_meta.get("result")
    result_meta = result.get("meta") if type(result) is dict else None
    raw_rows = result_meta.get("guard_results") if type(result_meta) is dict else None
    if type(raw_rows) is not list or len(raw_rows) != len(EXPECTED_COMMON_GUARD_IDS):
        raise CMEEVerticalError("plan_bound_observation_guard_result_shape_mismatch")
    typed_admission_ref = _stage1_v2_typed_admission_ref_from_core_meta(
        core_meta
    )

    guard_results: list[CommonGuardResultProof] = []
    for expected_guard_id, raw_row in zip(
        EXPECTED_COMMON_GUARD_IDS,
        raw_rows,
        strict=True,
    ):
        if type(raw_row) is not dict:
            raise CMEEVerticalError("plan_bound_observation_guard_result_shape_mismatch")
        guard_id = raw_row.get("guard_name")
        passed = raw_row.get("passed")
        if type(guard_id) is not str or guard_id != expected_guard_id:
            raise CMEEVerticalError("plan_bound_observation_guard_set_mismatch")
        if type(passed) is not bool or passed is not True:
            raise CMEEVerticalError("plan_bound_observation_guard_failed")
        if (
            type(raw_row.get("rejection_reasons")) is not list
            or raw_row.get("rejection_reasons") != []
        ):
            raise CMEEVerticalError("plan_bound_observation_guard_result_mismatch")
        guard_results.append(
            CommonGuardResultProof(
                guard_id=guard_id,
                passed=passed,
                raw_passed=(
                    False
                    if typed_admission_ref is not None
                    and expected_guard_id == EXPECTED_COMMON_GUARD_IDS[1]
                    else None
                ),
                disposition=(
                    "TYPED_SOURCE_QUOTATION_ADMITTED"
                    if typed_admission_ref is not None
                    and expected_guard_id == EXPECTED_COMMON_GUARD_IDS[1]
                    else "DIRECT"
                ),
            )
        )

    combined = result_meta.get("combined_guard_result")
    combined_meta = combined.get("meta") if type(combined) is dict else None
    combined_guard_rows = (
        combined_meta.get("guard_results") if type(combined_meta) is dict else None
    )
    if (
        type(combined) is not dict
        or combined.get("guard_name") != "combined_text_generation_guards"
        or type(combined.get("passed")) is not bool
        or combined.get("passed") is not True
        or type(combined.get("rejection_reasons")) is not list
        or combined.get("rejection_reasons") != []
        or type(combined_guard_rows) is not list
        or len(combined_guard_rows) != len(EXPECTED_COMMON_GUARD_IDS)
        or any(type(row) is not dict for row in combined_guard_rows)
        or combined_guard_rows != raw_rows
        or (
            typed_admission_ref is not None
            and (
                result_meta.get(
                    "stage1_v2_typed_derivation_admission"
                )
                != core_meta.get(
                    "stage1_v2_typed_derivation_admission"
                )
                or combined_meta.get(
                    "stage1_v2_typed_derivation_admission"
                )
                != core_meta.get(
                    "stage1_v2_typed_derivation_admission"
                )
                or raw_rows[1].get("meta", {}).get(
                    "stage1_v2_typed_derivation_admission"
                )
                != core_meta.get(
                    "stage1_v2_typed_derivation_admission"
                )
            )
        )
    ):
        raise CMEEVerticalError("plan_bound_observation_combined_guard_mismatch")

    stabilization = core_meta.get("step15_common_core_stabilization")
    if type(stabilization) is not dict:
        raise CMEEVerticalError("plan_bound_observation_stabilization_missing")
    if (
        stabilization.get("report_name") != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or stabilization.get("phase") != COMMON_GUARD_STABILIZATION_PHASE
        or stabilization.get("core_id") != COMMON_GUARD_STABILIZATION_CORE_ID
    ):
        raise CMEEVerticalError("plan_bound_observation_stabilization_identity_mismatch")
    if (
        type(stabilization.get("passed")) is not bool
        or stabilization.get("passed") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_stabilization_failed")
    if (
        type(stabilization.get("common_shapes_ready")) is not bool
        or stabilization.get("common_shapes_ready") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_shapes_not_ready")

    raw_guard_names = stabilization.get("guard_names")
    if type(raw_guard_names) is not list or tuple(raw_guard_names) != EXPECTED_COMMON_GUARD_IDS:
        raise CMEEVerticalError("plan_bound_observation_stabilization_guard_set_mismatch")
    raw_issue_codes = stabilization.get("issue_codes")
    if type(raw_issue_codes) is not list or raw_issue_codes:
        raise CMEEVerticalError("plan_bound_observation_stabilization_issues")
    shared_parts = stabilization.get("shared_quality_parts")
    if (
        type(shared_parts) is not dict
        or tuple(shared_parts) != EXPECTED_COMMON_SHAPE_PART_IDS
        or any(type(shared_parts.get(key)) is not bool or shared_parts.get(key) is not True for key in EXPECTED_COMMON_SHAPE_PART_IDS)
    ):
        raise CMEEVerticalError("plan_bound_observation_common_shape_parts_mismatch")

    return _CommonGuardSealMaterial(
        guard_results=tuple(guard_results),
        stabilization_report_name=COMMON_GUARD_STABILIZATION_REPORT_NAME,
        stabilization_phase=COMMON_GUARD_STABILIZATION_PHASE,
        stabilization_core_id=COMMON_GUARD_STABILIZATION_CORE_ID,
        stabilization_passed=True,
        common_shapes_ready=True,
        stabilization_guard_names=EXPECTED_COMMON_GUARD_IDS,
        issue_codes=(),
        typed_admission_refs=(
            (typed_admission_ref,)
            if typed_admission_ref is not None
            else ()
        ),
    )


def _common_guard_proof_id(
    *,
    source_envelope_id: str,
    graph_id: str,
    plan_id: str,
    guarded_observation_units: Sequence[tuple[str, str]],
    guard_results: Sequence[CommonGuardResultProof],
    stabilization_report_name: str,
    stabilization_phase: str,
    stabilization_core_id: str,
    stabilization_passed: bool,
    common_shapes_ready: bool,
    stabilization_guard_names: Sequence[str],
    issue_codes: Sequence[str],
    typed_admission_refs: Sequence[str] = (),
) -> str:
    guard_result_material = [
        {"guard_id": row.guard_id, "passed": row.passed}
        for row in guard_results
    ]
    material = {
        "schema_version": CMEE_COMMON_GUARD_PROOF_VERSION,
        "source_envelope_id": source_envelope_id,
        "graph_id": graph_id,
        "plan_id": plan_id,
        "guarded_observation_units": [list(row) for row in guarded_observation_units],
        "guard_results": guard_result_material,
        "stabilization": {
            "report_name": stabilization_report_name,
            "phase": stabilization_phase,
            "core_id": stabilization_core_id,
            "passed": stabilization_passed,
            "common_shapes_ready": common_shapes_ready,
            "guard_names": list(stabilization_guard_names),
            "issue_codes": list(issue_codes),
        },
    }
    if typed_admission_refs:
        material["guard_results"] = [
            {
                "guard_id": row.guard_id,
                "passed": row.passed,
                "raw_passed": row.raw_passed,
                "disposition": row.disposition,
            }
            for row in guard_results
        ]
        material["typed_admission_refs"] = list(typed_admission_refs)
    canonical = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"common-guard-proof-{hashlib.sha256(canonical).hexdigest()}"


def _graph_id(
    source_envelope_id: str,
    owner_universe_digest: str,
    nodes: Sequence[MeaningNode],
    edges: Sequence[MeaningEdge],
    dispositions: Sequence[OwnerDisposition],
) -> str:
    node_parts = tuple(
        "\x1f".join(
            (
                row.node_id,
                row.owner_id,
                row.node_kind,
                row.grounding_kind,
                _sha256_text(row.value),
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in nodes
    )
    edge_parts = tuple(
        "\x1f".join(
            (
                row.edge_id,
                row.owner_id,
                row.relation,
                row.source_node_id,
                row.target_node_id,
                row.grounding_kind,
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in edges
    )
    disposition_parts = tuple(
        "\x1f".join(
            (
                row.meaning_owner_id,
                row.owner_class.value,
                row.resolver_resolution.value,
                row.attachment_admission.value,
                row.visible_authority.value,
                row.source_owner_disposition.value,
                "visible_claim_refs",
                *row.visible_claim_refs,
                "evidence_refs",
                *row.evidence_refs,
                "target_unknown_ref",
                row.target_unknown_ref or "",
                "reason_codes",
                *row.reason_codes,
            )
        )
        for row in dispositions
    )
    return _stable_id(
        "graph",
        source_envelope_id,
        owner_universe_digest,
        *node_parts,
        *edge_parts,
        *disposition_parts,
    )


def _plan_id(
    source_envelope_id: str,
    graph_id: str,
    plan: ExperiencePlan,
    visible_line_ids: Sequence[str],
) -> str:
    return _stable_id(
        "plan",
        source_envelope_id,
        graph_id,
        plan.source_envelope_id,
        plan.source_version,
        plan.obligation_version,
        plan.owner_universe_digest,
        plan.source_plan_version,
        plan.observation_duty_id,
        plan.unknown_duty_id,
        plan.reception_duty_id,
        plan.reception_plan_digest,
        *plan.allowed_reception_act_ids,
        *plan.required_observation_owner_ids,
        *plan.reception_target_owner_ids,
        *plan.visible_owner_ids,
        *plan.unresolved_owner_ids,
        *plan.visible_unknown_owner_ids,
        *plan.required_unknown_owner_ids,
        *visible_line_ids,
    )


def _reception_plan_contract(
    grounded_plan: Any,
    resolver: Any,
) -> tuple[str, tuple[str, ...]]:
    reception_plan = _cmee_semantic_reception_plan(grounded_plan, resolver)
    return _reception_plan_digest(reception_plan), _ordered(
        move.reception_act for move in reception_plan.moves
    )


def _reception_plan_digest(reception_plan: Any) -> str:
    """Seal the complete body-free nested plan with named JSON boundaries."""

    return _sha256_text(
        json.dumps(
            asdict(reception_plan),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _artifact_id(
    source_envelope_id: str,
    graph_id: str,
    plan_id: str,
    common_guard_proof_id: str,
    observation: str,
    visible_unknowns: Sequence[str],
    reception: str,
    *,
    emlis_stage1_projection_ref: str | None = None,
) -> str:
    stage1_identity_parts: tuple[str, ...] = ()
    stage1_schema_version = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
    if emlis_stage1_projection_ref is not None:
        try:
            stage1_schema_version = _stage1_schema_from_projection_artifact_ref(
                emlis_stage1_projection_ref
            )
            validate_stage1_projection_artifact_ref(
                emlis_stage1_projection_ref,
                expected_schema_version=stage1_schema_version,
            )
        except Exception:
            raise CMEEVerticalError(
                "stage1_projection_artifact_ref_invalid"
            ) from None
        stage1_identity_parts = (emlis_stage1_projection_ref,)
    _trace_schema_version, _owner_ref, realizer_contract_ids = (
        _stage1_runtime_contract(stage1_schema_version)
    )
    return _stable_id(
        "artifact",
        source_envelope_id,
        graph_id,
        plan_id,
        common_guard_proof_id,
        *realizer_contract_ids,
        *_stage1_trust_policy_ids(stage1_schema_version),
        _sha256_text(observation),
        *(_sha256_text(row) for row in visible_unknowns),
        _sha256_text(reception),
        *stage1_identity_parts,
    )


def _build_common_guard_proof(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    safe_lines: Sequence[Any],
    material: _CommonGuardSealMaterial,
) -> CommonGuardProof:
    guarded_observation_units = tuple(
        (line.sentence_id, _sha256_text(line.text))
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    if not guarded_observation_units:
        raise CMEEVerticalError("common_guard_proof_observation_missing")
    proof_id = _common_guard_proof_id(
        source_envelope_id=source.envelope.envelope_id,
        graph_id=graph.graph_id,
        plan_id=plan.plan_id,
        guarded_observation_units=guarded_observation_units,
        guard_results=material.guard_results,
        stabilization_report_name=material.stabilization_report_name,
        stabilization_phase=material.stabilization_phase,
        stabilization_core_id=material.stabilization_core_id,
        stabilization_passed=material.stabilization_passed,
        common_shapes_ready=material.common_shapes_ready,
        stabilization_guard_names=material.stabilization_guard_names,
        issue_codes=material.issue_codes,
        typed_admission_refs=material.typed_admission_refs,
    )
    return CommonGuardProof(
        schema_version=CMEE_COMMON_GUARD_PROOF_VERSION,
        proof_id=proof_id,
        source_envelope_id=source.envelope.envelope_id,
        graph_id=graph.graph_id,
        plan_id=plan.plan_id,
        guarded_observation_units=guarded_observation_units,
        guard_results=material.guard_results,
        stabilization_report_name=material.stabilization_report_name,
        stabilization_phase=material.stabilization_phase,
        stabilization_core_id=material.stabilization_core_id,
        stabilization_passed=material.stabilization_passed,
        common_shapes_ready=material.common_shapes_ready,
        stabilization_guard_names=material.stabilization_guard_names,
        issue_codes=material.issue_codes,
        typed_admission_refs=material.typed_admission_refs,
    )


def _ordered(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _cmee_valid_source_fragment_rows(
    anchor: str,
    rows: Sequence[tuple[str, int, int]],
) -> tuple[str, ...] | None:
    """Prove finite source fragments by their exact, ordered source offsets."""

    if not rows:
        return None
    previous_end = 0
    values: list[str] = []
    for value, start, end in rows:
        if (
            not value
            or start < previous_end
            or end <= start
            or end > len(anchor)
            or anchor[start:end] != value
            or len(value) > _CMEE_SOURCE_FRAGMENT_MAX
            or anchor.find(value) != start
            or anchor.find(value, start + 1) != -1
        ):
            return None
        values.append(value)
        previous_end = end
    if len(set(values)) != len(values):
        return None
    return tuple(values)


def _cmee_named_source_fragments(
    anchor: str,
    match: Any,
    names: Sequence[str],
) -> tuple[str, ...] | None:
    rows: list[tuple[str, int, int]] = []
    for name in names:
        start, end = match.span(name)
        value = str(match.group(name) or "")
        rows.append((value, start, end))
    return _cmee_valid_source_fragment_rows(anchor, rows)


def _cmee_parse_direct_contrast_shape(
    nucleus: Any,
    anchor: str,
) -> tuple[tuple[str, str], tuple[str, str]] | None:
    """Classify exactly one source-ordered direction/typed-other contrast."""

    matches = tuple(_CMEE_DIRECT_CONTRAST_SHAPE_RE.finditer(anchor))
    if len(matches) != 1:
        return None
    connector = matches[0]
    rows = _cmee_valid_source_fragment_rows(
        anchor,
        (
            (anchor[: connector.start()], 0, connector.start()),
            (anchor[connector.end() :], connector.end(), len(anchor)),
        ),
    )
    if rows is None:
        return None
    left, right = rows
    left_direction = bool(_cmee_semantic_desire(nucleus, left))
    right_direction = bool(_cmee_semantic_desire(nucleus, right))
    if left_direction == right_direction:
        return None
    other = right if left_direction else left
    if _CMEE_HESITATION_SHAPE_RE.search(other):
        other_kind = "hesitation"
    elif _cmee_has_current_burden(other):
        other_kind = "burden"
    else:
        return None
    return (
        (left, "direction" if left_direction else other_kind),
        (right, "direction" if right_direction else other_kind),
    )


def _cmee_parse_context_direction_residue_shape(
    anchor: str,
) -> tuple[str, str, str] | None:
    match = _CMEE_CONTEXT_DIRECTION_RESIDUE_SHAPE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = _cmee_named_source_fragments(
        anchor,
        match,
        ("context", "direction", "residue"),
    )
    return None if rows is None else (rows[0], rows[1], rows[2])


def _cmee_parse_open_question_shape(
    anchor: str,
) -> tuple[str, str] | None:
    match = _CMEE_OPEN_QUESTION_SHAPE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = _cmee_named_source_fragments(
        anchor,
        match,
        ("burden", "question"),
    )
    if rows is None:
        return None
    burden, question = rows
    burden_role = _cmee_bounded_source_burden_role(burden)
    # The registered surface adds the attributive link owned by the frozen
    # frame.  Admit only a terminal CJK nominal/na-state cue; arbitrary X+de,
    # verbal negatives, and adjectival predicates cannot use that link.
    if (
        not burden_role
        or not burden.endswith(burden_role)
        or not all(0x3400 <= ord(char) <= 0x9FFF for char in burden_role)
    ):
        return None
    return burden, question


def _cmee_parse_compound_burden_shape(
    anchor: str,
) -> tuple[str, str, str] | None:
    match = _CMEE_COMPOUND_BURDEN_SHAPE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = _cmee_named_source_fragments(
        anchor,
        match,
        ("context", "fatigue", "burden"),
    )
    if rows is None:
        return None
    context, fatigue, burden = rows
    if not _cmee_has_current_burden(fatigue) or not (
        _cmee_has_current_burden(burden)
        or _cmee_bounded_source_burden_role(burden)
    ):
        return None
    return context, fatigue, burden


def _cmee_parse_action_change_shape(
    anchor: str,
) -> tuple[str, str, str] | None:
    match = _CMEE_ACTION_CHANGE_SHAPE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = _cmee_named_source_fragments(
        anchor,
        match,
        ("context", "action", "result"),
    )
    if rows is None:
        return None
    context, source_action, result = rows
    inflections = tuple(
        (
            key,
            str(_CMEE_SOURCE_SHAPE_INFLECTIONS[key][0]),
            str(_CMEE_SOURCE_SHAPE_INFLECTIONS[key][1]),
        )
        for key in (
            "conditional_tara",
            "conditional_dara",
            "conditional_nara",
        )
        if source_action.endswith(
            str(_CMEE_SOURCE_SHAPE_INFLECTIONS[key][0])
        )
    )
    if len(inflections) != 1 or inflections[0][0] == "conditional_nara":
        return None
    _key, suffix, replacement = inflections[0]
    stem = source_action[: -len(suffix)]
    action = stem + replacement
    if (
        not stem
        or source_action != stem + suffix
        or action != stem + replacement
        or not COMPLETED_FACTUAL_CHANGE_RESULT_RE.fullmatch(result)
    ):
        return None
    return context, action, result


def _cmee_parse_simple_change_shape(
    anchor: str,
) -> tuple[str, str, str] | None:
    match = _CMEE_SIMPLE_CHANGE_SHAPE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = _cmee_named_source_fragments(
        anchor,
        match,
        ("context", "result"),
    )
    if rows is None:
        return None
    context, result = rows
    connector = str(match.group("connector") or "")
    simple_te = str(_CMEE_SOURCE_SHAPE_INFLECTIONS["simple_te"])
    simple_de = str(_CMEE_SOURCE_SHAPE_INFLECTIONS["simple_de"])
    if connector == simple_te:
        # A generic ku+te split cannot distinguish adjective, negative, or
        # desiderative morphology.  None of those can be reconstructed as a
        # past event by appending the registered ta replacement.
        if not context or ord(context[-1]) == 0x304F:
            return None
        replacement = str(
            _CMEE_SOURCE_SHAPE_INFLECTIONS["conditional_tara"][1]
        )
    elif connector == simple_de:
        # Narrow the voiced class to the unambiguous n+de verb shape.  This
        # deliberately excludes noun/na-adjective copulas and ambiguous i+de.
        if not context or ord(context[-1]) != 0x3093:
            return None
        replacement = str(
            _CMEE_SOURCE_SHAPE_INFLECTIONS["conditional_dara"][1]
        )
    else:
        return None
    reconstructed = context + replacement
    if not reconstructed or anchor != context + connector + result:
        return None
    return context, reconstructed, result


def _cmee_named_shape_fragments_within_l1_limit(
    pattern: re.Pattern[str],
    value: str,
    names: Sequence[str],
) -> bool:
    """Return whether a registered multipart shape fits its L1 role slots.

    Source-shape parsers are owned by the finite multipart microgrammar, not
    by generic source-role realization.  A regex hit whose exact named roles
    cannot fit those slots must therefore leave the source role generic; it
    is not malformed input.  Once the roles fit, the parser remains the
    fail-closed authority for morphology, ordering, and duplicate anchors.
    """

    match = pattern.fullmatch(value)
    if match is None:
        return False
    return all(
        bool(fragment := str(match.group(name) or ""))
        and len(fragment) <= _CMEE_SOURCE_FRAGMENT_MAX
        for name in names
    )


def _cmee_direct_contrast_fragments_within_l1_limit(value: str) -> bool:
    """Return whether exactly one contrast has two bounded source roles."""

    matches = tuple(_CMEE_DIRECT_CONTRAST_SHAPE_RE.finditer(value))
    if len(matches) != 1:
        return False
    match = matches[0]
    return all(
        len(fragment) <= _CMEE_SOURCE_FRAGMENT_MAX
        for fragment in (value[: match.start()], value[match.end() :])
    )


def _cmee_validate_typed_source_shape(nucleus: Any, value: str) -> None:
    """Dispatch finite multipart recognizers exactly once or fail closed."""

    attributes = frozenset(nucleus.semantic_frame.attribute_codes)
    signatures: list[str] = []
    parsed: list[str] = []

    if "operator:positive_change" in attributes:
        for name, pattern, fragment_names, parser in (
            (
                "action_change",
                _CMEE_ACTION_CHANGE_SHAPE_RE,
                ("context", "action", "result"),
                _cmee_parse_action_change_shape,
            ),
            (
                "simple_positive_change",
                _CMEE_SIMPLE_CHANGE_SHAPE_RE,
                ("context", "result"),
                _cmee_parse_simple_change_shape,
            ),
        ):
            if _cmee_named_shape_fragments_within_l1_limit(
                pattern,
                value,
                fragment_names,
            ):
                signatures.append(name)
                if parser(value) is not None:
                    parsed.append(name)
    else:
        retained_direction = bool(
            nucleus.kind == "wish"
            or nucleus.semantic_frame.modality in {"wish", "intention"}
            or "semantic_role:retained_intention" in attributes
        )
        if retained_direction:
            for name, pattern, fragment_names, parser in (
                (
                    "context_direction_residue",
                    _CMEE_CONTEXT_DIRECTION_RESIDUE_SHAPE_RE,
                    ("context", "direction", "residue"),
                    _cmee_parse_context_direction_residue_shape,
                ),
                (
                    "open_question",
                    _CMEE_OPEN_QUESTION_SHAPE_RE,
                    ("burden", "question"),
                    _cmee_parse_open_question_shape,
                ),
            ):
                if _cmee_named_shape_fragments_within_l1_limit(
                    pattern,
                    value,
                    fragment_names,
                ):
                    signatures.append(name)
                    if parser(value) is not None:
                        parsed.append(name)

        if nucleus.kind in {"state", "reaction", "constraint"}:
            if _cmee_named_shape_fragments_within_l1_limit(
                _CMEE_COMPOUND_BURDEN_SHAPE_RE,
                value,
                ("context", "fatigue", "burden"),
            ):
                signatures.append("compound_burden")
                if _cmee_parse_compound_burden_shape(value) is not None:
                    parsed.append("compound_burden")

        typed_direct_contrast_owner = bool(
            nucleus.kind in {"wish", "constraint"}
            or {
                "semantic_role:retained_intention",
                "semantic_role:burden",
            }.intersection(attributes)
        ) and "semantic_role:embedded_turn" not in attributes
        if (
            typed_direct_contrast_owner
            and _cmee_direct_contrast_fragments_within_l1_limit(value)
            and _cmee_semantic_desire(nucleus, value)
        ):
            signatures.append("direct_contrast")
            if _cmee_parse_direct_contrast_shape(nucleus, value) is not None:
                parsed.append("direct_contrast")

    if len(signatures) > 1 or len(parsed) > 1:
        raise CMEEVerticalError("stage1_source_shape_ambiguous")
    if signatures and not parsed:
        raise CMEEVerticalError("stage1_source_shape_malformed")


def _owner_for_source_span(source: AdmittedTextSource, source_span_id: str) -> str:
    try:
        return source.meaning_owner_for_span(source_span_id)
    except Exception:
        raise CMEEVerticalError("source_span_owner_binding_mismatch") from None


def _owner_for_nucleus(source: AdmittedTextSource, nucleus: Any) -> str:
    source_span_ids = _ordered(getattr(nucleus, "source_span_ids", ()))
    if len(source_span_ids) != 1:
        raise CMEEVerticalError("nucleus_owner_binding_not_exact1")
    return _owner_for_source_span(source, source_span_ids[0])


def _owner_for_relation(source: AdmittedTextSource, relation: Any) -> str:
    owners = _ordered(
        _owner_for_source_span(source, source_span_id)
        for source_span_id in getattr(relation, "source_span_ids", ())
    )
    if len(owners) != 1:
        raise CMEEVerticalError("relation_endpoint_binding_not_supported")
    return owners[0]


def _cmee_typed_relation_fragment_value(
    nucleus: Any,
    raw_value: str,
) -> str | None:
    """Return an exact source slice only for the new typed relation child."""

    attributes = tuple(getattr(nucleus.semantic_frame, "attribute_codes", ()))
    scalar_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_range:")
    )
    source_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_source:")
    )
    legacy_scalar_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith(
            ("surface_scalar_range:", "surface_scalar_source:")
        )
    )
    marker_rows = tuple(
        code
        for code in attributes
        if code == "semantic_role:generic_relation_fragment"
    )
    if not marker_rows:
        if scalar_rows or source_rows:
            raise CMEEVerticalError("typed_fragment_scalar_range_invalid")
        return None
    if (
        len(marker_rows) != 1
        or len(scalar_rows) != 1
        or source_rows
        != ("source_fragment_scalar_source:normalized_raw_text",)
        or legacy_scalar_rows
    ):
        raise CMEEVerticalError("typed_fragment_scalar_range_invalid")
    parts = scalar_rows[0].split(":")
    if len(parts) != 3:
        raise CMEEVerticalError("typed_fragment_scalar_range_invalid")
    try:
        start, end = int(parts[1]), int(parts[2])
    except (IndexError, ValueError):
        raise CMEEVerticalError("typed_fragment_scalar_range_invalid") from None
    normalized = re.sub(
        r"\s+",
        " ",
        str(raw_value or "").replace("\u3000", " "),
    ).strip()
    if not (0 <= start < end <= len(normalized)):
        raise CMEEVerticalError("typed_fragment_scalar_range_invalid")
    fragment = normalized[start:end]
    if not fragment or fragment != fragment.strip():
        raise CMEEVerticalError("typed_fragment_scalar_range_invalid")
    return fragment


def _cmee_tentative_state_core(text: str) -> str:
    """Remove only the typed tentative-state shell from a source role."""

    match = re.fullmatch(r"(.+?)感じがある", str(text or ""))
    return match.group(1) if match else ""


def _cmee_bounded_source_burden_role(text: str) -> str:
    """Return one complete, exact source burden predicate when available."""

    value = re.sub(r"\s+", "", str(text or "")).strip(
        "、。！？!?「」『』 "
    )
    matches = tuple(
        match.group(0)
        for match in re.finditer(
            r"(?:[ぁ-んァ-ン一-龥ー]{1,16}(?:られなくて|れなくて|"
            r"できなくて|なくて)(?:疲れた|疲れました|つらい|苦しい|"
            r"しんどい)|何も手につかない|手につかない|"
            r"何もしたくない|限界が近い|動けない|できない|"
            r"疲れている|疲れています|疲れた|疲れました|"
            r"つらい|苦しい|しんどい|だるい|重い|不安|心配|"
            r"迷惑(?:かもしれない)?|痛い)",
            value,
        )
    )
    return matches[-1] if matches else ""


def _cmee_bounded_source_direction_role(text: str) -> str:
    """Drop only a source object/topic prefix from one complete desire role."""

    desire = _cmee_desire_phrase(text)
    if not desire:
        return ""
    if len(desire) <= CMEE_FROZEN_ROLE_MAX:
        bounded = desire
    else:
        bounded = ""
    contextual = re.fullmatch(
        r".+?(?:を|に|へ|では|には|なら)(?P<predicate>"
        r"[ぁ-んァ-ン一-龥ー]{1,12}たい)",
        desire,
    )
    if contextual:
        predicate = str(contextual.group("predicate") or "")
        if predicate and len(predicate) <= CMEE_FROZEN_ROLE_MAX:
            bounded = predicate
    return bounded


def _cmee_exact_contrast_parts(text: str) -> tuple[str, str, str] | None:
    """Return both exact source sides and their exact admitted connector."""

    value = re.sub(r"\s+", "", str(text or "")).strip(
        "、。！？!?「」『』 "
    )
    pair = _cmee_split_contrast(value)
    if pair is None:
        return None
    left, right = pair
    if not value.startswith(left) or not value.endswith(right):
        return None
    right_start = len(value) - len(right)
    separator = value[len(left) : right_start]
    if not left or not separator or not right:
        return None
    return left, separator, right


def _cmee_bounded_exclusive_focus_role(text: str) -> str:
    """Return one exact ``XしかV-neg`` source role, or fail closed.

    Japanese exclusive focus uses a finite negative carrier without negating
    the focused role itself.  This recognizer deliberately admits only one
    short punctuation-bounded source clause; quoted, metalinguistic, nested,
    multi-focus, and other-experiencer readings remain outside the finite
    Stage 1 lexical-role contract.
    """

    raw = str(text or "")
    compact = re.sub(r"\s+", "", raw)
    if not compact or compact.count("しか") != 1:
        return ""
    source_segments = tuple(
        segment
        for segment in re.split(r"[、,。！？!?]+", compact)
        if segment
    )
    focus_segments = tuple(
        segment for segment in source_segments if "しか" in segment
    )
    if len(focus_segments) != 1:
        return ""
    candidate = focus_segments[0]
    if (
        not candidate
        or candidate not in raw
        or len(candidate) > CMEE_FROZEN_ROLE_MAX
    ):
        return ""
    focus_index = candidate.find("しか")
    if focus_index < 1:
        return ""
    carriers = tuple(_CMEE_FINITE_NEGATIVE_CARRIER_RE.finditer(candidate))
    if len(carriers) != 1:
        return ""
    carrier = carriers[0]
    if (
        carrier.start() < focus_index + len("しか")
        or carrier.end() != len(candidate)
    ):
        return ""
    if any(
        segment != candidate
        and EXPLICIT_WHOLE_STATE_NEGATION_RE.search(segment)
        for segment in source_segments
    ):
        return ""
    if (
        _CMEE_EXCLUSIVE_FOCUS_GROUP_RE.search(candidate)
        or _CMEE_EXCLUSIVE_FOCUS_METALINGUISTIC_RE.search(compact)
        or _CMEE_EXCLUSIVE_FOCUS_SCOPE_NEGATION_RE.search(candidate)
        or _CMEE_EXCLUSIVE_FOCUS_OTHER_EXPERIENCER_RE.search(candidate)
        or _CMEE_EXCLUSIVE_FOCUS_OTHER_CONTEXT_RE.search(compact)
    ):
        return ""
    subject_match = re.match(
        rf"^(?P<subject>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})"
        r"(?:が|は|には|では|こそ|も)(?=.+しか)",
        candidate,
    )
    if subject_match:
        subject = str(subject_match.group("subject") or "")
        safe_subject = bool(
            subject in FIRST_PERSON_SUBJECTS
            or subject in SAFE_NONPERSON_TOPIC_EXACT
            or any(
                pattern.fullmatch(subject)
                for pattern in SAFE_NONPERSON_TOPIC_PATTERNS
            )
            or subject
            in {
                "ここ",
                "そこ",
                "実際",
                "現在",
                "当時",
                "そのとき",
                "その時",
                "疲れ",
                "不安",
                "心配",
                "つらさ",
                "苦しさ",
                "しんどさ",
            }
        )
        if not safe_subject:
            return ""
    return candidate


def _cmee_typed_exclusive_focus_role_owner(nucleus: Any) -> bool:
    """Require one explicit current-user negative state owner."""

    frame = getattr(nucleus, "semantic_frame", None)
    attributes = frozenset(getattr(frame, "attribute_codes", ()))
    return bool(
        str(getattr(nucleus, "kind", "")) in {"state", "reaction"}
        and str(getattr(nucleus, "grounding_kind", "")) == "explicit"
        and tuple(getattr(nucleus, "source_span_ids", ()))
        and str(getattr(frame, "actor", "")) == "current_user"
        and str(getattr(frame, "predicate_kind", "")) == "state"
        and str(getattr(frame, "polarity", "")) == "negative"
        and str(getattr(frame, "modality", "")) == "fact"
        and "operator:negation" in attributes
        and "operator:refusal" not in attributes
        and "semantic_role:retained_intention" not in attributes
    )


def _cmee_frozen_lexical_role_surface(
    nucleus: Any,
    source_text: str,
    *,
    allow_final_exclusive_focus: bool = False,
) -> str:
    """Freeze one finite source-grounded semantic-role surface.

    The only transformations are driven by canonical frame roles.  They
    preserve exact source chunks and admitted connectors.  No request,
    fixture, structured optional owner, or output text participates in the
    decision.
    """

    value = re.sub(r"\s+", "", str(source_text or "")).strip(
        "、。！？!?「」『』 "
    )
    if not value:
        raise CMEEVerticalError("lexical_role_surface_missing")
    frame = nucleus.semantic_frame
    attributes = frozenset(frame.attribute_codes)
    contrast = _cmee_exact_contrast_parts(value)
    _cmee_validate_typed_source_shape(nucleus, value)

    # Explicitly negated desire cannot be promoted to a retained direction.
    if (
        nucleus.kind == "wish"
        or frame.modality in {"wish", "intention"}
        or "semantic_role:retained_intention" in attributes
    ) and NEGATED_DESIRE_RE.search(value):
        raise CMEEVerticalError("lexical_role_negated_desire_conflict")

    exclusive_focus_role = (
        _cmee_bounded_exclusive_focus_role(source_text)
        if allow_final_exclusive_focus
        and _cmee_typed_exclusive_focus_role_owner(nucleus)
        else ""
    )

    # The finite Stage 1 operator matrix has no general negated-state
    # realization.  Refusal is representable by its registered modality
    # wrapper; every other explicit negation fails closed before a positive
    # burden/state predicate could reverse it.
    if (
        "operator:negation" in attributes
        and EXPLICIT_WHOLE_STATE_NEGATION_RE.search(value)
        and not (
            frame.modality == "refusal"
            and "operator:refusal" in attributes
        )
        and not exclusive_focus_role
    ):
        raise CMEEVerticalError("lexical_role_negation_unrepresentable")
    if exclusive_focus_role:
        return exclusive_focus_role

    # Discourse markers are owned by the admitted relation (or remain an
    # unclaimed source-order marker).  They are not part of either endpoint's
    # lexical role, so remove only a registered leading marker and retain the
    # complete endpoint predicate.
    if "operator:cause" in attributes:
        candidate = re.sub(
            r"^(?:そのため|だから|なので|その結果)[、,]?",
            "",
            value,
            count=1,
        )
        if candidate and candidate != value:
            return candidate
    elif nucleus.kind in {"state", "reaction"}:
        candidate = re.sub(
            r"^(?:そのあと|その後)[、,]?",
            "",
            value,
            count=1,
        )
        if candidate and candidate != value:
            return candidate

    # For a contrast-side burden, a non-person source topic is context rather
    # than the lexical predicate.  Retaining the unique contiguous predicate
    # avoids cross-binding when both endpoints repeat the same topic phrase.
    if (
        nucleus.kind in {"state", "reaction"}
        and "semantic_role:contrast_before" in attributes
    ):
        topic_match = re.fullmatch(
            rf"(?P<topic>{GENERIC_EXPERIENCER_SUBJECT_PATTERN})(?:が|は)"
            r"(?P<predicate>.+)",
            value,
        )
        if topic_match:
            topic = str(topic_match.group("topic") or "")
            predicate = str(topic_match.group("predicate") or "")
            safe_topic = topic in SAFE_NONPERSON_TOPIC_EXACT or any(
                pattern.fullmatch(topic)
                for pattern in SAFE_NONPERSON_TOPIC_PATTERNS
            )
            if (
                safe_topic
                and predicate
                and value.count(predicate) == 1
                and len(predicate) <= CMEE_FROZEN_ROLE_MAX
                and _cmee_has_current_burden(predicate)
            ):
                return predicate

    # A typed past/present shift already realizes its time scope through the
    # frozen microgrammar wrapper.  Remove only the matching leading temporal
    # topic from its role surface; this avoids replaying the same full source
    # clause in both the required temporal relation and its bounded direct
    # contribution.  Contrast/change clauses keep their complete source role.
    if (
        nucleus.kind in {"state", "reaction"}
        and "operator:shift" in attributes
        and "operator:contrast" not in attributes
    ):
        candidate = value
        if frame.time_scope == "past":
            candidate = re.sub(
                rf"^(?:{PAST_SCOPE_MARKER_PATTERN})(?:は|も|に)?",
                "",
                value,
                count=1,
            )
        elif frame.time_scope == "present":
            candidate = re.sub(
                r"^(?:今日|今)(?:は|も|に)?",
                "",
                value,
                count=1,
            )
        if (
            candidate
            and candidate != value
            and len(candidate) <= CMEE_FROZEN_ROLE_MAX
        ):
            return candidate

    # A direct PRESENT_CHANGE role keeps the source-stated conditional action
    # and result together.  A leading typed temporal context may be removed
    # only when the remaining complete ACTION -> CHANGE clause is a contiguous
    # source substring within the registered bound.
    if "operator:positive_change" in attributes:
        change_parts = _cmee_change_parts(value)
        if change_parts and contrast is not None:
            current_context = re.sub(r"^今日は?", "", value, count=1)
            if (
                current_context
                and current_context != value
                and len(current_context) <= CMEE_FROZEN_ROLE_MAX
            ):
                return current_context
            before, _action, result = change_parts
            left, separator, right = contrast
            before_result = before + separator + result
            if (
                left.endswith(before)
                and not _cmee_has_current_burden(before)
                and len(before_result) <= CMEE_FROZEN_ROLE_MAX
            ):
                return before_result
            candidate = right
            if len(candidate) > CMEE_FROZEN_ROLE_MAX:
                temporal_context = re.fullmatch(
                    r".+?てから(?P<transition>.+?(?:たら|だら|なら).+)",
                    candidate,
                )
                if temporal_context:
                    candidate = str(temporal_context.group("transition") or "")
            if (
                candidate
                and len(candidate) <= CMEE_FROZEN_ROLE_MAX
                and re.fullmatch(r".+?(?:たら|だら|なら).+", candidate)
            ):
                return candidate

    # A bounded counterposition targets the source-stated limiting conclusion,
    # not a right-edge text fragment.  When the same nucleus also contains its
    # asserted reason, retain the complete conclusion after the exact source
    # causal connector.
    if (
        nucleus.kind == "self_evaluation"
        and "operator:self_evaluation" in attributes
        and len(value) > CMEE_FROZEN_ROLE_MAX
    ):
        conclusion_match = re.fullmatch(
            r".+?(?:から|ので)[、,]?(?P<conclusion>.+)",
            value,
        )
        if conclusion_match:
            candidate = str(conclusion_match.group("conclusion") or "")
            if candidate and len(candidate) <= CMEE_FROZEN_ROLE_MAX:
                return candidate

    # A long contrast role may bind one retained direction and one burden.
    # Keep their exact source order and connector; if the full burden clause
    # exceeds the bound, use only a complete source predicate rather than a
    # grapheme window or a newly inflected summary.
    if (
        contrast is not None
        and nucleus.kind != "constraint"
        and "operator:help_seeking" not in attributes
    ):
        left, separator, right = contrast
        left_desire = _cmee_semantic_desire(nucleus, left)
        right_desire = _cmee_semantic_desire(nucleus, right)
        if bool(left_desire) != bool(right_desire):
            direction = left_desire or right_desire
            burden = right if left_desire else left
            candidate = (
                direction + separator + burden
                if left_desire
                else burden + separator + direction
            )
            if len(candidate) <= CMEE_FROZEN_ROLE_MAX:
                return candidate
            burden_role = _cmee_bounded_source_burden_role(burden)
            candidate = (
                direction + separator + burden_role
                if left_desire
                else burden_role + separator + direction
            )
            if (
                burden_role
                and candidate
                and len(candidate) <= CMEE_FROZEN_ROLE_MAX
            ):
                return candidate
            direction_role = _cmee_bounded_source_direction_role(direction)
            candidate = (
                direction_role + separator + burden_role
                if left_desire
                else burden_role + separator + direction_role
            )
            if (
                direction_role
                and burden_role
                and len(candidate) <= CMEE_FROZEN_ROLE_MAX
            ):
                return candidate

    # A source-stated retained direction with a residue is a bounded nominal
    # role when its complete predicate would exceed the surface limit.  Every
    # retained chunk is contiguous source text; the terminal residue predicate
    # is carried by the typed PRESENT_RESIDUE/shift frame rather than cut.
    if (
        nucleus.kind == "wish"
        and "semantic_role:retained_intention" in attributes
    ):
        current_context = re.sub(r"^今日は?", "", value, count=1)
        if (
            current_context != value
            and current_context.endswith(("が残っている", "が残っています"))
            and len(current_context) <= CMEE_FROZEN_ROLE_MAX
        ):
            return current_context

        open_question = _cmee_parse_open_question_shape(value)
        if open_question:
            # Keep the complete bounded question, including the user's stated
            # ongoing act of thinking.  Step 4 partitions it into exact role
            # fragments and finite grammar.
            if len(value) <= CMEE_FROZEN_ROLE_MAX:
                return value
            raise CMEEVerticalError("stage1_source_shape_over_limit")

        residue_match = re.search(
            r"(?P<direction>[ぁ-んァ-ン一-龥ー]{1,24}たい)"
            r"(?P<wrapper>気持ち|願い)?(?P<separator>と|や)"
            r"(?P<residue>[^、。！？!?]{1,16}?)(?:が|は)"
            r"(?:残っている|残っています)$",
            value,
        )
        if residue_match:
            candidate = "".join(
                str(residue_match.group(name) or "")
                for name in ("direction", "wrapper", "separator", "residue")
            )
            if len(candidate) <= CMEE_FROZEN_ROLE_MAX:
                return candidate

        help_match = re.fullmatch(
            r"(?P<burden>.+?)(?P<separator>で[、,]?)"
            r"(?P<question>どうしたら(?:いい|よい)のか)"
            r"(?:考えて(?:いる|います))?",
            value,
        )
        if help_match:
            burden_role = _cmee_bounded_source_burden_role(
                str(help_match.group("burden") or "")
            )
            candidate = (
                burden_role
                + str(help_match.group("separator") or "")
                + str(help_match.group("question") or "")
            )
            if (
                burden_role
                and len(candidate) <= CMEE_FROZEN_ROLE_MAX
            ):
                return candidate

    # Embedded help seeking keeps source order.  The multipart Stage 1 frame
    # types its desire and hesitation separately, so no clause reordering is
    # needed to make a single generic wish slot grammatical.
    if (
        nucleus.kind == "wish"
        and {
            "operator:help_seeking",
            "semantic_role:retained_intention",
        }.issubset(attributes)
        and contrast is not None
    ):
        left, separator, right = contrast
        left_desire = _cmee_semantic_desire(nucleus, left)
        right_desire = _cmee_semantic_desire(nucleus, right)
        if bool(left_desire) != bool(right_desire):
            if len(value) <= CMEE_FROZEN_ROLE_MAX:
                return value

    # A complete simple intention can use its finite sentence-object
    # inflection.  Compound wishes are deliberately left untouched.
    if (
        nucleus.kind == "wish"
        and "semantic_role:retained_intention" in attributes
    ):
        desire = _cmee_semantic_desire(nucleus, value)
        first_person_pattern = "|".join(
            re.escape(subject)
            for subject in sorted(FIRST_PERSON_SUBJECTS, key=len, reverse=True)
        )
        plain_first_person = re.fullmatch(
            rf"(?:{first_person_pattern})は(?P<predicate>.+たい)",
            desire,
        )
        reported = GENERIC_EXPERIENCER_REPORTED_DESIRE_RE.search(value)
        first_person_report = bool(
            reported is not None
            and any(
                str(reported.group("subject") or "").endswith(subject)
                for subject in FIRST_PERSON_SUBJECTS
            )
        )
        if desire and (desire == value or first_person_report):
            candidate = (
                str(plain_first_person.group("predicate") or "")
                if plain_first_person is not None
                else _cmee_sentence_desire_phrase(desire)
                if first_person_report
                else desire
            )
            if candidate and len(candidate) <= CMEE_FROZEN_ROLE_MAX:
                return candidate

    # A constraint-side tentative shell is itself source epistemic content.
    # Preserve the complete bounded role so Stage 1 cannot quote a stronger
    # burden core while silently dropping the user's tentative framing.
    if (
        nucleus.kind == "constraint"
        and {
            "detected_type:limit_signal",
            "operator:constraint",
        }.issubset(attributes)
        and contrast is not None
    ):
        left, separator, right = contrast
        left_desire = _cmee_semantic_desire(nucleus, left)
        right_desire = _cmee_semantic_desire(nucleus, right)
        if bool(left_desire) != bool(right_desire):
            if len(value) <= CMEE_FROZEN_ROLE_MAX:
                return value
            raise CMEEVerticalError("stage1_source_shape_over_limit")

    # A long standalone burden can retain one complete punctuation-delimited
    # source clause or registered burden predicate.  Relation-bearing roles
    # are excluded because collapsing either endpoint would change meaning.
    if (
        nucleus.kind in {"state", "reaction", "constraint"}
        and len(value) > CMEE_FROZEN_ROLE_MAX
        and "operator:contrast" not in attributes
        and "operator:positive_change" not in attributes
    ):
        complete_clauses = tuple(
            clause
            for clause in re.split(r"[、,]", value)
            if clause
            and len(clause) <= CMEE_FROZEN_ROLE_MAX
            and _cmee_has_current_burden(clause)
        )
        candidate = (
            complete_clauses[-1]
            if complete_clauses
            else _cmee_bounded_source_burden_role(value)
        )
        if candidate and len(candidate) <= CMEE_FROZEN_ROLE_MAX:
            return candidate

    # Registered short burden inflections prevent a complete short evidence
    # span from being replayed as a quote.  These are bounded Japanese
    # morphology changes only; actor, polarity, modality, and time scope stay
    # owned by the canonical semantic frame.
    if nucleus.kind in {"state", "reaction", "constraint"}:
        if value in {"疲れているかもしれない", "私は疲れているかもしれない"}:
            return "疲れている可能性"
        if value in {"疲れている", "私は疲れている", "疲れた"}:
            return "疲れ"

    return value


def _build_graph(
    source: AdmittedTextSource,
    grounded_plan: Any,
    planned_visible_nucleus_ids: Sequence[str],
    planned_visible_relation_ids: Sequence[str],
) -> GroundedMeaningGraph:
    try:
        canonical_universe = build_source_owner_universe(
            source.envelope,
            source.evidence_refs,
        )
    except Exception:
        raise CMEEVerticalError("source_owner_universe_recompute_failed") from None
    if source.owner_universe != canonical_universe:
        raise CMEEVerticalError("source_owner_universe_mismatch")

    visible_nuclei = set(planned_visible_nucleus_ids)
    visible_relations = set(planned_visible_relation_ids)
    allow_final_exclusive_focus = (
        FINAL_STAGE1_GROUNDED_PROJECTION_VERSION
        in tuple(getattr(grounded_plan, "source_contracts", ()))
    )
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    planned_visible_span_ids = {
        source_span_id
        for nucleus in grounded_plan.nuclei
        if nucleus.nucleus_id in visible_nuclei
        for source_span_id in nucleus.source_span_ids
    }
    planned_visible_span_ids.update(
        source_span_id
        for relation in grounded_plan.relations
        if relation.relation_id in visible_relations
        for source_span_id in relation.source_span_ids
    )

    nodes: list[MeaningNode] = []
    node_id_by_source: dict[str, str] = {}
    visible_claims_by_owner: dict[str, list[str]] = {}
    for nucleus in grounded_plan.nuclei:
        is_visible = nucleus.nucleus_id in visible_nuclei
        if nucleus.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            if is_visible:
                raise CMEEVerticalError("provisional_nucleus_visible_authority_forbidden")
            continue
        owner = _owner_for_nucleus(source, nucleus)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in nucleus.source_span_ids
            if span_id in ref_by_span
        )
        if len(evidence) != len(tuple(nucleus.source_span_ids)) or not evidence:
            raise CMEEVerticalError("nucleus_evidence_binding_mismatch")
        node_id = _stable_id("mn", source.envelope.envelope_id, nucleus.nucleus_id)
        node_id_by_source[nucleus.nucleus_id] = node_id
        raw_value = "\n".join(
            str(getattr(span, "raw_text", "") or "")
            for span in source.evidence_spans
            if str(getattr(span, "span_id", "") or "") in set(nucleus.source_span_ids)
        )
        typed_fragment = _cmee_typed_relation_fragment_value(
            nucleus,
            raw_value,
        )
        value = (
            typed_fragment
            if typed_fragment is not None
            else _cmee_frozen_lexical_role_surface(
                nucleus,
                raw_value,
                allow_final_exclusive_focus=allow_final_exclusive_focus,
            )
        )
        nodes.append(
            MeaningNode(
                node_id=node_id,
                owner_id=owner,
                node_kind=str(nucleus.kind),
                grounding_kind=str(nucleus.grounding_kind),
                value=value,
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=evidence,
            )
        )
        # Every admitted direct source nucleus is eligible for the bounded
        # request-local semantic pool.  Record that authority explicitly on
        # its source owner instead of letting Stage 1 read a claim from a
        # NOT_VISIBLE_UNRESOLVED owner.  Non-realized strength and unknown
        # attachment nodes remain governed by their existing dispositions.
        visible_claims_by_owner.setdefault(owner, []).append(node_id)

    edges: list[MeaningEdge] = []
    for relation in grounded_plan.relations:
        is_visible = relation.relation_id in visible_relations
        if relation.grounding_kind not in ADMISSIBLE_RELATION_GROUNDING:
            if is_visible:
                raise CMEEVerticalError("provisional_relation_visible_authority_forbidden")
            # The source-owner boundary keeps provisional resolver/legacy
            # proposals outside the
            # grounded graph; absence does not create a post-plan owner.
            continue
        owner = _owner_for_relation(source, relation)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in relation.source_span_ids
            if span_id in ref_by_span
        )
        if len(evidence) != len(tuple(relation.source_span_ids)) or not evidence:
            raise CMEEVerticalError("relation_evidence_binding_mismatch")
        if relation.from_nucleus_id not in node_id_by_source or relation.to_nucleus_id not in node_id_by_source:
            raise CMEEVerticalError("relation_endpoint_unknown")
        edge_id = _stable_id("me", source.envelope.envelope_id, relation.relation_id)
        edges.append(
            MeaningEdge(
                edge_id=edge_id,
                owner_id=owner,
                relation=str(relation.type),
                source_node_id=node_id_by_source[relation.from_nucleus_id],
                target_node_id=node_id_by_source[relation.to_nucleus_id],
                grounding_kind=str(relation.grounding_kind),
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=evidence,
            )
        )
        if is_visible:
            visible_claims_by_owner.setdefault(owner, []).append(edge_id)

    # Strength is part of the admitted structured source but this slice does
    # not realize it. It remains SOURCE_EXPLICIT but is not misclassified as
    # an unknown merely because it is not selected for the visible plan.
    strength_ref = source.evidence_ref("structured:emotion_strength")
    strength_owner = _owner_for_source_span(source, strength_ref.source_span_id)
    nodes.append(
        MeaningNode(
            node_id=_stable_id("mn", source.envelope.envelope_id, strength_owner),
            owner_id=strength_owner,
            node_kind="STRUCTURED_EMOTION_STRENGTH",
            grounding_kind="source_explicit_not_realized",
            value=source.strength,
            epistemic_state=EpistemicState.SOURCE_EXPLICIT,
            evidence_ids=(strength_ref.evidence_id,),
        )
    )

    dispositions: list[OwnerDisposition] = []
    for obligation in source.owner_universe.obligations:
        owner_id = obligation.meaning_owner_id
        visible_claim_refs = tuple(visible_claims_by_owner.get(owner_id, ()))
        if obligation.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT":
            selected_attachment_refs = tuple(
                ref_by_span[source_span_id]
                for source_span_id in obligation.source_span_ids
                if source_span_id in planned_visible_span_ids
                and source_span_id in ref_by_span
            )
            selected_field_paths = {
                row.field_path for row in selected_attachment_refs
            }
            attachment_is_material = bool(
                selected_field_paths.intersection({"memo", "memo_action"})
                and any(
                    field_path not in {"memo", "memo_action"}
                    for field_path in selected_field_paths
                )
            )
            if attachment_is_material:
                unknown_node_id = _stable_id(
                    "mn",
                    source.envelope.envelope_id,
                    owner_id,
                    "structured_attachment_unknown",
                )
                nodes.append(
                    MeaningNode(
                        node_id=unknown_node_id,
                        owner_id=owner_id,
                        node_kind="STRUCTURED_CONTEXT_ATTACHMENT_RELATION",
                        grounding_kind="unresolved_attachment_relation",
                        value="",
                        epistemic_state=EpistemicState.UNKNOWN,
                        evidence_ids=obligation.evidence_refs,
                    )
                )
                dispositions.append(
                    OwnerDisposition(
                        meaning_owner_id=owner_id,
                        owner_class=obligation.owner_class,
                        resolver_resolution=ResolverResolution.UNRESOLVED,
                        attachment_admission=AttachmentAdmission.UNRESOLVED,
                        visible_authority=VisibleAuthority.NONE,
                        source_owner_disposition=(
                            SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
                        ),
                        visible_claim_refs=(unknown_node_id,),
                        evidence_refs=obligation.evidence_refs,
                        target_unknown_ref=unknown_node_id,
                        reason_codes=("ATTACHMENT_UNRESOLVED",),
                    )
                )
                continue
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    resolver_resolution=ResolverResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.NONE,
                    source_owner_disposition=(
                        SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                    ),
                    visible_claim_refs=(),
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=("ATTACHMENT_UNRESOLVED",),
                )
            )
        elif visible_claim_refs:
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    resolver_resolution=ResolverResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.SOURCE_EXPLICIT,
                    source_owner_disposition=(
                        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
                    ),
                    visible_claim_refs=visible_claim_refs,
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=(),
                )
            )
        else:
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    resolver_resolution=ResolverResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.NONE,
                    source_owner_disposition=(
                        SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                    ),
                    visible_claim_refs=(),
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=("ATTACHMENT_UNRESOLVED",),
                )
            )

    owner_refs = tuple(row.meaning_owner_id for row in dispositions)
    expected_owner_refs = (
        source.owner_universe.required_owner_refs
        + source.owner_universe.active_optional_owner_refs
    )
    if owner_refs != expected_owner_refs or len(owner_refs) != len(set(owner_refs)):
        raise CMEEVerticalError("source_owner_duplicate")
    owner_digest = source.owner_universe.owner_universe_digest
    graph_id = _graph_id(
        source.envelope.envelope_id,
        owner_digest,
        nodes,
        edges,
        dispositions,
    )
    graph = GroundedMeaningGraph(
        graph_id=graph_id,
        source_envelope_id=source.envelope.envelope_id,
        nodes=tuple(nodes),
        edges=tuple(edges),
        owner_dispositions=tuple(dispositions),
        required_owner_refs=source.owner_universe.required_owner_refs,
        active_optional_owner_refs=source.owner_universe.active_optional_owner_refs,
        source_version=source.owner_universe.source_version,
        obligation_version=source.owner_universe.obligation_version,
        owner_universe_digest=owner_digest,
    )
    if tuple(row.owner_id for row in graph.owner_dispositions) != expected_owner_refs:
        raise CMEEVerticalError("source_owner_denominator_mismatch")
    return graph


def _planned_visible_source_ids(grounded_plan: Any) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    required_nuclei = tuple(grounded_plan.coverage_requirements.required_nucleus_ids)
    required_relations = tuple(grounded_plan.coverage_requirements.required_relation_ids)
    if any(
        row_id not in nucleus_index
        or nucleus_index[row_id].grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING
        for row_id in required_nuclei
    ):
        raise CMEEVerticalError("required_nucleus_visible_authority_unavailable")
    if any(
        row_id not in relation_index
        or relation_index[row_id].grounding_kind not in ADMISSIBLE_RELATION_GROUNDING
        for row_id in required_relations
    ):
        raise CMEEVerticalError("required_relation_visible_authority_unavailable")

    reception_targets = tuple(
        row_id
        for row_id in grounded_plan.response_plan.human_follow_target_ids
        if row_id in nucleus_index
        and nucleus_index[row_id].grounding_kind in ADMISSIBLE_NUCLEUS_GROUNDING
    )
    if not required_nuclei or not reception_targets:
        raise CMEEVerticalError("experience_plan_required_owner_missing")
    if not set(reception_targets).issubset(set(required_nuclei)):
        raise CMEEVerticalError("reception_target_not_in_observation_plan")
    return required_nuclei, required_relations, reception_targets


def _source_plan_binding_version(
    grounded_plan: Any,
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> str:
    """Seal exact private realization obligations into the existing plan field."""

    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    material = {
        "binding_version": "cocolon.cmee.emlis.r4_realization_obligations.v1",
        "source_plan_schema_version": str(grounded_plan.schema_version),
        "source_plan_generation_path": str(grounded_plan.generation_path),
        "required_nucleus_ids": list(required_nucleus_ids),
        "required_relations": [
            {
                "relation_id": relation_id,
                "relation_type": str(relation_index[relation_id].type),
                "from_nucleus_id": str(
                    relation_index[relation_id].from_nucleus_id
                ),
                "to_nucleus_id": str(relation_index[relation_id].to_nucleus_id),
                "evidence_span_ids": list(
                    relation_index[relation_id].source_span_ids
                ),
            }
            for relation_id in required_relation_ids
        ],
        "reception_target_ids": list(reception_target_ids),
    }
    digest = _sha256_text(
        json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return (
        f"{grounded_plan.schema_version}|{grounded_plan.generation_path}|"
        f"cocolon.cmee.emlis.r4_realization_obligations.v1:{digest}"
    )


def _build_experience_plan(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> ExperiencePlan:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    positive_dispositions = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition in positive_dispositions
    )
    unresolved = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition not in positive_dispositions
    )
    unresolved_required = tuple(
        row
        for row in graph.owner_dispositions
        if row.owner_class is OwnerClass.REQUIRED
        and row.disposition not in positive_dispositions
    )
    visible_unknown = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if source.owner_obligation(row.owner_id).obligation_kind
        == "STRUCTURED_CONTEXT_ATTACHMENT"
        and (
            row.disposition is SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
            or row in unresolved_required
        )
    )
    if any(row.owner_id not in set(visible_unknown) for row in unresolved_required):
        raise CMEEVerticalError("required_unknown_not_safely_visible")
    required_unknown = tuple(
        row.owner_id for row in unresolved_required
    )
    source_plan_version = _source_plan_binding_version(
        grounded_plan,
        required_nucleus_ids,
        required_relation_ids,
        reception_target_ids,
    )
    reception_target_owners = _ordered(
        _owner_for_nucleus(source, nucleus_index[row_id])
        for row_id in reception_target_ids
    )
    required_owner_set = {
        *graph.required_owner_refs,
        *reception_target_owners,
    }
    required_observation_owners = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.owner_id in required_owner_set
        and row.disposition in positive_dispositions
    )
    if not set(required_observation_owners + reception_target_owners).issubset(set(visible)):
        raise CMEEVerticalError("experience_plan_visible_owner_mismatch")
    reception_resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    reception_plan_digest, allowed_reception_act_ids = _reception_plan_contract(
        grounded_plan,
        reception_resolver,
    )
    return ExperiencePlan(
        plan_id=_stable_id(
            "plan",
            source.envelope.envelope_id,
            graph.graph_id,
            source_plan_version,
            *required_observation_owners,
            *reception_target_owners,
        ),
        source_envelope_id=source.envelope.envelope_id,
        source_version=graph.source_version,
        obligation_version=graph.obligation_version,
        owner_universe_digest=graph.owner_universe_digest,
        source_plan_version=source_plan_version,
        observation_duty_id=OBSERVATION_DUTY_ID,
        unknown_duty_id=UNKNOWN_DUTY_ID,
        reception_duty_id=RECEPTION_DUTY_ID,
        reception_plan_digest=reception_plan_digest,
        allowed_reception_act_ids=allowed_reception_act_ids,
        required_observation_owner_ids=required_observation_owners,
        reception_target_owner_ids=reception_target_owners,
        visible_owner_ids=visible,
        unresolved_owner_ids=unresolved,
        visible_unknown_owner_ids=visible_unknown,
        required_unknown_owner_ids=required_unknown,
        visible_line_ids=(),
    )


def _cmee_rr4_aggregate_support_exact(
    reception_plan: Any,
    *,
    nucleus_index: Mapping[str, Any],
) -> bool:
    """Check the adapter-only RR4 selected-Move aggregate closure."""

    target_ids = tuple(reception_plan.target_nucleus_ids)
    support_ids = tuple(reception_plan.support_nucleus_ids)
    moves = tuple(reception_plan.moves)
    if not target_ids or not support_ids or not moves:
        return False
    move_nucleus_ids = _ordered(
        nucleus_id
        for move in moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    )
    move_nucleus_set = set(move_nucleus_ids)
    expected_support_ids = tuple(
        nucleus_id
        for nucleus_id in move_nucleus_ids
        if nucleus_id not in set(target_ids)
    )
    aggregate_nucleus_ids = _ordered((*target_ids, *support_ids))
    return (
        support_ids == expected_support_ids
        and set(aggregate_nucleus_ids)
        == set(target_ids) | move_nucleus_set
        and set(aggregate_nucleus_ids).issubset(
            set(reception_plan.observation_owned_nucleus_ids)
        )
        and all(
            nucleus_id in nucleus_index
            for nucleus_id in aggregate_nucleus_ids
        )
    )


def _cmee_target_self_evidences_retained_intention(
    reception_plan: Any,
    *,
    nucleus_index: Mapping[str, Any],
    resolver: Any,
) -> bool:
    """Accept an exact source-stated intention without invented support.

    ``operator:value`` is also used for open deliberation.  Such a target
    still needs a separate source-stated desire, while a target that already
    is that desire must not be forced to borrow an unrelated support row.
    """

    target_ids = tuple(reception_plan.target_nucleus_ids)
    if len(target_ids) != 1 or tuple(reception_plan.support_nucleus_ids):
        return False
    nucleus = nucleus_index.get(target_ids[0])
    if nucleus is None:
        return False
    frame = nucleus.semantic_frame
    attributes = frozenset(frame.attribute_codes)
    retained_intention = bool(
        nucleus.kind == "wish"
        or frame.modality in {"wish", "intention"}
        or "semantic_role:retained_intention" in attributes
    )
    source_explicit = str(nucleus.grounding_kind) == "explicit"
    target_span_set = set(nucleus.source_span_ids)
    exact_target_evidence = tuple(
        span_id
        for span_id in resolver.span_ids
        if span_id in target_span_set
    )
    if (
        not target_span_set
        or set(exact_target_evidence) != target_span_set
        or tuple(reception_plan.source_evidence_span_ids)
        != exact_target_evidence
    ):
        return False
    source_text = _cmee_source_text(nucleus, resolver)
    open_deliberation = bool(
        nucleus.kind == "uncertainty"
        or frame.modality == "uncertain"
        or "operator:uncertainty" in attributes
        or "semantic_role:limiting_unknown" in attributes
        or _cmee_parse_open_question_shape(source_text) is not None
    )
    nonnegated = bool(
        str(frame.polarity) != "negative"
        and "operator:negation" not in attributes
        and not NEGATED_DESIRE_RE.search(source_text)
    )
    return bool(
        retained_intention
        and source_explicit
        and not open_deliberation
        and nonnegated
    )


def _cmee_semantic_reception_plan(
    grounded_plan: Any,
    resolver: Any,
    *,
    material_quality: str = CMEE_RECEPTION_MATERIAL_MODE,
) -> Any:
    """Project the existing target into a polarity-strict CMEE reception plan.

    The legacy short-state compatibility policy intentionally collapses every
    one-span target to current burden.  CMEE keeps the source-selected target
    and evidence unchanged, but asks the existing semantic selector to choose
    the act from that target rather than from the short-input compatibility
    bucket.  This is a private adapter projection; it does not mutate or
    reclassify ``GroundedObservationPlan.input_profile``.
    """

    response_plan = grounded_plan.response_plan
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    reception_plan = build_grounded_human_reception_plan(
        required=grounded_plan.coverage_requirements.human_follow_required,
        human_follow_target_ids=response_plan.human_follow_target_ids,
        primary_nucleus_ids=response_plan.primary_nucleus_ids,
        supporting_nucleus_ids=response_plan.supporting_nucleus_ids,
        required_nucleus_ids=response_plan.required_nucleus_ids,
        fact_boundary_nucleus_ids=response_plan.fact_boundary_nucleus_ids,
        nuclei=grounded_plan.nuclei,
        relations=grounded_plan.relations,
        safety_kind=grounded_plan.safety_policy.safety_kind,
        material_quality=material_quality,
        semantic_complexity=grounded_plan.input_profile.semantic_complexity,
    )
    if reception_plan is None or not reception_plan.required:
        raise CMEEVerticalError("bound_human_reception_plan_missing")

    # A retained-intention target that consists of uncertainty plus an actual
    # thinking action cannot itself supply the content of the intention.  Bind
    # the request-local observation support as evidence for that content so
    # Stage 1 can keep desire, current action, and result separate.
    semantic_support_ids: tuple[str, ...] = ()
    generic_relation_support_bound = False
    rr4_aggregate_support_bound = False
    initial_support_ids = tuple(reception_plan.support_nucleus_ids)
    if initial_support_ids:
        selected_relation_endpoint_ids = _ordered(
            (
                *reception_plan.target_nucleus_ids,
                *initial_support_ids,
            )
        )
        selected_relation_endpoint_set = frozenset(
            selected_relation_endpoint_ids
        )
        typed_relation_rows = tuple(
            relation
            for relation in grounded_plan.relations
            if (
                relation.source_relation_ids
                == ("typed_projection:top_level_connective",)
                or (
                    str(relation.type) == "action_supports_change"
                    and relation.source_relation_ids
                    == (
                        "typed_projection:"
                        "perfective_action_before_bounded_change",
                    )
                )
            )
            and frozenset(
                (
                    relation.from_nucleus_id,
                    relation.to_nucleus_id,
                )
            )
            == selected_relation_endpoint_set
        )
        selected_relation_nuclei = tuple(
            nucleus_index[row_id]
            for row_id in selected_relation_endpoint_ids
            if row_id in nucleus_index
        )
        # A generic exact2 relation is already a source-bound semantic unit.
        # Its second endpoint may therefore support the selected reception
        # move without becoming new evidence or a family-specific bridge.
        # All other support shapes retain the pre-existing fail-closed check.
        if (
            len(initial_support_ids) == 1
            and len(selected_relation_endpoint_ids) == 2
            and len(typed_relation_rows) == 1
            and len(selected_relation_nuclei) == 2
            and len(
                {
                    tuple(row.source_span_ids)
                    for row in selected_relation_nuclei
                }
            )
            == 1
            and all(
                "semantic_role:generic_relation_fragment"
                in set(row.semantic_frame.attribute_codes)
                for row in selected_relation_nuclei
            )
        ):
            semantic_support_ids = initial_support_ids
            generic_relation_support_bound = True
            move_endpoint_set = {
                row_id
                for move in reception_plan.moves
                for row_id in (
                    *move.target_nucleus_ids,
                    *move.support_nucleus_ids,
                )
            }
            # A single burden Move may have been selected from the support
            # endpoint while the stable public follow target is the other
            # endpoint.  Retarget that exact-one opportunity without changing
            # its act; multi-Move plans already cover both relation endpoints.
            if not set(reception_plan.target_nucleus_ids).issubset(
                move_endpoint_set
            ):
                if (
                    len(reception_plan.moves) != 1
                    or len(reception_plan.opportunities) != 1
                ):
                    raise CMEEVerticalError(
                        "bound_human_reception_relation_support_invalid"
                    )
                selected_evidence_set = {
                    source_span_id
                    for row_id in selected_relation_endpoint_ids
                    for source_span_id in nucleus_index[row_id].source_span_ids
                }
                selected_evidence_ids = tuple(
                    source_span_id
                    for source_span_id in resolver.span_ids
                    if source_span_id in selected_evidence_set
                )
                selected_source_field_count = len(
                    {
                        field
                        for row_id in selected_relation_endpoint_ids
                        for field in nucleus_index[row_id].source_fields
                    }
                )
                reception_plan = replace(
                    reception_plan,
                    opportunities=tuple(
                        replace(
                            opportunity,
                            target_nucleus_ids=reception_plan.target_nucleus_ids,
                            support_nucleus_ids=semantic_support_ids,
                            source_evidence_span_ids=selected_evidence_ids,
                            source_field_count=selected_source_field_count,
                        )
                        for opportunity in reception_plan.opportunities
                    ),
                    moves=tuple(
                        replace(
                            move,
                            target_nucleus_ids=reception_plan.target_nucleus_ids,
                            support_nucleus_ids=semantic_support_ids,
                            source_evidence_span_ids=selected_evidence_ids,
                        )
                        for move in reception_plan.moves
                    ),
                    source_evidence_span_ids=selected_evidence_ids,
                )
        if (
            not generic_relation_support_bound
            and not validate_grounded_human_reception_plan(
                reception_plan,
                expected_target_ids=tuple(
                    response_plan.human_follow_target_ids
                ),
                nucleus_index=nucleus_index,
                resolver=resolver,
                safety_kind=grounded_plan.safety_policy.safety_kind,
                material_quality=material_quality,
            )
            and _cmee_rr4_aggregate_support_exact(
                reception_plan,
                nucleus_index=nucleus_index,
            )
        ):
            semantic_support_ids = tuple(
                reception_plan.support_nucleus_ids
            )
            rr4_aggregate_support_bound = True
    initial_acts = _ordered(move.reception_act for move in reception_plan.moves)
    target_has_value_operator = any(
        "operator:value" in set(nucleus_index[row_id].semantic_frame.attribute_codes)
        for row_id in reception_plan.target_nucleus_ids
        if row_id in nucleus_index
    )
    if (
        "protect_retained_intention" in initial_acts
        and target_has_value_operator
        and not reception_plan.support_nucleus_ids
        and not _cmee_target_self_evidences_retained_intention(
            reception_plan,
            nucleus_index=nucleus_index,
            resolver=resolver,
        )
    ):
        semantic_support_ids = tuple(
            row_id
            for row_id in response_plan.supporting_nucleus_ids
            if row_id in nucleus_index
            and row_id not in set(reception_plan.target_nucleus_ids)
            and not NEGATED_DESIRE_RE.search(
                _cmee_source_text(nucleus_index[row_id], resolver)
            )
            and _cmee_desire_phrase(
                _cmee_source_text(nucleus_index[row_id], resolver)
            )
        )[:1]
        if not semantic_support_ids:
            raise CMEEVerticalError(
                "bound_human_reception_retained_intention_evidence_missing"
            )
        if semantic_support_ids:
            selected_ids = _ordered(
                (*reception_plan.target_nucleus_ids, *semantic_support_ids)
            )
            selected_evidence_set = {
                source_span_id
                for row_id in selected_ids
                for source_span_id in nucleus_index[row_id].source_span_ids
            }
            selected_evidence_ids = tuple(
                source_span_id
                for source_span_id in resolver.span_ids
                if source_span_id in selected_evidence_set
            )
            selected_source_field_count = len(
                {
                    field
                    for row_id in selected_ids
                    for field in nucleus_index[row_id].source_fields
                }
            )
            reception_plan = replace(
                reception_plan,
                opportunities=tuple(
                    replace(
                        opportunity,
                        support_nucleus_ids=semantic_support_ids,
                        source_evidence_span_ids=selected_evidence_ids,
                        source_field_count=selected_source_field_count,
                    )
                    if opportunity.reception_act == "protect_retained_intention"
                    else opportunity
                    for opportunity in reception_plan.opportunities
                ),
                moves=tuple(
                    replace(
                        move,
                        support_nucleus_ids=semantic_support_ids,
                        source_evidence_span_ids=selected_evidence_ids,
                    )
                    if move.reception_act == "protect_retained_intention"
                    else move
                    for move in reception_plan.moves
                ),
                support_nucleus_ids=semantic_support_ids,
                source_evidence_span_ids=selected_evidence_ids,
            )
    expected_targets = tuple(response_plan.human_follow_target_ids)
    if reception_plan.target_nucleus_ids != expected_targets:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    if reception_plan.support_nucleus_ids != semantic_support_ids:
        raise CMEEVerticalError("bound_human_reception_support_not_supported")

    if any(row_id not in nucleus_index for row_id in reception_plan.target_nucleus_ids):
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    selected_nucleus_ids = _ordered(
        (*reception_plan.target_nucleus_ids, *reception_plan.support_nucleus_ids)
    )
    expected_evidence_set = {
        source_span_id
        for row_id in selected_nucleus_ids
        for source_span_id in nucleus_index[row_id].source_span_ids
    }
    expected_evidence_ids = tuple(
        source_span_id
        for source_span_id in resolver.span_ids
        if source_span_id in expected_evidence_set
    )
    if reception_plan.source_evidence_span_ids != expected_evidence_ids:
        raise CMEEVerticalError("bound_human_reception_source_evidence_mismatch")
    if not reception_plan.moves:
        raise CMEEVerticalError("bound_human_reception_move_missing")
    if generic_relation_support_bound:
        move_endpoint_ids = {
            row_id
            for move in reception_plan.moves
            for row_id in (
                *move.target_nucleus_ids,
                *move.support_nucleus_ids,
            )
        }
        if move_endpoint_ids != set(selected_nucleus_ids):
            raise CMEEVerticalError(
                "bound_human_reception_move_binding_mismatch"
            )
    elif rr4_aggregate_support_bound:
        if not _cmee_rr4_aggregate_support_exact(
            reception_plan,
            nucleus_index=nucleus_index,
        ):
            raise CMEEVerticalError(
                "bound_human_reception_move_binding_mismatch"
            )
    elif any(
        move.target_nucleus_ids != reception_plan.target_nucleus_ids
        or move.support_nucleus_ids != reception_plan.support_nucleus_ids
        or move.source_evidence_span_ids != reception_plan.source_evidence_span_ids
        for move in reception_plan.moves
    ):
        raise CMEEVerticalError("bound_human_reception_move_binding_mismatch")

    plan_issues = validate_grounded_human_reception_plan(
        reception_plan,
        expected_target_ids=expected_targets,
        nucleus_index=nucleus_index,
        resolver=resolver,
        safety_kind=grounded_plan.safety_policy.safety_kind,
        material_quality=material_quality,
    )
    if plan_issues:
        raise CMEEVerticalError("bound_human_reception_plan_invalid")

    def positive_act_is_compatible(
        act_id: str,
        target_nuclei: Sequence[Any],
    ) -> bool:
        return any(
            (
                act_id == "protect_retained_intention"
                and (
                    nucleus.kind == "wish"
                    or nucleus.semantic_frame.modality in {"wish", "intention"}
                    or "semantic_role:retained_intention"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            or (
                act_id == "recognize_lived_change"
                and (
                    nucleus.kind in {"change", "value"}
                    or "operator:positive_change"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            or (
                act_id == "hold_help_seeking"
                and "operator:help_seeking"
                in set(nucleus.semantic_frame.attribute_codes)
            )
            or (
                act_id == "honor_concrete_effort"
                and (
                    nucleus.kind == "action"
                    or "semantic_role:concrete_action_evidence"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            for nucleus in target_nuclei
        )

    if generic_relation_support_bound or rr4_aggregate_support_bound:
        for move in reception_plan.moves:
            move_target_nuclei = tuple(
                nucleus_index[row_id]
                for row_id in move.target_nucleus_ids
            )
            move_target_polarities = {
                str(nucleus.semantic_frame.polarity)
                for nucleus in move_target_nuclei
            }
            if (
                move_target_polarities == {"positive"}
                and move.reception_act in CMEE_BURDEN_RECEPTION_ACTS
            ):
                raise CMEEVerticalError(
                    "bound_human_reception_positive_burden_promotion"
                )
            if (
                move.reception_act in CMEE_POSITIVE_RECEPTION_ACTS
                and not positive_act_is_compatible(
                    move.reception_act,
                    move_target_nuclei,
                )
            ):
                raise CMEEVerticalError(
                    "bound_human_reception_target_act_semantic_mismatch"
                )
    else:
        target_polarities = {
            str(nucleus_index[row_id].semantic_frame.polarity)
            for row_id in reception_plan.target_nucleus_ids
        }
        act_ids = _ordered(move.reception_act for move in reception_plan.moves)
        if target_polarities == {"positive"} and CMEE_BURDEN_RECEPTION_ACTS.intersection(act_ids):
            raise CMEEVerticalError("bound_human_reception_positive_burden_promotion")
        target_nuclei = tuple(
            nucleus_index[row_id]
            for row_id in reception_plan.target_nucleus_ids
        )
        for act_id in CMEE_POSITIVE_RECEPTION_ACTS.intersection(act_ids):
            if positive_act_is_compatible(act_id, target_nuclei):
                continue
            raise CMEEVerticalError(
                "bound_human_reception_target_act_semantic_mismatch"
            )
    return reception_plan


def _cmee_source_anchor(nucleus: Any, resolver: Any) -> str:
    source = "".join(
        str(resolver.resolve(source_span_id).raw_text or "")
        for source_span_id in nucleus.source_span_ids
    )
    compact = re.sub(r"\s+", "", source).strip("、。！？!?「」『』")
    compact = re.sub(
        r"^(?:それでも|けれども?|でも|だけど|一方で|ただ|とはいえ|なのに)",
        "",
        compact,
    )
    # Keep a complete source-local phrase. Mid-clause head/tail splicing made
    # the visible Japanese unreadable and could change the source predicate.
    if len(compact) <= CMEE_SOURCE_ANCHOR_LIMIT:
        return compact
    return _cmee_natural_fragment(compact, limit=CMEE_SOURCE_ANCHOR_LIMIT)


def _cmee_nucleus_surface_label(nucleus: Any) -> str:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if nucleus.kind == "wish":
        return "保ちたい方向"
    if nucleus.kind == "constraint":
        return "前に進む際の制約"
    if nucleus.kind == "change" or "operator:positive_change" in attributes:
        return "前向きな変化"
    if nucleus.kind == "reaction":
        return (
            "負荷を伴う反応"
            if nucleus.semantic_frame.polarity == "negative"
            else "今の反応"
        )
    if nucleus.kind == "state":
        return (
            "負荷を伴う状態"
            if nucleus.semantic_frame.polarity == "negative"
            else "今の状態"
        )
    return {
        "action": "入力内の行動",
        "self_evaluation": "現在の自己評価",
        "value": "大切にしている向き",
        "event": "入力内の出来事",
    }.get(str(nucleus.kind), "現在の意味")


def _cmee_source_reference(
    anchor: str,
    nucleus: Any,
    *,
    include_semantic_label: bool = False,
) -> str:
    semantic_label = _cmee_nucleus_surface_label(nucleus)
    if not anchor:
        return f"{semantic_label}に関する記述"
    reference = f"「{anchor}」という記述"
    return (
        f"{reference}にある{semantic_label}"
        if include_semantic_label
        else reference
    )


def _cmee_source_text(nucleus: Any, resolver: Any) -> str:
    text = "".join(
        str(resolver.resolve(source_span_id).raw_text or "")
        for source_span_id in nucleus.source_span_ids
    )
    return re.sub(r"\s+", " ", text).strip().strip("、。！？!?「」『』 ")


def _cmee_split_contrast(text: str) -> tuple[str, str] | None:
    match = re.match(
        r"^(.+?)(?:けれども?|けど|なのに|のに|だけど|でも|一方で|ただ)(?:、)?(.+)$",
        str(text or "").strip(),
    )
    if not match:
        return None
    left = match.group(1).strip("、。 ")
    right = match.group(2).strip("、。 ")
    return (left, right) if left and right else None


def _cmee_has_current_burden(text: str) -> bool:
    """Recognize a current burden cue while preserving explicit negation."""

    value = re.sub(r"\s+", "", str(text or ""))
    current_only = NONCURRENT_BURDEN_RE.sub("", value)
    return bool(
        SOURCE_BURDEN_CUE_RE.search(current_only)
        or SOURCE_BURDEN_EXTRA_RE.search(current_only)
    )


def _stage1_v2_typed_unfinished_scope_supported(grounded_plan: Any) -> bool:
    """Accept only final-plan current-user unfinished predicates as scoped."""

    if FINAL_STAGE1_GROUNDED_PROJECTION_VERSION not in tuple(
        getattr(grounded_plan, "source_contracts", ())
    ):
        return False
    typed_candidates = tuple(
        nucleus
        for nucleus in tuple(getattr(grounded_plan, "nuclei", ()))
        if (
            str(getattr(nucleus, "kind", "")) == "uncertainty"
            or str(
                getattr(
                    getattr(nucleus, "semantic_frame", None),
                    "predicate_kind",
                    "",
                )
            )
            == "unfinished"
            or "operator:unfinished"
            in set(
                getattr(
                    getattr(nucleus, "semantic_frame", None),
                    "attribute_codes",
                    (),
                )
            )
        )
    )
    required_codes = {
        "operator:uncertainty",
        "operator:unfinished",
        "semantic_role:present_unfinished",
    }
    return bool(typed_candidates) and all(
        str(getattr(nucleus, "kind", "")) == "uncertainty"
        and bool(tuple(getattr(nucleus, "source_span_ids", ())))
        and str(getattr(nucleus, "grounding_kind", "")) == "explicit"
        and str(getattr(nucleus.semantic_frame, "actor", "")) == "current_user"
        and str(getattr(nucleus.semantic_frame, "predicate_kind", ""))
        == "unfinished"
        and str(getattr(nucleus.semantic_frame, "modality", "")) == "uncertain"
        and str(getattr(nucleus.semantic_frame, "time_scope", "")) == "present"
        and required_codes.issubset(
            set(getattr(nucleus.semantic_frame, "attribute_codes", ()))
        )
        for nucleus in typed_candidates
    )


def _stage1_v2_typed_exclusive_focus_scope_supported(
    text: str,
    grounded_plan: Any,
) -> bool:
    """Admit only a final-plan typed owner for one bounded exclusive role."""

    if FINAL_STAGE1_GROUNDED_PROJECTION_VERSION not in tuple(
        getattr(grounded_plan, "source_contracts", ())
    ):
        return False
    if not _cmee_bounded_exclusive_focus_role(text):
        return False
    return any(
        _cmee_typed_exclusive_focus_role_owner(nucleus)
        for nucleus in tuple(getattr(grounded_plan, "nuclei", ()))
    )


def _cmee_assert_current_first_person_scope_supported(
    text: str,
    grounded_plan: Any,
    *,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
) -> None:
    """Fail closed when Stage 1 cannot safely bind experiencer or time scope."""

    _stage1_runtime_contract(stage1_response_schema_version)
    value = re.sub(r"\s+", "", str(text or ""))
    typed_v2_unfinished_scope = (
        stage1_response_schema_version
        == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        and _stage1_v2_typed_unfinished_scope_supported(grounded_plan)
    )
    typed_v2_exclusive_focus_scope = (
        stage1_response_schema_version
        == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        and _stage1_v2_typed_exclusive_focus_scope_supported(
            value,
            grounded_plan,
        )
    )
    exclusive_focus_role = (
        _cmee_bounded_exclusive_focus_role(value)
        if typed_v2_exclusive_focus_scope
        else ""
    )
    explicit_whole_state_negation = EXPLICIT_WHOLE_STATE_NEGATION_RE.search(
        value.strip("、。！？!?「」『』 ")
    )
    # Preserve the existing scope-classifier precedence for a negation that
    # is itself inside an uncertainty, deontic, nonfactive, or historical
    # construction.  The finite standalone noun/adjective/verb morphology
    # family below is otherwise rejected with its role-specific reason before
    # a positive state can be compiled.
    legacy_scope_preempts_negation = bool(
        any(
            pattern.search(value)
            for pattern in (
                UNKNOWN_OR_INTERROGATIVE_STATE_OR_DESIRE_RE,
                DEONTIC_STATE_OR_DESIRE_RE,
                NONFACTIVE_STATE_OR_DESIRE_RE,
                NOMINALIZED_PAST_STATE_RE,
            )
        )
        or re.search(
            r"(?:少しも|全く|まったく|全然|一切)"
            r"(?:ない|なかった|ありません(?:でした)?)",
            value,
        )
        or re.search(
            r"(?:不安|心配|疲れ|つらさ|苦しさ|しんどさ|悲しさ|"
            r"怒り|怖さ|限界|痛み)(?:は|が|を)?感じてい"
            r"(?:ない|なかった|ません(?:でした)?)",
            value,
        )
        or re.search(
            r"(?:たら|だら|なら)[^。！？!?]{1,32}か(?:どうか)?"
            r"(?:覚えていない|分からない|わからない)",
            value,
        )
    )
    if (
        explicit_whole_state_negation
        and not legacy_scope_preempts_negation
        and not typed_v2_exclusive_focus_scope
    ):
        raise CMEEVerticalError("lexical_role_negation_unrepresentable")
    for pattern in (
        GENERIC_EXPERIENCER_APPEARANCE_RE,
        GENERIC_EXPERIENCER_REPORTED_DESIRE_RE,
        GENERIC_OTHER_THEN_FIRST_PERSON_RE,
        GENERIC_EXPERIENCER_STATE_OR_DESIRE_RE,
        GENERIC_EXPERIENCER_ATTRIBUTION_RE,
        GENERIC_OTHER_SOURCE_BEFORE_CUE_RE,
        GENERIC_POSSESSIVE_EXPERIENCER_RE,
        GENERIC_AFFECTED_OBJECT_RE,
        GENERIC_AFFECTED_DATIVE_RE,
        GENERIC_BARE_OTHER_EXPERIENCER_RE,
        ATTRIBUTIVE_OTHER_EXPERIENCER_RE,
        POSTPOSED_EXPERIENCER_RE,
        QUOTED_OR_MARKED_OTHER_OWNERSHIP_RE,
        QUOTED_OTHER_AUTHOR_RE,
        OTHER_SOURCE_LABEL_PREFIX_RE,
        PARENTHETICAL_OTHER_SOURCE_RE,
        PARENTHETICAL_SOURCE_LABEL_RE,
        RELATIVE_CLAUSE_OTHER_EXPERIENCER_RE,
    ):
        for match in pattern.finditer(value):
            subject = str(match.group("subject") or "")
            if any(
                subject.endswith(first_person)
                for first_person in FIRST_PERSON_SUBJECTS
            ):
                continue
            if (
                pattern is GENERIC_EXPERIENCER_STATE_OR_DESIRE_RE
                and exclusive_focus_role
                and subject.endswith(("とき", "時", "場合", "頃"))
                and match.end() > value.find(exclusive_focus_role)
            ):
                # A temporal subordinate ending immediately before the exact
                # focus clause is context, not an experiencer attribution.
                continue
            if (
                pattern is GENERIC_EXPERIENCER_STATE_OR_DESIRE_RE
                and (
                    subject in SAFE_NONPERSON_TOPIC_EXACT
                    or any(
                        safe_pattern.fullmatch(subject)
                        for safe_pattern in SAFE_NONPERSON_TOPIC_PATTERNS
                    )
                    or (
                        typed_v2_unfinished_scope
                        and subject == "まだ気持ち"
                        and match.group(0).endswith("どうしたい")
                    )
                )
            ):
                continue
            raise CMEEVerticalError(
                "current_experiencer_or_time_scope_unsupported"
            )
    scope_forbidden_patterns = (
        OTHER_EXPERIENCER_BURDEN_REPORT_RE,
        OTHER_EXPERIENCER_BURDEN_RE,
        OTHER_EXPERIENCER_DESIRE_RE,
        QUOTED_OTHER_REPORT_RE,
        REPORTED_EXTERNAL_APPEARANCE_RE,
        UNBOUND_EPISTEMIC_STATE_OR_DESIRE_RE,
        UNBOUND_REPORTED_STATE_OR_DESIRE_RE,
        UNBOUND_REPORT_OR_EPISTEMIC_WINDOW_RE,
        DIRECT_UNCERTAIN_STATE_OR_DESIRE_RE,
        EXTERNAL_ASCRIPTION_RE,
        CONDITIONAL_STATE_OR_DESIRE_RE,
        UNKNOWN_OR_INTERROGATIVE_STATE_OR_DESIRE_RE,
        FUTURE_OR_POTENTIAL_STATE_RE,
        RETRACTED_STATE_OR_DESIRE_RE,
        SEMANTIC_NEGATION_STATE_OR_DESIRE_RE,
        NOMINALIZED_PAST_STATE_RE,
        METALINGUISTIC_STATE_OR_DESIRE_MENTION_RE,
        GENERIC_PROPOSITION_RE,
        DIRECTIVE_STATE_OR_DESIRE_RE,
        DIRECT_QUESTION_STATE_OR_DESIRE_RE,
        NONFACTIVE_STATE_OR_DESIRE_RE,
        DEONTIC_STATE_OR_DESIRE_RE,
        EMPTY_CLASS_DESIRE_RE,
        LEXICAL_FALSE_CUE_RE,
        NEGATED_DESIDERATIVE_BURDEN_RE,
        HABITUAL_OR_DISPOSITIONAL_STATE_RE,
        NONEXPERIENTIAL_STATE_THEME_RE,
        NEGATED_OR_RESOLVED_BURDEN_WINDOW_RE,
        RESOLVED_DESIRE_RE,
        FUTURE_HYPOTHETICAL_BURDEN_RE,
        FUTURE_HYPOTHETICAL_DESIRE_RE,
        PAST_DESIRE_WITH_CURRENT_SCOPE_RE,
    )
    matched_scope_patterns = tuple(
        pattern for pattern in scope_forbidden_patterns if pattern.search(value)
    )
    typed_v2_unfinished = (
        typed_v2_unfinished_scope
        and matched_scope_patterns == (
            UNKNOWN_OR_INTERROGATIVE_STATE_OR_DESIRE_RE,
        )
    )
    if matched_scope_patterns and not typed_v2_unfinished:
        raise CMEEVerticalError("current_experiencer_or_time_scope_unsupported")
    change_parts = _cmee_change_parts(value)
    change_result = change_parts[2] if change_parts else ""
    has_source_bound_positive_change = any(
        str(getattr(nucleus.semantic_frame, "actor", "") or "")
        == "current_user"
        and "operator:positive_change"
        in set(nucleus.semantic_frame.attribute_codes)
        for nucleus in grounded_plan.nuclei
    )
    completed_factual_change = bool(
        change_parts
        and COMPLETED_FACTUAL_CHANGE_RESULT_RE.fullmatch(change_result)
    )
    if (
        change_parts
        and has_source_bound_positive_change
        and not completed_factual_change
    ):
        raise CMEEVerticalError("current_experiencer_or_time_scope_unsupported")
    source_bound_actual_change = bool(
        completed_factual_change
        and has_source_bound_positive_change
    )
    if (
        PAST_BURDEN_OR_DESIRE_RE.search(value)
        or PAST_TO_CURRENT_SCOPE_RE.search(value)
        or PAST_STATE_OR_DESIRE_MORPHOLOGY_RE.search(value)
    ) and not any(
        str(relation.type) in DIRECTIONAL_GROUNDED_RELATION_TYPES
        for relation in grounded_plan.relations
    ) and not source_bound_actual_change:
        raise CMEEVerticalError("current_experiencer_or_time_scope_unsupported")


def _cmee_natural_fragment(text: str, *, limit: int = 28) -> str:
    value = re.sub(r"\s+", "", str(text or "")).strip("、。！？!?「」『』 ")
    value = re.sub(r"^(?:それでも|けれども?|でも|だけど|一方で|ただ|今日は)", "", value)
    if len(value) <= limit:
        return value
    candidates = tuple(
        part.strip("、。！？!? ")
        for part in re.split(
            r"[、。！？!?]+|(?:けれども?|だけど|一方で|とはいえ)",
            value,
        )
        if part.strip("、。！？!? ")
    )
    fitting = tuple(part for part in candidates if 2 <= len(part) <= limit)
    if fitting:
        return fitting[-1]
    desire_candidates = tuple(
        match[-limit:]
        for match in re.findall(r"[ぁ-んァ-ン一-龥ー]{1,32}たい", value)
        if len(match[-limit:]) >= 2
    )
    if desire_candidates:
        return desire_candidates[-1]
    # A generic complete referent is safer than exposing a broken source
    # clause. The full evidence remains bound in the private trace.
    return "今書かれたこと"


def _cmee_desire_phrase(text: str) -> str:
    value = re.sub(r"\s+", "", str(text or "")).strip("、。！？!?「」『』 ")
    candidates = tuple(re.finditer(r"[ぁ-んァ-ン一-龥ー]{1,22}たい", value))
    for candidate in reversed(candidates):
        tail = value[candidate.end() : candidate.end() + 16]
        if NEGATED_DESIRE_SUFFIX_RE.match(tail):
            continue
        phrase = candidate.group(0)
        for marker in ("けれど", "けど", "のに", "でも", "あと"):
            if marker in phrase:
                phrase = phrase.rsplit(marker, 1)[-1]
        return phrase[-22:]
    return ""


def _cmee_sentence_desire_phrase(desire: str) -> str:
    """Turn a source desire into a sentence object without objectifying I."""

    value = str(desire or "")
    first_person_pattern = "|".join(
        re.escape(subject)
        for subject in sorted(FIRST_PERSON_SUBJECTS, key=len, reverse=True)
    )
    value = re.sub(rf"^(?:{first_person_pattern})は", "", value)
    return re.sub(r"^(.{1,18})は(.+たい)$", r"\1を\2", value)


def _cmee_semantic_desire(nucleus: Any, text: str) -> str:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    allowed = (
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality in {"wish", "intention"}
        or "operator:wish" in attributes
        or "operator:continuation" in attributes
        or {"operator:contrast", "operator:negation"}.issubset(attributes)
    )
    if not allowed:
        return ""
    if NEGATED_DESIRE_RE.search(str(text or "")):
        return ""
    desire = _cmee_desire_phrase(text)
    if desire.endswith("みたい") and "operator:wish" not in attributes:
        return ""
    return desire


def _cmee_source_state_phrase(text: str) -> str:
    """Return a source-only state reference without adding a sensation label."""

    value = re.sub(r"\s+", "", str(text or "")).strip("、。！？!?「」『』 ")
    if not _cmee_has_current_burden(value) and (
        SOURCE_BURDEN_CUE_RE.search(value)
        or SOURCE_BURDEN_EXTRA_RE.search(value)
    ):
        return f"「{_cmee_natural_fragment(value, limit=24)}」という状態"
    if re.search(r"(?:なくて|られなくて).*(?:疲|つら|苦し|しんど)", value):
        return f"「{_cmee_natural_fragment(value, limit=28)}」という状態"
    for cue, noun in (
        ("つら", "つらさ"),
        ("苦し", "苦しさ"),
        ("しんど", "しんどさ"),
        ("痛", "痛み"),
        ("不安", "不安"),
        ("疲", "疲れ"),
    ):
        if cue in value:
            context = value.split(cue, 1)[0].rstrip("がはをにで、")
            if 2 <= len(context) <= 14:
                if context.endswith("て"):
                    return f"{context}いる中で感じている{noun}"
                return f"「{context}」について感じている{noun}"
            return f"いま感じている{noun}"
    return f"「{_cmee_natural_fragment(text, limit=12)}」という状態"


def _cmee_refusal_state_text(text: str) -> str:
    """Naturalize an explicit present refusal without adding a diagnosis."""

    value = re.sub(r"\s+", "", str(text or "")).strip("、。！？!? ")
    match = re.match(r"^(.+?)し(.+?(?:たくない|できない|したくない))$", value)
    if not match:
        return f"いまは、「{_cmee_natural_fragment(value, limit=24)}」という状態です。"
    first = match.group(1)
    second = match.group(2)
    state_noun = {
        "だるい": "だるさ",
        "つらい": "つらさ",
        "しんどい": "しんどさ",
        "苦しい": "苦しさ",
    }.get(first)
    if state_noun:
        return f"いまは、{state_noun}があり、{second}状態です。"
    return f"いまは、「{first}」という状態と、{second}状態が重なっています。"


def _cmee_change_parts(text: str) -> tuple[str, str, str] | None:
    """Return source-stated before/action/result parts without inferring cause."""

    compact = re.sub(r"\s+", "", str(text or ""))
    if compact and ord(compact[-1]) in {0xFF1F, 0x003F, 0xFF01, 0x0021}:
        return None
    value = compact.strip("、。！？!?「」『』 ")
    parsed = _cmee_parse_action_change_shape(value)
    if parsed is None:
        return None
    before, action, result = parsed
    before = re.sub(r"^今日は", "", before).strip("、。 ")
    return (before, action, result) if before and action and result else None


def _cmee_polite_source_clause(text: str) -> str:
    """Apply only terminal-form normalization to a source-local clause."""

    value = re.sub(r"\s+", "", str(text or "")).strip("、。！？!? ")
    for pattern, replacement in (
        (r"ている$", "ています"),
        (r"でいる$", "でいます"),
        (r"がある$", "があります"),
        (r"もある$", "もあります"),
    ):
        if re.search(pattern, value):
            return re.sub(pattern, replacement, value)
    return value + "と書かれています"


def _cmee_nucleus_observation_text(nucleus: Any, resolver: Any) -> str:
    source_text = _cmee_source_text(nucleus, resolver)
    attributes = set(nucleus.semantic_frame.attribute_codes)
    desire = _cmee_semantic_desire(nucleus, source_text)
    contrast = _cmee_split_contrast(source_text)
    source_fields = {
        str(getattr(resolver.resolve(source_span_id), "source_field", "") or "")
        for source_span_id in nucleus.source_span_ids
    }

    if "emotion_details" in source_fields:
        return f"選ばれた気持ちの詳細には「{source_text}」とあります。"
    if "emotions" in source_fields:
        return f"気持ちの一覧にも「{source_text}」が含まれています。"
    if "category" in source_fields:
        return f"記録のカテゴリには「{source_text}」が選ばれています。"

    if "operator:help_seeking" in attributes:
        if contrast:
            left, right = contrast
            left_desire = _cmee_semantic_desire(nucleus, left)
            right_desire = _cmee_semantic_desire(nucleus, right)
            if not left_desire and not right_desire:
                raise CMEEVerticalError(
                    "plan_bound_observation_semantic_desire_mismatch"
                )
            desire_side = left if left_desire else right
            hesitation_side = right if desire_side == left else left
            return (
                f"「{_cmee_natural_fragment(desire_side)}」という気持ちに、"
                f"「{_cmee_natural_fragment(hesitation_side)}」というためらいが重なっています。"
            )
        return f"今の記録には、「{_cmee_natural_fragment(source_text, limit=36)}」とあります。"

    if "operator:positive_change" in attributes:
        change_parts = _cmee_change_parts(source_text)
        if change_parts:
            before, action, result = change_parts
            return (
                f"{before}あと、{action}ことがあり、"
                f"その後には「{result}」という変化があります。"
            )
        if contrast:
            return (
                f"「{_cmee_natural_fragment(contrast[0], limit=24)}」という状態のあとに、"
                f"「{_cmee_natural_fragment(contrast[1], limit=24)}」という変化があります。"
            )
        positive_event = re.match(r"^(.+?)て(.+?かった)$", source_text)
        if positive_event:
            return (
                f"{positive_event.group(1)}たことがあり、"
                f"そのときに「{positive_event.group(2)}」という変化があります。"
            )
        return f"「{source_text}」という変化が、今の記録にあります。"

    if contrast:
        left, right = contrast
        left_raw_desire = _cmee_desire_phrase(left)
        right_raw_desire = _cmee_desire_phrase(right)
        left_desire = _cmee_semantic_desire(nucleus, left) or (
            left_raw_desire
            if left_raw_desire and not left_raw_desire.endswith("みたい")
            else ""
        )
        right_desire = _cmee_semantic_desire(nucleus, right) or (
            right_raw_desire
            if right_raw_desire and not right_raw_desire.endswith("みたい")
            else ""
        )
        if right_desire:
            return (
                f"{_cmee_source_state_phrase(left)}がありながら、"
                f"「{right_desire}」という気持ちもあります。"
            )
        if left_desire:
            return (
                f"「{left_desire}」という気持ちはある一方で、"
                f"{_cmee_source_state_phrase(right)}も同時にあります。"
            )

    if "operator:refusal" in attributes:
        return _cmee_refusal_state_text(source_text)
    if nucleus.kind in {"state", "reaction", "constraint"}:
        return f"いまは、{_cmee_source_state_phrase(source_text)}があります。"
    if nucleus.kind == "wish" and desire:
        visible_desire = _cmee_sentence_desire_phrase(desire)
        temporal = re.match(
            r"^(?:今日は)?(.+?(?:あと|後))[、,](.+)$",
            source_text,
        )
        if temporal:
            source_prefix = temporal.group(1).strip("、。 ")
            tail_clause = temporal.group(2).strip("、。 ")
            retained_pair = re.match(
                r"^(.+?たい)気持ちと(.+?)が残っている$",
                tail_clause,
            )
            if retained_pair:
                return (
                    f"{source_prefix}にも、{retained_pair.group(1)}気持ちがあり、"
                    f"{retained_pair.group(2)}も残っています。"
                )
            return f"{source_prefix}にも、{_cmee_polite_source_clause(tail_clause)}。"
        compact_source = re.sub(r"\s+", "", source_text)
        if len(compact_source) >= len(desire) + 9:
            return (
                f"「{visible_desire}」という気持ちだけでなく、"
                "その前後に書かれたことも、同じ今の記録にあります。"
            )
        return f"「{visible_desire}」という気持ちが、今の言葉の中にあります。"
    if nucleus.kind == "wish" and "operator:value" in attributes:
        uncertain_thought = re.match(
            r"^(?:ずっと)?(.+?)なのが不安で[、,](.+)$",
            source_text,
        )
        if uncertain_thought:
            uncertain_state = uncertain_thought.group(1).strip("、。 ")
            thought = uncertain_thought.group(2).strip("、。 ")
            thought = re.sub(r"いいのか考えている$", "よいかを考えています", thought)
            thought = re.sub(r"ている$", "ています", thought)
            return (
                f"{uncertain_state}かもしれないという不安の中で、"
                f"{thought}。"
            )
        return f"{_cmee_polite_source_clause(source_text)}。"
    anchor = _cmee_source_anchor(nucleus, resolver)
    if anchor:
        return f"「{anchor}」という出来事が、今の記録に残っています。"
    return "今の入力には、ひとつの具体的な出来事が記録されています。"


def _cmee_relation_observation_text(
    relation: Any,
    from_nucleus: Any,
    to_nucleus: Any,
    resolver: Any,
) -> str:
    from_text = _cmee_source_text(from_nucleus, resolver)
    to_text = _cmee_source_text(to_nucleus, resolver)
    relation_type = str(relation.type)
    from_desire = _cmee_semantic_desire(from_nucleus, from_text)
    to_desire = _cmee_semantic_desire(to_nucleus, to_text)

    if relation_type == "contrast":
        if to_desire:
            return (
                f"{_cmee_source_state_phrase(from_text)}がある一方で、"
                f"「{to_desire}」という気持ちもあります。"
            )
        if from_desire:
            return (
                f"「{from_desire}」という気持ちがあり、"
                f"それと同時に{_cmee_source_state_phrase(to_text)}もあります。"
            )
        return (
            f"{_cmee_source_state_phrase(from_text)}と{_cmee_source_state_phrase(to_text)}が、"
            "同時にあります。"
        )
    if relation_type == "preserves_despite":
        desire = to_desire or from_desire
        other_text = from_text if to_desire else to_text
        desire_text = desire or _cmee_natural_fragment(
            to_text if from_text == other_text else from_text,
            limit=24,
        )
        return (
            f"{_cmee_source_state_phrase(other_text)}がありながら、"
            f"「{desire_text}」という気持ちは残っています。"
        )
    if relation_type == "wish_and_constraint":
        desire = from_desire or to_desire
        if desire:
            return (
                f"「{desire}」という気持ちは、まだ実際にできたという結果ではなく、"
                "いま残っている願いです。"
            )
        return (
            "ここにある願いは、まだ実際にできたという結果ではなく、"
            "いま残っている気持ちです。"
        )
    if relation_type == "coexistence":
        return (
            f"「{_cmee_natural_fragment(from_text)}」と"
            f"「{_cmee_natural_fragment(to_text)}」が、同じ時点にあります。"
        )
    if relation_type in DIRECTIONAL_GROUNDED_RELATION_TYPES:
        return (
            f"「{_cmee_natural_fragment(from_text)}」のあとに"
            f"「{_cmee_natural_fragment(to_text)}」が起きたという順序です。"
        )
    return (
        f"「{_cmee_natural_fragment(from_text)}」と"
        f"「{_cmee_natural_fragment(to_text)}」が、一つの流れの中にあります。"
    )


def _cmee_stage1_reception_text(
    act_ids: Sequence[str],
    target_nuclei: Sequence[Any],
    resolver: Any,
) -> str:
    target_text = "。".join(
        _cmee_source_text(nucleus, resolver) for nucleus in target_nuclei
    )
    desire = next(
        (
            value
            for nucleus in target_nuclei
            if (value := _cmee_semantic_desire(
                nucleus,
                _cmee_source_text(nucleus, resolver),
            ))
        ),
        "",
    )
    acts = set(act_ids)
    attributes = {
        code
        for nucleus in target_nuclei
        for code in nucleus.semantic_frame.attribute_codes
    }
    primary_text = (
        _cmee_source_text(target_nuclei[0], resolver)
        if target_nuclei
        else target_text
    )
    contrast = _cmee_split_contrast(primary_text)
    sentence_desire = _cmee_sentence_desire_phrase(desire)

    if "hold_help_seeking" in acts:
        if not sentence_desire:
            raise CMEEVerticalError(
                "bound_human_reception_target_act_semantic_mismatch"
            )
        hesitation = "同時にあるためらい"
        if contrast:
            left, right = contrast
            hesitation = right if _cmee_desire_phrase(left) else left
            hesitation = f"{_cmee_natural_fragment(hesitation, limit=28)}というためらい"
        help_text = sentence_desire or "助けを求めたい"
        return (
            f"{help_text}という気持ちは、助けを求める大切な動きとして、"
            f"{hesitation}とは別に心に留めます。"
        )
    if "recognize_lived_change" in acts:
        change_parts = _cmee_change_parts(primary_text)
        if change_parts:
            _before, action, result = change_parts
            return (
                f"{action}あとに{result}という変化を、"
                "今回起きた一度のこととして見過ごさず、静かに喜びます。"
            )
        positive_event = re.match(r"^(.+?)て(.+?かった)$", primary_text)
        if positive_event:
            return (
                f"{positive_event.group(1)}たあとに{positive_event.group(2)}という変化を、"
                "今回起きた一度のこととして見過ごさず、静かに喜びます。"
            )
        return (
            "今回ここに書かれた変化を、一度の実感として"
            "軽いこととして流さず受け止めます。"
        )
    if "protect_retained_intention" in acts:
        if NEGATED_DESIRE_RE.search(primary_text) and not sentence_desire:
            raise CMEEVerticalError(
                "bound_human_reception_target_act_semantic_mismatch"
            )
        named_desire = (
            f"{sentence_desire}という願い"
            if sentence_desire
            else "今の考えに残っている願い"
        )
        if "operator:value" in attributes:
            supported_desire = next(
                (
                    _cmee_desire_phrase(_cmee_source_text(nucleus, resolver))
                    for nucleus in target_nuclei
                    if not NEGATED_DESIRE_RE.search(
                        _cmee_source_text(nucleus, resolver)
                    )
                    and _cmee_desire_phrase(
                        _cmee_source_text(nucleus, resolver)
                    )
                ),
                "",
            )
            if supported_desire:
                supported_sentence_desire = _cmee_sentence_desire_phrase(
                    supported_desire
                )
                named_desire = f"{supported_sentence_desire}という願い"
            uncertain_thought = re.match(
                r"^(?:ずっと)?(.+?)なのが不安で[、,](.+)$",
                primary_text,
            )
            if uncertain_thought:
                uncertain_state = uncertain_thought.group(1).strip("、。 ")
                thought = uncertain_thought.group(2).strip("、。 ")
                thought = re.sub(r"いいのか考えている$", "よいか考えていること", thought)
                return (
                    f"{named_desire}を大切に受け止め、{thought}は、"
                    "その願いがまだ消えていない中で実際にしていることとして、"
                    "答えが出た結果とは分けて見守ります。"
                )
            return (
                f"{named_desire}を大切に受け止め、"
                "まだ実際に起きた結果と同じものにはしません。"
            )
        if "operator:shift" in attributes:
            companion = "同時に残っている感覚"
            if desire:
                companion_match = re.search(
                    rf"{re.escape(desire)}(?:という)?気持ちと(.+?)が残",
                    primary_text,
                )
                if companion_match:
                    companion = companion_match.group(1).strip("、。 ")
            return (
                f"{named_desire}を大切にし、{companion}が残っている今を、"
                "急いで片づけずに見守ります。"
            )
        if "operator:contrast" in attributes:
            other_state = "同時にある状態"
            if contrast:
                left, right = contrast
                other_text = right if _cmee_desire_phrase(left) else left
                other_state = _cmee_source_state_phrase(other_text).translate(
                    str.maketrans("", "", "「」")
                )
            return (
                f"{named_desire}を、{other_state}と並んでいる大切な気持ちとして、"
                "そのまま受け取ります。"
            )
        return (
            f"{named_desire}を、今ここで言葉になった"
            "大切な気持ちとして、丁寧に受け取ります。"
        )
    if "stay_with_current_burden" in acts:
        if not _cmee_has_current_burden(primary_text):
            raise CMEEVerticalError(
                "bound_human_reception_target_act_semantic_mismatch"
            )
        if desire and "operator:negation" in attributes:
            burden_text = primary_text
            if contrast:
                left, right = contrast
                burden_text = right if _cmee_desire_phrase(left) else left
            return (
                f"{burden_text}という負荷を小さくせず、"
                "その重さに静かに目を留めます。"
            )
        if "detected_type:limit_signal" in attributes:
            tentative_state = _cmee_source_state_phrase(primary_text).translate(
                str.maketrans("", "", "「」")
            )
            if contrast:
                left, right = contrast
                state_text = right if _cmee_desire_phrase(left) else left
                state_core = _cmee_tentative_state_core(state_text)
                tentative_state = (
                    f"{state_core}と感じていること"
                    if state_core
                    else state_text
                )
            wish_prefix = f"{sentence_desire}という気持ちと、" if sentence_desire else ""
            if not wish_prefix:
                return (
                    f"{tentative_state}にある負荷を小さくせず、"
                    "その重さに静かに目を留めます。"
                )
            return (
                f"{re.sub(r'こと$', '', tentative_state)}、"
                "その感覚にある負荷を軽く扱わず、"
                "今の言葉としてそのまま受け取ります。"
            )
        return "ここに書かれた負荷を小さくせず、今置かれた言葉を軽く扱いません。"
    return "ここに置かれた言葉を軽く扱わず、そのまま大切に受け止めます。"


def _cmee_structured_attachment_unknown_text(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
) -> tuple[str, tuple[str, ...]]:
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    text_by_span = {
        str(getattr(row, "span_id", "") or ""): str(
            getattr(row, "raw_text", "") or ""
        ).strip()
        for row in source.evidence_spans
    }
    categories: list[str] = []
    emotions: list[str] = []
    focus_rows: list[tuple[str, str]] = []
    for ref in source.evidence_refs:
        if ref.field_path not in {"memo", "memo_action"}:
            continue
        raw_text = text_by_span.get(ref.source_span_id, "")
        if not raw_text:
            continue
        contrast = _cmee_split_contrast(raw_text)
        parts = contrast or tuple(
            part.strip("、。 ")
            for part in re.split(r"[。！？!?]+", raw_text)
            if part.strip("、。 ")
        )
        for part in parts:
            fragment = _cmee_natural_fragment(part, limit=14)
            if fragment and all(fragment != existing for existing, _span_id in focus_rows):
                focus_rows.append((fragment, ref.source_span_id))
    for owner_id in plan.visible_unknown_owner_ids:
        for source_span_id in source.owner_obligation(owner_id).source_span_ids:
            ref = ref_by_span.get(source_span_id)
            value = text_by_span.get(source_span_id, "")
            field_path = str(getattr(ref, "field_path", "") or "")
            if not value:
                continue
            if field_path.startswith("category.") and value not in categories:
                categories.append(value)
            elif (
                field_path.endswith(".type") or field_path.startswith("emotions.")
            ) and value not in emotions:
                emotions.append(value)
    focus_span_ids = _ordered(span_id for _text, span_id in focus_rows)
    if emotions and len(focus_rows) >= 2:
        first, second = focus_rows[0][0], focus_rows[-1][0]
        if emotions[0] in "".join(text for text, _span_id in focus_rows):
            return (
                f"本文にも「{emotions[0]}」とありますが、その言葉が"
                f"「{first}」だけに向くのか、「{second}」にも重なるのかまでは、"
                "今の記録からは読み切れません。",
                focus_span_ids,
            )
        return (
            f"選ばれた「{emotions[0]}」が、「{first}」と「{second}」の"
            "どちらに向くのか、両方に重なるのかまでは、"
            "今の記録からは読み切れません。",
            focus_span_ids,
        )
    if emotions:
        return (
            f"選ばれた「{emotions[0]}」と、本文に書かれた今の状態のつながり方までは、"
            "今の記録からは読み切れません。",
            focus_span_ids,
        )
    if categories:
        return (
            f"選ばれた「{categories[0]}」と、ここに書かれた出来事のつながり方は、"
            "今の記録からは読み切れません。",
            focus_span_ids,
        )
    return STRUCTURED_ATTACHMENT_UNKNOWN_TEXT, focus_span_ids


def _canonical_r4_observation_lines(
    source: AdmittedTextSource,
    grounded_plan: Any,
    resolver: Any,
) -> tuple[_CMEEVisibleLine, ...]:
    """Build exact plan-bound observation duties without raw clause replay."""

    sentence_plan = build_grounded_sentence_plan(grounded_plan, resolver)
    required_nucleus_ids = tuple(
        grounded_plan.coverage_requirements.required_nucleus_ids
    )
    required_relation_ids = tuple(
        grounded_plan.coverage_requirements.required_relation_ids
    )
    if (
        sentence_plan.status != "generated"
        or sentence_plan.required_nucleus_ids != required_nucleus_ids
        or set(sentence_plan.covered_required_nucleus_ids) != set(required_nucleus_ids)
        or sentence_plan.required_relation_ids != required_relation_ids
        or set(sentence_plan.covered_required_relation_ids) != set(required_relation_ids)
        or sentence_plan.unresolved_evidence_span_ids
    ):
        raise CMEEVerticalError("grounded_sentence_plan_required_coverage_mismatch")

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    oracle_observation_lines = tuple(
        row for row in sentence_plan.lines if row.binding.line_role != "human_follow"
    )
    for relation_id in required_relation_ids:
        relation = relation_index.get(relation_id)
        owning_lines = tuple(
            row
            for row in oracle_observation_lines
            if relation_id in row.binding.relation_ids
        )
        if relation is None or not owning_lines:
            raise CMEEVerticalError("grounded_sentence_plan_relation_missing")
        expected_endpoints = {
            relation.from_nucleus_id,
            relation.to_nucleus_id,
        }
        expected_evidence = set(relation.source_span_ids)
        if any(
            not expected_endpoints.issubset(set(row.binding.nucleus_ids))
            or not expected_evidence.issubset(set(row.binding.evidence_span_ids))
            for row in owning_lines
        ):
            raise CMEEVerticalError("grounded_sentence_plan_relation_binding_mismatch")

    lines: list[_CMEEVisibleLine] = []
    covered_nucleus_ids: set[str] = set()
    for relation_id in required_relation_ids:
        relation = relation_index[relation_id]
        from_nucleus = nucleus_index[relation.from_nucleus_id]
        to_nucleus = nucleus_index[relation.to_nucleus_id]
        text = _cmee_relation_observation_text(
            relation,
            from_nucleus,
            to_nucleus,
            resolver,
        )
        lines.append(
            _CMEEVisibleLine(
                sentence_id=f"cmee:observation:{len(lines) + 1}",
                text=text,
                binding=_CMEEVisibleBinding(
                    line_role="cmee_observation",
                    nucleus_ids=(
                        relation.from_nucleus_id,
                        relation.to_nucleus_id,
                    ),
                    relation_ids=(relation_id,),
                    evidence_span_ids=tuple(relation.source_span_ids),
                    claim_scope="cmee_plan_bound_grounded_relation",
                    required=True,
                ),
            )
        )
        covered_nucleus_ids.update(
            (relation.from_nucleus_id, relation.to_nucleus_id)
        )

    span_order = {
        str(getattr(row, "span_id", "") or ""): index
        for index, row in enumerate(source.evidence_spans)
    }
    uncovered_nucleus_ids = sorted(
        (
            nucleus_id
            for nucleus_id in required_nucleus_ids
            if nucleus_id not in covered_nucleus_ids
        ),
        key=lambda nucleus_id: min(
            (span_order.get(row_id, len(span_order)) for row_id in nucleus_index[nucleus_id].source_span_ids),
            default=len(span_order),
        ),
    )
    uncovered_groups: list[list[str]] = []
    group_index: dict[tuple[str, str, str, str, tuple[str, ...]], int] = {}
    for nucleus_id in uncovered_nucleus_ids:
        nucleus = nucleus_index[nucleus_id]
        group_key = (
            str(nucleus.kind),
            _cmee_source_text(nucleus, resolver),
            str(nucleus.semantic_frame.polarity),
            str(nucleus.semantic_frame.modality),
            tuple(
                sorted(
                    str(
                        getattr(
                            resolver.resolve(source_span_id),
                            "source_field",
                            "",
                        )
                        or ""
                    )
                    for source_span_id in nucleus.source_span_ids
                )
            ),
        )
        if group_key not in group_index:
            group_index[group_key] = len(uncovered_groups)
            uncovered_groups.append([])
        uncovered_groups[group_index[group_key]].append(nucleus_id)

    for nucleus_ids in uncovered_groups:
        nucleus = nucleus_index[nucleus_ids[0]]
        evidence_span_ids = _ordered(
            source_span_id
            for nucleus_id in nucleus_ids
            for source_span_id in nucleus_index[nucleus_id].source_span_ids
        )
        lines.append(
            _CMEEVisibleLine(
                sentence_id=f"cmee:observation:{len(lines) + 1}",
                text=_cmee_nucleus_observation_text(nucleus, resolver),
                binding=_CMEEVisibleBinding(
                    line_role="cmee_observation",
                    nucleus_ids=tuple(nucleus_ids),
                    relation_ids=(),
                    evidence_span_ids=evidence_span_ids,
                    claim_scope="cmee_plan_bound_grounded_nucleus",
                    required=True,
                ),
            )
        )

    observed_nuclei = {
        nucleus_id for line in lines for nucleus_id in line.binding.nucleus_ids
    }
    observed_relations = {
        relation_id for line in lines for relation_id in line.binding.relation_ids
    }
    if observed_nuclei != set(required_nucleus_ids):
        raise CMEEVerticalError("post_realization_required_nucleus_mismatch")
    if observed_relations != set(required_relation_ids):
        raise CMEEVerticalError("post_realization_required_relation_mismatch")
    if not lines:
        raise CMEEVerticalError("experience_plan_projection_empty")
    return tuple(lines)


def _canonical_r4_tail_lines(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
    grounded_plan: Any,
    resolver: Any,
) -> tuple[_CMEEVisibleLine, ...]:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    reception_plan = _cmee_semantic_reception_plan(grounded_plan, resolver)
    reception_surface = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    )
    expected_reception_digest, expected_reception_acts = (
        _reception_plan_contract(grounded_plan, resolver)
    )
    if (
        plan.reception_plan_digest != expected_reception_digest
        or plan.allowed_reception_act_ids != expected_reception_acts
        or tuple(reception_surface.realized_reception_acts)
        != expected_reception_acts
    ):
        raise CMEEVerticalError("bound_human_reception_act_contract_mismatch")
    reception_owner_set = set(plan.reception_target_owner_ids)
    reception_targets = tuple(
        row_id
        for row_id in grounded_plan.response_plan.human_follow_target_ids
        if row_id in nucleus_index
        and _owner_for_nucleus(source, nucleus_index[row_id])
        in reception_owner_set
    )
    reception_bound_nucleus_ids = _ordered(
        (*reception_plan.target_nucleus_ids, *reception_plan.support_nucleus_ids)
    )
    if tuple(reception_surface.grounded_nucleus_ids) != reception_bound_nucleus_ids:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    if tuple(reception_plan.target_nucleus_ids) != reception_targets:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    target_nuclei = tuple(
        nucleus_index[row_id] for row_id in reception_bound_nucleus_ids
    )
    stage1_reception_text = _cmee_stage1_reception_text(
        expected_reception_acts,
        target_nuclei,
        resolver,
    )
    reception_quotes = tuple(re.findall(r"「([^」]*)」", stage1_reception_text))
    stage1_reception_surface = replace(
        reception_surface,
        text=stage1_reception_text,
        sentence_count=len(split_sentences(stage1_reception_text, skip_greeting=False)),
        source_anchor_count=len(reception_quotes),
        source_anchor_max_visible_chars=max(
            (len(value) for value in reception_quotes),
            default=0,
        ),
    )
    if validate_grounded_human_reception_surface(
        stage1_reception_surface,
        reception_plan,
        resolver,
    ):
        raise CMEEVerticalError("bound_human_reception_surface_rejected")
    reception_line = _CMEEVisibleLine(
        sentence_id="cmee:reception:1",
        text=stage1_reception_text,
        binding=_CMEEVisibleBinding(
            line_role="human_follow",
            nucleus_ids=reception_bound_nucleus_ids,
            relation_ids=(),
            evidence_span_ids=tuple(
                stage1_reception_surface.grounded_evidence_span_ids
            ),
            claim_scope="cmee_grounded_human_reception",
            required=True,
        ),
    )
    if not plan.visible_unknown_owner_ids:
        return (reception_line,)

    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    owner_unknown_span_ids = _ordered(
        source_span_id
        for owner_id in plan.visible_unknown_owner_ids
        for source_span_id in source.owner_obligation(owner_id).source_span_ids
    )
    if not plan.visible_unknown_owner_ids or not owner_unknown_span_ids:
        raise CMEEVerticalError("visible_unknown_evidence_unavailable")
    unknown_text, focus_span_ids = _cmee_structured_attachment_unknown_text(
        source,
        plan,
    )
    unknown_span_ids = _ordered((*owner_unknown_span_ids, *focus_span_ids))
    if any(source_span_id not in ref_by_span for source_span_id in unknown_span_ids):
        raise CMEEVerticalError("visible_unknown_cross_source_evidence")
    unknown_line = _CMEEVisibleLine(
        sentence_id="cmee:unknown:1",
        text=unknown_text,
        binding=_CMEEVisibleBinding(
            line_role="cmee_unknown",
            nucleus_ids=(),
            relation_ids=(),
            evidence_span_ids=unknown_span_ids,
            constrained_owner_ids=plan.visible_unknown_owner_ids,
            claim_scope="cmee_evidence_bound_unknown_preservation",
            required=True,
        ),
    )
    return unknown_line, reception_line


def _stage1_unknown_lines(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
) -> tuple[_CMEEVisibleLine, ...]:
    """Realize only the unchanged evidence-bound UNKNOWN duty, when present."""

    if not plan.visible_unknown_owner_ids:
        return ()
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    owner_unknown_span_ids = _ordered(
        source_span_id
        for owner_id in plan.visible_unknown_owner_ids
        for source_span_id in source.owner_obligation(owner_id).source_span_ids
    )
    if not owner_unknown_span_ids:
        raise CMEEVerticalError("visible_unknown_evidence_unavailable")
    unknown_text, focus_span_ids = _cmee_structured_attachment_unknown_text(
        source,
        plan,
    )
    unknown_span_ids = _ordered((*owner_unknown_span_ids, *focus_span_ids))
    if any(source_span_id not in ref_by_span for source_span_id in unknown_span_ids):
        raise CMEEVerticalError("visible_unknown_cross_source_evidence")
    return (
        _CMEEVisibleLine(
            sentence_id="cmee:unknown:1",
            text=unknown_text,
            binding=_CMEEVisibleBinding(
                line_role="cmee_unknown",
                nucleus_ids=(),
                relation_ids=(),
                evidence_span_ids=unknown_span_ids,
                constrained_owner_ids=plan.visible_unknown_owner_ids,
                claim_scope="cmee_evidence_bound_unknown_preservation",
                required=True,
            ),
        ),
    )


def _stage1_local_ref_id(value: str, *, expected_kind: str) -> str:
    prefix = f"{expected_kind}:"
    if type(value) is not str or not value.startswith(prefix) or "@" not in value:
        raise CMEEVerticalError("stage1_visible_semantic_ref_invalid")
    local_id = value[len(prefix) :].split("@", 1)[0]
    if not local_id:
        raise CMEEVerticalError("stage1_visible_semantic_ref_invalid")
    return local_id


def _stage1_v2_unit_seal(unit: RealizedSentenceUnit) -> Stage1V2UnitSeal:
    """Require the exact private provenance carried by one v2 unit."""

    seal = unit.v2_trace_seal
    if type(seal) is not Stage1V2UnitSeal:
        raise CMEEVerticalError("stage1_v2_unit_trace_seal_invalid")
    tuple_fields = (
        seal.covered_duty_refs,
        seal.sentence_job_refs,
        seal.source_reception_act_refs,
    )
    if (
        any(type(refs) is not tuple for refs in tuple_fields)
        or not seal.covered_duty_refs
        or not seal.sentence_job_refs
        or any(
            any(type(ref) is not str or not ref for ref in refs)
            or len(refs) != len(set(refs))
            for refs in tuple_fields
        )
        or any(
            type(ref) is not str or not ref
            for ref in (
                seal.composition_candidate_ref,
                seal.composition_layout_ref,
                seal.selected_stage1_artifact_ref,
            )
        )
    ):
        raise CMEEVerticalError("stage1_v2_unit_trace_seal_invalid")
    return seal


def _stage1_line_for_unit(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    projection: EmlisStage1Projection,
    unit: RealizedSentenceUnit,
    *,
    ordinal: int,
) -> _CMEEVisibleLine:
    """Map one selected compiler unit to the existing private line envelope."""

    schema_version = projection.schema_version
    _stage1_runtime_contract(schema_version)
    if (
        type(unit.basis_anchor_refs) is not tuple
        or not unit.basis_anchor_refs
        or len(unit.basis_anchor_refs) != len(set(unit.basis_anchor_refs))
        or (
            schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
            and len(unit.basis_anchor_refs) != 1
        )
    ):
        raise CMEEVerticalError("stage1_visible_anchor_invalid")
    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        if unit.v2_trace_seal is not None:
            raise CMEEVerticalError("stage1_v2_unit_trace_seal_invalid")
    else:
        _stage1_v2_unit_seal(unit)
    if unit.layer == "LAYER_1":
        contribution_by_id = {
            row.contribution_id: row
            for row in projection.observation_contributions
        }
        anchors = tuple(
            contribution_by_id.get(anchor_ref)
            for anchor_ref in unit.basis_anchor_refs
        )
        if any(anchor is None for anchor in anchors):
            raise CMEEVerticalError("stage1_visible_anchor_invalid")
        semantic_refs = _ordered(
            (
                *(
                    ref
                    for anchor in anchors
                    for ref in (
                        *anchor.semantic_refs,
                        *anchor.relation_basis_refs,
                    )
                ),
                *(row.semantic_ref for row in unit.realized_semantic_bindings),
            )
        )
        line_role = "cmee_observation"
        sentence_id = f"cmee:observation:{ordinal}"
        claim_scope = "cmee_stage1_interpretive_observation"
    elif unit.layer == "LAYER_2":
        claim_by_id = {
            row.subjective_claim_id: row
            for row in projection.subjective_claims
        }
        anchors = tuple(
            claim_by_id.get(anchor_ref) for anchor_ref in unit.basis_anchor_refs
        )
        if any(anchor is None for anchor in anchors):
            raise CMEEVerticalError("stage1_visible_anchor_invalid")
        semantic_refs = _ordered(
            (
                *(
                    ref
                    for anchor in anchors
                    for ref in anchor.basis_semantic_refs
                ),
                *(row.semantic_ref for row in unit.realized_semantic_bindings),
            )
        )
        line_role = "human_follow"
        sentence_id = f"cmee:reception:{ordinal}"
        claim_scope = "cmee_stage1_subjective_response"
    else:
        raise CMEEVerticalError("stage1_visible_layer_invalid")

    node_ref_ids = {
        _stage1_local_ref_id(ref, expected_kind="node")
        for ref in semantic_refs
        if ref.startswith("node:")
    }
    edge_ref_ids = {
        _stage1_local_ref_id(ref, expected_kind="edge")
        for ref in semantic_refs
        if ref.startswith("edge:")
    }
    if len(node_ref_ids) + len(edge_ref_ids) != len(set(semantic_refs)):
        raise CMEEVerticalError("stage1_visible_semantic_ref_invalid")

    node_by_id = {row.node_id: row for row in graph.nodes}
    edge_by_id = {row.edge_id: row for row in graph.edges}
    if not node_ref_ids.issubset(node_by_id) or not edge_ref_ids.issubset(edge_by_id):
        raise CMEEVerticalError("stage1_visible_semantic_ref_unreachable")

    source_node_id = {
        _stable_id("mn", source.envelope.envelope_id, row.nucleus_id): row.nucleus_id
        for row in grounded_plan.nuclei
    }
    source_edge_id = {
        _stable_id("me", source.envelope.envelope_id, row.relation_id): row.relation_id
        for row in grounded_plan.relations
    }
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    if not node_ref_ids.issubset(source_node_id) or not edge_ref_ids.issubset(
        source_edge_id
    ):
        raise CMEEVerticalError("stage1_visible_semantic_ref_unreachable")
    relation_ids = tuple(
        row.relation_id
        for row in grounded_plan.relations
        if _stable_id("me", source.envelope.envelope_id, row.relation_id)
        in edge_ref_ids
    )
    nucleus_id_set = {
        source_node_id[node_id] for node_id in node_ref_ids
    }
    nucleus_id_set.update(
        endpoint
        for relation_id in relation_ids
        for endpoint in (
            relation_index[relation_id].from_nucleus_id,
            relation_index[relation_id].to_nucleus_id,
        )
    )
    nucleus_ids = tuple(
        row.nucleus_id
        for row in grounded_plan.nuclei
        if row.nucleus_id in nucleus_id_set
    )

    evidence_id_set = {
        evidence_id
        for node_id in node_ref_ids
        for evidence_id in node_by_id[node_id].evidence_ids
    }
    evidence_id_set.update(
        evidence_id
        for edge_id in edge_ref_ids
        for evidence_id in edge_by_id[edge_id].evidence_ids
    )
    evidence_span_ids = tuple(
        row.source_span_id
        for row in source.evidence_refs
        if row.evidence_id in evidence_id_set
    )
    if not nucleus_ids or not evidence_span_ids:
        raise CMEEVerticalError("stage1_visible_lineage_missing")
    return _CMEEVisibleLine(
        sentence_id=sentence_id,
        text=unit.text,
        binding=_CMEEVisibleBinding(
            line_role=line_role,
            nucleus_ids=nucleus_ids,
            relation_ids=relation_ids,
            evidence_span_ids=evidence_span_ids,
            claim_scope=claim_scope,
            required=True,
        ),
    )


def _stage1_visible_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    projection: EmlisStage1Projection,
    selected_units: Sequence[RealizedSentenceUnit],
) -> tuple[tuple[_CMEEVisibleLine, ...], tuple[_CMEEVisibleLine, ...]]:
    units = tuple(selected_units)
    observation_units = tuple(row for row in units if row.layer == "LAYER_1")
    reception_units = tuple(row for row in units if row.layer == "LAYER_2")
    if units != (*observation_units, *reception_units):
        raise CMEEVerticalError("stage1_visible_role_order_invalid")
    observation_lines = tuple(
        _stage1_line_for_unit(
            source,
            graph,
            grounded_plan,
            projection,
            unit,
            ordinal=index,
        )
        for index, unit in enumerate(observation_units, start=1)
    )
    reception_lines = tuple(
        _stage1_line_for_unit(
            source,
            graph,
            grounded_plan,
            projection,
            unit,
            ordinal=index,
        )
        for index, unit in enumerate(reception_units, start=1)
    )
    if not observation_lines or not reception_lines:
        raise CMEEVerticalError("stage1_visible_required_layer_missing")
    return observation_lines, reception_lines


def _stage1_v2_typed_derivation_admission_ref(
    projection: EmlisStage1Projection,
    selected_units: Sequence[RealizedSentenceUnit],
    observation_lines: Sequence[_CMEEVisibleLine],
    *,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    grounded_plan: Any,
) -> str:
    """Seal the exact final-plan derivation eligible for echo-only admission."""

    if (
        projection.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        or FINAL_STAGE1_GROUNDED_PROJECTION_VERSION
        not in tuple(getattr(grounded_plan, "source_contracts", ()))
    ):
        raise CMEEVerticalError("stage1_v2_typed_derivation_invalid")
    try:
        projection_ref = stage1_projection_artifact_ref(projection)
        validate_stage1_projection_artifact_ref(
            projection_ref,
            expected_schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        )
    except CMEEStage1ContractError:
        raise CMEEVerticalError("stage1_v2_typed_derivation_invalid") from None

    units = tuple(selected_units)
    observation_units = tuple(
        unit for unit in units if unit.layer == "LAYER_1"
    )
    reception_units = tuple(
        unit for unit in units if unit.layer == "LAYER_2"
    )
    lines = tuple(observation_lines)
    if (
        not observation_units
        or not reception_units
        or units != (*observation_units, *reception_units)
        or len(lines) != len(observation_units)
        or any(
            line.text != unit.text
            or line.binding.line_role != "cmee_observation"
            or not line.binding.evidence_span_ids
            or not (line.binding.nucleus_ids or line.binding.relation_ids)
            for line, unit in zip(lines, observation_units, strict=True)
        )
    ):
        raise CMEEVerticalError("stage1_v2_typed_derivation_invalid")

    prior_unit_ids: list[str] = []
    seal_rows: list[tuple[Any, ...]] = []
    covered_duty_refs: list[str] = []
    for unit in units:
        try:
            validate_stage1_sentence_unit(
                unit,
                projection,
                grounded_graph=graph,
                parent_plan=plan,
                prior_unit_ids=tuple(prior_unit_ids),
            )
        except CMEEStage1ContractError:
            raise CMEEVerticalError(
                "stage1_v2_typed_derivation_invalid"
            ) from None
        prior_unit_ids.append(unit.unit_id)
        seal = _stage1_v2_unit_seal(unit)
        covered_duty_refs.extend(seal.covered_duty_refs)
        seal_rows.append(
            (
                unit.unit_id,
                unit.layer,
                unit.basis_anchor_refs,
                unit.composition_variant_id,
                seal.covered_duty_refs,
                seal.sentence_job_refs,
                seal.source_reception_act_refs,
                seal.composition_candidate_ref,
                seal.composition_layout_ref,
                seal.selected_stage1_artifact_ref,
            )
        )

    flattened_observation_refs = tuple(
        ref for unit in observation_units for ref in unit.basis_anchor_refs
    )
    flattened_subjective_refs = tuple(
        ref for unit in reception_units for ref in unit.basis_anchor_refs
    )
    if (
        len(flattened_observation_refs)
        != len(set(flattened_observation_refs))
        or not set(flattened_observation_refs).issubset(
            set(projection.ordered_observation_refs)
        )
        or len(flattened_subjective_refs)
        != len(set(flattened_subjective_refs))
        or not set(flattened_subjective_refs).issubset(
            set(projection.ordered_subjective_refs)
        )
        or len(covered_duty_refs) != len(set(covered_duty_refs))
        or any(
            len({row[index] for row in seal_rows}) != 1
            for index in (3, 7, 8, 9)
        )
    ):
        raise CMEEVerticalError("stage1_v2_typed_derivation_invalid")

    material = (
        projection_ref,
        graph.graph_id,
        plan.plan_id,
        FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
        tuple(seal_rows),
        tuple(
            (
                line.sentence_id,
                _sha256_text(line.text),
                line.binding.nucleus_ids,
                line.binding.relation_ids,
                line.binding.evidence_span_ids,
            )
            for line in lines
        ),
    )
    digest = _sha256_text(
        json.dumps(
            material,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return f"stage1-v2-typed-derivation-{digest}"


def _cmee_core_phrase_unit_id(source_span_id: str) -> str:
    return f"cmee-phrase:{source_span_id}"


def _stage1_v2_composer_binding_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    observation_lines: Sequence[_CMEEVisibleLine],
    selected_units: Sequence[RealizedSentenceUnit],
) -> tuple[_CMEEVisibleLine, ...]:
    """Project grouped v2 units to exact per-clause common-core bindings."""

    lines = tuple(observation_lines)
    units = tuple(row for row in selected_units if row.layer == "LAYER_1")
    if len(lines) != len(units):
        raise CMEEVerticalError("stage1_v2_core_binding_unit_mismatch")
    node_by_id = {row.node_id: row for row in graph.nodes}
    edge_by_id = {row.edge_id: row for row in graph.edges}
    source_node_id = {
        _stable_id("mn", source.envelope.envelope_id, row.nucleus_id): row.nucleus_id
        for row in grounded_plan.nuclei
    }
    source_edge_id = {
        _stable_id("me", source.envelope.envelope_id, row.relation_id): row.relation_id
        for row in grounded_plan.relations
    }
    relation_by_id = {
        row.relation_id: row for row in grounded_plan.relations
    }
    expanded: list[_CMEEVisibleLine] = []
    for line, unit in zip(lines, units, strict=True):
        canonical_sentences = split_sentences(
            line.text,
            skip_greeting=False,
        )
        if len(canonical_sentences) == 1:
            if len(line.binding.relation_ids) > 1:
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_relation_cardinality_mismatch"
                )
            expanded.append(line)
            continue
        if (
            len(canonical_sentences) != len(unit.clause_frames)
            or any(type(value) is not str or not value for value in canonical_sentences)
        ):
            raise CMEEVerticalError(
                "stage1_v2_core_binding_clause_cardinality_mismatch"
            )

        grouped_nucleus_ids: list[str] = []
        grouped_relation_ids: list[str] = []
        grouped_evidence_span_ids: list[str] = []
        for ordinal, (sentence, frame) in enumerate(
            zip(canonical_sentences, unit.clause_frames, strict=True),
            start=1,
        ):
            semantic_refs = _ordered(
                (
                    *((frame.topic_ref,) if frame.topic_ref is not None else ()),
                    *((frame.object_ref,) if frame.object_ref is not None else ()),
                    *(row.semantic_ref for row in frame.argument_bindings),
                    *frame.actor_refs,
                    *frame.experiencer_refs,
                )
            )
            node_ids = {
                _stage1_local_ref_id(ref, expected_kind="node")
                for ref in semantic_refs
                if ref.startswith("node:")
            }
            relation_ids: tuple[str, ...] = ()
            discourse_ref = frame.discourse_relation
            if type(discourse_ref) is not str or not discourse_ref:
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_relation_invalid"
                )
            if discourse_ref.startswith("edge:"):
                edge_id = _stage1_local_ref_id(
                    discourse_ref,
                    expected_kind="edge",
                )
                source_relation_id = source_edge_id.get(edge_id)
                if source_relation_id is None:
                    raise CMEEVerticalError(
                        "stage1_v2_core_binding_relation_invalid"
                    )
                relation_ids = (source_relation_id,)
            elif not discourse_ref.startswith("relation:none:"):
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_relation_invalid"
                )
            if not node_ids.issubset(node_by_id):
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_semantic_ref_invalid"
                )
            nucleus_id_set = {
                source_node_id[node_id]
                for node_id in node_ids
                if node_id in source_node_id
            }
            if len(nucleus_id_set) != len(node_ids):
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_semantic_ref_invalid"
                )
            nucleus_id_set.update(
                endpoint
                for relation_id in relation_ids
                for endpoint in (
                    relation_by_id[relation_id].from_nucleus_id,
                    relation_by_id[relation_id].to_nucleus_id,
                )
            )
            nucleus_ids = tuple(
                row.nucleus_id
                for row in grounded_plan.nuclei
                if row.nucleus_id in nucleus_id_set
            )
            edge_ids = {
                _stable_id(
                    "me",
                    source.envelope.envelope_id,
                    relation_id,
                )
                for relation_id in relation_ids
            }
            evidence_ids = {
                evidence_id
                for node_id in node_ids
                for evidence_id in node_by_id[node_id].evidence_ids
            }
            evidence_ids.update(
                evidence_id
                for edge_id in edge_ids
                for evidence_id in edge_by_id[edge_id].evidence_ids
            )
            evidence_span_ids = tuple(
                row.source_span_id
                for row in source.evidence_refs
                if row.evidence_id in evidence_ids
            )
            if not nucleus_ids or not evidence_span_ids:
                raise CMEEVerticalError(
                    "stage1_v2_core_binding_lineage_missing"
                )
            grouped_nucleus_ids.extend(nucleus_ids)
            grouped_relation_ids.extend(relation_ids)
            grouped_evidence_span_ids.extend(evidence_span_ids)
            expanded.append(
                _CMEEVisibleLine(
                    sentence_id=f"{line.sentence_id}:clause:{ordinal}",
                    text=sentence,
                    binding=_CMEEVisibleBinding(
                        line_role=line.binding.line_role,
                        nucleus_ids=nucleus_ids,
                        relation_ids=relation_ids,
                        evidence_span_ids=evidence_span_ids,
                        claim_scope=line.binding.claim_scope,
                        required=line.binding.required,
                    ),
                )
            )
        if (
            _ordered(grouped_nucleus_ids) != line.binding.nucleus_ids
            or len(grouped_relation_ids) != len(set(grouped_relation_ids))
            or set(grouped_relation_ids) != set(line.binding.relation_ids)
            or set(grouped_evidence_span_ids)
            != set(line.binding.evidence_span_ids)
        ):
            raise CMEEVerticalError("stage1_v2_core_binding_cover_mismatch")
    return tuple(expanded)


def _cmee_core_relation_type(line: _CMEEVisibleLine, grounded_plan: Any) -> str:
    if not line.binding.relation_ids:
        return "source_explicit_nucleus"
    if len(line.binding.relation_ids) != 1:
        raise CMEEVerticalError("plan_bound_relation_binding_not_exact1")
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    relation = relation_index.get(line.binding.relation_ids[0])
    if relation is None:
        raise CMEEVerticalError("plan_bound_relation_binding_unknown")
    return str(relation.type)


def _cmee_composer_binding_row(
    line: _CMEEVisibleLine,
    grounded_plan: Any,
) -> dict[str, Any]:
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    relation_bindings = [
        {
            "relation_id": relation_id,
            "relation_type": str(relation_index[relation_id].type),
            "from_nucleus_id": str(relation_index[relation_id].from_nucleus_id),
            "to_nucleus_id": str(relation_index[relation_id].to_nucleus_id),
            "evidence_span_ids": list(relation_index[relation_id].source_span_ids),
        }
        for relation_id in line.binding.relation_ids
    ]
    binding_material = {
        "nucleus_ids": list(line.binding.nucleus_ids),
        "relation_bindings": relation_bindings,
        "evidence_span_ids": list(line.binding.evidence_span_ids),
    }
    return {
        "version": "cocolon.cmee.emlis.r4_sentence_binding.v1",
        "binding_version": "cocolon.cmee.emlis.r4_sentence_binding.v1",
        "sentence_id": line.sentence_id,
        "text": line.text,
        "used_evidence_span_ids": list(line.binding.evidence_span_ids),
        "used_phrase_unit_ids": [
            _cmee_core_phrase_unit_id(source_span_id)
            for source_span_id in line.binding.evidence_span_ids
        ],
        "relation_type": _cmee_core_relation_type(line, grounded_plan),
        "line_role": "cmee_observation",
        "coverage_scope": "cmee_required_plan",
        "must_include": True,
        "raw_input_included": False,
        "meta": {
            "cmee_nucleus_ids": list(line.binding.nucleus_ids),
            "cmee_relation_ids": list(line.binding.relation_ids),
            "cmee_relation_bindings": relation_bindings,
            "cmee_binding_digest": _sha256_text(
                json.dumps(
                    binding_material,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ),
            "raw_input_included": False,
        },
    }


def _cmee_guard_binding_projection(binding: Mapping[str, Any]) -> dict[str, Any]:
    """Hide finished surface bytes from the common guard's binding matcher.

    The outer private binding retains the exact text.  The unchanged common
    guard receives the same ordered semantic lineage without ``text`` so its
    sentence-to-binding resolver uses the explicit ordinal contract instead
    of fuzzy-matching two lexically similar Stage 1 sentences.
    """

    return {key: value for key, value in binding.items() if key != "text"}


def _json_exact_identity(actual: Any, expected: Any) -> bool:
    """Compare JSON-shaped contract values without Python bool/int coercion."""

    try:
        return json.dumps(
            actual,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) == json.dumps(
            expected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        return False


def _cmee_core_binding_projection(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": "emlis.sentence_binding.v1",
        "binding_version": "emlis.sentence_binding.v1",
        "sentence_id": binding["sentence_id"],
        "line_role": binding["line_role"],
        "relation_type": binding["relation_type"],
        "used_evidence_span_ids": list(binding["used_evidence_span_ids"]),
        "used_phrase_unit_ids": list(binding["used_phrase_unit_ids"]),
        "coverage_scope": binding["coverage_scope"],
        "must_include": binding["must_include"],
        "raw_input_included": binding["raw_input_included"],
        "meta": {
            "source_adapter": "emlis_observation_composer_adapter.v1",
            "source_kind": "emlis_sentence_binding",
        },
    }


def _cmee_binding_aliases(meta: Mapping[str, Any]) -> tuple[Any, ...]:
    aliases: list[Any] = []
    for bundle_key in ("sentence_binding_bundle", "binding_bundle", "binding"):
        bundle = meta.get(bundle_key)
        if type(bundle) is not dict:
            return ()
        aliases.extend(
            bundle.get(alias_key)
            for alias_key in ("bindings", "sentence_bindings", "items")
        )
    diagnostic = meta.get("composer_diagnostic")
    diagnostic_bundle = (
        diagnostic.get("sentence_binding_bundle")
        if type(diagnostic) is dict
        else None
    )
    if type(diagnostic_bundle) is not dict:
        return ()
    aliases.extend(
        diagnostic_bundle.get(alias_key)
        for alias_key in ("bindings", "sentence_bindings", "items")
    )
    aliases.append(diagnostic.get("sentence_bindings"))
    return tuple(aliases)


def _stage1_v2_echo_only_admitted_core_meta(
    core_meta: Mapping[str, Any],
    *,
    admission_ref: str,
    canonical_text: str,
    used_evidence_span_ids: Sequence[str],
    evidence_digest: str,
) -> dict[str, Any] | None:
    """Admit only an otherwise-clear v2 typed derivation echo rejection."""

    allowed_reasons = {"raw_input_echo", "excessive_raw_quote"}
    expected_quality_flags = (
        "template_echo_failed",
        "core_text_composer_rejected",
        "guard_rejected",
    )
    normalized_canonical_text = re.sub(
        r"\s+",
        " ",
        str(canonical_text or "").replace("\r", " ").replace("\n", " "),
    ).strip(" \t\r\n　、,。.!！?？『』\"'")
    expected_evidence_ids = tuple(used_evidence_span_ids)
    if (
        type(core_meta) is not dict
        or not admission_ref.startswith("stage1-v2-typed-derivation-")
        or type(canonical_text) is not str
        or not canonical_text
        or re.fullmatch(r"[0-9a-f]{64}", evidence_digest) is None
        or core_meta.get("core_id") != "emlis"
        or core_meta.get("status") != "rejected"
        or type(core_meta.get("passed")) is not bool
        or core_meta.get("passed") is not False
        or core_meta.get("text_length") != len(normalized_canonical_text)
        or tuple(core_meta.get("quality_flags") or ())
        != expected_quality_flags
        or type(core_meta.get("used_evidence_span_ids")) is not list
        or len(core_meta.get("used_evidence_span_ids"))
        != len(set(core_meta.get("used_evidence_span_ids")))
        or set(core_meta.get("used_evidence_span_ids"))
        != set(expected_evidence_ids)
    ):
        return None
    rejection_reasons = tuple(core_meta.get("rejection_reasons") or ())
    if (
        not rejection_reasons
        or len(rejection_reasons) != len(set(rejection_reasons))
        or not set(rejection_reasons).issubset(allowed_reasons)
    ):
        return None

    result = core_meta.get("result")
    result_meta = result.get("meta") if type(result) is dict else None
    raw_rows = (
        result_meta.get("guard_results")
        if type(result_meta) is dict
        else None
    )
    combined = (
        result_meta.get("combined_guard_result")
        if type(result_meta) is dict
        else None
    )
    combined_meta = combined.get("meta") if type(combined) is dict else None
    combined_rows = (
        combined_meta.get("guard_results")
        if type(combined_meta) is dict
        else None
    )
    guarded_candidate = (
        result_meta.get("candidate")
        if type(result_meta) is dict
        else None
    )
    if (
        type(result) is not dict
        or result.get("status") != "rejected"
        or result.get("used_evidence_span_ids") != []
        or tuple(result.get("quality_flags") or ())
        != expected_quality_flags
        or tuple(result.get("rejection_reasons") or ())
        != rejection_reasons
        or type(result_meta) is not dict
        or type(raw_rows) is not list
        or len(raw_rows) != len(EXPECTED_COMMON_GUARD_IDS)
        or type(combined) is not dict
        or combined.get("guard_name") != "combined_text_generation_guards"
        or type(combined.get("passed")) is not bool
        or combined.get("passed") is not False
        or tuple(combined.get("quality_flags") or ())
        != ("template_echo_failed",)
        or tuple(combined.get("rejection_reasons") or ())
        != rejection_reasons
        or type(combined_rows) is not list
        or combined_rows != raw_rows
        or type(guarded_candidate) is not dict
        or guarded_candidate.get("text_length")
        != len(normalized_canonical_text)
        or type(guarded_candidate.get("used_evidence_span_ids")) is not list
        or len(guarded_candidate.get("used_evidence_span_ids"))
        != len(set(guarded_candidate.get("used_evidence_span_ids")))
        or set(guarded_candidate.get("used_evidence_span_ids"))
        != set(expected_evidence_ids)
        or guarded_candidate.get("coverage_scope") != "cmee_required_plan"
        or type(
            result_meta.get("declared_used_evidence_span_ids")
        ) is not list
        or len(result_meta.get("declared_used_evidence_span_ids"))
        != len(set(result_meta.get("declared_used_evidence_span_ids")))
        or set(result_meta.get("declared_used_evidence_span_ids"))
        != set(expected_evidence_ids)
    ):
        return None

    for index, (expected_guard_id, raw_row) in enumerate(
        zip(EXPECTED_COMMON_GUARD_IDS, raw_rows, strict=True)
    ):
        expected_passed = index != 1
        if (
            type(raw_row) is not dict
            or raw_row.get("guard_name") != expected_guard_id
            or type(raw_row.get("passed")) is not bool
            or raw_row.get("passed") is not expected_passed
            or (
                index != 1
                and (
                    raw_row.get("quality_flags") != []
                    or raw_row.get("rejection_reasons") != []
                )
            )
        ):
            return None
    template_row = raw_rows[1]
    template_meta = template_row.get("meta")
    if (
        tuple(template_row.get("quality_flags") or ())
        != ("template_echo_failed",)
        or tuple(template_row.get("rejection_reasons") or ())
        != rejection_reasons
        or type(template_meta) is not dict
        or type(template_meta.get("raw_echo_ratio")) not in {int, float}
        or type(template_meta.get("raw_quote_ratio")) not in {int, float}
        or type(template_meta.get("previous_similarity")) not in {int, float}
        or template_meta.get("previous_similarity") >= 0.72
        or type(template_meta.get("raw_quote_hits")) is not list
        or any(
            type(value) is not str or not value
            for value in template_meta.get("raw_quote_hits")
        )
        or (
            "raw_input_echo" in rejection_reasons
            and template_meta.get("raw_echo_ratio") < 0.82
        )
        or (
            "excessive_raw_quote" in rejection_reasons
            and not template_meta.get("raw_quote_hits")
        )
        or template_meta.get("limited_surface_repetition_score") != 0.0
        or template_meta.get("repeated_limited_surface_patterns") != []
        or template_meta.get("repeated_sentence_pattern_score") != 0.0
        or template_meta.get("piece_preserves_source_claims") is not False
        or template_meta.get("analysis_report_observation") is not False
    ):
        return None

    admitted = copy.deepcopy(dict(core_meta))
    admitted_result = admitted["result"]
    admitted_result_meta = admitted_result["meta"]
    admitted_rows = admitted_result_meta["guard_results"]
    admission_preimage = {
        "policy_id": _STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY,
        "typed_derivation_ref": admission_ref,
        "original_rejection_reasons": list(rejection_reasons),
        "original_quality_flags": list(expected_quality_flags),
        "raw_echo_ratio": template_meta["raw_echo_ratio"],
        "raw_quote_ratio": template_meta["raw_quote_ratio"],
        "raw_quote_hit_digests": [
            _sha256_text(value)
            for value in template_meta["raw_quote_hits"]
        ],
        "evidence_digest": evidence_digest,
        "surface_digest": _sha256_text(canonical_text),
    }
    admission_digest = _sha256_text(
        json.dumps(
            admission_preimage,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    typed_admission_ref = (
        f"typed-source-quotation:{admission_digest}"
        f"@{_STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY}"
    )
    admission_detail = {
        "typed_admission_ref": typed_admission_ref,
        "digest_preimage": admission_preimage,
    }
    admitted_template_row = admitted_rows[1]
    admitted_template_row["passed"] = True
    admitted_template_row["quality_flags"] = []
    admitted_template_row["rejection_reasons"] = []
    admitted_template_row["meta"] = {
        **admitted_template_row["meta"],
        "stage1_v2_typed_derivation_admission": admission_detail,
    }
    admitted_combined = admitted_result_meta["combined_guard_result"]
    admitted_combined["passed"] = True
    admitted_combined["quality_flags"] = []
    admitted_combined["rejection_reasons"] = []
    admitted_combined["meta"]["guard_results"] = copy.deepcopy(
        admitted_rows
    )
    admitted_combined["meta"][
        "stage1_v2_typed_derivation_admission"
    ] = admission_detail
    admitted_result_meta[
        "stage1_v2_typed_derivation_admission"
    ] = admission_detail
    admitted_result["status"] = "generated"
    admitted_evidence_ids = list(
        admitted_result_meta["declared_used_evidence_span_ids"]
    )
    admitted_result["used_evidence_span_ids"] = admitted_evidence_ids
    admitted_result["coverage_scope"] = "cmee_required_plan"
    admitted_result["quality_flags"] = []
    admitted_result["rejection_reasons"] = []
    admitted["status"] = "generated"
    admitted["passed"] = True
    admitted["used_evidence_span_ids"] = admitted_evidence_ids
    admitted["coverage_scope"] = "cmee_required_plan"
    admitted["quality_flags"] = []
    admitted["rejection_reasons"] = []
    admitted["stage1_v2_typed_derivation_admission"] = admission_detail
    return admitted


class _CMEER4PlanBoundComposerClient:
    """One-shot adapter from canonical CMEE duties to the unchanged common core."""

    def __init__(
        self,
        observation_lines: Sequence[_CMEEVisibleLine],
        grounded_plan: Any,
        *,
        composer_binding_lines: Sequence[_CMEEVisibleLine] | None = None,
        typed_derivation_admission_ref: str | None = None,
    ) -> None:
        self._observation_lines = tuple(observation_lines)
        self._composer_binding_lines = (
            self._observation_lines
            if composer_binding_lines is None
            else tuple(composer_binding_lines)
        )
        if not self._composer_binding_lines:
            raise CMEEVerticalError("plan_bound_observation_binding_missing")
        self._grounded_plan = grounded_plan
        self._typed_derivation_admission_ref = (
            typed_derivation_admission_ref
        )

    def generate(self, payload: Any) -> dict[str, Any]:
        if type(payload) is not dict:
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_payload_invalid"],
            }
        evidence_items = payload.get("evidence_spans")
        if type(evidence_items) is not list or any(
            type(row) is not dict for row in evidence_items
        ):
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_evidence_invalid"],
            }
        evidence_by_id = {
            str(row.get("span_id") or ""): row for row in evidence_items
        }
        used_evidence_ids = _ordered(
            source_span_id
            for line in self._observation_lines
            for source_span_id in line.binding.evidence_span_ids
        )
        if not used_evidence_ids or any(
            source_span_id not in evidence_by_id
            for source_span_id in used_evidence_ids
        ):
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_evidence_missing"],
            }

        phrase_units = tuple(
            _CMEECorePhraseUnit(
                phrase_unit_id=_cmee_core_phrase_unit_id(source_span_id),
                evidence_span_id=source_span_id,
                raw_text=str(evidence_by_id[source_span_id].get("raw_text") or ""),
                compressed_text=str(
                    evidence_by_id[source_span_id].get("raw_text") or ""
                ),
            )
            for source_span_id in used_evidence_ids
        )
        binding_rows = [
            _cmee_composer_binding_row(line, self._grounded_plan)
            for line in self._composer_binding_lines
        ]
        guard_binding_rows = [
            _cmee_guard_binding_projection(row) for row in binding_rows
        ]
        sentence_plans = tuple(
            _CMEECoreSentencePlan(
                sentence_plan_id=f"cmee-plan:{index}",
                line_role="cmee_observation",
                phrase_unit_ids=tuple(row["used_phrase_unit_ids"]),
                relation_type=str(row["relation_type"]),
            )
            for index, row in enumerate(binding_rows, start=1)
        )
        binding_bundle = {
            "bindings": binding_rows,
            "sentence_bindings": binding_rows,
            "items": binding_rows,
            "raw_text_included": False,
            "raw_input_required_for_debug": False,
        }
        guard_binding_bundle = {
            "bindings": guard_binding_rows,
            "sentence_bindings": guard_binding_rows,
            "items": guard_binding_rows,
            "raw_text_included": False,
            "raw_input_required_for_debug": False,
        }
        composer_meta = {
            "cmee_plan_bound_grounded_surface": {
                "version": "cocolon.cmee.emlis.plan_bound_grounded_surface.v1",
                "observation_line_count": len(binding_rows),
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            },
            "required_roles": [],
            "covered_roles": [],
            "sentence_binding_bundle": binding_bundle,
            "binding_bundle": binding_bundle,
            "binding": binding_bundle,
            "sentence_bindings": binding_rows,
            "composer_diagnostic": {
                "sentence_binding_bundle": binding_bundle,
                "sentence_bindings": binding_rows,
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            },
        }
        guard_composer_meta = {
            **composer_meta,
            "sentence_binding_bundle": guard_binding_bundle,
            "binding_bundle": guard_binding_bundle,
            "binding": guard_binding_bundle,
            "sentence_bindings": guard_binding_rows,
            "composer_diagnostic": {
                "sentence_binding_bundle": guard_binding_bundle,
                "sentence_bindings": guard_binding_rows,
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            },
        }
        scope = payload.get("limited_observation_scope")
        scope = scope if type(scope) is dict else {}
        response = {
            "schema_version": "emlis.composer.response.v1",
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "status": "generated",
            "composer_model": "cocolon.cmee.emlis.plan_bound_grounded_surface.v1",
            "generation_method": "cmee_plan_bound_grounded_surface",
            "generation_scope": "current_input_only",
            "fixed_string_renderer_used": False,
            "coverage_scope": "cmee_required_plan",
            "comment_text": "\n".join(
                line.text for line in self._observation_lines
            ),
            "used_evidence_span_ids": list(used_evidence_ids),
            "used_claim_ids": list(scope.get("included_claim_ids") or []),
            "used_relation_ids": list(scope.get("included_relation_ids") or []),
            "confidence": 1.0,
            "used_phrase_unit_ids": [
                row.phrase_unit_id for row in phrase_units
            ],
            "sentence_binding_bundle": binding_bundle,
            "composer_meta": composer_meta,
        }
        guard_response = {
            **response,
            "sentence_binding_bundle": guard_binding_bundle,
            "composer_meta": guard_composer_meta,
        }
        evaluation = evaluate_emlis_observation_candidate(
            composer_payload=payload,
            evidence_items=evidence_items,
            phrase_units=phrase_units,
            sentence_plans=sentence_plans,
            comment_text=str(response["comment_text"]),
            used_evidence_span_ids=tuple(used_evidence_ids),
            used_phrase_unit_ids=tuple(response["used_phrase_unit_ids"]),
            coverage_scope="cmee_required_plan",
            composer_model=str(response["composer_model"]),
            composer_meta=guard_composer_meta,
            response=guard_response,
        )
        if evaluation.passed:
            return attach_core_evaluation_meta(response, evaluation)
        core_meta = evaluation.as_meta()
        if self._typed_derivation_admission_ref is not None:
            evidence_digest = _sha256_text(
                json.dumps(
                    tuple(
                        (
                            source_span_id,
                            _sha256_text(
                                str(
                                    evidence_by_id[source_span_id].get(
                                        "raw_text"
                                    )
                                    or ""
                                )
                            ),
                        )
                        for source_span_id in used_evidence_ids
                    ),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            admitted_core_meta = _stage1_v2_echo_only_admitted_core_meta(
                core_meta,
                admission_ref=self._typed_derivation_admission_ref,
                canonical_text=str(response["comment_text"]),
                used_evidence_span_ids=used_evidence_ids,
                evidence_digest=evidence_digest,
            )
            if admitted_core_meta is not None:
                admitted_response = dict(response)
                admitted_composer_meta = dict(composer_meta)
                admitted_composer_meta[
                    "text_generation_core"
                ] = admitted_core_meta
                admitted_composer_meta[
                    "core_text_generation"
                ] = admitted_core_meta
                admitted_response["composer_meta"] = admitted_composer_meta
                return admitted_response
        return {
            "composer_source": "unavailable",
            "status": "unavailable",
            "rejection_reasons": [core_rejection_reason(evaluation)],
            "composer_meta": {
                "text_generation_core": core_meta,
                "core_text_generation": core_meta,
            },
        }


def _experience_plan_projection(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
    grounded_plan: Any,
    observation_lines: Sequence[_CMEEVisibleLine],
) -> LimitedObservationScope:
    """Project the selected Layer 1 scope into the common-core input port.

    Meaning-owner IDs remain disposition authority only.  Request-local
    nucleus and relation identities own claims/endpoints so two source meanings
    under one owner can never collapse into one graph claim.  The Stage 1
    compiler's selected Observation units, including admitted optional meaning,
    are the sole guard scope; legacy owner visibility is not re-projected here.
    """

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    span_text = {
        str(getattr(row, "span_id", "") or ""): str(getattr(row, "raw_text", "") or "")
        for row in source.evidence_spans
    }
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    selected_nucleus_ids = _ordered(
        nucleus_id
        for line in observation_lines
        for nucleus_id in line.binding.nucleus_ids
    )
    selected_relation_ids = _ordered(
        relation_id
        for line in observation_lines
        for relation_id in line.binding.relation_ids
    )
    if (
        not selected_nucleus_ids
        or any(row_id not in nucleus_index for row_id in selected_nucleus_ids)
        or any(row_id not in relation_index for row_id in selected_relation_ids)
    ):
        raise CMEEVerticalError("experience_plan_projection_selection_invalid")
    claims: list[GraphClaim] = []
    claim_id_by_nucleus: dict[str, str] = {}
    for row_id in selected_nucleus_ids:
        row = nucleus_index[row_id]
        evidence_ids = list(row.source_span_ids)
        text = " / ".join(span_text[span_id] for span_id in evidence_ids if span_id in span_text).strip()
        if not text or row.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            raise CMEEVerticalError("experience_plan_projection_nucleus_invalid")
        claim_id = _stable_id("gc", source.envelope.envelope_id, row_id)
        claim_id_by_nucleus[row_id] = claim_id
        claims.append(
            GraphClaim(
                claim_id=claim_id,
                claim_type=str(row.kind),
                text=text,
                evidence_span_ids=evidence_ids,
                confidence=1.0,
            )
        )
    if not claims:
        raise CMEEVerticalError("experience_plan_projection_empty")

    relations: list[RelationEdge] = []
    for row_id in selected_relation_ids:
        row = relation_index[row_id]
        if (
            row.grounding_kind not in ADMISSIBLE_RELATION_GROUNDING
            or row.from_nucleus_id not in claim_id_by_nucleus
            or row.to_nucleus_id not in claim_id_by_nucleus
        ):
            raise CMEEVerticalError(
                "experience_plan_projection_relation_endpoint_missing"
            )
        relations.append(
            RelationEdge(
                edge_id=_stable_id("gr", source.envelope.envelope_id, row_id),
                from_claim_id=claim_id_by_nucleus[row.from_nucleus_id],
                to_claim_id=claim_id_by_nucleus[row.to_nucleus_id],
                relation_type=str(row.type),
                evidence_span_ids=list(row.source_span_ids),
                confidence=1.0,
            )
        )
    claim_ids = {row.claim_id for row in claims}
    if any(
        row.from_claim_id not in claim_ids or row.to_claim_id not in claim_ids
        for row in relations
    ):
        raise CMEEVerticalError("experience_plan_projection_relation_endpoint_missing")

    primary = claims[0]
    remainder = claims[1:]
    projected_graph = ObservationGraph(
        primary_state=primary,
        core_tensions=relations,
        pressure_sources=[row for row in remainder if row.claim_type in {"state", "reaction"}],
        limit_signals=[row for row in remainder if row.claim_type in {"limit", "constraint"}],
        self_awareness=[row for row in remainder if row.claim_type == "self_awareness"],
        value_or_strength_signals=[
            row
            for row in remainder
            if row.claim_type not in {"state", "reaction", "limit", "constraint", "self_awareness"}
        ],
        addressee_notes=AddresseeNotes(
            sentence_target=max(1, min(4, len(claims) + len(relations)))
        ),
        safety_boundaries=[],
        forbidden_claims=[],
        missing_information=[],
    )
    return LimitedObservationScope(
        scope_status="eligible",
        scoped_graph=projected_graph,
        included_claim_ids=[row.claim_id for row in claims],
        included_relation_ids=[row.edge_id for row in relations],
        excluded_claims=[],
        min_reply_sentence_count=1,
        max_reply_sentence_count=4,
        coverage_scope="current_input_core",
        rejection_reasons=[],
        coverage_groups=["cmee_required_visible_owner_exact"],
        scope_expansion={"enabled": False, "owner": "CMEEExperiencePlan"},
        safety_boundary={},
        safety_boundary_policy={},
    )


def _realize_cmee_experience(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    grounded_plan: Any,
    *,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    stage1_compiler: Any = None,
) -> tuple[
    tuple[_CMEEVisibleLine, ...],
    _CommonGuardSealMaterial,
    EmlisStage1Projection,
    tuple[RealizedSentenceUnit, ...],
]:
    _stage1_runtime_contract(stage1_response_schema_version)
    compiler = (
        compile_stage1_response
        if stage1_compiler is None
        else stage1_compiler
    )
    if not callable(compiler):
        raise CMEEVerticalError("stage1_compiler_invalid")
    try:
        projection, selected_units = compiler(
            source=source,
            grounded_graph=graph,
            parent_plan=plan,
            grounded_plan=grounded_plan,
        )
    except CMEEStage1ContractError as exc:
        reason_code = (
            "stage1_no_hard_valid_realization"
            if str(exc) == "stage1_no_hard_valid_realization"
            else "stage1_projection_unavailable"
        )
        raise CMEEVerticalError(reason_code) from None
    if (
        type(projection) is not EmlisStage1Projection
        or projection.schema_version != stage1_response_schema_version
    ):
        raise CMEEVerticalError("stage1_compiler_schema_version_mismatch")
    canonical_observation_lines, reception_lines = _stage1_visible_lines(
        source,
        graph,
        grounded_plan,
        projection,
        selected_units,
    )
    typed_derivation_admission_ref = (
        _stage1_v2_typed_derivation_admission_ref(
            projection,
            selected_units,
            canonical_observation_lines,
            graph=graph,
            plan=plan,
            grounded_plan=grounded_plan,
        )
        if stage1_response_schema_version
        == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        else None
    )
    composer_binding_lines = (
        canonical_observation_lines
        if stage1_response_schema_version
        == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
        else _stage1_v2_composer_binding_lines(
            source,
            graph,
            grounded_plan,
            canonical_observation_lines,
            selected_units,
        )
    )
    expected_binding_rows = [
        _cmee_composer_binding_row(line, grounded_plan)
        for line in composer_binding_lines
    ]
    expected_core_binding_rows = [
        _cmee_core_binding_projection(row) for row in expected_binding_rows
    ]
    expected_guard_binding_rows = [
        _cmee_guard_binding_projection(row) for row in expected_binding_rows
    ]
    scope = _experience_plan_projection(
        source,
        plan,
        grounded_plan,
        canonical_observation_lines,
    )
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=source.evidence_spans,
        composer_client=_CMEER4PlanBoundComposerClient(
            canonical_observation_lines,
            grounded_plan,
            composer_binding_lines=composer_binding_lines,
            typed_derivation_admission_ref=(
                typed_derivation_admission_ref
            ),
        ),
        trace_id=_stable_id("composer", source.envelope.envelope_id, plan.plan_id),
        limited_observation_scope=scope,
    )
    if candidate.status != "generated" or candidate.composer_source != "ai_generated":
        raise CMEEVerticalError("plan_bound_observation_realizer_unavailable")
    composer_meta = candidate.composer_meta if isinstance(candidate.composer_meta, dict) else {}
    core_meta = composer_meta.get("core_text_generation")
    if (
        not isinstance(core_meta, dict)
        or core_meta.get("core_id") != "emlis"
        or core_meta.get("status") != "generated"
        or type(core_meta.get("passed")) is not bool
        or core_meta.get("passed") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_core_rejected")
    binding_reflection = core_meta.get("step7_gate_binding_reflection")
    if (
        type(binding_reflection) is not dict
        or type(binding_reflection.get("binding_used")) is not bool
        or binding_reflection.get("binding_used") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_core_binding_unused")
    common_guard_material = _extract_common_guard_seal(core_meta)
    core_bindings = core_meta.get("sentence_bindings")
    raw_bindings = composer_meta.get("sentence_bindings")
    result = core_meta.get("result")
    result_meta = result.get("meta") if type(result) is dict else None
    guarded_candidate = (
        result_meta.get("candidate") if type(result_meta) is dict else None
    )
    guarded_candidate_meta = (
        guarded_candidate.get("meta") if type(guarded_candidate) is dict else None
    )
    guarded_bindings = (
        guarded_candidate_meta.get("sentence_bindings")
        if type(guarded_candidate_meta) is dict
        else None
    )
    if type(raw_bindings) is not list or not raw_bindings:
        raise CMEEVerticalError("plan_bound_observation_binding_missing")
    if type(core_bindings) is not list or len(core_bindings) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")
    if type(guarded_bindings) is not list or len(guarded_bindings) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_guarded_binding_mismatch")
    if not _json_exact_identity(raw_bindings, expected_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_exact_binding_mismatch")
    if not _json_exact_identity(guarded_bindings, expected_guard_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_guarded_exact_binding_mismatch")
    if not _json_exact_identity(core_bindings, expected_core_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_core_exact_binding_mismatch")

    outer_binding_aliases = _cmee_binding_aliases(composer_meta)
    guarded_binding_aliases = _cmee_binding_aliases(guarded_candidate_meta)
    if any(
        type(alias) is not list
        or not _json_exact_identity(alias, expected_binding_rows)
        for alias in outer_binding_aliases
    ) or any(
        type(alias) is not list
        or not _json_exact_identity(alias, expected_guard_binding_rows)
        for alias in guarded_binding_aliases
    ) or len(outer_binding_aliases) != 13 or len(guarded_binding_aliases) != 13:
        raise CMEEVerticalError("plan_bound_observation_binding_alias_mismatch")
    if any(
        type(alias) is not list
        or len(alias) != len(expected_binding_rows)
        for alias in (*outer_binding_aliases, *guarded_binding_aliases)
    ):
        raise CMEEVerticalError("plan_bound_observation_binding_alias_shape_mismatch")

    guard_rows = result_meta.get("guard_results") if type(result_meta) is dict else None
    grounding_row = (
        guard_rows[3]
        if type(guard_rows) is list and len(guard_rows) == len(EXPECTED_COMMON_GUARD_IDS)
        else None
    )
    grounding_meta = grounding_row.get("meta") if type(grounding_row) is dict else None
    sentence_claims = (
        grounding_meta.get("sentence_claims")
        if type(grounding_meta) is dict
        else None
    )
    if type(sentence_claims) is not list or len(sentence_claims) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_guarded_claim_mismatch")

    guarded_claim_sentences: list[str] = []
    for core_binding, surface_binding, guarded_binding, claim in zip(
        core_bindings,
        raw_bindings,
        guarded_bindings,
        sentence_claims,
        strict=True,
    ):
        if (
            type(core_binding) is not dict
            or type(surface_binding) is not dict
            or type(guarded_binding) is not dict
            or type(claim) is not dict
        ):
            raise CMEEVerticalError("plan_bound_observation_binding_invalid")
        for key, expected_type in (
            ("sentence_id", str),
            ("used_evidence_span_ids", list),
            ("used_phrase_unit_ids", list),
            ("relation_type", str),
            ("line_role", str),
        ):
            core_value = core_binding.get(key)
            surface_value = surface_binding.get(key)
            guarded_value = guarded_binding.get(key)
            if (
                type(core_value) is not expected_type
                or type(surface_value) is not expected_type
                or type(guarded_value) is not expected_type
                or not core_value
                or core_value != surface_value
                or core_value != guarded_value
                or (
                    expected_type is list
                    and (
                        any(type(value) is not str or not value for value in core_value)
                        or len(core_value) != len(set(core_value))
                    )
                )
            ):
                raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")
        surface_text = surface_binding.get("text")
        canonical_sentences = split_sentences(surface_text, skip_greeting=False)
        if (
            type(surface_text) is not str
            or not surface_text
            or surface_text != surface_text.strip()
            or "text" in guarded_binding
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_binding_mismatch")
        if (
            len(canonical_sentences) != 1
            or type(claim.get("sentence")) is not str
            or claim.get("sentence") != canonical_sentences[0]
            or type(claim.get("binding_present")) is not bool
            or claim.get("binding_present") is not True
            or type(claim.get("binding_used")) is not bool
            or claim.get("binding_used") is not True
            or type(claim.get("binding_sentence_id")) is not str
            or claim.get("binding_sentence_id") != surface_binding["sentence_id"]
            or type(claim.get("binding_evidence_span_ids")) is not list
            or claim.get("binding_evidence_span_ids")
            != surface_binding["used_evidence_span_ids"]
            or type(claim.get("binding_phrase_unit_ids")) is not list
            or claim.get("binding_phrase_unit_ids")
            != surface_binding["used_phrase_unit_ids"]
            or type(claim.get("binding_relation_type")) is not str
            or claim.get("binding_relation_type") != surface_binding["relation_type"]
            or type(claim.get("declared_evidence_span_ids")) is not list
            or claim.get("declared_evidence_span_ids")
            != surface_binding["used_evidence_span_ids"]
            or type(claim.get("declared_phrase_unit_ids")) is not list
            or claim.get("declared_phrase_unit_ids")
            != surface_binding["used_phrase_unit_ids"]
            or type(claim.get("evidence_span_ids")) is not list
            or any(
                type(value) is not str or not value
                for value in claim.get("evidence_span_ids")
            )
            or len(claim.get("evidence_span_ids"))
            != len(set(claim.get("evidence_span_ids")))
            or set(surface_binding["used_evidence_span_ids"])
            != set(claim.get("evidence_span_ids"))
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_claim_mismatch")
        guarded_claim_sentences.append(claim["sentence"])

    if type(candidate.comment_text) is not str or not candidate.comment_text:
        raise CMEEVerticalError("plan_bound_observation_guarded_surface_mismatch")
    guarded_surface_sentences = split_sentences(candidate.comment_text)
    guarded_claim_sentence_tuple = tuple(guarded_claim_sentences)
    if guarded_surface_sentences != guarded_claim_sentence_tuple:
        completion = composer_meta.get(
            "environment_state_output_scope_marker_completion"
        )
        marker = completion.get("scope_marker") if type(completion) is dict else None
        expected_scoped_sentences = (
            f"{marker}、{guarded_claim_sentence_tuple[0]}",
            *guarded_claim_sentence_tuple[1:],
        )
        if (
            type(completion) is not dict
            or type(completion.get("applied")) is not bool
            or completion.get("applied") is not True
            or type(marker) is not str
            or not marker
            or type(completion.get("target_line_index")) is not int
            or guarded_surface_sentences != expected_scoped_sentences
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_surface_mismatch")

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    required_owner_set = set(plan.required_observation_owner_ids)
    try:
        required_nucleus_ids = stage1_required_projection_nucleus_ids(
            source=source,
            grounded_graph=graph,
            parent_plan=plan,
            grounded_plan=grounded_plan,
        )
    except CMEEStage1ContractError:
        raise CMEEVerticalError("stage1_projection_unavailable") from None
    _planned_nucleus_ids, required_relation_ids, _planned_reception_ids = (
        _planned_visible_source_ids(grounded_plan)
    )
    if any(
        _owner_for_nucleus(source, nucleus_index[row_id])
        not in required_owner_set
        for row_id in required_nucleus_ids
    ) or any(
        _owner_for_relation(source, relation_index[row_id])
        not in required_owner_set
        for row_id in required_relation_ids
    ):
        raise CMEEVerticalError("plan_bound_observation_owner_missing")
    if candidate.comment_text != "\n".join(
        line.text for line in canonical_observation_lines
    ):
        raise CMEEVerticalError("plan_bound_observation_exact_surface_mismatch")
    observation_lines = tuple(canonical_observation_lines)
    unknown_lines = _stage1_unknown_lines(source, plan)
    reception_targets = {
        nucleus_id
        for line in reception_lines
        for nucleus_id in line.binding.nucleus_ids
    }
    lines = (*observation_lines, *unknown_lines, *reception_lines)
    observed_nuclei = {
        nucleus_id
        for line in observation_lines
        for nucleus_id in line.binding.nucleus_ids
    }
    observed_relations = {
        relation_id
        for line in observation_lines
        for relation_id in line.binding.relation_ids
    }
    if not set(required_nucleus_ids).issubset(observed_nuclei):
        raise CMEEVerticalError("post_realization_required_nucleus_mismatch")
    if not set(required_relation_ids).issubset(observed_relations):
        raise CMEEVerticalError("post_realization_required_relation_mismatch")
    if not reception_targets.issubset(observed_nuclei):
        raise CMEEVerticalError("bound_human_reception_target_not_observed")
    _validate_reception_semantic_compatibility(source, lines, projection)
    return tuple(lines), common_guard_material, projection, selected_units


def _validate_reception_semantic_compatibility(
    source: AdmittedTextSource,
    visible_lines: Sequence[Any],
    projection: EmlisStage1Projection,
) -> None:
    schema_version = projection.schema_version
    _stage1_runtime_contract(schema_version)
    lines = tuple(visible_lines)
    roles = tuple(
        "OBSERVATION"
        if line.binding.line_role == "cmee_observation"
        else (
            "UNKNOWN"
            if line.binding.line_role == "cmee_unknown"
            else "RECEPTION"
        )
        for line in lines
    )
    observation_count = roles.count("OBSERVATION")
    unknown_count = roles.count("UNKNOWN")
    reception_count = roles.count("RECEPTION")
    depth_ranges = {
        "FOCUSED": (1, 1),
        "LAYERED": (2, 3),
        "DENSE": (3, 4),
    }
    reception_floor, reception_ceiling = depth_ranges.get(
        projection.subjective_depth_class.value,
        (0, 0),
    )
    reception_semantic_count = (
        reception_count
        if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
        else len(projection.ordered_subjective_refs)
    )
    anchor_cardinality_valid = (
        observation_count == len(projection.ordered_observation_refs)
        and reception_count == len(projection.ordered_subjective_refs)
        if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
        else (
            observation_count <= len(projection.ordered_observation_refs)
            and reception_count <= len(projection.ordered_subjective_refs)
        )
    )
    if (
        not 1 <= observation_count <= 5
        or not 0 <= unknown_count <= 1
        or not 1 <= reception_count <= 4
        or not (
            reception_floor
            <= reception_semantic_count
            <= reception_ceiling
        )
        or not anchor_cardinality_valid
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(unknown_count)),
            *("RECEPTION" for _ in range(reception_count)),
        )
    ):
        raise CMEEVerticalError("reception_semantic_cardinality_mismatch")
    reception = tuple(
        line for line in lines if line.binding.line_role == "human_follow"
    )
    observation_span_ids = {
        span_id
        for line in visible_lines
        if line.binding.line_role == "cmee_observation"
        for span_id in line.binding.evidence_span_ids
    }
    source_text = "\n".join(
        str(getattr(span, "raw_text", "") or "")
        for span in source.evidence_spans
        if str(getattr(span, "span_id", "") or "") in observation_span_ids
    )
    if any(NEGATIVE_RECEPTION_RE.search(line.text) for line in reception) and not (
        _cmee_has_current_burden(source_text)
    ):
        raise CMEEVerticalError("reception_negative_meaning_promotion")


def _bind_plan_to_visible_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    visible_lines: Sequence[Any],
) -> ExperiencePlan:
    line_ids = tuple(line.sentence_id for line in visible_lines)
    return replace(
        plan,
        plan_id=_plan_id(source.envelope.envelope_id, graph.graph_id, plan, line_ids),
        visible_line_ids=line_ids,
    )


def _trace_for_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    safe_lines: Sequence[Any],
    artifact_common_guard_proof_ref: str,
    projection: EmlisStage1Projection,
    selected_units: Sequence[RealizedSentenceUnit],
) -> tuple[VisibleUnitTrace, ...]:
    schema_version = projection.schema_version
    trace_schema_version, owner_ref, _realizer_contract_ids = (
        _stage1_runtime_contract(schema_version)
    )
    node_ids = {row.node_id for row in graph.nodes}
    edge_ids = {row.edge_id for row in graph.edges}
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    units = tuple(selected_units)
    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        if any(unit.v2_trace_seal is not None for unit in units):
            raise CMEEVerticalError("stage1_v2_unit_trace_seal_invalid")
    else:
        for unit in units:
            _stage1_v2_unit_seal(unit)
    variants = {row.composition_variant_id for row in units}
    if len(variants) != 1:
        raise CMEEVerticalError("stage1_trace_variant_mismatch")
    composition_variant_id = next(iter(variants))
    observation_units = iter(row for row in units if row.layer == "LAYER_1")
    reception_units = iter(row for row in units if row.layer == "LAYER_2")
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    contribution_trace_refs: dict[str, str] = {}
    traces: list[VisibleUnitTrace] = []
    for ordinal, line in enumerate(safe_lines, start=1):
        is_reception = line.binding.line_role == "human_follow"
        is_unknown = line.binding.line_role == "cmee_unknown"
        bound_node_ids = tuple(
            _stable_id("mn", source.envelope.envelope_id, source_id)
            for source_id in line.binding.nucleus_ids
        )
        bound_edge_ids = tuple(
            _stable_id("me", source.envelope.envelope_id, source_id)
            for source_id in line.binding.relation_ids
        )
        if not set(bound_node_ids).issubset(node_ids) or not set(bound_edge_ids).issubset(edge_ids):
            raise CMEEVerticalError("visible_trace_claim_binding_missing")
        if any(source_id not in ref_by_span for source_id in line.binding.evidence_span_ids):
            raise CMEEVerticalError("visible_trace_evidence_binding_missing")
        evidence_ids = tuple(
            ref_by_span[source_id].evidence_id
            for source_id in line.binding.evidence_span_ids
        )
        role = "UNKNOWN" if is_unknown else ("RECEPTION" if is_reception else "OBSERVATION")
        operation = (
            "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            if is_unknown
            else (
                "BOUND_HUMAN_RECEPTION"
                if is_reception
                else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
            )
        )
        duty_id = (
            plan.unknown_duty_id
            if is_unknown
            else (plan.reception_duty_id if is_reception else plan.observation_duty_id)
        )
        constrained_owner_ids = (
            line.binding.constrained_owner_ids
            if is_unknown
            else ()
        )
        extension = None
        visible_unit_id = f"visible:{ordinal}"
        if role == "OBSERVATION":
            try:
                unit = next(observation_units)
            except StopIteration:
                raise CMEEVerticalError("stage1_trace_unit_coverage_mismatch") from None
            contribution_refs = unit.basis_anchor_refs
            if (
                not contribution_refs
                or len(contribution_refs) != len(set(contribution_refs))
                or (
                    schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                    and len(contribution_refs) != 1
                )
            ):
                raise CMEEVerticalError("stage1_trace_unit_anchor_invalid")
            contributions = tuple(
                contribution_by_id.get(ref) for ref in contribution_refs
            )
            if any(row is None for row in contributions) or any(
                ref in contribution_trace_refs for ref in contribution_refs
            ):
                raise CMEEVerticalError("stage1_trace_unit_anchor_invalid")
            for contribution_ref in contribution_refs:
                contribution_trace_refs[contribution_ref] = visible_unit_id
            extension_base = dict(
                schema_version=trace_schema_version,
                claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION,
                owner_ref=owner_ref,
                contribution_refs=contribution_refs,
                basis_trace_refs=(),
                interpretation_candidate_refs=_ordered(
                    ref
                    for contribution in contributions
                    for ref in contribution.interpretation_candidate_refs
                ),
                subjective_claim_ref=None,
                basis_observation_contribution_refs=(),
                value_principle_refs=(),
                speaker_owner=None,
                user_fact_effect=0,
                composition_variant_id=composition_variant_id,
            )
            if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
                extension = EmlisStage1PositiveTraceExtension(**extension_base)
            else:
                seal = _stage1_v2_unit_seal(unit)
                extension = EmlisStage1PositiveTraceExtension(
                    **extension_base,
                    subjective_claim_refs=(),
                    covered_duty_refs=seal.covered_duty_refs,
                    sentence_job_refs=seal.sentence_job_refs,
                    source_reception_act_refs=seal.source_reception_act_refs,
                    composition_candidate_ref=seal.composition_candidate_ref,
                    composition_layout_ref=seal.composition_layout_ref,
                    selected_stage1_artifact_ref=(
                        seal.selected_stage1_artifact_ref
                    ),
                )
        elif role == "RECEPTION":
            try:
                unit = next(reception_units)
            except StopIteration:
                raise CMEEVerticalError("stage1_trace_unit_coverage_mismatch") from None
            claim_refs = unit.basis_anchor_refs
            if (
                not claim_refs
                or len(claim_refs) != len(set(claim_refs))
                or (
                    schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                    and len(claim_refs) != 1
                )
            ):
                raise CMEEVerticalError("stage1_trace_unit_anchor_invalid")
            claims = tuple(claim_by_id.get(ref) for ref in claim_refs)
            if any(claim is None for claim in claims):
                raise CMEEVerticalError("stage1_trace_unit_anchor_invalid")
            basis_observation_refs = _ordered(
                ref
                for claim in claims
                for ref in claim.basis_observation_contribution_refs
            )
            if any(
                ref not in contribution_trace_refs
                for ref in basis_observation_refs
            ):
                raise CMEEVerticalError("stage1_trace_reception_basis_missing")
            extension_base = dict(
                schema_version=trace_schema_version,
                claim_domain=EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE,
                owner_ref=owner_ref,
                contribution_refs=(),
                basis_trace_refs=_ordered(
                    contribution_trace_refs[ref]
                    for ref in basis_observation_refs
                ),
                interpretation_candidate_refs=(),
                subjective_claim_ref=(
                    claim_refs[0]
                    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                    else None
                ),
                basis_observation_contribution_refs=basis_observation_refs,
                value_principle_refs=_ordered(
                    ref for claim in claims for ref in claim.value_principle_refs
                ),
                speaker_owner="EMLIS",
                user_fact_effect=0,
                composition_variant_id=composition_variant_id,
            )
            if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
                extension = EmlisStage1PositiveTraceExtension(**extension_base)
            else:
                seal = _stage1_v2_unit_seal(unit)
                extension = EmlisStage1PositiveTraceExtension(
                    **extension_base,
                    subjective_claim_refs=claim_refs,
                    covered_duty_refs=seal.covered_duty_refs,
                    sentence_job_refs=seal.sentence_job_refs,
                    source_reception_act_refs=seal.source_reception_act_refs,
                    composition_candidate_ref=seal.composition_candidate_ref,
                    composition_layout_ref=seal.composition_layout_ref,
                    selected_stage1_artifact_ref=(
                        seal.selected_stage1_artifact_ref
                    ),
                )
        traces.append(
            VisibleUnitTrace(
                visible_unit_id=visible_unit_id,
                source_sentence_id=line.sentence_id,
                source_envelope_id=source.envelope.envelope_id,
                source_version=graph.source_version,
                obligation_version=graph.obligation_version,
                owner_universe_digest=graph.owner_universe_digest,
                artifact_common_guard_proof_ref=artifact_common_guard_proof_ref,
                role=role,
                operation=operation,
                text_sha256=_sha256_text(line.text),
                duty_id=duty_id,
                meaning_node_ids=() if is_unknown else bound_node_ids,
                meaning_edge_ids=() if is_unknown else bound_edge_ids,
                evidence_ids=evidence_ids,
                constrained_by_owner_ids=constrained_owner_ids,
                emlis_stage1_extension=extension,
            )
        )
    try:
        next(observation_units)
        raise CMEEVerticalError("stage1_trace_unit_coverage_mismatch")
    except StopIteration:
        pass
    try:
        next(reception_units)
        raise CMEEVerticalError("stage1_trace_unit_coverage_mismatch")
    except StopIteration:
        pass
    return tuple(traces)


def _validate_source_owner_graph_contract(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
) -> None:
    try:
        universe = build_source_owner_universe(source.envelope, source.evidence_refs)
    except Exception:
        raise CMEEVerticalError("source_owner_universe_recompute_failed") from None
    if source.owner_universe != universe:
        raise CMEEVerticalError("source_owner_universe_mismatch")

    required = universe.required_owner_refs
    active = universe.active_optional_owner_refs
    credit = universe.credit_only_owner_refs
    if (
        len(required) != len(set(required))
        or len(active) != len(set(active))
        or len(credit) != len(set(credit))
        or set(required).intersection(active)
        or set(required).intersection(credit)
        or set(active).intersection(credit)
    ):
        raise CMEEVerticalError("source_owner_partition_invalid")
    expected_owners = required + active
    rows = graph.owner_dispositions
    actual_owners = tuple(row.meaning_owner_id for row in rows)
    if actual_owners != expected_owners or len(actual_owners) != len(set(actual_owners)):
        raise CMEEVerticalError("source_owner_denominator_mismatch")
    if (
        graph.source_envelope_id != universe.source_envelope_id
        or graph.required_owner_refs != required
        or graph.active_optional_owner_refs != active
        or graph.source_version != universe.source_version
        or graph.obligation_version != universe.obligation_version
        or graph.owner_universe_digest != universe.owner_universe_digest
    ):
        raise CMEEVerticalError("source_owner_universe_binding_mismatch")

    obligation_by_owner = {
        row.meaning_owner_id: row for row in universe.obligations
    }
    evidence_by_id = {row.evidence_id: row for row in source.evidence_refs}
    claim_by_id: dict[str, MeaningNode | MeaningEdge] = {
        **{row.node_id: row for row in graph.nodes},
        **{row.edge_id: row for row in graph.edges},
    }
    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in rows:
        obligation = obligation_by_owner.get(row.meaning_owner_id)
        if obligation is None or row.owner_class is not obligation.owner_class:
            raise CMEEVerticalError("source_owner_class_mismatch")
        if row.evidence_refs != obligation.evidence_refs or not row.evidence_refs:
            raise CMEEVerticalError("source_owner_evidence_mismatch")
        if any(
            reason_code not in SOURCE_OWNER_REASON_CODES
            for reason_code in row.reason_codes
        ):
            raise CMEEVerticalError("source_owner_reason_code_invalid")
        if any(
            evidence_id not in evidence_by_id
            or evidence_by_id[evidence_id].source_envelope_id
            != source.envelope.envelope_id
            for evidence_id in row.evidence_refs
        ):
            raise CMEEVerticalError("source_owner_cross_source_evidence")
        if (
            row.resolver_resolution is ResolverResolution.MISSING_OR_INVALID
            and row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
        ):
            raise CMEEVerticalError("source_owner_resolver_admission_mismatch")

        if row.source_owner_disposition in positive:
            expected_authority = (
                VisibleAuthority.SOURCE_EXPLICIT
                if row.source_owner_disposition
                is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
                else VisibleAuthority.SUPPLEMENTAL_USER
            )
            if (
                row.visible_authority is not expected_authority
                or not row.visible_claim_refs
                or row.target_unknown_ref is not None
                or row.reason_codes
            ):
                raise CMEEVerticalError(
                    "source_owner_positive_visible_field_mismatch"
                )
            for claim_ref in row.visible_claim_refs:
                claim = claim_by_id.get(claim_ref)
                if (
                    claim is None
                    or claim.owner_id != row.meaning_owner_id
                    or claim.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not set(claim.evidence_ids).issubset(set(row.evidence_refs))
                ):
                    raise CMEEVerticalError(
                        "source_owner_positive_visible_claim_mismatch"
                    )
        elif (
            row.source_owner_disposition
            is SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
        ):
            target = claim_by_id.get(row.target_unknown_ref or "")
            if (
                row.resolver_resolution is not ResolverResolution.UNRESOLVED
                or row.attachment_admission is not AttachmentAdmission.UNRESOLVED
                or row.visible_authority is not VisibleAuthority.NONE
                or row.target_unknown_ref is None
                or row.visible_claim_refs != (row.target_unknown_ref,)
                or not isinstance(target, MeaningNode)
                or target.owner_id != row.meaning_owner_id
                or target.epistemic_state is not EpistemicState.UNKNOWN
                or target.evidence_ids != row.evidence_refs
                or obligation.obligation_kind != "STRUCTURED_CONTEXT_ATTACHMENT"
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                raise CMEEVerticalError(
                    "source_owner_visible_unknown_field_mismatch"
                )
        elif (
            row.source_owner_disposition
            is SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
        ):
            if (
                row.resolver_resolution
                is not ResolverResolution.MISSING_OR_INVALID
                or row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
                or row.visible_authority is not VisibleAuthority.NONE
                or row.visible_claim_refs
                or row.target_unknown_ref is not None
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                raise CMEEVerticalError("source_owner_nonvisible_field_mismatch")
        else:
            raise CMEEVerticalError(
                "source_owner_disposition_unsupported_in_limited"
            )

    expected_owner_set = set(expected_owners)
    if any(row.owner_id not in expected_owner_set for row in (*graph.nodes, *graph.edges)):
        raise CMEEVerticalError("grounded_graph_owner_outside_universe")


def _validate_common_guard_proof(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    artifact: GenerationArtifactBundle,
    safe_lines: Sequence[Any],
    *,
    stage1_response_schema_version: str,
) -> None:
    """Independently verify the sealed one-shot guard proof and its bindings."""

    proof = artifact.common_guard_proof
    if type(proof) is not CommonGuardProof:
        raise CMEEVerticalError("common_guard_proof_type_mismatch")
    expected_units = tuple(
        (line.sentence_id, _sha256_text(line.text))
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    if not expected_units:
        raise CMEEVerticalError("common_guard_proof_observation_missing")
    if (
        type(proof.guarded_observation_units) is not tuple
        or proof.guarded_observation_units != expected_units
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str for value in row)
            for row in proof.guarded_observation_units
        )
    ):
        raise CMEEVerticalError("common_guard_proof_observation_binding_mismatch")
    if (
        proof.schema_version != CMEE_COMMON_GUARD_PROOF_VERSION
        or proof.source_envelope_id != source.envelope.envelope_id
        or proof.source_envelope_id != graph.source_envelope_id
        or proof.graph_id != graph.graph_id
        or proof.plan_id != artifact.plan.plan_id
    ):
        raise CMEEVerticalError("common_guard_proof_artifact_binding_mismatch")

    if type(proof.guard_results) is not tuple or len(proof.guard_results) != len(
        EXPECTED_COMMON_GUARD_IDS
    ):
        raise CMEEVerticalError("common_guard_proof_result_shape_mismatch")
    if (
        type(proof.typed_admission_refs) is not tuple
        or any(type(value) is not str for value in proof.typed_admission_refs)
    ):
        raise CMEEVerticalError("common_guard_proof_typed_admission_mismatch")
    typed_admission_ref = (
        proof.typed_admission_refs[0]
        if len(proof.typed_admission_refs) == 1
        else None
    )
    if proof.typed_admission_refs and (
        typed_admission_ref is None
        or stage1_response_schema_version
        != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        or re.fullmatch(
            (
                r"typed-source-quotation:[0-9a-f]{64}@"
                + re.escape(
                    _STAGE1_V2_TYPED_DERIVATION_ECHO_ADMISSION_POLICY
                )
            ),
            typed_admission_ref,
        )
        is None
    ):
        raise CMEEVerticalError("common_guard_proof_typed_admission_mismatch")
    if typed_admission_ref is not None:
        positive_extensions = tuple(
            row.emlis_stage1_extension
            for row in artifact.trace
            if row.role in {"OBSERVATION", "RECEPTION"}
        )
        if not positive_extensions or any(
            type(extension) is not EmlisStage1PositiveTraceExtension
            or extension.schema_version
            != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2
            or extension.owner_ref != CMEE_STAGE1_EMLIS_OWNER_REF_V2
            for extension in positive_extensions
        ):
            raise CMEEVerticalError(
                "common_guard_proof_typed_admission_trace_mismatch"
            )
    for ordinal, (expected_guard_id, row) in enumerate(zip(
        EXPECTED_COMMON_GUARD_IDS,
        proof.guard_results,
        strict=True,
    )):
        expected_raw_passed = (
            False
            if typed_admission_ref is not None and ordinal == 1
            else None
        )
        expected_disposition = (
            "TYPED_SOURCE_QUOTATION_ADMITTED"
            if typed_admission_ref is not None and ordinal == 1
            else "DIRECT"
        )
        if (
            type(row) is not CommonGuardResultProof
            or type(row.guard_id) is not str
            or row.guard_id != expected_guard_id
            or type(row.passed) is not bool
            or row.passed is not True
            or row.raw_passed is not expected_raw_passed
            or type(row.disposition) is not str
            or row.disposition != expected_disposition
        ):
            raise CMEEVerticalError("common_guard_proof_result_mismatch")

    if (
        proof.stabilization_report_name
        != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or proof.stabilization_phase != COMMON_GUARD_STABILIZATION_PHASE
        or proof.stabilization_core_id != COMMON_GUARD_STABILIZATION_CORE_ID
        or type(proof.stabilization_passed) is not bool
        or proof.stabilization_passed is not True
        or type(proof.common_shapes_ready) is not bool
        or proof.common_shapes_ready is not True
        or type(proof.stabilization_guard_names) is not tuple
        or proof.stabilization_guard_names != EXPECTED_COMMON_GUARD_IDS
        or type(proof.issue_codes) is not tuple
        or proof.issue_codes
    ):
        raise CMEEVerticalError("common_guard_proof_stabilization_mismatch")

    expected_proof_id = _common_guard_proof_id(
        source_envelope_id=proof.source_envelope_id,
        graph_id=proof.graph_id,
        plan_id=proof.plan_id,
        guarded_observation_units=proof.guarded_observation_units,
        guard_results=proof.guard_results,
        stabilization_report_name=proof.stabilization_report_name,
        stabilization_phase=proof.stabilization_phase,
        stabilization_core_id=proof.stabilization_core_id,
        stabilization_passed=proof.stabilization_passed,
        common_shapes_ready=proof.common_shapes_ready,
        stabilization_guard_names=proof.stabilization_guard_names,
        issue_codes=proof.issue_codes,
        typed_admission_refs=proof.typed_admission_refs,
    )
    if proof.proof_id != expected_proof_id:
        raise CMEEVerticalError("common_guard_proof_identity_mismatch")
    if not artifact.trace or any(
        type(row.artifact_common_guard_proof_ref) is not str
        or row.artifact_common_guard_proof_ref != proof.proof_id
        for row in artifact.trace
    ):
        raise CMEEVerticalError("common_guard_proof_trace_binding_mismatch")


def validate_positive_realization_trace(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    artifact: GenerationArtifactBundle,
    safe_lines: Sequence[Any],
    *,
    projection: EmlisStage1Projection,
    selected_units: Sequence[RealizedSentenceUnit],
) -> None:
    if type(projection) is not EmlisStage1Projection:
        raise CMEEVerticalError("stage1_projection_schema_version_invalid")
    schema_version = projection.schema_version
    _trace_schema_version, _owner_ref, realizer_contract_ids = (
        _stage1_runtime_contract(schema_version)
    )
    _validate_source_owner_graph_contract(source, graph)
    canonical_resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    canonical_grounded_plan = _build_stage1_grounded_observation_plan_for_schema(
        source,
        schema_version=schema_version,
    )
    if validate_grounded_observation_plan(canonical_grounded_plan, canonical_resolver):
        raise CMEEVerticalError("canonical_grounded_meaning_plan_invalid")
    canonical_nuclei, canonical_relations, canonical_reception_targets = (
        _planned_visible_source_ids(canonical_grounded_plan)
    )
    canonical_graph = _build_graph(
        source,
        canonical_grounded_plan,
        _ordered((*canonical_nuclei, *canonical_reception_targets)),
        canonical_relations,
    )
    if graph != canonical_graph:
        raise CMEEVerticalError("grounded_meaning_graph_source_semantic_mismatch")
    canonical_plan = _build_experience_plan(
        source,
        canonical_graph,
        canonical_grounded_plan,
        canonical_nuclei,
        canonical_relations,
        canonical_reception_targets,
    )
    units = tuple(selected_units)
    if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
        try:
            canonical_projection, canonical_units = (
                compile_stage1_response(
                    source=source,
                    grounded_graph=canonical_graph,
                    parent_plan=canonical_plan,
                    grounded_plan=canonical_grounded_plan,
                )
            )
        except CMEEStage1ContractError:
            raise CMEEVerticalError(
                "stage1_v2_canonical_compilation_unavailable"
            ) from None
        if (
            type(canonical_projection) is not EmlisStage1Projection
            or type(canonical_units) is not tuple
            or projection != canonical_projection
            or units != canonical_units
        ):
            raise CMEEVerticalError(
                "stage1_v2_canonical_compilation_mismatch"
            )
    prior_unit_ids: list[str] = []
    for unit in units:
        try:
            validate_stage1_sentence_unit(
                unit,
                projection,
                grounded_graph=canonical_graph,
                parent_plan=canonical_plan,
                prior_unit_ids=tuple(prior_unit_ids),
            )
        except CMEEStage1ContractError:
            raise CMEEVerticalError("stage1_selected_unit_invalid") from None
        prior_unit_ids.append(unit.unit_id)
    canonical_observation_lines, canonical_reception_lines = _stage1_visible_lines(
        source,
        canonical_graph,
        canonical_grounded_plan,
        projection,
        units,
    )
    canonical_unknown_lines = _stage1_unknown_lines(
        source,
        canonical_plan,
    )
    canonical_safe_lines = (
        *canonical_observation_lines,
        *canonical_unknown_lines,
        *canonical_reception_lines,
    )
    if tuple(safe_lines) != canonical_safe_lines:
        raise CMEEVerticalError("visible_line_source_semantic_mismatch")
    _validate_reception_semantic_compatibility(
        source,
        canonical_safe_lines,
        projection,
    )
    canonical_plan = _bind_plan_to_visible_lines(
        source,
        canonical_graph,
        canonical_plan,
        canonical_safe_lines,
    )
    if artifact.plan != canonical_plan:
        raise CMEEVerticalError("experience_plan_source_semantic_mismatch")
    if graph.source_envelope_id != source.envelope.envelope_id:
        raise CMEEVerticalError("graph_source_envelope_mismatch")
    owners = tuple(row.owner_id for row in graph.owner_dispositions)
    expected_owners = graph.required_owner_refs + graph.active_optional_owner_refs
    if owners != expected_owners or len(owners) != len(set(owners)):
        raise CMEEVerticalError("source_owner_denominator_mismatch")
    if graph.graph_id != _graph_id(
        source.envelope.envelope_id,
        graph.owner_universe_digest,
        graph.nodes,
        graph.edges,
        graph.owner_dispositions,
    ):
        raise CMEEVerticalError("grounded_meaning_graph_identity_mismatch")
    if artifact.plan.observation_duty_id != OBSERVATION_DUTY_ID:
        raise CMEEVerticalError("observation_duty_identity_mismatch")
    if artifact.plan.unknown_duty_id != UNKNOWN_DUTY_ID:
        raise CMEEVerticalError("unknown_duty_identity_mismatch")
    if artifact.plan.reception_duty_id != RECEPTION_DUTY_ID:
        raise CMEEVerticalError("reception_duty_identity_mismatch")
    expected_binding = (
        graph.source_envelope_id,
        graph.source_version,
        graph.obligation_version,
        graph.owner_universe_digest,
    )
    plan_binding = (
        artifact.plan.source_envelope_id,
        artifact.plan.source_version,
        artifact.plan.obligation_version,
        artifact.plan.owner_universe_digest,
    )
    if plan_binding != expected_binding:
        raise CMEEVerticalError("experience_plan_universe_binding_mismatch")
    if artifact.realizer_contract_ids != realizer_contract_ids:
        raise CMEEVerticalError("realizer_contract_identity_mismatch")
    if artifact.trust_policy_ids != _stage1_trust_policy_ids(schema_version):
        raise CMEEVerticalError("trust_policy_identity_mismatch")
    _validate_common_guard_proof(
        source,
        graph,
        artifact,
        safe_lines,
        stage1_response_schema_version=schema_version,
    )
    if artifact.plan.plan_id != _plan_id(
        source.envelope.envelope_id,
        graph.graph_id,
        artifact.plan,
        artifact.plan.visible_line_ids,
    ):
        raise CMEEVerticalError("experience_plan_identity_mismatch")
    if set(artifact.plan.visible_owner_ids).intersection(artifact.plan.unresolved_owner_ids):
        raise CMEEVerticalError("plan_owner_partition_overlap")
    if set(artifact.plan.visible_owner_ids + artifact.plan.unresolved_owner_ids) != set(owners):
        raise CMEEVerticalError("plan_owner_partition_mismatch")
    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    disposition_claims = {
        **{row.node_id: row for row in graph.nodes},
        **{row.edge_id: row for row in graph.edges},
    }
    if any(
        (row.disposition in positive and not row.visible_claim_refs)
        or len(row.visible_claim_refs) != len(set(row.visible_claim_refs))
        or any(
            ref not in disposition_claims
            or disposition_claims[ref].owner_id != row.owner_id
            or (
                row.disposition in positive
                and disposition_claims[ref].epistemic_state
                is not EpistemicState.SOURCE_EXPLICIT
            )
            for ref in row.visible_claim_refs
        )
        for row in graph.owner_dispositions
    ):
        raise CMEEVerticalError("source_owner_visible_claim_authority_mismatch")
    expected_visible_owners = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition in positive
    )
    expected_unresolved_owners = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition not in positive
    )
    if (
        artifact.plan.visible_owner_ids != expected_visible_owners
        or artifact.plan.unresolved_owner_ids != expected_unresolved_owners
    ):
        raise CMEEVerticalError("plan_owner_disposition_partition_mismatch")
    unresolved_required = tuple(
        row
        for row in graph.owner_dispositions
        if row.owner_class is OwnerClass.REQUIRED and row.disposition not in positive
    )
    expected_visible_unknown = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if source.owner_obligation(row.owner_id).obligation_kind
        == "STRUCTURED_CONTEXT_ATTACHMENT"
        and (
            row.disposition is SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
            or row in unresolved_required
        )
    )
    expected_required_unknown = tuple(
        row.owner_id for row in unresolved_required
    )
    if any(
        row.owner_id not in set(expected_visible_unknown)
        for row in unresolved_required
    ):
        raise CMEEVerticalError("required_unknown_not_safely_visible")
    if (
        artifact.plan.visible_unknown_owner_ids != expected_visible_unknown
        or artifact.plan.required_unknown_owner_ids != expected_required_unknown
    ):
        raise CMEEVerticalError("plan_required_unknown_owner_mismatch")
    if artifact.plan.visible_line_ids != tuple(line.sentence_id for line in safe_lines):
        raise CMEEVerticalError("plan_visible_line_set_mismatch")
    if len(artifact.trace) != len(safe_lines):
        raise CMEEVerticalError("visible_trace_count_mismatch")
    expected_visible_unit_ids = tuple(
        f"visible:{ordinal}" for ordinal in range(1, len(safe_lines) + 1)
    )
    if tuple(row.visible_unit_id for row in artifact.trace) != expected_visible_unit_ids:
        raise CMEEVerticalError("visible_trace_unit_identity_mismatch")
    line_roles = tuple(line.binding.line_role for line in safe_lines)
    observation_role_count = line_roles.count("cmee_observation")
    unknown_role_count = line_roles.count("cmee_unknown")
    reception_role_count = line_roles.count("human_follow")
    flattened_observation_anchors = tuple(
        ref
        for unit in units
        if unit.layer == "LAYER_1"
        for ref in unit.basis_anchor_refs
    )
    flattened_subjective_anchors = tuple(
        ref
        for unit in units
        if unit.layer == "LAYER_2"
        for ref in unit.basis_anchor_refs
    )
    role_anchor_cardinality_valid = (
        observation_role_count == len(projection.ordered_observation_refs)
        and reception_role_count == len(projection.ordered_subjective_refs)
        if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
        else (
            observation_role_count
            == sum(unit.layer == "LAYER_1" for unit in units)
            and reception_role_count
            == sum(unit.layer == "LAYER_2" for unit in units)
            and len(flattened_observation_anchors)
            == len(set(flattened_observation_anchors))
            and set(flattened_observation_anchors).issubset(
                set(projection.ordered_observation_refs)
            )
            and len(flattened_subjective_anchors)
            == len(set(flattened_subjective_anchors))
            and set(flattened_subjective_anchors).issubset(
                set(projection.ordered_subjective_refs)
            )
        )
    )
    if (
        line_roles
        != (
            *("cmee_observation" for _ in range(observation_role_count)),
            *("cmee_unknown" for _ in range(unknown_role_count)),
            *("human_follow" for _ in range(reception_role_count)),
        )
        or not role_anchor_cardinality_valid
        or unknown_role_count > 1
        or bool(unknown_role_count)
        != bool(artifact.plan.visible_unknown_owner_ids)
    ):
        raise CMEEVerticalError("visible_line_role_cardinality_mismatch")
    if any(
        (
            row.source_envelope_id,
            row.source_version,
            row.obligation_version,
            row.owner_universe_digest,
        )
        != expected_binding
        for row in artifact.trace
    ):
        raise CMEEVerticalError("visible_trace_universe_binding_mismatch")
    try:
        validate_stage1_trace_spine(
            artifact.trace,
            projection,
            grounded_graph=graph,
            parent_plan=artifact.plan,
        )
    except CMEEStage1ContractError:
        raise CMEEVerticalError("stage1_positive_trace_extension_invalid") from None
    positive_trace_rows = tuple(
        row for row in artifact.trace if row.role in {"OBSERVATION", "RECEPTION"}
    )
    if len(positive_trace_rows) != len(units):
        raise CMEEVerticalError("stage1_trace_unit_coverage_mismatch")
    for trace_row, unit in zip(positive_trace_rows, units, strict=True):
        extension = trace_row.emlis_stage1_extension
        anchor_refs = unit.basis_anchor_refs
        if (
            extension is None
            or not anchor_refs
            or len(anchor_refs) != len(set(anchor_refs))
            or (
                schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                and len(anchor_refs) != 1
            )
        ):
            raise CMEEVerticalError("stage1_trace_unit_anchor_mismatch")
        reception_claim_binding_valid = (
            extension.subjective_claim_ref == anchor_refs[0]
            and not extension.subjective_claim_refs
            if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
            else (
                extension.subjective_claim_ref is None
                and extension.subjective_claim_refs == anchor_refs
            )
        )
        if (
            extension.composition_variant_id != unit.composition_variant_id
            or (
                unit.layer == "LAYER_1"
                and (
                    trace_row.role != "OBSERVATION"
                    or extension.contribution_refs != anchor_refs
                    or extension.subjective_claim_ref is not None
                    or extension.subjective_claim_refs
                )
            )
            or (
                unit.layer == "LAYER_2"
                and (
                    trace_row.role != "RECEPTION"
                    or extension.contribution_refs
                    or not reception_claim_binding_valid
                )
            )
            or unit.layer not in {"LAYER_1", "LAYER_2"}
        ):
            raise CMEEVerticalError("stage1_trace_unit_anchor_mismatch")
        extension_seal = (
            extension.covered_duty_refs,
            extension.sentence_job_refs,
            extension.source_reception_act_refs,
            extension.composition_candidate_ref,
            extension.composition_layout_ref,
            extension.selected_stage1_artifact_ref,
        )
        if schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
            if unit.v2_trace_seal is not None or extension_seal != (
                (),
                (),
                (),
                "",
                "",
                "",
            ):
                raise CMEEVerticalError("stage1_trace_unit_seal_mismatch")
        else:
            seal = _stage1_v2_unit_seal(unit)
            if extension_seal != (
                seal.covered_duty_refs,
                seal.sentence_job_refs,
                seal.source_reception_act_refs,
                seal.composition_candidate_ref,
                seal.composition_layout_ref,
                seal.selected_stage1_artifact_ref,
            ):
                raise CMEEVerticalError("stage1_trace_unit_seal_mismatch")

    canonical_trace = _trace_for_lines(
        source,
        graph,
        artifact.plan,
        canonical_safe_lines,
        artifact.common_guard_proof.proof_id,
        projection,
        units,
    )
    canonical_positive_extensions = tuple(
        row.emlis_stage1_extension
        for row in canonical_trace
        if row.role in {"OBSERVATION", "RECEPTION"}
    )
    if tuple(
        row.emlis_stage1_extension for row in positive_trace_rows
    ) != canonical_positive_extensions:
        raise CMEEVerticalError("stage1_positive_trace_canonical_mismatch")

    unknown_lines = tuple(
        line for line in safe_lines if line.binding.line_role == "cmee_unknown"
    )
    expected_unknown_line_count = (
        1 if artifact.plan.visible_unknown_owner_ids else 0
    )
    if len(unknown_lines) != expected_unknown_line_count:
        raise CMEEVerticalError("visible_required_unknown_missing")
    covered_unknown_owners = tuple(
        owner_id
        for line in unknown_lines
        for owner_id in line.binding.constrained_owner_ids
    )
    if (
        covered_unknown_owners != artifact.plan.visible_unknown_owner_ids
        or len(covered_unknown_owners) != len(set(covered_unknown_owners))
    ):
        raise CMEEVerticalError("visible_required_unknown_coverage_mismatch")
    if unknown_lines:
        owner_unknown_span_ids = _ordered(
            source_span_id
            for owner_id in artifact.plan.visible_unknown_owner_ids
            for source_span_id in source.owner_obligation(owner_id).source_span_ids
        )
        expected_unknown_text, focus_span_ids = (
            _cmee_structured_attachment_unknown_text(
                source,
                artifact.plan,
            )
        )
        expected_unknown_span_ids = _ordered(
            (*owner_unknown_span_ids, *focus_span_ids)
        )
        unknown_line = unknown_lines[0]
        if (
            unknown_line.sentence_id != "cmee:unknown:1"
            or unknown_line.text != expected_unknown_text
            or unknown_line.binding.nucleus_ids
            or unknown_line.binding.relation_ids
            or unknown_line.binding.evidence_span_ids != expected_unknown_span_ids
            or unknown_line.binding.constrained_owner_ids
            != artifact.plan.visible_unknown_owner_ids
            or unknown_line.binding.claim_scope
            != "cmee_evidence_bound_unknown_preservation"
            or unknown_line.binding.contains_question
            or not unknown_line.binding.required
        ):
            raise CMEEVerticalError("visible_unknown_canonical_binding_mismatch")

    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    dispositions = {row.owner_id: row for row in graph.owner_dispositions}
    refs = {row.source_span_id: row for row in source.evidence_refs}
    observation_text: list[str] = []
    unknown_text: list[str] = []
    reception_text: list[str] = []
    for trace, line in zip(artifact.trace, safe_lines, strict=True):
        is_reception = line.binding.line_role == "human_follow"
        is_unknown = line.binding.line_role == "cmee_unknown"
        if not is_reception and not is_unknown and line.binding.line_role != "cmee_observation":
            raise CMEEVerticalError("visible_line_role_invalid")
        expected_role = (
            "UNKNOWN" if is_unknown else ("RECEPTION" if is_reception else "OBSERVATION")
        )
        expected_duty = (
            artifact.plan.unknown_duty_id
            if is_unknown
            else (
                artifact.plan.reception_duty_id
                if is_reception
                else artifact.plan.observation_duty_id
            )
        )
        expected_operation = (
            "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            if is_unknown
            else (
                "BOUND_HUMAN_RECEPTION"
                if is_reception
                else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
            )
        )
        expected_nodes = (
            ()
            if is_unknown
            else tuple(
                _stable_id("mn", source.envelope.envelope_id, source_id)
                for source_id in line.binding.nucleus_ids
            )
        )
        expected_edges = (
            ()
            if is_unknown
            else tuple(
                _stable_id("me", source.envelope.envelope_id, source_id)
                for source_id in line.binding.relation_ids
            )
        )
        expected_evidence = tuple(
            refs[source_id].evidence_id
            for source_id in line.binding.evidence_span_ids
        )
        expected_constraints = (
            line.binding.constrained_owner_ids
            if is_unknown
            else ()
        )
        if (
            trace.source_sentence_id != line.sentence_id
            or trace.role != expected_role
            or trace.duty_id != expected_duty
            or trace.operation != expected_operation
            or trace.text_sha256 != _sha256_text(line.text)
            or trace.meaning_node_ids != expected_nodes
            or trace.meaning_edge_ids != expected_edges
            or trace.evidence_ids != expected_evidence
            or trace.constrained_by_owner_ids != expected_constraints
        ):
            raise CMEEVerticalError("visible_trace_exact_binding_mismatch")
        if is_unknown:
            if not trace.evidence_ids or trace.meaning_node_ids or trace.meaning_edge_ids:
                raise CMEEVerticalError("visible_unknown_trace_authority_mismatch")
        else:
            if not expected_nodes and not expected_edges:
                raise CMEEVerticalError("positive_visible_claim_binding_empty")
            for node_id in trace.meaning_node_ids:
                node = nodes.get(node_id)
                row = dispositions.get(node.owner_id) if node is not None else None
                if (
                    node is None
                    or row is None
                    or row.disposition not in positive
                    or node.owner_id not in set(artifact.plan.visible_owner_ids)
                    or node.node_id not in set(row.visible_claim_refs)
                    or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not node.evidence_ids
                ):
                    raise CMEEVerticalError("visible_trace_node_authority_mismatch")
            for edge_id in trace.meaning_edge_ids:
                edge = edges.get(edge_id)
                row = dispositions.get(edge.owner_id) if edge is not None else None
                if (
                    edge is None
                    or row is None
                    or row.disposition not in positive
                    or edge.owner_id not in set(artifact.plan.visible_owner_ids)
                    or edge.edge_id not in set(row.visible_claim_refs)
                    or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not edge.evidence_ids
                ):
                    raise CMEEVerticalError("visible_trace_edge_authority_mismatch")
        for source_id in line.binding.evidence_span_ids:
            ref = refs[source_id]
            selected_raw = source.envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
            expected_normalized = next(
                str(getattr(span, "raw_text", "") or "")
                for span in source.evidence_spans
                if str(getattr(span, "span_id", "") or "") == source_id
            )
            if (
                ref.source_envelope_id != source.envelope.envelope_id
                or normalize_evidence_literal(selected_raw.decode("utf-8"))
                != expected_normalized
                or _sha256_text(selected_raw.decode("utf-8")) != ref.literal_sha256
                or _sha256_text(
                    source.envelope.raw_utf8[
                        ref.field_utf8_start : ref.field_utf8_end
                    ].decode("utf-8")
                )
                != ref.field_sha256
            ):
                raise CMEEVerticalError("visible_trace_source_locator_mismatch")
        (
            unknown_text
            if is_unknown
            else (reception_text if is_reception else observation_text)
        ).append(line.text)
    if (
        artifact.observation != "\n".join(observation_text)
        or artifact.reception != "\n".join(reception_text)
    ):
        raise CMEEVerticalError("artifact_surface_trace_mismatch")
    if (
        not observation_text
        or not reception_text
        or bool(unknown_text)
        != bool(artifact.plan.visible_unknown_owner_ids)
    ):
        raise CMEEVerticalError("artifact_duty_missing")
    expected_visible_unknowns = tuple(
        VisibleUnknownUnit(
            unknown_unit_id=trace.visible_unit_id,
            source_sentence_id=line.sentence_id,
            source_envelope_id=trace.source_envelope_id,
            source_version=trace.source_version,
            obligation_version=trace.obligation_version,
            owner_universe_digest=trace.owner_universe_digest,
            duty_id=trace.duty_id,
            text=line.text,
            owner_ids=trace.constrained_by_owner_ids,
            evidence_ids=trace.evidence_ids,
        )
        for trace, line in zip(artifact.trace, safe_lines, strict=True)
        if trace.role == "UNKNOWN"
    )
    if artifact.visible_unknowns != expected_visible_unknowns:
        raise CMEEVerticalError("visible_unknown_unit_exact_binding_mismatch")
    realized_observation_owners = {
        *(nodes[node_id].owner_id for row in artifact.trace if row.role == "OBSERVATION" for node_id in row.meaning_node_ids),
        *(edges[edge_id].owner_id for row in artifact.trace if row.role == "OBSERVATION" for edge_id in row.meaning_edge_ids),
    }
    if not set(artifact.plan.required_observation_owner_ids).issubset(
        realized_observation_owners
    ):
        raise CMEEVerticalError("required_observation_owner_realization_mismatch")
    realized_reception_owners = {
        nodes[node_id].owner_id
        for row in artifact.trace
        if row.role == "RECEPTION"
        for node_id in row.meaning_node_ids
    }
    if not set(artifact.plan.reception_target_owner_ids).issubset(
        realized_reception_owners
    ):
        raise CMEEVerticalError("reception_target_owner_realization_mismatch")
    if artifact.artifact_id != _artifact_id(
        source.envelope.envelope_id,
        graph.graph_id,
        artifact.plan.plan_id,
        artifact.common_guard_proof.proof_id,
        artifact.observation,
        tuple(row.text for row in artifact.visible_unknowns),
        artifact.reception,
        emlis_stage1_projection_ref=stage1_projection_artifact_ref(projection),
    ):
        raise CMEEVerticalError("artifact_identity_mismatch")


def _build_text_grounded_limited_artifact_for_schema(
    source: AdmittedTextSource,
    *,
    stage1_response_schema_version: str,
    stage1_compiler: Any,
) -> tuple[GroundedMeaningGraph, ExperiencePlan, GenerationArtifactBundle]:
    _trace_schema_version, _owner_ref, realizer_contract_ids = (
        _stage1_runtime_contract(stage1_response_schema_version)
    )
    if not callable(stage1_compiler):
        raise CMEEVerticalError("stage1_compiler_invalid")
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    grounded_plan = _build_stage1_grounded_observation_plan_for_schema(
        source,
        schema_version=stage1_response_schema_version,
    )
    if grounded_plan.input_profile.material_quality in {"labels_only_limited", "empty"}:
        raise CMEEVerticalError("text_grounded_material_unavailable")
    if grounded_plan.input_profile.safety_kind != TRIAGE_SAFE_OBSERVATION:
        raise CMEEVerticalError("separate_safety_owner_required")
    if validate_grounded_observation_plan(grounded_plan, resolver):
        raise CMEEVerticalError("grounded_meaning_plan_invalid")
    _cmee_assert_current_first_person_scope_supported(
        "。".join(
            str(source.normalized_current_input.get(field_path, "") or "")
            for field_path in ("memo", "memo_action")
            if str(source.normalized_current_input.get(field_path, "") or "").strip()
        ),
        grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )

    required_nucleus_ids, required_relation_ids, reception_target_ids = (
        _planned_visible_source_ids(grounded_plan)
    )
    planned_visible_nucleus_ids = _ordered((*required_nucleus_ids, *reception_target_ids))
    graph = _build_graph(
        source,
        grounded_plan,
        planned_visible_nucleus_ids,
        required_relation_ids,
    )
    plan = _build_experience_plan(
        source,
        graph,
        grounded_plan,
        required_nucleus_ids,
        required_relation_ids,
        reception_target_ids,
    )
    (
        safe_lines,
        common_guard_material,
        stage1_projection,
        selected_units,
    ) = _realize_cmee_experience(
        source,
        graph,
        plan,
        grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
        stage1_compiler=stage1_compiler,
    )
    plan = _bind_plan_to_visible_lines(source, graph, plan, safe_lines)
    observation = "\n".join(
        line.text
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    reception = "\n".join(
        line.text for line in safe_lines if line.binding.line_role == "human_follow"
    )
    common_guard_proof = _build_common_guard_proof(
        source,
        graph,
        plan,
        safe_lines,
        common_guard_material,
    )
    trace = _trace_for_lines(
        source,
        graph,
        plan,
        safe_lines,
        common_guard_proof.proof_id,
        stage1_projection,
        selected_units,
    )
    visible_unknowns = tuple(
        VisibleUnknownUnit(
            unknown_unit_id=trace_row.visible_unit_id,
            source_sentence_id=line.sentence_id,
            source_envelope_id=trace_row.source_envelope_id,
            source_version=trace_row.source_version,
            obligation_version=trace_row.obligation_version,
            owner_universe_digest=trace_row.owner_universe_digest,
            duty_id=trace_row.duty_id,
            text=line.text,
            owner_ids=trace_row.constrained_by_owner_ids,
            evidence_ids=trace_row.evidence_ids,
        )
        for trace_row, line in zip(trace, safe_lines, strict=True)
        if trace_row.role == "UNKNOWN"
    )
    artifact = GenerationArtifactBundle(
        artifact_id=_artifact_id(
            source.envelope.envelope_id,
            graph.graph_id,
            plan.plan_id,
            common_guard_proof.proof_id,
            observation,
            tuple(row.text for row in visible_unknowns),
            reception,
            emlis_stage1_projection_ref=stage1_projection_artifact_ref(
                stage1_projection
            ),
        ),
        realizer_contract_ids=realizer_contract_ids,
        trust_policy_ids=_stage1_trust_policy_ids(
            stage1_response_schema_version
        ),
        common_guard_proof=common_guard_proof,
        observation=observation,
        reception=reception,
        plan=plan,
        trace=trace,
        visible_unknowns=visible_unknowns,
    )
    validate_positive_realization_trace(
        source,
        graph,
        artifact,
        safe_lines,
        projection=stage1_projection,
        selected_units=selected_units,
    )
    return graph, plan, artifact


def build_text_grounded_limited_artifact(
    source: AdmittedTextSource,
) -> tuple[GroundedMeaningGraph, ExperiencePlan, GenerationArtifactBundle]:
    """Build the active v2 artifact through the immutable public facade."""

    return _build_text_grounded_limited_artifact_for_schema(
        source,
        stage1_response_schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        stage1_compiler=compile_stage1_response,
    )


__all__ = [
    "ADMISSIBLE_NUCLEUS_GROUNDING",
    "ADMISSIBLE_RELATION_GROUNDING",
    "CMEEVerticalError",
    "OBSERVATION_DUTY_ID",
    "RECEPTION_DUTY_ID",
    "UNKNOWN_DUTY_ID",
    "build_text_grounded_limited_artifact",
    "validate_positive_realization_trace",
]
