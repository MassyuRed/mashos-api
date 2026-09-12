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
from .emlis_question import original_meaning_plan, validate_question_binding
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
_FEELING = re.compile(r"^(?:私は|私も|自分は)?(?:少し|とても|本当は|まだ|全然|あまり)?(?:嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)(?:い|かった|くない|くなかった)(?:です)?$")
_PAST = re.compile(r"(?:た|だった|でした|ました)(?:んです|のです|です)?$")
_BELIEF = re.compile(r"^.+(?:と思った|と感じた|と思いました|と感じました)$")
_FOREIGN_HOST = re.compile(r"(?:と|って).{1,16}(?:は|が|も)(?:思|感じ|言)|^(?:彼|彼女|母|父|妹|弟|兄|姉|友人|上司)(?:は|が|も)")
_PERCEIVED_REACTION = re.compile(r"^.+(?:ようで|ように感じて|気がして|と思って)[、,](?:少し|とても|まだ)?(?:重|苦し|つら|辛|怖|悲し|寂し|嬉し|うれし|軽)(?:かった|くなかった)(?:です)?$")
_SELF_CORRECTIVE_STATE = re.compile(r"^.+(?:のではなく|ではなく)[、,]?(?:私|自分)(?:では|は|も).+(?:していた|していなかった|できなかった)(?:です)?$")
_OTHER_TIME = re.compile(r"^(?:昨日|一昨日|先週|去年|昨年|別の日|翌日|今日)(?:は|も|の)?")


@dataclass(frozen=True, slots=True, repr=False)
class PreparedEmlisMeaning:
    thread: AdmittedEmlisThread
    original_plan: gp.GroundedObservationPlan
    accepted_nuclei: tuple[gp.GroundedSemanticNucleus, ...]
    checkpoint: EmlisMeaningCheckpointV1


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


def _answer_nucleus(span, *, raw: str, about_time: str, source_start: int = 0, source_end: int | None = None):
    """Use the shared source grammar with a real answer field and no labels."""
    text = span.raw_text
    offset = source_start
    end = len(text) if source_end is None else source_end
    bounded = text[offset:end].strip()
    # Parse only the admitted claim range. The old text in a correction is a
    # locator, not a source of polarity/operators for the replacement claim.
    local = {ANSWER_FIELD: bounded}
    local_span = replace(span, raw_text=bounded, detected_type=_detect_type(bounded, ()))
    safety = classify_emlis_safety_triage_text(bounded)
    kind = gp._kind_for_span(local_span, roles=(), safety_decision=safety,
                            safety_span_order={}, normalized_input=local)
    frame = gp._semantic_frame_for_span(local_span, kind=kind, roles=(), claim_ids=(),
                                        normalized_input=local)
    # A finite self belief is retained as a belief, not its complement's
    # truth. The question only supplies the omitted response target.
    if (any(pattern.fullmatch(bounded) for pattern in (_BELIEF, _PERCEIVED_REACTION, _SELF_CORRECTIVE_STATE))
            and not _FOREIGN_HOST.search(bounded)):
        if (not _SELF_CORRECTIVE_STATE.fullmatch(bounded)
                and re.match(r"^(?!(?:私は|私が|私も|自分は|自分が|自分も|次も))[^、,「」]{1,28}?(?:は|が|も)", bounded)):
            return None
        kind = "reaction"
        frame = replace(frame, predicate_kind="feeling", modality="feeling",
                        polarity="negative" if re.search(r"ない|なかった|重|苦|つら|辛", bounded) else "neutral")
    elif _FEELING.fullmatch(bounded):
        kind = "reaction"
        negative = bool(re.search(r"くない|くなかった|寂|さび|悲|苦|つら|辛|怖|こわ|重", bounded))
        frame = replace(frame, predicate_kind="feeling", modality="feeling",
                        polarity="negative" if negative else "positive")
    elif not gp._source_operator_owner_scope_is_bound(bounded):
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


def _active_plan(original, thread, added, inactive, updates, unresolved=()):
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
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(dict.fromkeys((*n.semantic_frame.attribute_codes,
            "thread_subject:withdrawn_source_event"))))) if n.nucleus_id in detached else n
        for n in nuclei)
    relations = tuple(row for row in original.relations if row.relation_id not in inactive
                      and row.from_nucleus_id not in inactive and row.to_nucleus_id not in inactive)
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
    # Bind distinguishable original source clauses before body-free reception
    # selection. Different evidence IDs alone cannot distinguish repeated text.
    answer_subjects = {}
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
    subject_texts = tuple(answer_subjects.values())
    proof = "thread_subject:unique_source_clause"
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=(
        *(c for c in n.semantic_frame.attribute_codes if c != proof),
        *((proof,) if n.nucleus_id in answer_subjects and subject_texts.count(answer_subjects[n.nucleus_id]) == 1 else ()),
    ))) if n.source_fields == (ANSWER_FIELD,) else n for n in nuclei)
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
            prepared = _prepare_answer(prefix, plan)
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
    return _prepare_answer(thread, original)


def _prepare_answer(thread, original):
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
    spans = tuple(resolver.resolve(sid) for sid in resolver.span_ids
                  if resolver.qualified_ref(sid).source_envelope_id == answer.envelope.envelope_id)
    correcting_then = any(_CORRECTION_META.fullmatch(span.raw_text) for span in spans)
    updates, unresolved, added, inactive = [], [], [], []
    known_unchanged = False
    for span in spans:
        text = span.raw_text
        ev = (resolver.qualified_ref(span.span_id).evidence.evidence_id,)
        # The legacy ledger can split a reported quotation at punctuation.
        # Its interior is not a standalone self answer, bare unknown, or
        # correction meta, even when those words happen to match our grammar.
        prefix = answer.source.answer_text_private[:resolver.qualified_ref(span.span_id).evidence.scalar_start]
        quoted_depth = 0
        for character in prefix:
            if character in "「『":
                quoted_depth += 1
            elif character in "」』":
                quoted_depth = max(0, quoted_depth - 1)
        if quoted_depth:
            unresolved.append(EmlisUnresolvedPartV1(ev, "answer_syntax_unsupported"))
            continue
        if _CORRECTION_META.fullmatch(text):
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
            if len(targets) != 1:
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
            nucleus = None if withdrawal else _answer_nucleus(span, raw=answer.source.answer_text_private,
                about_time="PRIOR_ANSWER_TIME" if prior_answer_time else about, source_start=replacement.start("new"), source_end=replacement.end("new"))
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
                                      about_time=about, source_start=offset)
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
                        prepared.checkpoint.unresolved_parts)
