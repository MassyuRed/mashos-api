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
from emlis_ai_evidence_ledger_service import EvidenceLedgerValidationReport
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
_THEN = re.compile(r"^(?:あの時|その時|当時)(?:は|も)?(?:本当は|実際は)?[、,\s]*")
_NOW = re.compile(r"^(?:今|現在)(?:は|も)[、,\s]*")
_FEELING = re.compile(r"^(?:私は|私も|自分は)?(?:少し|とても|本当は|まだ|全然|あまり)?(?:嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)(?:い|かった|くない|くなかった)(?:です)?$")
_PAST = re.compile(r"(?:た|だった|でした|ました)(?:んです|のです|です)?$")
_BELIEF = re.compile(r"^.+(?:と思った|と感じた|と思いました|と感じました)$")
_FOREIGN_HOST = re.compile(r"(?:と|って).{1,16}(?:は|が|も)(?:思|感じ|言)|^(?:彼|彼女|母|父|妹|弟|兄|姉|友人|上司)(?:は|が|も)")


@dataclass(frozen=True, slots=True, repr=False)
class PreparedEmlisMeaning:
    thread: AdmittedEmlisThread
    original_plan: gp.GroundedObservationPlan
    accepted_nuclei: tuple[gp.GroundedSemanticNucleus, ...]
    checkpoint: EmlisMeaningCheckpointV1


def _text(row, index, resolver) -> str:
    return final_reception_source_anchor_text(row.nucleus_id, index, resolver)


def _base_ref(thread, plan) -> str:
    return identity("emlis-base-meaning", thread.original.envelope.envelope_id,
                    tuple(asdict(row) for row in plan.nuclei),
                    tuple(asdict(row) for row in plan.relations))


def _dependent_refs(plan, targets: tuple[str, ...]) -> tuple[str, ...]:
    # Relations/derived readings are not allowed to revive a withdrawn endpoint.
    # The other independently sourced endpoint remains active.
    return tuple(row.relation_id for row in plan.relations
                 if row.from_nucleus_id in targets or row.to_nucleus_id in targets)


def _answer_nucleus(span, *, raw: str, about_time: str, source_start: int = 0):
    """Use the shared source grammar with a real answer field and no labels."""
    local = {ANSWER_FIELD: raw}
    safety = classify_emlis_safety_triage_text(raw)
    kind = gp._kind_for_span(span, roles=(), safety_decision=safety,
                            safety_span_order={}, normalized_input=local)
    frame = gp._semantic_frame_for_span(span, kind=kind, roles=(), claim_ids=(),
                                        normalized_input=local)
    text = span.raw_text
    offset = source_start
    bounded = text[offset:].strip()
    # A finite self belief is retained as a belief, not its complement's
    # truth. The question only supplies the omitted response target.
    if _BELIEF.fullmatch(bounded) and not _FOREIGN_HOST.search(bounded):
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
    time_scope = "present" if about_time == "ANSWER_TIME" else "past"
    codes = tuple(c for c in frame.attribute_codes if not c.startswith(("time_scope:", "operator:change", "operator:positive_change")))
    frame = replace(frame, time_scope=time_scope, attribute_codes=(
        *codes, f"time_scope:{time_scope}", f"thread_time:{about_time.lower()}",
        "lexical:preserve_source_predicate", "lexical:no_new_sensation_family",
        "semantic_role:generic_relation_fragment",
        f"source_fragment_scalar_range:{offset}:{len(text)}",
        "source_fragment_scalar_source:normalized_raw_text",
    ))
    return gp.GroundedSemanticNucleus(
        f"answer:{span.span_id}", kind, (span.span_id,), (ANSWER_FIELD,), (span.span_id,),
        frame, "explicit", 1.0, 1.0, "required", "explicit_supplemental_answer",
        ("no_unstated_cause", "no_third_party_intention", "no_stable_personality"),
    )


def _active_plan(original, thread, added, inactive):
    nuclei = tuple(row for row in original.nuclei if row.nucleus_id not in inactive
                   and set(row.source_fields) & {"memo", "memo_action"}) + tuple(added)
    relations = tuple(row for row in original.relations if row.relation_id not in inactive
                      and row.from_nucleus_id not in inactive and row.to_nucleus_id not in inactive)
    safety = classify_emlis_safety_triage_text(thread.answers[0].source.answer_text_private)
    complexity = gp._semantic_complexity(nuclei=nuclei, relations=relations, meaning_artifacts=gp._MeaningArtifacts())
    response, coverage, surface, safety_policy = gp._build_response_and_policies(
        nuclei=nuclei, relations=relations, safety_decision=safety, complexity=complexity,
        material_quality="grounded", include_reception_relation_support=True,
        final_source_fidelity=True,
        primary_focus_nucleus_ids=tuple(row.nucleus_id for row in added),
    )
    resolver = thread.resolver()
    return replace(original, nuclei=nuclei, relations=relations, unknown_boundaries=(),
        input_profile=replace(original.input_profile, nucleus_count=len(nuclei),
            relation_count=len(relations), semantic_complexity=complexity, material_quality="grounded"),
        response_plan=response, coverage_requirements=coverage, surface_policy=surface,
        safety_policy=safety_policy, source_contracts=(*original.source_contracts, THREAD_SCHEMA),
        referenced_evidence_span_ids=gp._all_plan_evidence_ids(nuclei, relations, ()),
        evidence_ledger_validation=EvidenceLedgerValidationReport(True, canonical_span_ids=resolver.span_ids))


def prepare_emlis_meaning(request: GenerationRequest) -> PreparedEmlisMeaning:
    thread = admit_emlis_thread(request)
    original = original_meaning_plan(thread)
    base = _base_ref(thread, original)
    if not thread.answers:
        checkpoint = EmlisMeaningCheckpointV1(
            identity("emlis-checkpoint", thread.source_prefix_ref, base),
            thread.source_prefix_ref, base, None, "RESOLVED", (), (), (),
        )
        return PreparedEmlisMeaning(thread, original, (), checkpoint)
    validate_question_binding(thread, original)
    answer = thread.answers[0]
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
        if _CORRECTION_META.fullmatch(text):
            continue
        if _UNKNOWN.fullmatch(text):
            known_unchanged = True
            continue
        withdrawal = _WITHDRAWAL.fullmatch(text)
        then, now = _THEN.match(text), _NOW.match(text)
        targets: tuple[str, ...] = ()
        operation, binding = "ADD", "QUESTION_FOCUS"
        if withdrawal:
            quoted = withdrawal.group("old").rstrip("。．.")
            targets = tuple(row.nucleus_id for row in original.nuclei
                            if set(row.source_fields) & {"memo", "memo_action"}
                            and _text(row, index, resolver).rstrip("。．.") == quoted)
            if len(targets) != 1:
                unresolved.append(EmlisUnresolvedPartV1(ev, "correction_target_unresolved"))
                continue
            operation, binding, about = "WITHDRAW", "EXPLICIT_CORRECTION", "ORIGINAL_OCCASION"
            nucleus = None
        else:
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
                    and set(row.source_fields) & {"memo", "memo_action"})
                if len(candidates) != 1:
                    unresolved.append(EmlisUnresolvedPartV1(ev, "correction_target_unresolved"))
                    continue
                targets, operation, binding = candidates, "REVISE", "EXPLICIT_CORRECTION"
            # Exact source-semantic repetition is assessed, not relabelled as
            # a fresh interpretation. Politeness alone cannot change meaning.
            normalized = re.sub(r"(?:です|ました)$", "", text[offset:])
            if any(re.sub(r"(?:です|ました)$", "", _text(row, index, resolver)) == normalized
                   for row in original.nuclei if row.nucleus_id in focus):
                known_unchanged = True
                continue
        temporal = AnswerTemporalBindingV1(about, thread.original.envelope.envelope_id,
            ev if then or now else (), "answer_deictic_now" if now else None)
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
    return _active_plan(prepared.original_plan, prepared.thread,
                        prepared.accepted_nuclei, set(prepared.checkpoint.inactive_claim_refs))
