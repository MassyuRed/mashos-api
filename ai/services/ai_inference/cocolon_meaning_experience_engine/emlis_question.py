from __future__ import annotations

"""Pure Emlis question selection from grounded input meaning, never prose."""

from dataclasses import replace
import re

from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    _source_self_appraisal, _source_self_appraisal_parts,
)
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION

from .emlis_thread_contracts import EmlisClarificationV1, EmlisQuestionDecisionV1
from .emlis_thread_source import AdmittedEmlisThread, identity

_RECEIVED_EVENT = re.compile(
    r"(?:褒められ|ほめられ|言われ|伝えられ|評価され|断られ|誘われ|頼まれ|"
    r"連絡が来|返事が来|返信が来|声をかけられ|声を掛けられ)"
)
_PERSONAL_MEANING = re.compile(
    r"(?:自分|私|わたし|僕|ぼく).{0,24}(?:にとって|には).{1,36}(?:意味|感じ|思)|"
    r"(?:と|ように|ようで|みたいに)(?:受け取|感じ|思)|"
    r"(?:から|ので|ため).{0,30}(?:嬉|うれ|重|寂|さび|悲|辛|つら)|"
    r"(?:嬉|うれ|重|寂|さび|悲|辛|つら).{0,20}(?:のは|理由は)|"
    r"(?:ようで|と思って)[、,].{0,12}(?:重|寂|悲|怖|嬉|うれ|つら)|"
    r"と思った$"
)
_NONFACT = re.compile(r"(?:と言った|と言って|そうなら|たら|なら|かもしれ|と言う話|なかった|ていない|なかったら|だろう)")
_FACTUAL_RECEIVED = re.compile(r"(?:褒められ|ほめられ|言われ|伝えられ|評価され|断られ|誘われ|頼まれ|声をかけられ|声を掛けられ)(?:た|ました)$|(?:連絡|返事|返信)が来(?:た|ました)$")


def original_meaning_plan(thread: AdmittedEmlisThread):
    source = thread.original
    return build_final_stage1_grounded_observation_plan(
        source.normalized_current_input, evidence_spans=source.evidence_spans,
    )



# The proposal lives in question control, never in an original/answer claim.
# Its two premises are independently sourced; neither implies a hidden goal.
_APPRAISAL_STANDARD = "PERSONAL_OUTCOME_STANDARD"
_ZERO_OUTCOME = re.compile(r"(?:何も|何一つ|何ひとつ|一つも|ひとつも)(?:でき|出来)(?:なかった|ていない)")
_MATERIAL_PREFIX = re.compile(
    r"^(?:(?:今日|今|現在)(?:は|も)?[、,]?)?"
    r"(?:(?:私|わたし|僕|ぼく|俺|おれ|自分)(?:は|も)[、,]?)?")


def _appraisal_standard_candidate(thread, plan, *, parent_request_id, respect_control):
    """Ask whether an outcome appraisal uses a personally intended standard.

    A completed record beside a whole zero-outcome
    appraisal supplies a possible distinction between doing and satisfaction.
    No specific activity, motive, failure cause, or personality is inferred.
    Other sources/extra claims and already supplied standards are not ignored.
    """
    text = tuple(n for n in plan.nuclei if set(n.source_fields) & {"memo", "memo_action"})
    appraisals = tuple(n for n in text if _source_self_appraisal(n))
    material_rows = tuple(n for n in text if n not in appraisals)
    if len(appraisals) != 1 or len(material_rows) != 1:
        return None
    material_row = material_rows[0]
    if (material_row.source_fields not in {("memo",), ("memo_action",)}
        or material_row.retention != "required" or len(material_row.source_span_ids) != 1
        or material_row.grounding_kind not in {"explicit", "user_stated_relation"}
        or material_row.allowed_claim_scope not in {"explicit_current_input", "source_bounded_relation"}
        or material_row.semantic_frame.actor != "current_user"
        or set(material_row.source_span_ids) & set(appraisals[0].source_span_ids)
        or any(r.retention == "required" for r in plan.relations
               if {r.from_nucleus_id, r.to_nucleus_id} & {n.nucleus_id for n in text})):
        return None
    pair = (*appraisals, material_row)
    resolver = thread.resolver()
    index = {n.nucleus_id: n for n in plan.nuclei}
    appraisal, material = (final_reception_source_anchor_text(n.nucleus_id, index, resolver)
                           for n in pair)
    proof = _source_self_appraisal_parts(appraisal)
    if (proof is None or len(proof[1]) != 1 or proof[1][0][0] != "appraisal"
        or not _ZERO_OUTCOME.fullmatch(appraisal[slice(*proof[1][0][1:])])):
        return None
    finite = _MATERIAL_PREFIX.sub("", material, count=1)
    # A retained word alone cannot prove a completed record. Check its
    # whole finite form, rather than inferring an action from a field label.
    # Copular/adjectival pasts are records of a state, not completed activity;
    # an ambiguous bare -katta form stays outside this bounded candidate.
    if (not re.fullmatch(r"[^はがも、,。．.!！?？\s「」『』]+(?:た|ました)(?:だけ(?:です)?)?", finite)
        or re.search(r"ない|なかった|ません|たかった|たくな|かもしれ|らしい|なら|たら|もし|という|と言|と思|そうだ|予定|つもり", finite)
        or re.search(r"(?:かった|だった|でした)(?:だけ(?:です)?)?$", finite)
        or pair[1].semantic_frame.modality != "fact"
        or re.search(r"昨日|以前|先週|去年|昨年|明日", appraisal + material)):
        return None
    # Require complete coverage of the original free-text fields, not just
    # whichever claims an upstream finite grammar happened to retain.
    selected_spans = {s for n in pair for s in n.source_span_ids}
    text_spans = {s.span_id for s in thread.original.evidence_spans
                  if s.source_field in {"memo", "memo_action"}}
    if selected_spans != text_spans:
        return None
    control = thread.control.question_control_context
    target = identity("emlis-target", thread.original.envelope.envelope_id,
                      pair[0].nucleus_id, "personal_outcome_standard")
    if ((respect_control or thread.control.capability_snapshot.startswith("Q3_"))
        and target in control.asked_target_refs):
        return None
    evidence = tuple(resolver.qualified_ref(s).evidence.evidence_id
                     for n in pair for s in n.source_span_ids)
    affected = tuple(n.nucleus_id for n in pair)
    decision = EmlisQuestionDecisionV1("ASK", target, _APPRAISAL_STANDARD, evidence,
        "personal_outcome_standard", affected, affected,
        control.asked_target_refs if respect_control else (),
        "performed_material_and_zero_outcome_standard_unconfirmed")
    question = EmlisClarificationV1(
        identity("emlis-question", thread.control.thread_id, target), parent_request_id,
        thread.control.thread_id, thread.original.envelope.envelope_id, decision,
        f"「{appraisal}」は、やりたかったことには手が届かなかった、ということでしょうか。"
        "違っていたら、その意味を教えてください。")
    return decision, question


def question_candidate(thread: AdmittedEmlisThread, plan, *, parent_request_id: str,
                       respect_control: bool = True):
    control = thread.control.question_control_context
    q3 = thread.control.capability_snapshot.startswith("Q3_")
    if respect_control and (control.stop or control.issued_count >= control.question_limit
                            or (thread.answers and not q3)):
        return EmlisQuestionDecisionV1("END", decision_reason="free_round_complete"), None
    if plan.input_profile.safety_kind != TRIAGE_SAFE_OBSERVATION:
        return EmlisQuestionDecisionV1("BLOCKED", decision_reason="separate_safety_owner"), None
    original = thread.original
    # Read every admitted text field before treating a dimension as missing.
    texts = tuple(str(original.normalized_current_input.get(key, ""))
                  for key in ("memo", "memo_action"))
    resolver = thread.resolver()
    index = {row.nucleus_id: row for row in plan.nuclei}
    reactions = tuple(row for row in plan.nuclei
                      if row.kind in {"reaction", "state", "constraint", "value", "self_evaluation"}
                      and set(row.source_fields) & {"memo", "memo_action"})
    if not reactions:
        return EmlisQuestionDecisionV1("END", decision_reason="no_bound_personal_meaning_target"), None
    for nucleus in plan.nuclei:
        if not set(nucleus.source_fields) & {"memo", "memo_action"}:
            continue
        anchor = final_reception_source_anchor_text(nucleus.nucleus_id, index, resolver)
        match = _RECEIVED_EVENT.search(anchor)
        if not match or _NONFACT.search(anchor):
            continue
        # Keep the event clause only. No arbitrary character truncation and no
        # hidden cause/character/third-party intention in the question premise.
        event = re.split(r"(?:のに|けれど|けど|が[、,]|[、,])", anchor, maxsplit=1)[0]
        if (not event or not _FACTUAL_RECEIVED.search(event) or len(event) > 48
                or any(c in event for c in "「」『』\n")
                or re.match(r"^(?:彼|彼女|母|父|妹|弟|兄|姉|友人|上司)(?:は|が|も)", event)):
            continue
        bound_reactions = tuple(r for r in reactions
                                if set(r.source_span_ids) & set(nucleus.source_span_ids))
        if not bound_reactions:
            continue
        region = " ".join(resolver.resolve(s).raw_text for s in nucleus.source_span_ids)
        if _PERSONAL_MEANING.search(region):
            continue
        # An immediately following self explanation of this single received
        # event also answers the target. Foreign reports and marked other
        # occasions cannot suppress it merely by sharing an input field.
        source_spans = tuple(resolver.resolve(s) for s in resolver.span_ids)
        last = max(i for i, s in enumerate(source_spans) if s.span_id in nucleus.source_span_ids)
        if last + 1 < len(source_spans):
            following = source_spans[last + 1]
            if (following.source_field in nucleus.source_fields
                    and _PERSONAL_MEANING.search(following.raw_text)
                    and not re.search(r"別|ほか|他の|[「」『』]|(?:彼|彼女|母|父|上司)(?:は|が|も)", following.raw_text)):
                continue
        target = identity("emlis-target", original.envelope.envelope_id,
                          nucleus.nucleus_id, "personal_received_meaning")
        if (respect_control or q3) and target in control.asked_target_refs:
            continue
        evidence = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in nucleus.source_span_ids)
        affected = tuple(dict.fromkeys((nucleus.nucleus_id, *(r.nucleus_id for r in bound_reactions))))
        decision = EmlisQuestionDecisionV1(
            "ASK", target, "PERSONAL_RECEIVED_MEANING", evidence,
            "personal_received_meaning", affected,
            affected if q3 else tuple(plan.response_plan.human_reception_plan.target_nucleus_ids)
            if plan.response_plan.human_reception_plan else (),
            control.asked_target_refs if respect_control else (),
            "source_bound_event_personal_meaning_missing",
        )
        question = EmlisClarificationV1(
            identity("emlis-question", thread.control.thread_id, target), parent_request_id,
            thread.control.thread_id, original.envelope.envelope_id, decision,
            f"「{event}」は、あなたにはどんな意味として届きましたか。",
        )
        return decision, question
    appraisal = _appraisal_standard_candidate(thread, plan, parent_request_id=parent_request_id,
                                              respect_control=respect_control)
    if appraisal is not None:
        return appraisal
    return EmlisQuestionDecisionV1("END", decision_reason="no_bound_personal_meaning_target"), None


def validate_question_binding(thread: AdmittedEmlisThread, plan) -> None:
    question = thread.control.question_control_context.pending_question
    if question is None:
        raise ValueError("emlis_question_required")
    if thread.control.capability_snapshot.startswith("Q3_"):
        control = thread.control.question_control_context
        prior = replace(control, pending_question=None, issued_count=len(control.asked_target_refs) - 1,
                        asked_target_refs=control.asked_target_refs[:-1], issued_questions=control.issued_questions[:-1])
        thread = replace(thread, control=replace(thread.control, question_control_context=prior))
    _, canonical = question_candidate(thread, plan, parent_request_id=question.parent_request_id,
                                      respect_control=False)
    if canonical is None or question != replace(canonical, decision=replace(
            canonical.decision, asked_target_refs=question.decision.asked_target_refs)):
        raise ValueError("emlis_question_noncanonical")
