from __future__ import annotations

"""Pure Q1 meaning updates; successful meaning never depends on prose.

The supported correction grammar identifies a whole source clause (quoted
withdrawal), or an unambiguous occasion-bound self state. Other corrections
are explicitly unresolved. A missing parser rule is not a user-information
deficit and can never deactivate a prior claim.
"""

from dataclasses import asdict, dataclass, replace
import re

import emlis_ai_grounded_observation_plan as gp
from emlis_ai_evidence_ledger_service import EvidenceLedgerValidationReport, _detect_type
from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
from emlis_ai_safety_triage import classify_emlis_safety_triage_text, TRIAGE_SAFE_OBSERVATION

from .contracts import GenerationRequest
from .emlis_question import original_meaning_plan, validate_question_binding, _APPRAISAL_STANDARD
from .emlis_thread_contracts import (
    ANSWER_FIELD, SEMANTIC_SCHEMA, THREAD_SCHEMA, AnswerMeaningUpdateV1,
    AnswerTemporalBindingV1, EmlisAnswerUpdateItemV1, EmlisMeaningCheckpointV1,
    EmlisUnresolvedPartV1,
)
from .emlis_thread_source import AdmittedEmlisThread, admit_emlis_thread, identity

_UNKNOWN = re.compile(r"^(?:まだ|よく)?(?:分からない|わからない|分かりません|わかりません)(?:です)?$")
_CORRECTION_META = re.compile(r"^(?:書き方|記録|書いた内容|表現)(?:を|が)(?:間違えた|間違っていた|誤っていた)(?:んです|です)?$")
_WITHDRAWAL = re.compile(r"^「(?P<old>[^「」]+)」(?:という(?:記録|読み|部分))?は(?:違います|違う|誤りです|間違いです|取り消します)$")
_REPLACEMENT = re.compile(r"^「(?P<old>[^「」]+)」(?:ではなく|は誤りで)[、,]?「(?P<new>[^「」]+)」(?:です|でした)?$")
_THEN = re.compile(r"^(?:あの時|その時|当時)(?:は|も)?(?:本当は|実際は)?[、,\s]*")
_NOW = re.compile(r"^(?:今|現在)(?:は|も)[、,\s]*")
_FEELING = re.compile(r"^(?:私は|私も|自分は|私には|僕には)?(?:少し|とても|本当は|まだ|全然|あまり)?(?:嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)(?:い|かった|くない|くなかった)(?:です)?$")
_PAST = re.compile(r"(?:た|だった|でした|ました)(?:んです|のです|です)?$")
_BELIEF = re.compile(r"^.+(?:と思った|と感じた|と思いました|と感じました)$")
_FOREIGN_HOST = re.compile(r"(?:と|って).{1,16}(?:は|が|も)(?:思|感じ|言)|^(?:彼|彼女|母|父|妹|弟|兄|姉|友人|上司)(?:は|が|も)")
_PERCEIVED_REACTION = re.compile(r"^.+(?:ようで|ように感じて|気がして|と思って)[、,](?:少し|とても|まだ)?(?:重|苦し|つら|辛|怖|悲し|寂し|嬉し|うれし|軽)(?:かった|くなかった)(?:です)?$")
_SELF_CORRECTIVE_STATE = re.compile(r"^.+(?:のではなく|ではなく)[、,]?(?:私|自分)(?:では|は|も).+(?:していた|していなかった|できなかった)(?:です)?$")
_OTHER_TIME = re.compile(r"^(?:昨日|一昨日|先週|去年|昨年|別の日|翌日|今日)(?:は|も|の)?")


# A yes/no answer assesses the proposal; it does not create evidence for the
# unspecified activity. Complete personal content is still separately parsed.
_PROPOSAL_FEEDBACK = re.compile(r"^(?:はい|そうです|そうでした|その通りです|いいえ|違います|違いました|そうではありません|そういう意味ではありません)$")
_PAST_DESIRE = re.compile(
    r"(?:(?:私|わたし|僕|ぼく|俺|おれ|自分)(?:は|も))?"
    r"(?P<content>[^はがも、,。．.!！?？\s「」『』]+?)たかった(?:です)?$")


def _past_desire_source(text):
    """Finite past desiderative, without assigning its complement as fact.

    The kanji-plus-continuative inflection proof excludes bare -tai
    adjectives (cold/heavy/sleepy), quotes, foreign subjects and conditions.
    Kana-only ambiguous predicates remain unresolved rather than guessed.
    """
    match = _PAST_DESIRE.fullmatch(text)
    if match is None:
        return False
    head = match["content"]
    return bool((head in {"し", "やり", "なり"}
                 or (re.search(r"[一-鿿々〆〇]", head)
                     and re.search(r"[いきぎしじちぢにびぴみりえけげせぜてでねへべぺめれ]$", head)))
                and not re.search(r"と(?:思|言|聞|感じ)|って|なら|たら|もし|かもしれ|らしい|そう", head))


@dataclass(frozen=True, slots=True, repr=False)
class PreparedEmlisMeaning:
    thread: AdmittedEmlisThread
    original_plan: gp.GroundedObservationPlan
    accepted_nuclei: tuple[gp.GroundedSemanticNucleus, ...]
    checkpoint: EmlisMeaningCheckpointV1
    legacy_appraisal_retention: bool = False
    legacy_repeated_appraisal_context: bool = False
    legacy_received_appraisal_context: bool = False
    legacy_appraisal_reason: bool = False
    legacy_result_appraisal: bool = False
    legacy_appraisal_correction: bool = False
    legacy_duplicate_appraisal_source: bool = False
    legacy_shared_target_contrast: bool = False
    legacy_received_unfinished_context: bool = False
    legacy_received_reason_context: bool = False
    legacy_received_report_context: bool = False
    legacy_cognitive_feeling_scope: bool = False
    legacy_cognitive_temporal_topic: bool = False


def _text(row, index, resolver) -> str:
    return final_reception_source_anchor_text(row.nucleus_id, index, resolver)


def _repetition_key(text: str) -> str:
    text = re.sub(r"です$", "", text)
    # Orthographic variants of the same bounded adjective are not new meaning.
    for old, new in (("うれし", "嬉し"), ("さびし", "寂し"), ("こわ", "怖"), ("つら", "辛")):
        text = text.replace(old, new)
    return text


def _base_ref(thread, plan) -> str:
    return identity("emlis-base-meaning", thread.original.envelope.envelope_id,
                    tuple(asdict(row) for row in plan.nuclei),
                    tuple(asdict(row) for row in plan.relations))


def _dependent_refs(plan, targets: tuple[str, ...]) -> tuple[str, ...]:
    # Relations/derived readings are not allowed to revive a withdrawn endpoint.
    # The other independently sourced endpoint remains active.
    return tuple(row.relation_id for row in plan.relations
                 if row.from_nucleus_id in targets or row.to_nucleus_id in targets)


def _answer_nucleus(span, *, raw: str, about_time: str, source_start: int = 0, source_end: int | None = None, outcome_standard: bool = False, prior_answer_source: str | None = None, result_appraisal_replacement: bool = False, legacy_appraisal_answer_time: bool = False):
    """Use the shared source grammar with a real answer field and no labels."""
    text = span.raw_text
    offset = source_start
    end = len(text) if source_end is None else source_end
    bounded = text[offset:end].strip()
    # A complete ordinary answer, or a uniquely located quoted replacement,
    # can keep the existing finite adjective grammar inside an explanation.
    # Only the new complete source range owns its operators; the old quote
    # locates the target without donating its polarity or predicate.
    explanation = re.fullmatch(r"(?P<predicate>.+)の(?:です|だ|だった)", bounded)
    explained_feeling = bool(explanation
        and not explanation["predicate"].endswith("です")
        # The complete existing finite answer grammar proves the inner
        # predicate. The shared memo lexicon is not a second admission rule:
        # its stem inventory omits otherwise supported answers such as 楽し.
        and _FEELING.fullmatch(explanation["predicate"]))
    # Parse only the admitted claim range. The old text in a correction is a
    # locator, not a source of polarity/operators for the replacement claim.
    local = {ANSWER_FIELD: bounded}
    local_span = replace(span, raw_text=bounded, detected_type=_detect_type(bounded, ()))
    safety = classify_emlis_safety_triage_text(bounded)
    kind = gp._kind_for_span(local_span, roles=(), safety_decision=safety,
                            safety_span_order={}, normalized_input=local)
    frame = gp._semantic_frame_for_span(local_span, kind=kind, roles=(), claim_ids=(),
                                        normalized_input=local)
    if result_appraisal_replacement:
        predicate = gp._result_appraisal_predicate(bounded)
        if predicate and bounded.startswith('今は') and legacy_appraisal_answer_time:
            # Reproduce only the known pre-u257 rejection for saved meaning.
            return None
        attributes = gp._result_appraisal_predicate_attributes(predicate) if predicate else None
        if attributes is not None:
            polarity, time, codes = attributes
            if about_time in {'ANSWER_TIME', 'PRIOR_ANSWER_TIME'} and time != 'present':
                return None
            # Re-derive every evaluation operator from the replacement range.
            # The old quoted predicate is a locator, never a donor of meaning.
            frame = replace(frame, actor="current_user", predicate_kind="feeling", modality="feeling",
                polarity=polarity, time_scope=time, attribute_codes=(*codes,
                    f"time_scope:{time}", f"thread_time:{'original_occasion' if legacy_appraisal_answer_time else about_time.lower()}",
                    "thread_subject:revised_result_appraisal",
                    "lexical:preserve_source_predicate", "lexical:no_new_sensation_family",
                    "semantic_role:generic_relation_fragment", "semantic_role:final_stage1_compound_meaning",
                    f"source_fragment_scalar_range:{offset}:{end}",
                    "source_fragment_scalar_source:normalized_raw_text"))
            return gp.GroundedSemanticNucleus(
                f"answer:{span.span_id}", "reaction", (span.span_id,), (ANSWER_FIELD,), (span.span_id,),
                frame, "explicit", 1.0, 1.0, "required", "explicit_supplemental_answer",
                ("no_unstated_cause", "no_third_party_intention", "no_stable_personality"))
    nominal_explanation = gp._THREAD_NOMINAL_FEELING_EXPLANATION_RE.fullmatch(bounded)
    negative_nominal = (gp._THREAD_NEGATIVE_FEELING_COPULA_RE.fullmatch(bounded)
        or nominal_explanation and nominal_explanation['inner'].startswith('では'))
    nominal_feeling = bool((gp._THREAD_POSITIVE_FEELING_COPULA_RE.fullmatch(bounded)
        or negative_nominal or nominal_explanation)
        and kind not in {"event", "other_explicit"}
        and gp._source_operator_owner_scope_is_bound(bounded))
    # A finite self belief is retained as a belief, not its complement's
    # truth. The question only supplies the omitted response target.
    if outcome_standard and _past_desire_source(bounded):
        kind = "wish"
        frame = replace(frame, predicate_kind="wish", modality="wish", polarity="positive")
    elif (any(pattern.fullmatch(bounded) for pattern in (_BELIEF, _PERCEIVED_REACTION, _SELF_CORRECTIVE_STATE))
            and not _FOREIGN_HOST.search(bounded)):
        if (not _SELF_CORRECTIVE_STATE.fullmatch(bounded)
                and re.match(r"^(?!(?:私は|私が|私も|自分は|自分が|自分も|次も))[^、,「」]{1,28}?(?:は|が|も)", bounded)):
            return None
        kind = "reaction"
        frame = replace(frame, predicate_kind="feeling", modality="feeling",
                        polarity="negative" if re.search(r"ない|なかった|重|苦|つら|辛", bounded) else "neutral")
    elif _FEELING.fullmatch(bounded) or explained_feeling or nominal_feeling:
        kind = "reaction"
        negative = bool(negative_nominal or re.search(r"くない|くなかった|寂|さび|悲|苦|つら|辛|怖|こわ|重", bounded))
        frame = replace(frame, predicate_kind="feeling", modality="feeling",
                        polarity="negative" if negative else "positive",
                        # The complete answer grammar is the feeling witness,
                        # including replacements whose source has no shared
                        # lexical operator. Preserve it for every admitted
                        # positive or nominal form, independently of the self pronoun.
                        attribute_codes=(frame.attribute_codes if negative and not nominal_feeling else
                            tuple(dict.fromkeys((*frame.attribute_codes, "operator:feeling")))))
    elif not gp._source_operator_owner_scope_is_bound(bounded):
        # A uniquely located, admitted answer can keep its own finite
        # copular grammar through a degree-only correction. Do not broaden
        # initial answers or the shared memo grammar with this witness.
        copular_source = (r"(?P<owner>(?:(?:私|わたし|自分|僕|ぼく|俺|おれ)"
                          r"(?:には|にも|は|も|が))?)(?:少し|とても)"
                          r"不安(?P<copula>です|でした|だ|だった)")
        previous = re.fullmatch(copular_source, prior_answer_source or "")
        revised = re.fullmatch(copular_source, bounded)
        if not (kind == "reaction" and frame.predicate_kind == "feeling"
                and frame.modality == "feeling" and previous and revised
                and previous.groupdict() == revised.groupdict()):
            return None
    if not bounded or kind in {"event", "other_explicit"} or _FOREIGN_HOST.search(bounded):
        return None
    time_scope = "present" if about_time in {"ANSWER_TIME","PRIOR_ANSWER_TIME"} else "past"
    codes = tuple(c for c in frame.attribute_codes if not c.startswith(("time_scope:", "operator:change", "operator:positive_change")))
    frame = replace(frame, time_scope=time_scope, attribute_codes=(
        *codes, f"time_scope:{time_scope}", f"thread_time:{about_time.lower()}",
        "lexical:preserve_source_predicate", "lexical:no_new_sensation_family",
        "semantic_role:generic_relation_fragment",
        f"source_fragment_scalar_range:{offset}:{end}",
        "source_fragment_scalar_source:normalized_raw_text",
    ))
    return gp.GroundedSemanticNucleus(
        f"answer:{span.span_id}", kind, (span.span_id,), (ANSWER_FIELD,), (span.span_id,),
        frame, "explicit", 1.0, 1.0, "required", "explicit_supplemental_answer",
        ("no_unstated_cause", "no_third_party_intention", "no_stable_personality"),
    )


def _separate_reasonless_appraisal_received_source(original, thread, *, include_unfinished=False):
    """Re-prove the two unchanged source scopes before retaining their duties."""
    links = tuple(r for r in original.relations
                  if gp.source_owned_result_appraisal(r, original.nuclei))
    required = tuple(n for n in original.nuclei if n.retention == 'required')
    if len(links) != 1:
        return {}
    index = {n.nucleus_id: n for n in required}
    link = links[0]
    event, appraisal = (index.get(nid) for nid in (link.from_nucleus_id, link.to_nucleus_id))
    if event is None or appraisal is None:
        return {}
    context = (gp.source_owned_result_appraisal_context(link, original.nuclei, original.relations)
               if include_unfinished else None)
    if len(original.relations) != (3 if context else 2) or len(required) != (5 if context else 4):
        return {}
    appraisal_nodes = (context, event, appraisal) if context else (event, appraisal)
    owned = {n.nucleus_id for n in appraisal_nodes}
    rest = tuple(n for n in required if n not in appraisal_nodes)
    received_relations = tuple(r for r in original.relations
                              if not owned & {r.from_nucleus_id, r.to_nucleus_id})
    received = gp._received_contrast_group_targets(rest, received_relations)
    if not received or len(received[0]) != 1:
        return {}
    received_event, reaction = (index[ids[0]] for ids in received)
    received_relation = received_relations[0]
    if (received_relation.grounding_kind != 'user_stated_relation'
        or received_relation.source_span_ids != received_event.source_span_ids
        or (appraisal.semantic_frame.polarity, appraisal.semantic_frame.time_scope) != ('positive', 'past')
        or {c for c in appraisal.semantic_frame.attribute_codes if c.startswith('source_appraisal_')}
            != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}):
        return {}
    resolver = thread.resolver()
    for node in required:
        if (node.source_fields not in {('memo',), ('memo_action',)}
            or len(node.source_span_ids) != 1 or node.source_span_ids[0] not in resolver.span_ids
            or node.surface_anchor_ids != node.source_span_ids
            or node.semantic_frame.target_anchor_ids != node.source_span_ids
            or node.grounding_kind != 'explicit' or node.allowed_claim_scope != 'explicit_current_input'
            or node.semantic_frame.actor != 'current_user'):
            return {}
    first, last = (resolver.resolve(n.source_span_ids[0]) for n in (event, received_event))
    if first.source_field == last.source_field:
        # Field identity is not occasion identity. Two complete, disjoint
        # sentences can own separate duties in the same field. Re-prove the
        # full field and both actual windows; IDs or family tags alone do not
        # authorize retaining an unrelated/overlapping source contribution.
        a, b = sorted((first, last), key=lambda span: span.start_index)
        source = str(thread.original.normalized_current_input.get(a.source_field) or '')
        if (a.start_index != 0 or not a.end_index < b.start_index < b.end_index <= len(source)
            or source[a.start_index:a.end_index] != a.raw_text
            or source[b.start_index:b.end_index] != b.raw_text
            or re.fullmatch(r'[。．.]\s*', source[a.end_index:b.start_index]) is None
            or re.fullmatch(r'[。．.]?', source[b.end_index:]) is None
            or tuple(s.span_id for s in resolver.resolve_many(resolver.span_ids)
                     if s.source_field == a.source_field) != (a.span_id, b.span_id)):
            return {}
    else:
        for span in (first, last):
            source = str(thread.original.normalized_current_input.get(span.source_field) or '')
            if (span.start_index != 0 or span.end_index != len(span.raw_text)
                or re.fullmatch(re.escape(span.raw_text) + r'[。．.]?', source) is None
                or tuple(s.span_id for s in resolver.resolve_many(resolver.span_ids)
                         if s.source_field == span.source_field) != (span.span_id,)):
                return {}
    appraisal_rows = gp._explicit_result_appraisal_projections(
        first, thread.original.normalized_current_input)
    received_rows = gp._received_event_reaction_text_projections(last.raw_text)
    if (tuple(row.nucleus_suffix for row in appraisal_rows)
            != ((':unfinished', ':event', ':appraisal') if context else (':event', ':appraisal'))
        or tuple(row.nucleus_suffix for row in received_rows) != (':event', ':reaction')):
        return {}
    # The shared received grammar admits a broad giver token. Reusing it
    # must not turn SELF as giver into SELF as the receiver of the event.
    received_text = last.raw_text[received_rows[0].scalar_start:received_rows[0].scalar_end]
    giver = re.sub(r'^(?:私|自分|わたし)(?:は|が)', '', received_text).rpartition('に')[0]
    if (gp._SELF_REFERENCE_RE.search(giver) is not None
        or 'に' in received_text and not gp._source_operator_owner_scope_is_bound(received_text)):
        return {}
    for row, node, span in zip((*appraisal_rows, *received_rows),
            (*appraisal_nodes, received_event, reaction),
            (*((first,) * len(appraisal_nodes)), last, last), strict=True):
        frame = node.semantic_frame
        if (node.source_fields != (span.source_field,) or node.source_span_ids != (span.span_id,)
            or (row.kind, row.predicate_kind, row.polarity, row.modality, row.time_scope, row.attribute_codes)
                != (node.kind, frame.predicate_kind, frame.polarity, frame.modality,
                    frame.time_scope, frame.attribute_codes)):
            return {}
    return dict(appraisal_event=event, appraisal=appraisal, received_event=received_event,
                reaction=reaction, received_relation=received_relation,
                **({'unfinished_context': context} if context else {}))


def _retained_reasonless_shared_target_duties(original, thread, nuclei, relations, updates):
    """Keep surviving duties after one correction, without renewing the group.

    This is a response-selection proof only. It changes neither saved meaning
    nor the initial-only joint reading or the component NORMAL admission.
    """
    if len(thread.answers) != 1 or len(updates) != 1:
        return ()
    group = gp.source_owned_shared_target_appraisal_contrast(
        original.nuclei, original.relations, thread.resolver())
    if not group:
        group = _separate_reasonless_appraisal_received_source(original, thread, include_unfinished=True)
    if not group or 'reason' in group:
        return ()
    update = updates[0]
    old = group['appraisal']
    if (update.operation != 'REVISE' or update.binding_kind != 'EXPLICIT_CORRECTION'
        or update.target_meaning_refs != (old.nucleus_id,)
        or update.superseded_claim_refs != (old.nucleus_id,)
        or update.temporal_binding.about_time != 'ORIGINAL_OCCASION'):
        return ()
    answers = tuple(n for n in nuclei if n.source_fields == (ANSWER_FIELD,))
    if len(answers) != 1:
        return ()
    evaluation = answers[0]
    frame = evaluation.semantic_frame
    if (update.changed_claim_refs != (evaluation.nucleus_id,)
        or (evaluation.kind, frame.predicate_kind, frame.modality, frame.polarity,
            frame.time_scope, frame.actor) != ('reaction', 'feeling', 'feeling', 'negative', 'past', 'current_user')
        or evaluation.retention != 'required' or evaluation.grounding_kind != 'explicit'
        or evaluation.allowed_claim_scope != 'explicit_supplemental_answer'
        or {c for c in frame.attribute_codes if c.startswith('thread_time:')}
            != {'thread_time:original_occasion'}
        or {c for c in frame.attribute_codes if c.startswith('source_appraisal_')}
            != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}):
        return ()
    index = {n.nucleus_id: n for n in nuclei}
    event, received, reaction = (group[k] for k in ('appraisal_event', 'received_event', 'reaction'))
    context = group.get('unfinished_context')
    for node in (event, received, reaction, *((context,) if context else ())):
        retained = replace(node, semantic_frame=replace(node.semantic_frame,
            attribute_codes=tuple(c for c in node.semantic_frame.attribute_codes
                if c != 'semantic_dependency:shared_target_appraisal_contrast_v1'
                and not c.startswith('source_shared_target_'))))
        if index.get(node.nucleus_id) != retained:
            return ()
    expected = {event.nucleus_id, received.nucleus_id, reaction.nucleus_id, evaluation.nucleus_id}
    if context:
        expected.add(context.nucleus_id)
    if {n.nucleus_id for n in nuclei if n.retention == 'required'} != expected:
        return ()
    links = tuple(r for r in relations if gp.source_owned_result_appraisal(r, nuclei))
    if (len(links) != 1 or len(relations) != 2 or group['received_relation'] not in relations
        or (links[0].from_nucleus_id, links[0].to_nucleus_id) != (event.nucleus_id, evaluation.nucleus_id)
        or links[0].source_relation_ids != (update.update_ref,)):
        return ()
    return (('current_burden', (evaluation.nucleus_id,), (event.nucleus_id,)),
            # The old contrast ended with the superseded appraisal. Keep the
            # unchanged unfinished fact independently, without claiming it is
            # a cause or contrast of the new negative evaluation.
            *((('current_burden', (context.nucleus_id,), ()),) if context else ()),
            ('current_burden', (received.nucleus_id,), (reaction.nucleus_id,)))


def _retained_unfinished_received_duties(prepared, nuclei, relations):
    """Retain two existing duties after only the received reaction is revised.

    The unchanged appraisal and the accepted positive answer share LIMITED
    attention. This does not admit a new component reading or revive the
    superseded received contrast.
    """
    from dataclasses import fields
    if prepared is None or any(getattr(prepared, f.name) for f in fields(prepared)
                               if f.name.startswith('legacy_')):
        return ()
    original, thread, checkpoint = prepared.original_plan, prepared.thread, prepared.checkpoint
    update = checkpoint.answer_update
    if (len(thread.answers) != 1 or len(thread.control.answers) != 1
        or thread.control.current_round != 1 or checkpoint.assessment_status != 'RESOLVED'
        or checkpoint.unresolved_parts or update is None or update.disposition != 'MATERIAL_UPDATE'
        or update.unresolved_parts or len(update.updates) != 1):
        return ()
    groups = tuple((r, gp.source_owned_result_appraisal_context(r, original.nuclei, original.relations)
                      or gp.source_owned_result_appraisal_reason(r, original.nuclei, original.relations))
        for r in original.relations if gp.source_owned_result_appraisal(r, original.nuclei))
    if len(groups) != 1:
        return ()
    appraisal, context = groups[0]
    index = {n.nucleus_id: n for n in original.nuclei}
    event, evaluation = (index[nid] for nid in (appraisal.from_nucleus_id, appraisal.to_nucleus_id))
    if context is None and (
        (event.semantic_frame.modality, event.semantic_frame.polarity, event.semantic_frame.time_scope)
            != ('fact', 'neutral', 'past')
        or (evaluation.semantic_frame.predicate_kind, evaluation.semantic_frame.modality,
            evaluation.semantic_frame.polarity) != ('feeling', 'feeling', 'positive')
        or evaluation.semantic_frame.time_scope not in {'past', 'present'}
        or {c for c in evaluation.semantic_frame.attribute_codes if c.startswith('source_appraisal_')}
            != {'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked'}
        or any(c.startswith('thread_time:') for n in (event, evaluation)
               for c in n.semantic_frame.attribute_codes)):
        return ()
    relation_count = 3 if context is not None else 2
    required = tuple(n for n in original.nuclei if n.retention == 'required')
    required_ids = {n.nucleus_id for n in required}
    if (len(required) != relation_count + 2 or len(original.relations) != relation_count
        or {n.nucleus_id for n in original.nuclei if set(n.source_fields)
            & {'memo', 'memo_action', ANSWER_FIELD}} != required_ids
        or set(original.coverage_requirements.required_nucleus_ids) != required_ids
        or set(original.coverage_requirements.required_relation_ids)
            != {r.relation_id for r in original.relations}):
        return ()
    supports = ((context.nucleus_id, event.nucleus_id) if context is not None else (event.nucleus_id,))
    owned = {evaluation.nucleus_id, *supports}
    edges = tuple(r for r in original.relations if owned & {r.from_nucleus_id, r.to_nucleus_id})
    rest = tuple(n for n in required if n.nucleus_id not in owned)
    received = tuple(r for r in original.relations if r not in edges)
    if (len(edges) != relation_count - 1 or len(rest) != 2 or len(received) != 1
        or not gp._received_contrast_group_targets(rest, received)):
        return ()
    old = received[0]
    resolver = thread.resolver()
    # Preserve the original, separately owned source window. The received
    # family marker alone does not prove giver, field or relation ownership.
    if (any(n.source_fields not in {('memo',), ('memo_action',)}
            or len(n.source_span_ids) != 1 or n.source_span_ids[0] not in resolver.span_ids
            or n.surface_anchor_ids != n.source_span_ids
            or n.semantic_frame.target_anchor_ids != n.source_span_ids
            or n.allowed_claim_scope != 'explicit_current_input' for n in required)
        or any(r.retention != 'required' or r.grounding_kind != 'user_stated_relation'
            or r.source_span_ids != index[r.from_nucleus_id].source_span_ids
            or r.source_span_ids != index[r.to_nucleus_id].source_span_ids for r in original.relations)):
        return ()
    spans = tuple(resolver.resolve(sid) for sid in
        dict.fromkeys(sid for n in required for sid in n.source_span_ids))
    if (len(spans) != 2
        or {s.span_id for s in resolver.resolve_many(resolver.span_ids)
            if s.source_field in {'memo', 'memo_action'}} != {s.span_id for s in spans}
        or any(sum(s.source_field == span.source_field and s.raw_text == span.raw_text
            for s in resolver.resolve_many(resolver.span_ids)) != 1 for span in spans)):
        return ()
    if spans[0].source_field == spans[1].source_field:
        first, last = sorted(spans, key=lambda s: s.start_index)
        if not 0 <= first.start_index < first.end_index <= last.start_index < last.end_index:
            return ()
    if context is None:
        rows = gp._explicit_result_appraisal_projections(
            resolver.resolve(event.source_span_ids[0]), thread.original.normalized_current_input)
        if tuple(row.nucleus_suffix for row in rows) != (':event', ':appraisal'):
            return ()
        for row, node in zip(rows, (event, evaluation), strict=True):
            frame = node.semantic_frame
            if (row.kind, row.predicate_kind, row.polarity, row.modality, row.time_scope, row.attribute_codes) != (
                node.kind, frame.predicate_kind, frame.polarity, frame.modality, frame.time_scope, frame.attribute_codes):
                return ()
    received_text = _text(index[old.from_nucleus_id], index, resolver)
    giver = re.sub(r'^(?:私|自分|わたし)(?:は|が)', '', received_text).rpartition('に')[0]
    if (gp._SELF_REFERENCE_RE.search(giver) is not None
        or 'に' in received_text and not gp._source_operator_owner_scope_is_bound(received_text)):
        return ()
    item = update.updates[0]
    if (item.operation != 'REVISE' or item.binding_kind != 'EXPLICIT_CORRECTION'
        or item.target_meaning_refs != (old.to_nucleus_id,)
        or item.superseded_claim_refs != (old.to_nucleus_id,)
        or item.affected_dependency_refs != (old.relation_id,)
        or item.temporal_binding.about_time != 'ORIGINAL_OCCASION'
        or item.temporal_binding.anchor_source_ref != thread.original.envelope.envelope_id
        or checkpoint.accepted_update_refs != (item.update_ref,)
        or checkpoint.inactive_claim_refs != (old.to_nucleus_id, old.relation_id)
        or len(item.changed_claim_refs) != 1):
        return ()
    current = {n.nucleus_id: n for n in nuclei}
    answer_id, = item.changed_claim_refs
    answer = current.get(answer_id)
    remaining = tuple(r for r in relations if r not in edges)
    if (len(current) != len(nuclei) or len(relations) != relation_count
        or len({r.relation_id for r in relations}) != relation_count
        or any(current.get(n.nucleus_id) != n for n in original.nuclei if n.nucleus_id != old.to_nucleus_id)
        or set(current) != ({n.nucleus_id for n in original.nuclei} - {old.to_nucleus_id}) | {answer_id}
        or not set(edges).issubset(relations) or len(remaining) != 1
        or answer is None or not gp.is_grounded_positive_feeling(answer)
        or answer.source_fields != (ANSWER_FIELD,) or answer.grounding_kind != 'explicit'
        or answer.retention != 'required' or answer.allowed_claim_scope != 'explicit_supplemental_answer'
        or answer.semantic_frame.actor != 'current_user' or answer.semantic_frame.time_scope != 'past'
        or len(answer.source_span_ids) != 1
        or 'thread_subject:unique_source_clause' not in answer.semantic_frame.attribute_codes
        or {c for c in answer.semantic_frame.attribute_codes if c.startswith('thread_time:')}
            != {'thread_time:original_occasion'}):
        return ()
    relation = remaining[0]
    event = current[old.from_nucleus_id]
    if (relation.type != 'evaluation_about_event' or relation.retention != 'required'
        or (relation.from_nucleus_id, relation.to_nucleus_id) != (event.nucleus_id, answer_id)
        or relation.grounding_kind != 'user_stated_relation'
        or relation.source_relation_ids != (item.update_ref,)
        or set(relation.source_span_ids) != set(event.source_span_ids + answer.source_span_ids)
        or {n.nucleus_id for n in nuclei if n.retention == 'required'} != owned | {event.nucleus_id, answer_id}):
        return ()
    return (('lived_change', (appraisal.to_nucleus_id,), supports),
            ('lived_change', (answer_id,), ()))


def _active_plan(original, thread, added, inactive, updates, unresolved=(), *, prepared=None):
    nuclei = tuple(row for row in original.nuclei if row.nucleus_id not in inactive) + tuple(added)
    # Withdrawing an event removes its relations, not the independently
    # stated reaction/answer. Certify that loss of subject from the admitted
    # prior relation; a missing edge alone is not a withdrawal witness.
    withdrawn_events = {n.nucleus_id for n in original.nuclei
                        if n.kind == "event" and n.nucleus_id in inactive}
    detached = {r.to_nucleus_id for r in original.relations
                if r.type in {"contrast", "evaluation_about_event"}
                and r.retention == "required" and r.from_nucleus_id in withdrawn_events}
    prior_detached = {n.nucleus_id for n in original.nuclei
                      if "thread_subject:withdrawn_source_event" in n.semantic_frame.attribute_codes
                      and not any(n.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id)
                                  for r in original.relations)}
    detached.update(changed for item in updates
                    if item.operation == "REVISE" and item.target_meaning_refs
                    and set(item.target_meaning_refs) <= prior_detached
                    for changed in item.changed_claim_refs)
    # One answer can withdraw an appraisal's event and revise its evaluation.
    # Both operations refer to the same prior plan, regardless of source order.
    # The new evaluation inherits the witnessed loss of its original object.
    detached_appraisal_replacements = {n.nucleus_id for n in added
        if "thread_subject:revised_result_appraisal" in n.semantic_frame.attribute_codes}
    detached.update(changed for item in updates
                    if item.operation == "REVISE" and item.binding_kind == "EXPLICIT_CORRECTION"
                    and len(item.target_meaning_refs) == 1
                    and set(item.target_meaning_refs) <= detached
                    for changed in item.changed_claim_refs if changed in detached_appraisal_replacements)
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(dict.fromkeys((*n.semantic_frame.attribute_codes,
            "thread_subject:withdrawn_source_event"))))) if n.nucleus_id in detached else n
        for n in nuclei)
    relations = tuple(row for row in original.relations if row.relation_id not in inactive
                      and row.from_nucleus_id not in inactive and row.to_nucleus_id not in inactive)
    # Ranking ownership lasts only while all three original operands survive.
    # A withdrawn/revised operand cannot keep its untouched siblings hidden.
    chain_spans = {n.source_span_ids for n in original.nuclei
        if "semantic_dependency:received_feeling_contrast_chain" in n.semantic_frame.attribute_codes}
    incomplete = {span for span in chain_spans if sum(n.source_span_ids == span
        and "semantic_dependency:received_feeling_contrast_chain" in n.semantic_frame.attribute_codes
        for n in nuclei) != 3}
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes
            if c != "semantic_role:compound_reception_coowned_nonprimary")))
        if n.source_span_ids in incomplete else n for n in nuclei)
    safety = classify_emlis_safety_triage_text(thread.answers[-1].source.answer_text_private)
    complexity = gp._semantic_complexity(nuclei=nuclei, relations=relations, meaning_artifacts=gp._MeaningArtifacts())
    unknowns = tuple(replace(row, affected_nucleus_ids=tuple(n for n in row.affected_nucleus_ids if n not in inactive))
                     for row in original.unknown_boundaries
                     if not row.affected_nucleus_ids or not set(row.affected_nucleus_ids).issubset(inactive))
    quality = original.input_profile.material_quality
    resolver = thread.resolver()
    # Preserve the limits of this interpretation, not a claim that the user
    # does not know. Only checkpoint-owned, unreflected answer evidence is
    # admitted here; assessed repetition / bare "I don't know" is not a gap.
    by_evidence = {ref.evidence.evidence_id: ref.thread_span_id
                   for ref in resolver.qualified_refs}
    groups = []
    for part in unresolved:
        spans = tuple(by_evidence[ref] for ref in part.evidence_refs)
        # Consecutive unresolved spans are one quoted range. The ledger can
        # split inside a source quote; its original separators must survive.
        if groups and int(spans[0][1:]) == int(groups[-1][-1][1:]) + 1:
            groups[-1] = (*groups[-1], *spans)
        else:
            groups.append(spans)
    unknowns = (*unknowns, *(gp.GroundedUnknownBoundary(
        identity("answer-limit", thread.answers[-1].envelope.envelope_id,
                 spans), "answer_interpretation_unresolved", (), spans, "do_not_claim")
        for spans in groups))
    index = {row.nucleus_id: row for row in nuclei}
    # This subject relation is both a premeaning scope basis and a required
    # source relation in Observation/Reception. It asserts no cause/contrast.
    focus = thread.control.question_control_context.pending_question.decision.affected_meaning_refs
    def subject_targets(item):
        if item.operation == "ADD":
            return item.target_meaning_refs
        if (item.operation == "REVISE" and item.binding_kind == "EXPLICIT_CORRECTION"
            and any(n.nucleus_id in item.target_meaning_refs and n.kind == "reaction"
                and "semantic_dependency:received_feeling_contrast_chain" in n.semantic_frame.attribute_codes
                for n in original.nuclei)):
            return ()
        if (item.operation == "REVISE" and set(item.target_meaning_refs).issubset(focus)
                and focus and focus[0] in index):
            return (focus[0],)
        if item.operation == "REVISE":
            return tuple(dict.fromkeys(r.from_nucleus_id for r in original.relations
                if r.type == "evaluation_about_event" and r.to_nucleus_id in item.target_meaning_refs
                and r.from_nucleus_id in index))
        return ()
    about_relations = tuple(gp.GroundedSemanticRelation(
        identity("answer-target", item.update_ref, target, changed), "evaluation_about_event",
        target, changed, tuple(dict.fromkeys((*index[target].source_span_ids, *index[changed].source_span_ids))),
        "user_stated_relation", 1.0, "required", (item.update_ref,))
        for item in updates
        for target in subject_targets(item) if target in index
        for changed in item.changed_claim_refs if changed in index)
    relations = (*relations, *about_relations)
    # An explicit correction of independent source material supplies its
    # own replacement duty. It does not borrow the pending question's event.
    # Certify the admitted revision before selection, and preserve that
    # provenance when the replacement itself is revised in a later round.
    replacement_proof = "thread_subject:independent_source_replacement"
    reaction_replacement_proof = "thread_subject:revised_original_reaction"
    original_index = {n.nucleus_id: n for n in original.nuclei}
    # A replaced reaction loses its old contrast. Prove that exact prior
    # pair without inheriting its edge or borrowing the current question.
    revised_reaction_targets = {r.to_nucleus_id for r in original.relations
        if r.type == "contrast" and r.retention == "required" and r.relation_id in inactive
        and r.to_nucleus_id in inactive and r.from_nucleus_id in index
        and r.from_nucleus_id in original_index and r.to_nucleus_id in original_index
        and gp._received_contrast_group_targets(
            (original_index[r.from_nucleus_id], original_index[r.to_nucleus_id]), (r,), minimum=1)}
    revised_reaction_targets.update(n.nucleus_id for n in original.nuclei
        if n.nucleus_id in inactive and n.kind == "reaction"
        and "semantic_dependency:received_feeling_contrast_chain" in n.semantic_frame.attribute_codes
        and any(r.type == "contrast" and r.retention == "required"
            and r.relation_id in inactive and n.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id)
            for r in original.relations))
    revised_reaction_targets.update(n.nucleus_id for n in original.nuclei
        if reaction_replacement_proof in n.semantic_frame.attribute_codes
        and replacement_proof in n.semantic_frame.attribute_codes
        and not any(n.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in original.relations))
    independent_targets = {n.nucleus_id for n in original.nuclei
        if n.retention == "required" and n.grounding_kind == "explicit"
        and n.semantic_frame.actor == "current_user"
        and ((n.source_fields in {("memo",), ("memo_action",)}
              and n.allowed_claim_scope == "explicit_current_input"
              and gp._is_independent_source_material(n, safety_kind=TRIAGE_SAFE_OBSERVATION))
             or (n.source_fields == (ANSWER_FIELD,)
                 and n.allowed_claim_scope == "explicit_supplemental_answer"
                 and replacement_proof in n.semantic_frame.attribute_codes))
        and not any(r.retention == "required"
                    and n.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id)
                    for r in original.relations)}
    independent_replacements = {changed for item in updates
        if item.operation == "REVISE" and item.binding_kind == "EXPLICIT_CORRECTION"
        and len(item.target_meaning_refs) == 1
        and set(item.target_meaning_refs) <= independent_targets | revised_reaction_targets
        and set(item.target_meaning_refs) <= set(item.superseded_claim_refs)
        for changed in item.changed_claim_refs
        if changed in index
        and (set(item.target_meaning_refs) <= independent_targets or (
            (index[changed].kind, index[changed].semantic_frame.predicate_kind,
             index[changed].semantic_frame.modality, index[changed].semantic_frame.polarity,
             index[changed].semantic_frame.actor, index[changed].semantic_frame.time_scope)
            in (("reaction", "feeling", "feeling", "negative", "current_user", "past"),
                ("reaction", "feeling", "feeling", "positive", "current_user", "past"))
            and item.temporal_binding.about_time == "ORIGINAL_OCCASION"))
        and not any(changed in (r.from_nucleus_id, r.to_nucleus_id)
                                       for r in relations)}
    revised_reactions = {changed for item in updates
        if item.operation == "REVISE" and item.binding_kind == "EXPLICIT_CORRECTION"
        and len(item.target_meaning_refs) == 1
        and set(item.target_meaning_refs) <= revised_reaction_targets
        and item.temporal_binding.about_time == "ORIGINAL_OCCASION"
        for changed in item.changed_claim_refs if changed in independent_replacements
        and (index[changed].kind, index[changed].semantic_frame.predicate_kind,
             index[changed].semantic_frame.modality, index[changed].semantic_frame.polarity,
             index[changed].semantic_frame.actor, index[changed].semantic_frame.time_scope)
            in (("reaction", "feeling", "feeling", "negative", "current_user", "past"),
                ("reaction", "feeling", "feeling", "positive", "current_user", "past"))}
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(dict.fromkeys((*n.semantic_frame.attribute_codes,
            replacement_proof, *((reaction_replacement_proof,) if n.nucleus_id in revised_reactions else ()))))))
        if n.nucleus_id in independent_replacements else n
        for n in nuclei)
    # Bind distinguishable original source clauses before body-free reception
    # selection. Different evidence IDs alone cannot distinguish repeated text.
    # A chain needs the received-link operand only when an updated plan must
    # distinguish equal event words. Keep ordinary and initial projections
    # unchanged; their graph identities do not owe this occurrence proof.
    linked_events = {}
    for event in nuclei:
        if (event.kind != "event" or event.source_fields not in {("memo",), ("memo_action",)}
            or len(event.source_span_ids) != 1
            or any(c.startswith("source_received_event_link:") for c in event.semantic_frame.attribute_codes)
            or not {"semantic_dependency:received_feeling_contrast_chain", "source_received_chain_slot:event"}
                <= set(event.semantic_frame.attribute_codes)):
            continue
        text = _text(event, index, resolver)
        if not any(other.nucleus_id != event.nucleus_id and other.kind == "event"
            and len(other.source_span_ids) == 1 and other.source_span_ids != event.source_span_ids
            and other.source_fields == event.source_fields and _text(other, index, resolver) == text
            for other in nuclei):
            continue
        link = re.match(re.escape(text) + r"(のに|けれども?|けど)",
                        gp._clean(resolver.resolve(event.source_span_ids[0]).raw_text))
        if link is not None:
            code = "source_received_event_link:" + {"のに": "noni", "けど": "kedo",
                "けれど": "keredo", "けれども": "keredomo"}[link[1]]
            linked_events[event.nucleus_id] = replace(event, semantic_frame=replace(event.semantic_frame,
                attribute_codes=tuple(dict.fromkeys((*event.semantic_frame.attribute_codes, code)))))
    nuclei = tuple(linked_events.get(n.nucleus_id, n) for n in nuclei)
    index = {n.nucleus_id: n for n in nuclei}
    answer_subjects = {}
    subject_occurrences = {}
    for n in nuclei:
        if n.source_fields != (ANSWER_FIELD,):
            continue
        about = tuple(r for r in relations if r.type == "evaluation_about_event"
                      and r.retention == "required" and r.to_nucleus_id == n.nucleus_id)
        if len(about) == 1 and about[0].from_nucleus_id in index:
            event = index[about[0].from_nucleus_id]
            text = _text(event, index, resolver)
            if (event.kind == "event" and event.source_fields in {("memo",), ("memo_action",)}
                and event.semantic_frame.modality == "fact" and event.semantic_frame.time_scope == "past"
                and len(event.source_span_ids) == 1 and text.endswith(("た", "だ"))
                and not re.search(r"[「」『』…‥?？!！]", resolver.resolve(event.source_span_ids[0]).raw_text)):
                answer_subjects[n.nucleus_id] = text
                # Equal event words can still belong to separately written
                # original clauses. Prove the actual occurrence here, where
                # the admitted source envelope and its ranges are available;
                # different local evidence IDs alone do not prove separation.
                span = resolver.resolve(event.source_span_ids[0])
                ref = resolver.qualified_ref(event.source_span_ids[0]).evidence
                answer_ref = (resolver.qualified_ref(n.source_span_ids[0]).evidence
                              if len(n.source_span_ids) == 1 else None)
                ranges = tuple(c for c in event.semantic_frame.attribute_codes
                               if c.startswith("source_fragment_scalar_range:"))
                links = tuple(c for c in event.semantic_frame.attribute_codes
                              if c.startswith("source_received_event_link:"))
                times = tuple(c for c in n.semantic_frame.attribute_codes if c.startswith("thread_time:"))
                if (n.kind == "reaction" and n.semantic_frame.polarity in {"negative", "positive"}
                    and n.semantic_frame.predicate_kind == n.semantic_frame.modality == "feeling"
                    and len(n.source_span_ids) == 1
                    and answer_ref.field_path == ANSWER_FIELD
                    and answer_ref.source_envelope_id != ref.source_envelope_id
                    and about[0].grounding_kind == "user_stated_relation"
                    and len(about[0].source_span_ids) == 2
                    and set(about[0].source_span_ids) == set((*event.source_span_ids, *n.source_span_ids))
                    and event.allowed_claim_scope == "explicit_current_input"
                    and event.semantic_frame.predicate_kind == "event"
                    and {"semantic_role:final_stage1_compound_meaning",
                         "source_fragment_scalar_source:normalized_raw_text"}
                        <= set(event.semantic_frame.attribute_codes)
                    and ranges == (f"source_fragment_scalar_range:0:{len(text)}",)
                    and len(links) == len(times) == 1
                    and links[0] in {"source_received_event_link:noni", "source_received_event_link:kedo",
                                     "source_received_event_link:keredo", "source_received_event_link:keredomo"}
                    and times[0] in {"thread_time:original_occasion", "thread_time:answer_time",
                                     "thread_time:prior_answer_time"}
                    and ref.source_envelope_id == thread.original.envelope.envelope_id
                    and ref.field_path == span.source_field == event.source_fields[0]
                    and (ref.scalar_start, ref.scalar_end) == (span.start_index, span.end_index)
                    and 0 <= ref.scalar_start < ref.scalar_end
                    and thread.original.envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode() == span.raw_text
                    and re.sub(r"\s+", " ", span.raw_text).strip().startswith(text)):
                    subject_occurrences[n.nucleus_id] = (event.nucleus_id, event.source_span_ids[0], ref,
                        n.source_span_ids[0], answer_ref.evidence_id, times[0], ranges[0], links[0])
    subject_texts = tuple(answer_subjects.values())
    proof = "thread_subject:unique_source_clause"
    occurrence_proof = "thread_subject:distinct_source_occurrence:"
    distinct_occurrences = {}
    # Selected category metadata is not a written occasion. Count every
    # original text event before validating its field/scope, including a
    # malformed mixed-field event, rather than filtering unproved rows out.
    original_events = tuple(n for n in nuclei if n.kind == "event"
        and any(f in {"memo", "memo_action"} for f in n.source_fields))
    answer_ids = {n.nucleus_id for n in nuclei if n.source_fields == (ANSWER_FIELD,)}
    active_about = tuple(r for r in relations if r.type == "evaluation_about_event"
        and r.retention == "required" and r.to_nucleus_id in answer_ids)
    def separate_occurrences(ids):
        if any(nid not in subject_occurrences for nid in ids):
            return False
        rows = sorted((subject_occurrences[nid] for nid in ids), key=lambda row: row[2].scalar_start)
        return (all(len({row[column] for row in rows}) == len(rows) for column in (0, 1, 3, 4))
            and len({(row[2].source_envelope_id, row[2].field_path) for row in rows}) == 1
            and all(left[2].scalar_end <= right[2].scalar_start
                    and left[2].utf8_end <= right[2].utf8_start for left, right in zip(rows, rows[1:])))

    # A complete three-answer positive window also proves repeated words
    # inside a mixed event set. Incomplete or negative mixed windows keep
    # their existing boundary; no event may borrow another answer's source.
    full_positive_window = (len(original_events) == len(active_about) == len(answer_subjects) == 3
        and {r.from_nucleus_id for r in active_about} == {n.nucleus_id for n in original_events}
        and {r.to_nucleus_id for r in active_about} == set(answer_subjects)
        and all((index[nid].kind, index[nid].semantic_frame.predicate_kind,
                 index[nid].semantic_frame.modality, index[nid].semantic_frame.polarity)
                == ("reaction", "feeling", "feeling", "positive") for nid in answer_subjects)
        and separate_occurrences(answer_subjects))
    # A retained three-part contrast can share its event words with one
    # other answered occasion. Keep both answers and all original feelings;
    # the same existing occurrence proof still owns each range and ABOUT.
    chain_slots = tuple(tuple(n for n in nuclei
        if "semantic_dependency:received_feeling_contrast_chain" in n.semantic_frame.attribute_codes
        and "source_received_chain_slot:" + slot in n.semantic_frame.attribute_codes)
        for slot in ("event", "first", "second"))
    chain_nodes = tuple(rows[0] for rows in chain_slots) if all(len(rows) == 1 for rows in chain_slots) else ()
    chain_feeling_window = (len(chain_nodes) == 3 and 2 <= len(original_events) <= 3
        and len(active_about) == len(answer_subjects) == 2 and len(set(subject_texts)) == 1
        and chain_nodes[0].nucleus_id in {r.from_nucleus_id for r in active_about}
        and len(chain_nodes[0].source_span_ids) == 1
        and all(n.source_span_ids == chain_nodes[0].source_span_ids
                and n.source_fields == chain_nodes[0].source_fields
                and n.allowed_claim_scope == "explicit_current_input"
                and n.retention == "required" and n.grounding_kind == "explicit" for n in chain_nodes)
        and {(r.from_nucleus_id, r.to_nucleus_id) for r in relations
             if r.type == "contrast" and r.retention == "required" and r.grounding_kind == "user_stated_relation"
             and r.from_nucleus_id in {n.nucleus_id for n in chain_nodes}}
            == {(a.nucleus_id, b.nucleus_id) for a, b in zip(chain_nodes, chain_nodes[1:])}
        and all((index[nid].kind, index[nid].semantic_frame.predicate_kind,
                 index[nid].semantic_frame.modality) == ("reaction", "feeling", "feeling")
                and index[nid].semantic_frame.polarity in {"positive", "negative"} for nid in answer_subjects)
        and separate_occurrences(answer_subjects))
    for text in set(subject_texts):
        ids = tuple(nid for nid, value in answer_subjects.items() if value == text)
        if any(event.source_fields not in {("memo",), ("memo_action",)}
               or event.allowed_claim_scope != "explicit_current_input" for event in original_events):
            continue
        entirely_equal = len(set(subject_texts)) == 1 and all(
            _text(event, index, resolver) == text for event in original_events)
        if (not (entirely_equal or full_positive_window or chain_feeling_window) or len(subject_texts) != len(active_about)
            or not 2 <= len(original_events) <= 3
            or not 2 <= len(ids) <= 3 or not separate_occurrences(ids)):
            continue
        distinct_occurrences.update({nid: occurrence_proof + subject_occurrences[nid][1]
            + ":" + ":".join(subject_occurrences[nid][5:]) for nid in ids})
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=(
        *(c for c in n.semantic_frame.attribute_codes if c != proof and not c.startswith(occurrence_proof)),
        *((proof,) if n.nucleus_id in answer_subjects and subject_texts.count(answer_subjects[n.nucleus_id]) == 1 else ()),
        *((distinct_occurrences[n.nucleus_id],) if n.nucleus_id in distinct_occurrences else ()),
    ))) if n.source_fields == (ANSWER_FIELD,) else n for n in nuclei)
    # The original joint reading expires when any of its source roles or
    # relations is revised/withdrawn. Preserve surviving experiences, while
    # removing the grouped outer edge and its proof from every remaining role.
    shared_tag = "semantic_dependency:shared_target_appraisal_contrast_v1"
    if (any(shared_tag in n.semantic_frame.attribute_codes for n in nuclei)
        and not gp.source_owned_shared_target_appraisal_contrast(nuclei, relations, thread.resolver())):
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
            attribute_codes=tuple(code for code in n.semantic_frame.attribute_codes
                if code != shared_tag and not code.startswith("source_shared_target_"))))
            for n in nuclei)
        relations = tuple(row for row in relations if row.source_relation_ids
                          != ("typed_projection:shared_target_appraisal_outer_contrast_v1",))
        complexity = gp._semantic_complexity(nuclei=nuclei, relations=relations,
                                             meaning_artifacts=gp._MeaningArtifacts())
    # A withdrawal supplies no replacement claim. Keep the latest remaining
    # accepted answer in focus instead of reverting to the original memo.
    focus_ids = tuple(row.nucleus_id for row in added) or tuple(
        row.nucleus_id for row in nuclei
        if row.source_fields == (ANSWER_FIELD,) and row.retention == "required"
        and row.allowed_claim_scope == "explicit_supplemental_answer"
    )[-1:]
    response, coverage, surface, safety_policy = gp._build_response_and_policies(
        nuclei=nuclei, relations=relations, safety_decision=safety, complexity=complexity,
        material_quality=quality, include_reception_relation_support=True,
        final_source_fidelity=True,
        primary_focus_nucleus_ids=focus_ids,
        retained_reaction_groups=(_retained_reasonless_shared_target_duties(
            original, thread, nuclei, relations, updates)
            or _retained_unfinished_received_duties(prepared, nuclei, relations) if not unresolved else ()),
    )
    return replace(original, nuclei=nuclei, relations=relations, unknown_boundaries=unknowns,
        input_profile=replace(original.input_profile, nucleus_count=len(nuclei),
            relation_count=len(relations), semantic_complexity=complexity, material_quality=quality),
        response_plan=response, coverage_requirements=coverage, surface_policy=surface,
        safety_policy=safety_policy, source_contracts=(*original.source_contracts, THREAD_SCHEMA),
        referenced_evidence_span_ids=gp._all_plan_evidence_ids(nuclei, relations, unknowns),
        evidence_ledger_validation=EvidenceLedgerValidationReport(True, canonical_span_ids=resolver.span_ids))


def prepare_emlis_meaning(request: GenerationRequest) -> PreparedEmlisMeaning:
    thread = admit_emlis_thread(request)
    original = original_meaning_plan(thread)
    try:
        return _prepare_emlis_meaning_from_plan(request, thread, original)
    except ValueError as exc:
        if (str(exc) == 'emlis_checkpoint_source_prefix_mismatch'
            and thread.control.prepared_meaning_checkpoint_ref is not None and thread.answers):
            for legacy_mode in ('legacy_withdrawal_precedence', 'legacy_reason_withdrawal', 'legacy_appraisal_original_time', 'legacy_appraisal_answer_time', 'legacy_appraisal_correction'):
                try:
                    prepared = _prepare_emlis_meaning_from_plan(request, thread, original,
                        **{'legacy_withdrawal_precedence': True, legacy_mode: True})
                except ValueError as legacy_exc:
                    if str(legacy_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                        raise
                else:
                    # Require the complete old checkpoint, including any
                    # other accepted correction in the same answer.
                    return replace(prepared, legacy_appraisal_correction=True) if legacy_mode == 'legacy_appraisal_correction' else prepared
        # A saved checkpoint is an identity of the complete source-derived
        # meaning, not permission to attach an old ID to the current plan.
        # Only known historical source projections may be re-derived. A saved
        # checkpoint must pass the unchanged identity checks. A new answer
        # to an already issued legacy question has no answer checkpoint yet:
        # its question must instead pass complete canonical re-validation
        # against that same legacy plan before a new checkpoint is formed.
        legacy_question = (str(exc) == "emlis_question_noncanonical"
            and bool(thread.answers)
            and thread.control.question_control_context.pending_question is not None)
        if (str(exc) not in {"emlis_checkpoint_source_prefix_mismatch", "emlis_question_noncanonical"}
            or thread.control.prepared_meaning_checkpoint_ref is None and not legacy_question):
            raise
        # Restore pre-u320 meaning without also disabling u319's independent
        # past-experience/cognitive-feeling scope repair. The old checkpoint
        # must match in full; a saved ID cannot relabel newly recognized scope.
        prior_temporal_topic = original_meaning_plan(thread, _legacy_cognitive_temporal_topic=True)
        if (prior_temporal_topic.nuclei != original.nuclei
            or prior_temporal_topic.relations != original.relations):
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_temporal_topic)
            except ValueError as prior_exc:
                if str(prior_exc) not in {"emlis_checkpoint_source_prefix_mismatch", "emlis_question_noncanonical"}:
                    raise
            else:
                return replace(restored, legacy_cognitive_temporal_topic=True)
        # Restore the complete pre-u319 source interpretation, including its
        # old scope limitations. The immutable checkpoint still has to match;
        # it cannot be relabelled with newly recognized present feelings.
        prior_scope = original_meaning_plan(thread, _legacy_cognitive_feeling_scope=True)
        if prior_scope.nuclei != original.nuclei or prior_scope.relations != original.relations:
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_scope)
            except ValueError as prior_exc:
                if str(prior_exc) not in {"emlis_checkpoint_source_prefix_mismatch", "emlis_question_noncanonical"}:
                    raise
            else:
                return replace(restored, legacy_cognitive_feeling_scope=True)
        # Restore the complete source interpretation before the received
        # polite contrast/report-prefix correction. Keep all unrelated source
        # capabilities; an old ID must never label newly recognized meaning.
        prior_received_report = original_meaning_plan(thread, _legacy_received_report_context=True)
        if (prior_received_report.nuclei != original.nuclei
            or prior_received_report.relations != original.relations):
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_received_report)
            except ValueError as prior_exc:
                if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                    raise
            else:
                return replace(restored, legacy_received_report_context=True)
        # u304 omitted a reasoned appraisal after a received sentence. Keep
        # all other source capabilities when reproducing that complete saved
        # checkpoint or an already issued question; never replace its identity.
        prior_received_reason = original_meaning_plan(thread, _legacy_received_reason_context=True)
        if (prior_received_reason.nuclei != original.nuclei
            or prior_received_reason.relations != original.relations):
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_received_reason)
            except ValueError as prior_exc:
                if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                    raise
            else:
                return replace(restored, legacy_received_reason_context=True)
        # u298 source interpretation omitted an unfinished appraisal after a
        # received sentence. Restore only that historical source seam; all
        # newer plain/reason/shared-target capabilities in other fields stay on.
        prior_unfinished = original_meaning_plan(thread, _legacy_received_unfinished_context=True)
        if (prior_unfinished.nuclei != original.nuclei
            or prior_unfinished.relations != original.relations):
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_unfinished)
            except ValueError as prior_exc:
                if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                    raise
            else:
                return replace(restored, legacy_received_unfinished_context=True)
        prior_shared_target = original_meaning_plan(thread, _legacy_shared_target_contrast=True)
        if (prior_shared_target.nuclei != original.nuclei
            or prior_shared_target.relations != original.relations):
            # A previously saved interpretation predates the grouped reading.
            # Re-derive its complete source plan and canonical question, never
            # attach the old checkpoint identity to newly recognized meaning.
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_shared_target)
            except ValueError as prior_exc:
                if str(prior_exc) not in {"emlis_checkpoint_source_prefix_mismatch", "emlis_question_noncanonical"}:
                    raise
            else:
                return replace(restored, legacy_shared_target_contrast=True)
        prior_duplicate = original_meaning_plan(thread, _legacy_duplicate_appraisal_source=True)
        if prior_duplicate.nuclei != original.nuclei or prior_duplicate.relations != original.relations:
            # Re-derive the complete historical source and correction state;
            # never substitute the old ID into a newly interpreted checkpoint.
            modes = (None,)
            if thread.control.prepared_meaning_checkpoint_ref is not None and thread.answers:
                modes += ('legacy_withdrawal_precedence', 'legacy_reason_withdrawal',
                          'legacy_appraisal_original_time', 'legacy_appraisal_answer_time',
                          'legacy_appraisal_correction')
            for mode in modes:
                flags = {'legacy_withdrawal_precedence': True, mode: True} if mode else {}
                try:
                    restored = _prepare_emlis_meaning_from_plan(request, thread, prior_duplicate, **flags)
                except ValueError as prior_exc:
                    if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                        raise
                else:
                    return replace(restored, legacy_duplicate_appraisal_source=True,
                        legacy_appraisal_correction=mode == 'legacy_appraisal_correction')
        prior_retention = original_meaning_plan(thread, _legacy_appraisal_retention=True,
            _legacy_duplicate_appraisal_source=True)
        if prior_retention.nuclei != original.nuclei or prior_retention.relations != original.relations:
            modes = ({},)
            if thread.control.prepared_meaning_checkpoint_ref is not None and thread.answers:
                modes += tuple({'legacy_withdrawal_precedence': True, name: True} for name in (
                    'legacy_withdrawal_precedence', 'legacy_reason_withdrawal', 'legacy_appraisal_original_time',
                    'legacy_appraisal_answer_time', 'legacy_appraisal_correction'))
            for options in modes:
                try:
                    restored = _prepare_emlis_meaning_from_plan(request, thread, prior_retention, **options)
                except ValueError as prior_exc:
                    if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                        raise
                else:
                    return replace(restored, legacy_appraisal_retention=True,
                        legacy_appraisal_correction=bool(options.get('legacy_appraisal_correction')))
        prior_repeated = original_meaning_plan(thread, _legacy_repeated_appraisal_context=True,
            _legacy_appraisal_retention=True)
        if prior_repeated.nuclei != original.nuclei or prior_repeated.relations != original.relations:
            modes = ({},)
            if thread.control.prepared_meaning_checkpoint_ref is not None and thread.answers:
                modes += tuple({'legacy_withdrawal_precedence': True, name: True} for name in (
                    'legacy_withdrawal_precedence', 'legacy_reason_withdrawal', 'legacy_appraisal_original_time',
                    'legacy_appraisal_answer_time', 'legacy_appraisal_correction'))
            for options in modes:
                try:
                    restored = _prepare_emlis_meaning_from_plan(request, thread, prior_repeated, **options)
                except ValueError as prior_exc:
                    if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                        raise
                else:
                    return replace(restored, legacy_repeated_appraisal_context=True,
                        legacy_appraisal_correction=bool(options.get('legacy_appraisal_correction')))
        prior_context = original_meaning_plan(thread, _legacy_received_appraisal_context=True,
            _legacy_repeated_appraisal_context=True, _legacy_appraisal_retention=True)
        if prior_context.nuclei != original.nuclei or prior_context.relations != original.relations:
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_context)
            except ValueError as prior_exc:
                if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                    raise
            else:
                return replace(restored, legacy_received_appraisal_context=True)
        prior_reason = original_meaning_plan(thread, _legacy_appraisal_reason=True,
            _legacy_received_appraisal_context=True, _legacy_repeated_appraisal_context=True,
            _legacy_appraisal_retention=True)
        if prior_reason.nuclei != original.nuclei or prior_reason.relations != original.relations:
            try:
                restored = _prepare_emlis_meaning_from_plan(request, thread, prior_reason)
            except ValueError as prior_exc:
                if str(prior_exc) not in {'emlis_checkpoint_source_prefix_mismatch', 'emlis_question_noncanonical'}:
                    raise
            else:
                return replace(restored, legacy_appraisal_reason=True)
        legacy = original_meaning_plan(thread, _legacy_result_appraisal=True, _legacy_appraisal_retention=True)
        if legacy.nuclei == original.nuclei and legacy.relations == original.relations:
            raise
        prepared = _prepare_emlis_meaning_from_plan(request, thread, legacy)
        return replace(prepared, legacy_result_appraisal=True)


def _prepare_emlis_meaning_from_plan(request, thread, original, *, legacy_appraisal_correction=False, legacy_appraisal_answer_time=False, legacy_appraisal_original_time=False, legacy_reason_withdrawal=False, legacy_withdrawal_precedence=False):
    if thread.control.capability_snapshot == "Q3_PREMIUM" and thread.control.admitted_history and not thread.answers:
        from .emlis_thread_history import frame_supported_focus
        focus = frame_supported_focus(thread, original)
        if focus:
            focus = tuple(dict.fromkeys((*focus, *(r.to_nucleus_id for r in original.relations if r.from_nucleus_id in focus))))
            safety = classify_emlis_safety_triage_text(" ".join(str(thread.original.normalized_current_input.get(k, "")) for k in ("memo", "memo_action")))
            response, coverage, surface, policy = gp._build_response_and_policies(
                nuclei=original.nuclei, relations=original.relations, safety_decision=safety,
                complexity=original.input_profile.semantic_complexity,
                material_quality=original.input_profile.material_quality,
                include_reception_relation_support=True, final_source_fidelity=True,
                primary_focus_nucleus_ids=focus)
            original = replace(original, response_plan=response, coverage_requirements=coverage,
                               surface_policy=surface, safety_policy=policy)
    if thread.control.capability_snapshot.startswith("Q3_") and thread.answers:
        plan = original
        accepted, inactive = (), ()
        for count in range(1, len(thread.answers) + 1):
            control = thread.control.question_control_context
            questions = control.issued_questions[:count]
            prefix_control = replace(control, pending_question=questions[-1],
                issued_questions=questions, issued_count=count,
                asked_target_refs=control.asked_target_refs[:count])
            prefix_request = replace(request, emlis_thread=replace(thread.control,
                answers=thread.control.answers[:count], current_round=count,
                question_control_context=prefix_control, prepared_meaning_checkpoint_ref=None))
            prefix = admit_emlis_thread(prefix_request)
            prepared = _prepare_answer(prefix, plan, legacy_appraisal_correction=legacy_appraisal_correction,
                legacy_appraisal_answer_time=legacy_appraisal_answer_time,
                legacy_appraisal_original_time=legacy_appraisal_original_time,
                legacy_reason_withdrawal=legacy_reason_withdrawal,
                legacy_withdrawal_precedence=legacy_withdrawal_precedence)
            cp = prepared.checkpoint
            accepted = tuple(dict.fromkeys((*accepted, *cp.accepted_update_refs)))
            inactive = tuple(dict.fromkeys((*inactive, *cp.inactive_claim_refs)))
            cp = replace(cp, accepted_update_refs=accepted, inactive_claim_refs=inactive)
            prepared = replace(prepared, checkpoint=cp)
            if count < len(thread.answers):
                if cp.answer_update.disposition != "MATERIAL_UPDATE" or cp.assessment_status != "RESOLVED":
                    raise ValueError("emlis_q3_unresolved_predecessor")
                plan = build_updated_grounded_plan(prepared)
        if thread.control.prepared_meaning_checkpoint_ref not in {None, cp.checkpoint_id}:
            raise ValueError("emlis_checkpoint_source_prefix_mismatch")
        return prepared
    return _prepare_answer(thread, original, legacy_appraisal_correction=legacy_appraisal_correction,
        legacy_appraisal_answer_time=legacy_appraisal_answer_time,
        legacy_appraisal_original_time=legacy_appraisal_original_time,
        legacy_reason_withdrawal=legacy_reason_withdrawal,
        legacy_withdrawal_precedence=legacy_withdrawal_precedence)


def _prepare_answer(thread, original, *, legacy_appraisal_correction=False, legacy_appraisal_answer_time=False, legacy_appraisal_original_time=False, legacy_reason_withdrawal=False, legacy_withdrawal_precedence=False):
    base = _base_ref(thread, original)
    if not thread.answers:
        checkpoint = EmlisMeaningCheckpointV1(
            identity("emlis-checkpoint", thread.source_prefix_ref, base),
            thread.source_prefix_ref, base, None, "RESOLVED", (), (), (),
        )
        if thread.control.prepared_meaning_checkpoint_ref not in {None, checkpoint.checkpoint_id}:
            raise ValueError("emlis_checkpoint_source_prefix_mismatch")
        return PreparedEmlisMeaning(thread, original, (), checkpoint)
    validate_question_binding(thread, original)
    answer = thread.answers[-1]
    if classify_emlis_safety_triage_text(answer.source.answer_text_private).safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
        raise ValueError("separate_safety_owner_required")
    resolver = thread.resolver()
    index = {row.nucleus_id: row for row in original.nuclei}
    question = thread.control.question_control_context.pending_question
    focus = question.decision.affected_meaning_refs
    outcome_standard = question.decision.target_kind == _APPRAISAL_STANDARD
    spans = tuple(resolver.resolve(sid) for sid in resolver.span_ids
                  if resolver.qualified_ref(sid).source_envelope_id == answer.envelope.envelope_id)
    # Resolve quote ownership before either clause interpretation or the
    # answer-wide correction flag. A quoted report cannot authorize revision
    # of the user's original reaction, even when a later self answer is valid.
    quoted_span_ids = set()
    for span in spans:
        prefix = answer.source.answer_text_private[:resolver.qualified_ref(span.span_id).evidence.scalar_start]
        quoted_depth = 0
        for character in prefix:
            if character in "「『":
                quoted_depth += 1
            elif character in "」』":
                quoted_depth = max(0, quoted_depth - 1)
        if quoted_depth:
            quoted_span_ids.add(span.span_id)
    correcting_then = any(span.span_id not in quoted_span_ids
                          and _CORRECTION_META.fullmatch(span.raw_text) for span in spans)
    updates, unresolved, added, inactive = [], [], [], []
    known_unchanged = False
    for span in spans:
        text = span.raw_text
        ev = (resolver.qualified_ref(span.span_id).evidence.evidence_id,)
        # The legacy ledger can split a reported quotation at punctuation.
        # Its interior remains unresolved, not a self answer or correction.
        if span.span_id in quoted_span_ids:
            unresolved.append(EmlisUnresolvedPartV1(ev, "answer_syntax_unsupported"))
            continue
        if _CORRECTION_META.fullmatch(text):
            continue
        if outcome_standard and _PROPOSAL_FEEDBACK.fullmatch(text):
            # The proposal never entered the claim graph, so rejection cannot
            # withdraw an original source and assent cannot invent its object.
            known_unchanged = True
            continue
        if _UNKNOWN.fullmatch(text):
            known_unchanged = True
            continue
        withdrawal = _WITHDRAWAL.fullmatch(text)
        replacement = _REPLACEMENT.fullmatch(text)
        then, now = _THEN.match(text), _NOW.match(text)
        targets: tuple[str, ...] = ()
        operation, binding = "ADD", "QUESTION_FOCUS"
        temporal_anchor = thread.original.envelope.envelope_id
        prior_answer_time = False
        if withdrawal or replacement:
            correction = withdrawal or replacement
            quoted = correction.group("old").rstrip("。．.")
            targets = tuple(row.nucleus_id for row in original.nuclei
                            if set(row.source_fields) & {"memo", "memo_action", ANSWER_FIELD}
                            and _text(row, index, resolver).rstrip("。．.") == quoted)
            # Only a uniquely located, complete appraisal source can withdraw
            # its owned pair (or proven reason + pair). Keep the full span
            # closure: unrelated/extra nuclei must not join the withdrawal.
            whole_appraisal = False
            if withdrawal and (not targets or not legacy_withdrawal_precedence):
                groups = []
                for relation in original.relations:
                    if not gp.source_owned_result_appraisal(relation, original.nuclei):
                        continue
                    event = index[relation.from_nucleus_id]
                    if resolver.resolve(event.source_span_ids[0]).raw_text.rstrip("。．.") != quoted:
                        continue
                    group = (relation.from_nucleus_id, relation.to_nucleus_id)
                    reason = None if legacy_reason_withdrawal else gp.source_owned_result_appraisal_reason(
                        relation, original.nuclei, original.relations)
                    if reason is not None:
                        group = (*group, reason.nucleus_id)
                    if {n.nucleus_id for n in original.nuclei
                        if n.source_fields == event.source_fields
                        and n.source_span_ids == event.source_span_ids} == set(group):
                        groups.append(group)
                # Count both representations of source occurrences. A direct
                # generic match must not hide another proven whole sentence.
                # Historical checkpoint replay alone keeps the old precedence.
                if len(targets) + len(groups) > 1:
                    targets = ()
                elif len(groups) == 1:
                    targets, whole_appraisal = groups[0], True
            if len(targets) != 1 and not whole_appraisal:
                unresolved.append(EmlisUnresolvedPartV1(ev, "correction_target_unresolved"))
                continue
            operation, binding, about = "WITHDRAW" if withdrawal else "REVISE", "EXPLICIT_CORRECTION", "ORIGINAL_OCCASION"
            target_nucleus = index[targets[0]]
            target_times = set(target_nucleus.semantic_frame.attribute_codes)
            if target_nucleus.source_fields == (ANSWER_FIELD,) and target_times & {"thread_time:answer_time","thread_time:prior_answer_time"}:
                about = "ANSWER_TIME"
                prior_answer_time = True
                temporal_anchor = next((x.split(":",1)[1] for x in target_times if x.startswith("thread_time_anchor:")),
                    resolver.qualified_ref(target_nucleus.source_span_ids[0]).source_envelope_id)
            appraisal_replacement = not legacy_appraisal_correction and (
                gp._thread_withdrawn_result_appraisal(target_nucleus, original.relations)
                or any(r.to_nucleus_id == target_nucleus.nucleus_id
                    and gp.source_owned_result_appraisal(r, original.nuclei) for r in original.relations))
            # The quoted old text locates the claim. Only the new range can
            # supply a deictic time, bound to this answer's source envelope.
            if (replacement and appraisal_replacement and not legacy_appraisal_answer_time
                and replacement['new'].startswith('今は')
                and gp._result_appraisal_predicate(replacement['new'])):
                now = _NOW.match(replacement['new'])
                about, temporal_anchor, prior_answer_time = 'ANSWER_TIME', answer.envelope.envelope_id, False
            elif (replacement and appraisal_replacement and not legacy_appraisal_answer_time
                and not legacy_appraisal_original_time and prior_answer_time and replacement['new'].startswith('その時は')
                and gp._result_appraisal_predicate(replacement['new'])):
                then = _THEN.match(replacement['new'])
                about, temporal_anchor, prior_answer_time = 'ORIGINAL_OCCASION', thread.original.envelope.envelope_id, False
            nucleus = None if withdrawal else _answer_nucleus(span, raw=answer.source.answer_text_private,
                about_time="PRIOR_ANSWER_TIME" if prior_answer_time else about, source_start=replacement.start("new"), source_end=replacement.end("new"), outcome_standard=outcome_standard,
                prior_answer_source=quoted if target_nucleus.source_fields == (ANSWER_FIELD,) else None,
                result_appraisal_replacement=appraisal_replacement,
                legacy_appraisal_answer_time=legacy_appraisal_answer_time)
            if nucleus and prior_answer_time:
                nucleus = replace(nucleus,semantic_frame=replace(nucleus.semantic_frame,
                    attribute_codes=(*nucleus.semantic_frame.attribute_codes,"thread_time_anchor:"+temporal_anchor)))
            if replacement and nucleus is None:
                unresolved.append(EmlisUnresolvedPartV1(ev, "correction_replacement_unsupported"))
                operation = "WITHDRAW"
        else:
            if _OTHER_TIME.match(text):
                unresolved.append(EmlisUnresolvedPartV1(ev, "explicit_other_time_target_unresolved"))
                continue
            about = "ANSWER_TIME" if now else "ORIGINAL_OCCASION" if then or _PAST.search(text) else "UNRESOLVED"
            if about == "UNRESOLVED":
                unresolved.append(EmlisUnresolvedPartV1(ev, "answer_target_time_unresolved"))
                continue
            offset = (then.end() if then else now.end() if now else 0)
            nucleus = _answer_nucleus(span, raw=answer.source.answer_text_private,
                                      about_time=about, source_start=offset, outcome_standard=outcome_standard)
            if nucleus is None:
                unresolved.append(EmlisUnresolvedPartV1(ev, "answer_syntax_unsupported"))
                continue
            targets = tuple(focus[:1])
            if now:
                binding = "SAME_OCCASION_CURRENT_STATE"
            elif then and correcting_then:
                candidates = tuple(row.nucleus_id for row in original.nuclei
                    if row.nucleus_id in focus and row.kind in {"reaction", "state", "value"}
                    and set(row.source_fields) & {"memo", "memo_action", ANSWER_FIELD})
                if len(candidates) != 1:
                    unresolved.append(EmlisUnresolvedPartV1(ev, "correction_target_unresolved"))
                    continue
                targets, operation, binding = candidates, "REVISE", "EXPLICIT_CORRECTION"
            # Exact source-semantic repetition is assessed, not relabelled as
            # a fresh interpretation. Politeness alone cannot change meaning.
            normalized = _repetition_key(text[offset:])
            if (operation == "ADD" and about == "ORIGINAL_OCCASION"
                    and any(_repetition_key(_text(row, index, resolver)) == normalized
                            and row.semantic_frame.actor == nucleus.semantic_frame.actor
                            and row.semantic_frame.time_scope == nucleus.semantic_frame.time_scope
                            and row.semantic_frame.polarity == nucleus.semantic_frame.polarity
                            for row in original.nuclei if row.nucleus_id in focus)):
                known_unchanged = True
                continue
        temporal = AnswerTemporalBindingV1(about, temporal_anchor,
            ev if then or now else (), "revision_of_answer_time" if prior_answer_time else "answer_deictic_now" if now else None)
        superseded = targets if operation in {"REVISE", "WITHDRAW"} else ()
        dependencies = _dependent_refs(original, superseded)
        changed = (nucleus.nucleus_id,) if nucleus else ()
        item = EmlisAnswerUpdateItemV1(
            identity("emlis-update", answer.envelope.envelope_id, ev, operation, targets, changed, about),
            binding, targets, ev, temporal, operation, changed, superseded, dependencies)
        updates.append(item)
        inactive.extend((*superseded, *dependencies))
        if nucleus:
            added.append(nucleus)
    if not updates and not unresolved and not known_unchanged:
        unresolved.append(EmlisUnresolvedPartV1(tuple(row.evidence_id for row in answer.evidence_refs),
                                               "answer_syntax_unsupported"))
    disposition = "MATERIAL_UPDATE" if updates else "UNRESOLVED" if unresolved else "NO_MATERIAL_UPDATE"
    new_meaning = identity("emlis-meaning", base, tuple(asdict(x) for x in updates)) if updates else base
    update = AnswerMeaningUpdateV1(answer.envelope.envelope_id, question.question_id, base,
                                   tuple(updates), tuple(unresolved), disposition, new_meaning)
    checkpoint = EmlisMeaningCheckpointV1(
        identity("emlis-checkpoint", thread.source_prefix_ref, base, asdict(update)),
        thread.source_prefix_ref, base, update,
        "PARTIAL" if updates and unresolved else "UNRESOLVED" if unresolved else "RESOLVED",
        tuple(row.update_ref for row in updates), tuple(dict.fromkeys(inactive)), tuple(unresolved))
    # The server-bound reference is checked by re-derivation from all sources.
    supplied = thread.control.prepared_meaning_checkpoint_ref
    if supplied is not None and supplied != checkpoint.checkpoint_id:
        raise ValueError("emlis_checkpoint_source_prefix_mismatch")
    return PreparedEmlisMeaning(thread, original, tuple(added), checkpoint)


def build_updated_grounded_plan(prepared: PreparedEmlisMeaning):
    """Post-checkpoint plan construction; failure cannot undo meaning."""
    if not prepared.thread.answers or prepared.checkpoint.answer_update.disposition == "NO_MATERIAL_UPDATE":
        return prepared.original_plan
    return _active_plan(prepared.original_plan, prepared.thread,
                        prepared.accepted_nuclei, set(prepared.checkpoint.inactive_claim_refs),
                        prepared.checkpoint.answer_update.updates if prepared.checkpoint.answer_update else (),
                        prepared.checkpoint.unresolved_parts, prepared=prepared)
