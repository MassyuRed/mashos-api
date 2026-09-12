from __future__ import annotations

"""Q3 owned-source interpretation, separate from current-thread evidence.

This owner derives a revisable mapping and a typed current/past connection;
all visible language remains with the shared Sentence Surface.
"""
from dataclasses import dataclass, replace, asdict
from .emlis_thread_source import identity
from .emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
from emlis_ai_safety_triage import classify_emlis_safety_triage_text, TRIAGE_SAFE_OBSERVATION

@dataclass(frozen=True, slots=True, repr=False)
class OwnedHistorySourceV1:
    request: object
    recorded_at: str
    source_guard: tuple[str, str, int]
    schema_version: str = 'cocolon.cmee.owned_history.v1'

@dataclass(frozen=True, slots=True, repr=False)
class FrameFeedbackSourceV1:
    frame_key: str
    frame_ref: str
    source_emotion_id: str
    status: str
    correction_text: str | None
    version: int
    updated_at: str
    schema_version: str = 'cocolon.cmee.frame_feedback.v1'

    @property
    def evidence_ref(self):
        return identity('frame-feedback-source',asdict(self))

@dataclass(frozen=True, slots=True, repr=False)
class InterpretationFrameV1:
    frame_key: str
    frame_ref: str
    trigger: str
    received_meaning: str
    input_id: str
    recorded_at: str
    evidence_refs: tuple[str, ...]
    status: str = 'TENTATIVE'

@dataclass(frozen=True, slots=True, repr=False)
class HistoryLinePlanV1:
    current_text: str
    past_text: str
    recorded_at: str
    relation: str
    current_evidence_refs: tuple[str, ...]
    past_evidence_refs: tuple[str, ...]
    input_id: str
    current_nucleus_id: str
    past_nucleus_id: str


def admitted_history_plans(thread):
    """Never recover an earlier body or ignore an unassessed latest answer."""
    results = []
    for source in thread.control.admitted_history:
        if type(source) is not OwnedHistorySourceV1 or source.schema_version != 'cocolon.cmee.owned_history.v1':
            raise ValueError('owned_history_contract_invalid')
        request = source.request
        if request.emlis_thread.admitted_history or request.emlis_thread.original_source_ref == thread.control.original_source_ref:
            raise ValueError('owned_history_recursive_or_current')
        try:
            prepared = prepare_emlis_meaning(request)
        except ValueError:
            continue
        if prepared.checkpoint.assessment_status != 'RESOLVED':
            continue
        plan = build_updated_grounded_plan(prepared)
        if plan.input_profile.material_quality in {'limited_grounding', 'labels_only_limited'}:
            continue
        results.append((source, prepared, plan))
    return tuple(results)


def _anchor(nid, plan, resolver):
    return final_reception_source_anchor_text(nid, {n.nucleus_id:n for n in plan.nuclei}, resolver)


def derive_interpretive_frames(thread):
    if thread.control.capability_snapshot != 'Q3_PREMIUM':
        return ()
    frames = []
    feedback = {f.frame_key:f for f in thread.control.frame_feedback_sources}
    for source, prepared, plan in admitted_history_plans(thread):
        resolver = prepared.thread.resolver()
        for relation in plan.relations:
            if relation.type != 'evaluation_about_event':
                continue
            index = {n.nucleus_id:n for n in plan.nuclei}
            target = index[relation.to_nucleus_id]
            if 'thread_time:original_occasion' not in target.semantic_frame.attribute_codes:
                continue
            trigger = _anchor(relation.from_nucleus_id, plan, resolver)
            meaning = _anchor(relation.to_nucleus_id, plan, resolver)
            refs = tuple(resolver.qualified_ref(s).evidence.evidence_id for s in relation.source_span_ids)
            key = identity('frame-key', source.source_guard[0], trigger, meaning)
            ref = identity('frame-version', key, refs, source.source_guard)
            fb = feedback.get(key)
            if fb and fb.status == 'REJECTED':
                continue
            if fb and fb.status == 'REVISED':
                # This is the person's stored revision of the mapping. It is
                # not promoted to a claim about the current occasion.
                meaning = fb.correction_text
                refs = (*refs,fb.evidence_ref)
                ref = identity('frame-version',ref,fb.evidence_ref)
            frames.append(InterpretationFrameV1(key, ref, trigger, meaning, source.source_guard[0], source.recorded_at, refs,
                          fb.status if fb else 'TENTATIVE'))
    return tuple(frames)


def frame_supported_focus(thread, plan):
    """Past meanings select among current source claims, never add one."""
    if thread.answers:  # the person's latest current answer wins
        return ()
    rejected = set(thread.control.rejected_frame_keys)
    resolver = thread.resolver()
    # Only break a tie between explicitly supported current readings. Never
    # replace a uniquely foregrounded present concern with a past expectation.
    required = [n for n in plan.nuclei if n.nucleus_id in plan.coverage_requirements.required_nucleus_ids]
    if len({r.from_nucleus_id for r in plan.relations if r.type == 'contrast'}) < 2:
        return ()
    for frame in derive_interpretive_frames(thread):
        if frame.frame_key in rejected:
            continue
        for relation in plan.relations:
            index = {n.nucleus_id:n for n in plan.nuclei}
            if relation.type != 'contrast' or _anchor(relation.from_nucleus_id,plan,resolver) != frame.trigger:
                continue
            target = index[relation.to_nucleus_id]
            if (_anchor(target.nucleus_id,plan,resolver) == frame.received_meaning
                    and target.priority >= max((n.priority for n in required),default=0)):
                return (relation.from_nucleus_id,relation.to_nucleus_id)
    return ()


def history_line_plan(prepared, plan):
    thread = prepared.thread
    if thread.control.capability_snapshot not in {'Q3_PLUS', 'Q3_PREMIUM'}:
        return None
    if prepared.checkpoint.assessment_status != 'RESOLVED' or plan.input_profile.material_quality in {'limited_grounding', 'labels_only_limited'}:
        return None
    from emlis_ai_user_label_connection_surface import CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW, CONNECTABLE_FAMILIES
    family = CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW if any(r.type == 'evaluation_about_event' for r in plan.relations) else None
    if family not in CONNECTABLE_FAMILIES:
        return None
    resolver = thread.resolver()
    # Multiple records: this current input plus one independently owned record.
    # An exact event anchor alone is not a personal trait or a shared cause.
    for source, past, past_plan in admitted_history_plans(thread):
        past_resolver = past.thread.resolver()
        for current in plan.nuclei:
            if current.kind not in {'event', 'reaction', 'state'} or not set(current.source_fields) & {'memo', 'memo_action', 'answer_text_private'}:
                continue
            current_text = _anchor(current.nucleus_id, plan, resolver)
            if classify_emlis_safety_triage_text(current_text).safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
                continue
            for previous in past_plan.nuclei:
                if previous.kind != current.kind or not set(previous.source_fields) & {'memo', 'memo_action', 'answer_text_private'}:
                    continue
                if any(getattr(previous.semantic_frame,k) != getattr(current.semantic_frame,k)
                       for k in ('actor','polarity','modality','time_scope','predicate_kind')):
                    continue
                past_text = _anchor(previous.nucleus_id, past_plan, past_resolver)
                if current_text != past_text or len(current_text) < 4 or any(x in current_text for x in ('「','」','\n')):
                    continue
                return HistoryLinePlanV1(current_text, past_text, source.recorded_at, 'REPEATED_EXPLICIT_WORDING',
                    tuple(resolver.qualified_ref(s).evidence.evidence_id for s in current.source_span_ids),
                    tuple(past_resolver.qualified_ref(s).evidence.evidence_id for s in previous.source_span_ids), source.source_guard[0], current.nucleus_id, previous.nucleus_id)
    return None
