from dataclasses import replace
from unittest.mock import patch
import pytest
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
import emlis_ai_grounded_sentence_surface as surface
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import contracts as c
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source, SourceAdmissionError
from cocolon_meaning_experience_engine.emlis_thread_contracts import ANSWER_FIELD, EmlisThreadInputV1, EmlisQuestionControlV1, SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan, question_candidate
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning

# Synthetic, public grammar cases. Private product-read cases remain private.
ORIGINAL = '褒められたのに、嬉しくなかった。'
A = '次も同じ成果を求められるようで、重かった。'
B = '結果だけで、そこまでの苦労は見てもらえていないと思った。'
C = '相手が嫌なのではなく、自分ではまだ納得していなかった。'

def initial(memo=ORIGINAL, memo_action=''):
    raw = dict(id='q1-synthetic', created_at='2026-09-10T00:00:00Z', memo=memo,
        memo_action=memo_action, category=['仕事'], emotions=['不安'],
        emotion_details=[dict(type='不安', strength='medium')], is_secret=False)
    req = c.GenerationRequest('q1-synthetic', build_emlis_current_input_bundle(raw), 'q1-synthetic')
    src = freeze_text_source(req)
    return replace(req, emlis_thread=EmlisThreadInputV1('q1-thread', src.envelope.envelope_id))

def answered(text, req=None):
    req = req or initial()
    admitted = admit_emlis_thread(req)
    decision, question = question_candidate(admitted, original_meaning_plan(admitted), parent_request_id=req.request_id)
    assert question is not None
    answer = SupplementalAnswerSource('q1-answer', 'q1-thread', question.question_id, 1,
        req.emlis_thread.original_source_ref, text, '2026-09-11T00:00:00Z')
    return replace(req, emlis_thread=replace(req.emlis_thread, answers=(answer,), current_round=1,
        question_control_context=EmlisQuestionControlV1(question, (decision.target_ref,), 1)))

def prepared_request(req):
    checkpoint = MeaningExperienceEngine().prepare_emlis_update(req)
    return replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)), checkpoint

def render(text, req=None):
    req, checkpoint = prepared_request(answered(text, req))
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    assert result.meaning_checkpoint == checkpoint
    return result

def test_initial_body_and_one_question_are_independent_and_pure():
    req = initial()
    one, two = MeaningExperienceEngine().generate(req), MeaningExperienceEngine().generate(req)
    assert one == two
    assert one.status is c.EngineStatus.QUESTION_PENDING
    assert one.body.status is c.EngineStatus.GENERATED and one.body_sufficiency == 'SUFFICIENT'
    assert one.body_state == 'PRE_QUESTION'
    assert one.question.skip_allowed and one.question.answer_limit == 1
    assert one.question.prompt_private not in one.artifact.text
    assert req.emlis_thread.question_control_context.issued_count == 0
    assert not one.automatic_progression

def test_separate_sources_preserve_original_evidence_and_real_answer_field():
    req = answered('その時は寂しかった。🫧')
    thread = admit_emlis_thread(req)
    old = freeze_text_source(replace(req, emlis_thread=None))
    resolver = thread.resolver()
    assert thread.original == old
    original_refs = tuple(q.evidence for q in resolver.qualified_refs
                          if q.source_envelope_id == old.envelope.envelope_id)
    assert len(original_refs) == len(old.evidence_spans)
    assert all(ref in old.evidence_refs for ref in original_refs)
    answer = thread.answers[0]
    assert answer.envelope.source_role == 'SUPPLEMENTAL_ANSWER'
    assert all(s.source_field == ANSWER_FIELD for s in answer.evidence_spans)
    for ref in answer.evidence_refs:
        span = resolver.resolve(next(q.thread_span_id for q in resolver.qualified_refs if q.evidence == ref))
        assert span.raw_text in answer.source.answer_text_private
        assert answer.envelope.raw_utf8[ref.utf8_start:ref.utf8_end].decode('utf-8') == span.raw_text
    assert not any(s.source_field in {'emotions', 'category', 'memo'} for s in answer.evidence_spans)

@pytest.mark.parametrize('change', [dict(thread_id='foreign'), dict(question_id='foreign'),
    dict(original_source_ref='foreign'), dict(round_index=2), dict(source_role='CURRENT_INPUT'), dict(recorded_at='2026-09-11')])
def test_wrong_answer_parent_or_contract_is_rejected(change):
    req = answered(A)
    req = replace(req, emlis_thread=replace(req.emlis_thread, answers=(replace(req.emlis_thread.answers[0], **change),)))
    with pytest.raises((SourceAdmissionError, ValueError)):
        prepare_emlis_meaning(req)

@pytest.mark.parametrize('change', [dict(admitted_history=('history',)), dict(capability_snapshot='PREMIUM'), dict(current_round=2), dict(answers=())])
def test_free_scope_rejects_history_or_invalid_round(change):
    req = answered(A)
    with pytest.raises((SourceAdmissionError, ValueError)):
        prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread, **change)))

@pytest.mark.parametrize('text', [A, B, C])
def test_design_answers_reach_selected_meaning_and_shared_human_reception(text):
    prepared = prepare_emlis_meaning(answered(text))
    projection = project_thread_meaning(prepared, build_updated_grounded_plan(prepared))
    assert any(r.relation_kind is c.EmlisThreadScopeRelationKind.ABOUT_TARGET for r in projection.premeaning.source_relation_rows)
    assert isinstance(projection.structure.meaning_decision_outcome, c.SelectedEmlisProvisionalReading)
    result = render(text)
    assert text.rstrip('。') in result.artifact.observation
    # Q4 retains the full finite source in Observation and realizes a
    # reversible, time-bound nominal in Reception. Its independent inverse
    # and mutation checks live in test_emlis_q4_application.
    expected = {A: '次も同じ成果を求められるようだという、その時の重さ',
                B: '結果だけで、そこまでの苦労は見てもらえていないという、その時の思い',
                C: C.rstrip('。')}[text]
    assert expected in result.artifact.reception
    supplemental = tuple(d for d in result.meaning_graph.owner_dispositions if d.visible_authority is c.VisibleAuthority.SUPPLEMENTAL_USER)
    assert supplemental and all(d.source_owner_disposition is c.SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE for d in supplemental)
    assert result.question is None and result.question_decision.disposition == 'END'

def test_distinct_received_meanings_change_actual_follow():
    a, b = render(A), render(B)
    assert a.artifact.reception != b.artifact.reception
    assert '次も同じ成果' not in b.artifact.reception
    assert '苦労は見てもらえていない' not in a.artifact.reception

def test_then_revision_deactivates_old_reaction_and_dependencies():
    text = 'あの時も本当は嬉しかった。書き方を間違えた。'
    prepared = prepare_emlis_meaning(answered(text))
    update = prepared.checkpoint.answer_update.updates[0]
    assert update.operation == 'REVISE' and update.temporal_binding.about_time == 'ORIGINAL_OCCASION'
    assert update.superseded_claim_refs and update.affected_dependency_refs
    assert any(row.type == 'evaluation_about_event' for row in build_updated_grounded_plan(prepared).relations)
    result = render(text)
    assert '嬉しくなかった' not in result.artifact.text
    assert '嬉しかった' in result.artifact.text

def test_now_addition_retains_past_and_visible_time():
    prepared = prepare_emlis_meaning(answered('今は嬉しい。'))
    update = prepared.checkpoint.answer_update.updates[0]
    assert update.operation == 'ADD' and update.temporal_binding.about_time == 'ANSWER_TIME'
    assert not prepared.checkpoint.inactive_claim_refs
    result = render('今は嬉しい。')
    assert '嬉しくなかった' in result.artifact.observation
    assert '回答した時点' in result.artifact.observation

@pytest.mark.parametrize('text', ['嬉しいです。', '昨日は別件で悲しかった。', '彼は寂しかった。', 'はい。', '別の会議でつらかった。', '「重かった」と彼は言った。'])
def test_unbound_time_foreign_report_and_unrelated_event_are_unresolved(text):
    req, checkpoint = prepared_request(answered(text))
    assert checkpoint.assessment_status == 'UNRESOLVED' and not checkpoint.inactive_claim_refs
    result = MeaningExperienceEngine().generate(req)
    assert result.body_state == 'ANSWER_UNREFLECTED' and result.artifact is None

def test_partial_answer_preserves_accepted_and_unresolved_parts():
    text = 'その時は寂しかった。どう表したらいいかはまだ分からない。'
    prepared = prepare_emlis_meaning(answered(text))
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert len(prepared.checkpoint.answer_update.updates) == 1
    assert render(text).body_state == 'PARTIALLY_REFINED'

def test_nonfocus_withdrawal_and_focus_addition_in_one_answer():
    req = initial(memo_action='帰宅しても苦しかった。')
    text = 'その時は寂しかった。「帰宅しても苦しかった」は誤りです。'
    prepared = prepare_emlis_meaning(answered(text, req))
    assert [r.operation for r in prepared.checkpoint.answer_update.updates] == ['ADD', 'WITHDRAW']
    assert '帰宅しても苦しかった' not in render(text, req).artifact.text

def test_nonfocus_clause_replacement_requires_unique_complete_target():
    req = initial(memo_action='寂しかった。')
    prepared = prepare_emlis_meaning(answered('「寂しかった」ではなく「悲しかった」です。', req))
    assert prepared.checkpoint.answer_update.updates[0].operation == 'REVISE'
    assert len(prepared.checkpoint.inactive_claim_refs) == 1
    ambiguous = initial(memo_action='寂しかった。寂しかった。')
    assert prepare_emlis_meaning(answered('「寂しかった」は誤りです。', ambiguous)).checkpoint.assessment_status == 'UNRESOLVED'

def test_unaffected_structured_meaning_and_unknowns_survive():
    prepared = prepare_emlis_meaning(answered(A))
    after = build_updated_grounded_plan(prepared)
    originals = tuple(n for n in prepared.original_plan.nuclei if not set(n.source_fields) & {'memo', 'memo_action'})
    assert originals and all(n in after.nuclei for n in originals)
    assert prepared.original_plan.unknown_boundaries == after.unknown_boundaries
    assert prepared.original_plan.input_profile.material_quality == after.input_profile.material_quality

@pytest.mark.parametrize('text', ['分からない。', 'その時は嬉しくなかった。'])
def test_assessed_no_change_is_not_refined(text):
    result = render(text)
    assert result.meaning_checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE'
    assert result.body_state == 'UNCHANGED'

def test_prepare_is_pure_and_does_not_generate_body():
    req = answered(A)
    with patch('cocolon_meaning_experience_engine.emlis_thread_engine.realize_emlis_thread_body', side_effect=AssertionError('no body')):
        assert MeaningExperienceEngine().prepare_emlis_update(req) == MeaningExperienceEngine().prepare_emlis_update(req)
    assert req.emlis_thread.prepared_meaning_checkpoint_ref is None

def test_checkpoint_survives_body_failure_without_old_current_body():
    req, checkpoint = prepared_request(answered('「嬉しくなかった」は誤りです。'))
    assert checkpoint.inactive_claim_refs
    with patch('cocolon_meaning_experience_engine.emlis_thread_engine.realize_emlis_thread_body', side_effect=ValueError('private leak')):
        result = MeaningExperienceEngine().generate(req)
    assert result.meaning_checkpoint == checkpoint and result.artifact is None
    assert result.body_state == 'MEANING_UPDATED_BODY_UNAVAILABLE'
    assert 'private leak' not in repr(result.reason_codes)

def test_generate_requires_checkpoint_for_exact_source_prefix():
    req = answered(A)
    assert MeaningExperienceEngine().generate(req).status is c.EngineStatus.REJECTED
    req, _ = prepared_request(req)
    changed = replace(req.emlis_thread.answers[0], answer_text_private=B)
    req = replace(req, emlis_thread=replace(req.emlis_thread, answers=(changed,)))
    assert MeaningExperienceEngine().generate(req).status is c.EngineStatus.REJECTED

def test_stop_keeps_body_and_ends_questions():
    req = initial()
    req = replace(req, emlis_thread=replace(req.emlis_thread, question_control_context=EmlisQuestionControlV1(stop=True)))
    result = MeaningExperienceEngine().generate(req)
    assert result.question is None and result.artifact is not None

@pytest.mark.parametrize('memo', ['褒められなかったけど、寂しかった。', '褒められたら、嬉しかった。', '彼は褒められたのに、嬉しくなかった。', '褒められたかもしれないけど、寂しかった。'])
def test_question_does_not_presuppose_negated_hypothetical_or_foreign_event(memo):
    thread = admit_emlis_thread(initial(memo))
    assert question_candidate(thread, original_meaning_plan(thread), parent_request_id='q1-synthetic')[1] is None

def test_question_target_excludes_unrelated_reaction_and_meaning():
    thread = admit_emlis_thread(initial(memo_action='別の件では、自分には大事な意味だと思った。寂しかった。'))
    plan = original_meaning_plan(thread)
    decision, question = question_candidate(thread, plan, parent_request_id='q1-synthetic')
    assert question is not None
    assert all('memo_action' not in n.source_fields for n in plan.nuclei if n.nucleus_id in decision.affected_meaning_refs)

def test_inverse_rejects_answer_time_and_content_tampering():
    prepared = prepare_emlis_meaning(answered('今は嬉しい。'))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence_plan = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    body = render('今は嬉しい。').artifact.text
    def inverse(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan, sentence_plan=sentence_plan,
            resolver=resolver, selected_subjective_input=projection.selected_reception)
    assert inverse(body).passed
    assert not inverse(body.replace('回答した時点', 'その時')).passed
    assert not inverse(body.replace('「嬉しい」', '「悲しい」')).passed
    changed = body.replace('に対する', 'から続く')
    assert changed != body and not inverse(changed).passed
    assert not inverse(body.replace('褒められたことについて、', '')).passed

def test_legacy_scope_vocabulary_and_matrix_remain_closed():
    assert tuple(x.value for x in c.ForegroundScopeRelationKind) == ('contrast', 'coexistence', 'continuation', 'correction')
    assert c.project_foreground_scope_relation_kind('evaluation_about_event') is None
    assert len(c.INTERPRETATION_MATRIX_EXACT16) == 16

def test_original_personal_explanation_already_answers_target():
    thread = admit_emlis_thread(initial(ORIGINAL + A))
    assert question_candidate(thread, original_meaning_plan(thread), parent_request_id='q1-synthetic')[1] is None

def test_orthographic_repetition_does_not_create_new_meaning():
    assert render('その時はうれしくなかったです。').body_state == 'UNCHANGED'

def test_now_repetition_is_still_distinct_from_past():
    req = answered('今は嬉しくなかった。')
    update = prepare_emlis_meaning(req).checkpoint.answer_update
    assert update.disposition == 'MATERIAL_UPDATE'
    assert update.updates[0].temporal_binding.about_time == 'ANSWER_TIME'

def test_question_failure_cannot_hide_missing_initial_body():
    failed = c.EngineOutcome(status=c.EngineStatus.UNAVAILABLE, reason_codes=('synthetic_body_failure',))
    with patch('cocolon_meaning_experience_engine.engine.build_text_grounded_limited_artifact', side_effect=ValueError('synthetic')):
        result = MeaningExperienceEngine().generate(initial())
    assert result.artifact is None and result.question is None
    assert result.question_decision.disposition == 'BLOCKED'

def test_source_target_relation_tampering_is_rejected_before_projection():
    from cocolon_meaning_experience_engine.emlis_input_specific_meaning import derive_grounded_situation_view, validate_grounded_situation_view
    prepared = prepare_emlis_meaning(answered(A))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    view = derive_grounded_situation_view(projection.premeaning)
    about = next(r for r in view.source_connected_relations if r.relation_kind is c.EmlisThreadScopeRelationKind.ABOUT_TARGET)
    wrong = replace(about, source_object_ref=about.target_object_ref, target_object_ref=about.source_object_ref)
    with pytest.raises(c.CMEEStage1ContractError):
        validate_grounded_situation_view(replace(view, source_connected_relations=tuple(wrong if r==about else r for r in view.source_connected_relations)), projection.premeaning, projection.graph)
    with pytest.raises(ValueError, match='checkpoint_mismatch'):
        project_thread_meaning(prepared, replace(plan, relations=tuple(r for r in plan.relations if r.type!='evaluation_about_event')))

def test_concrete_unaffected_unknown_is_not_erased_by_partial_answer():
    import emlis_ai_grounded_observation_plan as gp
    prepared = prepare_emlis_meaning(answered('その時は寂しかった。まだうまく説明できません。'))
    original = prepared.original_plan
    extra = gp.GroundedUnknownBoundary('synthetic-unknown', 'target', (original.nuclei[0].nucleus_id,), original.nuclei[0].source_span_ids)
    prepared = replace(prepared, original_plan=replace(original, unknown_boundaries=(*original.unknown_boundaries,extra)))
    assert extra in build_updated_grounded_plan(prepared).unknown_boundaries

def test_supplied_checkpoint_must_match_initial_prefix_too():
    req=initial()
    req=replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    assert MeaningExperienceEngine().generate(req).status is c.EngineStatus.REJECTED

@pytest.mark.parametrize('text', ['同僚は嬉しいと思った。', '花子は寂しいと感じた。', '田中も仕事を辞めたいと思った。'])
def test_arbitrary_foreign_subject_is_not_adopted_as_user_belief(text):
    update=prepare_emlis_meaning(answered(text)).checkpoint.answer_update
    assert update.disposition=='UNRESOLVED' and not update.updates

def test_replacement_frame_does_not_inherit_old_negation():
    prepared=prepare_emlis_meaning(answered('「嬉しくなかった」ではなく「嬉しかった」です。'))
    nucleus=prepared.accepted_nuclei[0]
    assert nucleus.semantic_frame.polarity=='positive'
    assert not any('negation' in c or 'denied' in c for c in nucleus.semantic_frame.attribute_codes)

def test_clear_withdrawal_survives_unsupported_replacement_in_same_sentence():
    req=initial(memo_action='寂しかった。')
    prepared=prepare_emlis_meaning(answered('「寂しかった」は誤りで「未整理」です。',req))
    assert prepared.checkpoint.assessment_status=='PARTIAL'
    assert prepared.checkpoint.answer_update.updates[0].operation=='WITHDRAW'
    assert prepared.checkpoint.inactive_claim_refs
    assert prepared.checkpoint.unresolved_parts[0].reason_code=='correction_replacement_unsupported'
