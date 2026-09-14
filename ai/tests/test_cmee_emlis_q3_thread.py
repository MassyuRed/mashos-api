"""Actual Q3 bodies: cumulative meaning, source time, pair composition and inverse."""
from dataclasses import replace
import pytest
from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisQuestionControlV1,SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning,build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface

MEMO='褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。'
def begin(memo=MEMO,memo_action=''):
    r=initial(memo,memo_action)
    return replace(r,emlis_thread=replace(r.emlis_thread,capability_snapshot='Q3_PREMIUM',question_control_context=EmlisQuestionControlV1(question_limit=3)))


@pytest.mark.parametrize('positive,burden', [
    ('その時は嬉しかった。','その時は重かった。'),
    ('今は嬉しい。','その時は重かった。'),
    ('その時は嬉しかった。','今は怖くない。'),
])
@pytest.mark.parametrize('positive_first',[False,True])
def test_mixed_answer_follow_retains_each_event_and_existing_feeling(positive,burden,positive_first):
    answers=(positive,burden) if positive_first else (burden,positive)
    r=advance(advance(begin(),answers[0]),answers[1])
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    follow=out.artifact.reception
    first,second=follow.split('。')[:2]
    assert follow.index('褒められた') < follow.index('誘われた') < follow.index('頼まれた')
    assert '褒められたのに嬉しくなかったこと' in first
    assert '誘われたのに悲しかったこと' in first
    assert '頼まれたのに寂しかったこと' in follow
    joy=second
    weight=first
    assert ('褒められた' if positive_first else '誘われた') + 'ことについて' in joy
    assert ('嬉しかった' if '嬉しかった' in positive else '嬉しい') in joy
    assert ('その時に' if 'その時' in positive else '回答した時点で') in joy
    assert '気持ちを受け止めています' in joy and '小さくせず' not in joy
    assert ('その時の重さ' if '重かった' in burden else '回答した時点で怖くないこと') in weight
    assert '小さくせずに受け止めています' in weight
    p=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(p)
    moves=plan.response_plan.human_reception_plan.moves
    positive_id = 'answer:s7' if positive_first else 'answer:s8'
    positive_move = next(m for m in moves if m.reception_act == 'recognize_lived_change')
    burden_move = next(m for m in moves if m.reception_act == 'stay_with_current_burden')
    assert positive_move.target_nucleus_ids == (positive_id,)
    assert 'nucleus:s3:reaction' in burden_move.support_nucleus_ids
    assert ('answer:s8' if positive_first else 'answer:s7') in burden_move.support_nucleus_ids
    assert {m.reception_act for m in moves}=={'recognize_lived_change','stay_with_current_burden'}


@pytest.mark.parametrize('third,old,new',[
    ('「重かった」ではなく「苦しかった」です。','重さ','苦しさ'),
    ('「重かった」は誤りです。','重さ',None),
])
def test_mixed_answer_correction_or_withdrawal_keeps_the_other_answer(third,old,new):
    r=advance(advance(advance(begin(),'その時は重かった。'),'その時は嬉しかった。'),third)
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert old not in out.artifact.text
    assert '誘われたことについて、その時に嬉しかったという気持ち' in out.artifact.reception
    if new is not None:assert '褒められたのに嬉しくなかったことと、その出来事へのその時の'+new in out.artifact.reception


def test_mixed_answer_body_inverse_rejects_missing_swapped_and_changed_answers():
    p=prepare_emlis_meaning(advance(advance(begin(),'その時は重かった。'),'その時は嬉しかった。'))
    plan=build_updated_grounded_plan(p);resolver=p.thread.resolver()
    projection=project_thread_meaning(p,plan);out=realize_emlis_thread_body(p)
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    def passes(body):
        return evaluate_grounded_surface_body_inverse(body=body.encode(),plan=plan,
            sentence_plan=sentence,resolver=resolver,selected_subjective_input=projection.selected_reception).passed
    assert passes(out.artifact.text)
    follow=out.artifact.reception
    mutations=[follow.split('。',1)[1],
        follow.replace('誘われたのに悲しかったことと、', ''),
        follow.replace('誘われたのに悲しかったこと', '誘われたのに悲しいこと'),
        follow.replace('その時の重さ','回答した時点の重さ'),
        follow.replace('嬉しかった','嬉しくなかった'),
        follow.replace('褒められた','TEMP').replace('誘われた','褒められた').replace('TEMP','誘われた')]
    for changed in mutations:
        assert changed!=follow and not passes(out.artifact.text.replace(follow,changed))


@pytest.mark.parametrize('replacement',[
    '回答した時点で嬉しかったという気持ち',
    'その時に嬉しくなかったという気持ち',
    '嬉しかったという気持ち',
    '「その時に嬉しかったという気持ち」',
])
def test_positive_answer_time_and_source_are_checked_without_replay(replacement):
    p=prepare_emlis_meaning(advance(advance(begin(),'その時は重かった。'),'その時は嬉しかった。'))
    plan=build_updated_grounded_plan(p);resolver=p.thread.resolver();projection=project_thread_meaning(p,plan)
    result=realize_emlis_thread_body(p)
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    body=result.artifact.text.replace('その時に嬉しかったという気持ち',replacement)
    inverse=evaluate_grounded_surface_body_inverse(body=body.encode(),plan=plan,sentence_plan=sentence,
        resolver=resolver,selected_subjective_input=projection.selected_reception)
    assert not inverse.passed
    assert any('positive_answer_source_time_missing' in reason for reason in inverse.failure_codes)


def test_mixed_shared_claim_partition_keeps_complete_disjoint_source_contributions():
    import emlis_ai_grounded_human_reception as hr
    p=prepare_emlis_meaning(advance(advance(begin(),'その時は重かった。'),'その時は嬉しかった。'))
    plan=build_updated_grounded_plan(p);projection=project_thread_meaning(p,plan)
    selected=projection.selected_reception;left,right=selected.decisions
    assert left.projected_claim_ref==right.projected_claim_ref
    assert left.subjective_proposition==right.subjective_proposition
    assert set(left.selected_contribution_refs).isdisjoint(right.selected_contribution_refs)
    all_refs={r.contribution_ref for r in left.basis_rows}
    assert set(left.selected_contribution_refs)|set(right.selected_contribution_refs)==all_refs
    wrong=hr.identify_selected_subjective_reception_decision(replace(left,decision_ref='',
        selected_contribution_refs=right.selected_contribution_refs))
    altered=hr.identify_selected_subjective_reception_input(replace(selected,input_ref='',decisions=(wrong,right)))
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    reception=plan.response_plan.human_reception_plan
    expressions=tuple(_bind_expression(plan,p.thread.resolver(),replace(projection,selected_reception=altered),m,'FINITE') for m in reception.moves)
    sentence=surface.build_grounded_sentence_plan(plan,p.thread.resolver(),recovery_stage='full')
    clauses=next(l.reception_clause_plans for l in sentence.lines if l.binding.line_role=='human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception,expressions,{n.nucleus_id:n for n in plan.nuclei},
            p.thread.resolver(),plan=plan,recovery_stage='full',clause_plans=clauses,selected_subjective_input=altered)

def advance(req,text):
    e=MeaningExperienceEngine();out=e.generate(req);assert out.artifact and out.question,out.reason_codes
    q,t=out.question,req.emlis_thread;control=t.question_control_context;n=len(t.answers)+1
    a=SupplementalAnswerSource('answer-'+str(n),t.thread_id,q.question_id,n,t.original_source_ref,text,f'2026-09-{10+n:02}T01:00:00Z')
    t=replace(t,answers=(*t.answers,a),current_round=n,prepared_meaning_checkpoint_ref=None,
      question_control_context=replace(control,pending_question=q,asked_target_refs=(*control.asked_target_refs,q.decision.target_ref),issued_count=n,issued_questions=(*control.issued_questions,q)))
    r=replace(req,emlis_thread=t);cp=e.prepare_emlis_update(r)
    return replace(r,emlis_thread=replace(t,prepared_meaning_checkpoint_ref=cp.checkpoint_id))


def test_three_distinct_answers_preserve_every_pair_and_end():
    r=begin()
    for count,text in enumerate(['その時は重かった。','その時は怖かった。','その時は苦しかった。'],1):
        r=advance(r,text)
        current=MeaningExperienceEngine().generate(r);assert current.artifact,current.reason_codes
        follow=current.artifact.reception
        for event,feeling in list(zip(('褒められた','誘われた','頼まれた'),('重さ','怖さ','苦しさ')))[:count]:
            assert event in follow and feeling in follow
        assert follow.count('受け止めています')==1
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert all(x in out.artifact.observation for x in ['褒められた','誘われた','頼まれた','重かった','怖かった','苦しかった'])
    assert out.question is None
    p=prepare_emlis_meaning(r);assert len(p.checkpoint.accepted_update_refs)==3


def test_later_correction_preserves_previous_answer_time_and_subject():
    r=advance(begin(),'今は重い。')
    r=advance(r,'「重い」ではなく「軽い」です。')
    prepared=prepare_emlis_meaning(r);update=prepared.checkpoint.answer_update.updates[0]
    assert update.temporal_binding.about_time=='ANSWER_TIME'
    assert update.temporal_binding.anchor_source_ref==prepared.thread.answers[0].envelope.envelope_id
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert '先の回答時点' in out.artifact.observation and '軽い' in out.artifact.reception
    assert '重い' not in out.artifact.text
    plan=build_updated_grounded_plan(prepared);index={n.nucleus_id:n for n in plan.nuclei}
    assert any(e.type=='evaluation_about_event' and e.to_nucleus_id==prepared.accepted_nuclei[0].nucleus_id for e in plan.relations)


def test_later_withdrawal_removes_earlier_answer_and_dependencies():
    r=advance(begin(),'その時は重かった。');r=advance(r,'「重かった」は誤りです。')
    p=prepare_emlis_meaning(r);out=MeaningExperienceEngine().generate(r)
    assert out.artifact,out.reason_codes
    assert '重かった' not in out.artifact.text
    assert any(x.startswith('answer:') for x in p.checkpoint.inactive_claim_refs)


def test_independent_pairs_cannot_be_crossed_by_a_surface_edit():
    p=prepare_emlis_meaning(begin());plan=build_updated_grounded_plan(p);resolver=p.thread.resolver()
    out=realize_emlis_thread_body(p);projection=project_thread_meaning(p,plan)
    sp=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    edited=out.artifact.text.replace('「嬉しくなかった」','TEMP').replace('「悲しかった」','「嬉しくなかった」').replace('TEMP','「悲しかった」')
    assert not evaluate_grounded_surface_body_inverse(body=edited.encode(),plan=plan,sentence_plan=sp,resolver=resolver,selected_subjective_input=projection.selected_reception).passed


def test_separate_source_fields_keep_pair_identity_in_coordinated_body():
    r=begin('褒められたのに、嬉しくなかった。','誘われたのに、悲しかった。')
    p=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(p)
    sp=surface.build_grounded_sentence_plan(plan,p.thread.resolver(),recovery_stage='full')
    assert len([l for l in sp.lines if l.binding.line_role!='human_follow'])==1
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert '褒められた' in out.artifact.observation and '誘われた' in out.artifact.observation
    assert {q.evidence.field_path for q in out.artifact.qualified_evidence_refs}>={'memo','memo_action'}


@pytest.mark.parametrize('second,fragment',[
    ('その時は重かった。','その時の重さ'),
    ('その時は私は怖かった。','その時に私は怖かったこと'),
    ('その時は少し怖かった。','その時に少し怖かったこと'),
    ('その時は怖くなかった。','その時に怖くなかったこと'),
    ('結果だけで、そこまでの苦労は見てもらえていないと思った。','苦労は見てもらえていないという、その時の思い'),
    ('次も同じ成果を求められるようで、重かった。','求められるようだという、その時の重さ'),
])
def test_follow_keeps_each_answer_subject_and_its_entire_expression(second,fragment):
    r=advance(advance(begin(),'その時は重かった。'),second)
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    follow=out.artifact.reception
    assert '褒められたのに嬉しくなかったことと、その出来事へのその時の重さ' in follow
    assert '誘われたのに悲しかったことと、その出来事' in follow and fragment in follow
    assert '頼まれたのに寂しかったこと' in follow
    assert 'ことへのその時に' not in follow
    assert follow.count('受け止めています')==1


@pytest.mark.parametrize('second',['今は怖い。','その時は嬉しかった。','分からない。','その時は怖かった。別のことです。'])
def test_follow_mixed_axes_and_unresolved_parts_keep_existing_availability(second):
    r=advance(advance(begin(),'その時は重かった。'),second)
    out=MeaningExperienceEngine().generate(r)
    if second=='分からない。':
        assert out.artifact is None and out.reason_codes==('reuse_saved_observation_required',)
        assert out.body_state=='UNCHANGED'
        return
    assert out.artifact,out.reason_codes
    assert '重かった' in out.artifact.observation
    if second.startswith('今は'):
        assert '回答した時点' in out.artifact.reception
    assert '別のことです' not in out.artifact.reception


@pytest.mark.parametrize('third,old,new',[
    ('「重かった」ではなく「苦しかった」です。','重さ','苦しさ'),
    ('「重かった」は誤りです。','重さ',None),
])
def test_later_correction_or_withdrawal_preserves_other_answer_follow(third,old,new):
    r=advance(advance(advance(begin(),'その時は重かった。'),'その時は怖かった。'),third)
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert old not in out.artifact.reception and '重かった' not in out.artifact.observation
    assert '誘われた' in out.artifact.reception and '怖さ' in out.artifact.reception
    if new is not None:assert '褒められた' in out.artifact.reception and new in out.artifact.reception


@pytest.mark.parametrize('second',['その時は重かった。','その時は怖かった。'])
def test_repeated_event_wording_keeps_single_answer_selection_available(second):
    r=advance(advance(begin('褒められたのに、嬉しくなかった。褒められたのに、悲しかった。'),
                      'その時は重かった。'),second)
    p=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(p)
    out=MeaningExperienceEngine().generate(r);assert out.artifact,out.reason_codes
    assert len(plan.response_plan.human_reception_plan.moves[0].target_nucleus_ids)==1


def test_collective_follow_inverse_requires_every_correct_subject_answer_time_pair():
    # The current original reaction retains the existing answer-only route.
    from emlis_ai_grounded_observation_gate import _body_inverse_thread_answer_group
    from unittest.mock import patch
    r=advance(advance(begin(MEMO.replace('寂しかった', '今は寂しい')),'その時は重かった。'),'その時は怖かった。')
    p=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(p);resolver=p.thread.resolver()
    out=realize_emlis_thread_body(p);projection=project_thread_meaning(p,plan)
    sp=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    body=out.artifact.text;follow=out.artifact.reception;move=plan.response_plan.human_reception_plan.moves[0]
    def body_pairs(text):
        raw=text.encode();witness=surface.parse_grounded_surface_body_bytes(raw)
        return tuple(_body_inverse_thread_answer_group(raw,witness,s,move,plan,resolver)
                     for s in witness.sentences if s.section=='reception')
    assert any(body_pairs(body))
    mutations=[
        follow.replace('褒められた','TEMP').replace('誘われた','褒められた').replace('TEMP','誘われた'),
        follow.replace('その時の重さと、','その時の怖さと、'),
        follow.replace('褒められたことへのその時の重さと、',''),
        follow.replace('と、','。'),follow.replace('その時の','回答した時点の',1),
        follow.replace('重さ','重くなかったこと'),
        follow.replace('褒められたことへのその時の重さ','「褒められたことへのその時の重さ」'),
    ]
    for changed in mutations:
        assert changed!=follow
        altered=body.replace(follow,changed)
        # This parser must reject even without consulting the shared author.
        with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',side_effect=AssertionError('no replay')):
            assert not any(body_pairs(altered))
        assert not evaluate_grounded_surface_body_inverse(body=altered.encode(),plan=plan,
            sentence_plan=sp,resolver=resolver,selected_subjective_input=projection.selected_reception).passed


@pytest.mark.parametrize('grammar',['answer-slot:1:PAST_FEELING:answer_time',
                                  'answer-slot:1:BELIEF:original_occasion',
                                  'answer-slot:0:PAST_FEELING:original_occasion'])
def test_collective_follow_ir_checks_later_answer_slot_time_and_grammar(grammar):
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    import emlis_ai_grounded_human_reception as hr
    r=advance(advance(begin(MEMO.replace('寂しかった', '今は寂しい')),'その時は重かった。'),'その時は怖かった。')
    p=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(p);resolver=p.thread.resolver()
    projection=project_thread_meaning(p,plan);reception=plan.response_plan.human_reception_plan
    expression=_bind_expression(plan,resolver,projection,reception.moves[0],'FINITE')
    assert len(expression.nominalization_plan)==3
    changed=hr.identify_source_grounded_reception_expression(replace(expression,expression_ref='',
        nominalization_plan=(*expression.nominalization_plan[:2],grammar)))
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    clauses=next(line.reception_clause_plans for line in sentence.lines if line.binding.line_role=='human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception,(changed,),{n.nucleus_id:n for n in plan.nuclei},resolver,
            plan=plan,recovery_stage='full',clause_plans=clauses,selected_subjective_input=projection.selected_reception)


@pytest.mark.parametrize('memo,expected',[
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。',
     ('褒められたのに嬉しくなかったこと','誘われたのに悲しかったこと')),
    (MEMO,('褒められたのに嬉しくなかったこと','誘われたのに悲しかったこと','頼まれたのに寂しかったこと')),
    ('褒められたのに、嬉しくなかった。褒められたけど、悲しかった。',
     ('褒められたのに嬉しくなかったこと','褒められたけど悲しかったこと')),
])
def test_initial_follow_keeps_all_received_reactions_before_an_answer(memo,expected):
    out=MeaningExperienceEngine().generate(begin(memo));assert out.artifact,out.reason_codes
    follow=out.artifact.reception
    assert all(part in follow for part in expected)
    assert [follow.index(part) for part in expected]==sorted(follow.index(part) for part in expected)
    assert follow.count('受け止めています')==1
    assert out.question is not None


@pytest.mark.parametrize('connector',['のに','けど','けれど','けれども'])
def test_initial_group_preserves_the_source_connective_and_negative_feeling(connector):
    memo=f'断られた{connector}、あまり悲しくなかった。誘われたのに、とても寂しかった。'
    out=MeaningExperienceEngine().generate(begin(memo));assert out.artifact,out.reason_codes
    follow=out.artifact.reception
    assert f'断られた{connector}あまり悲しくなかったこと' in follow
    assert '誘われたのにとても寂しかったこと' in follow
    assert '安心' not in follow


def test_initial_group_inverse_reads_every_pair_without_forward_replay():
    r=begin('褒められたけど、嬉しくなかった。誘われたのに、悲しかった。')
    prepared=prepare_emlis_meaning(r);plan=build_updated_grounded_plan(prepared);resolver=prepared.thread.resolver()
    projection=project_thread_meaning(prepared,plan);out=realize_emlis_thread_body(prepared)
    sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
    from emlis_ai_grounded_observation_gate import _body_inverse_received_contrast_group
    move=plan.response_plan.human_reception_plan.moves[0]
    def check(follow):
        body=out.artifact.text.replace(out.artifact.reception,follow).encode()
        witness=surface.parse_grounded_surface_body_bytes(body)
        actual=next(s for s in witness.sentences if s.section=='reception')
        independent=_body_inverse_received_contrast_group(body,witness,actual,move,plan,resolver)
        result=evaluate_grounded_surface_body_inverse(body=body,plan=plan,sentence_plan=sentence,
            resolver=resolver,selected_subjective_input=projection.selected_reception)
        return independent,result
    original=out.artifact.reception
    assert check(original)[0] and check(original)[1].passed
    mutations=[original.replace('褒められたけど','褒められたのに'),
        original.replace('嬉しくなかった','嬉しかった'),original.replace('悲しかった','悲しい'),
        original.replace('褒められたけど嬉しくなかったことと、',''),
        original.replace('嬉しくなかった','TMP').replace('悲しかった','嬉しくなかった').replace('TMP','悲しかった'),
        original.replace('誘われたのに悲しかったこと','褒められたけど嬉しくなかったこと'),
        original.replace('誘われたのに悲しかったこと','「誘われたのに悲しかったこと」')]
    for changed in mutations:
        independent,inverse=check(changed)
        assert changed!=original and not independent and not inverse.passed


def test_initial_group_allows_existing_answer_update_and_next_question():
    # Current answer selection still owns the refined reception; retaining all
    # unanswered original reactions after this point remains separate work.
    request=begin();initial_out=MeaningExperienceEngine().generate(request)
    request=advance(request,'その時は重かった。')
    out=MeaningExperienceEngine().generate(request);assert out.artifact,out.reason_codes
    assert 'その時の重さ' in out.artifact.reception
    assert initial_out.artifact.observation!=out.artifact.observation
    assert out.question is not None


@pytest.mark.parametrize('answer', ['その時は重かった。', '今は重い。', 'その時は嬉しかった。',
                                  'その時は重かった。どう表したらいいかはまだ分からない。'])
def test_answer_follow_retains_unanswered_original_reactions(answer):
    request = advance(begin(), answer)
    out = MeaningExperienceEngine().generate(request)
    assert out.artifact, out.reason_codes
    assert '誘われたのに悲しかったこと' in out.artifact.reception
    assert '頼まれたのに寂しかったこと' in out.artifact.reception
    assert out.artifact.reception.count('小さくせずに受け止めています') == 1
    prepared = prepare_emlis_meaning(request)
    assert not prepared.checkpoint.inactive_claim_refs
    if prepared.checkpoint.assessment_status == 'PARTIAL':
        assert out.body_state == 'PARTIALLY_REFINED' and out.question is None
    else:
        assert out.question and '誘われた' in out.question.prompt_private


@pytest.mark.parametrize('answer,removed,replacement', [
    ('「嬉しくなかった」ではなく「寂しかった」です。', '嬉しくなかった', 'その時の寂しさ'),
    ('「嬉しくなかった」は誤りです。', '嬉しくなかった', None),
    ('あの時も本当は嬉しかった。書き方を間違えた。', '嬉しくなかった', 'その時に嬉しかった'),
])
def test_original_correction_keeps_unaffected_reactions_without_reviving_old_meaning(answer, removed, replacement):
    request = advance(begin(), answer)
    prepared = prepare_emlis_meaning(request)
    assert 'nucleus:s1:reaction' in prepared.checkpoint.inactive_claim_refs
    out = realize_emlis_thread_body(prepared)
    assert removed not in out.artifact.text
    assert '誘われたのに悲しかったこと' in out.artifact.reception
    assert '頼まれたのに寂しかったこと' in out.artifact.reception
    if replacement:
        assert replacement in out.artifact.reception


def test_retained_original_and_each_answer_keep_their_own_time_through_three_rounds():
    request = begin()
    for answer in ('その時は重かった。', '今は怖い。', 'その時は苦しかった。'):
        request = advance(request, answer)
    out = MeaningExperienceEngine().generate(request)
    assert out.artifact and not out.question
    follow = out.artifact.reception
    assert '褒められたのに嬉しくなかったことと、その出来事へのその時の重さ' in follow
    assert '誘われたのに悲しかったことと、その出来事について、回答した時点で怖いこと' in follow
    assert '頼まれたのに寂しかったことと、その出来事へのその時の苦しさ' in follow
    assert follow.count('受け止めています') == 1


def test_three_mixed_answers_keep_original_burdens_and_the_positive_answer():
    request = begin()
    for answer in ('その時は重かった。', '今は嬉しい。', 'その時は怖かった。'):
        request = advance(request, answer)
    out = MeaningExperienceEngine().generate(request)
    assert out.artifact and not out.question
    follow = out.artifact.reception
    assert '褒められたのに嬉しくなかったことと、その出来事へのその時の重さ' in follow
    assert '頼まれたのに寂しかったことと、その出来事へのその時の怖さ' in follow
    assert '誘われたことについて、回答した時点で嬉しいという気持ちを受け止めています' in follow


def test_retained_group_inverse_rejects_missing_crossed_quoted_and_retimed_source_without_replay():
    from emlis_ai_grounded_observation_gate import _body_inverse_thread_received_group
    from unittest.mock import patch
    request = advance(advance(begin(), 'その時は重かった。'), '今は怖い。')
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    out = realize_emlis_thread_body(prepared)
    move = plan.response_plan.human_reception_plan.moves[0]
    follow = out.artifact.reception
    def parsed(text):
        raw = text.encode()
        witness = surface.parse_grounded_surface_body_bytes(raw)
        return tuple(_body_inverse_thread_received_group(raw, witness, sentence, move, plan, resolver)
                     for sentence in witness.sentences if sentence.section == 'reception')
    assert any(result is not None for result in parsed(out.artifact.text))
    mutations = [
        follow.replace('と、頼まれたのに寂しかったこと', ''),
        follow.replace('悲しかった', '寂しかった'),
        follow.replace('嬉しくなかった', '嬉しかった'),
        follow.replace('のに', 'から', 1),
        follow.replace('と、その出来事へのその時の重さ', ''),
        follow.replace('その出来事へのその時の重さ', 'その出来事への回答した時点の重さ'),
        follow.replace('回答した時点で怖いこと', 'その時に怖いこと'),
        follow.replace('その出来事', '別の出来事', 1),
        follow.replace('頼まれたのに寂しかったこと', '「頼まれたのに寂しかったこと」'),
        follow.replace('褒められた', 'TEMP').replace('誘われた', '褒められた').replace('TEMP', '誘われた'),
    ]
    for mutation in mutations:
        assert mutation != follow
        with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no replay')):
            assert all(result is None for result in parsed(out.artifact.text.replace(follow, mutation)))


@pytest.mark.parametrize('change', ['time', 'grammar', 'reaction_slot', 'answer_slot'])
def test_retained_group_expression_rechecks_later_slot_ownership_and_time(change):
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    import emlis_ai_grounded_human_reception as hr
    prepared = prepare_emlis_meaning(advance(advance(begin(), 'その時は重かった。'), '今は怖い。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    reception = plan.response_plan.human_reception_plan
    expression = _bind_expression(plan, resolver, projection, reception.moves[0], 'FINITE')
    codes = list(expression.nominalization_plan)
    original = codes[2]
    pieces = original.split(':')
    if change == 'time': pieces[-1] = 'original_occasion'
    elif change == 'grammar': pieces[-2] = 'PAST_FEELING'
    elif change == 'reaction_slot': pieces[2] = codes[1].split(':')[2]
    else: pieces[-3] = codes[1].split(':')[-3]
    codes[2] = ':'.join(pieces)
    assert codes[2] != original
    changed = hr.identify_source_grounded_reception_expression(replace(expression, expression_ref='', nominalization_plan=tuple(codes)))
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    clauses = next(line.reception_clause_plans for line in sentence.lines if line.binding.line_role == 'human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception, (changed,), {n.nucleus_id:n for n in plan.nuclei}, resolver,
            plan=plan, recovery_stage='full', clause_plans=clauses, selected_subjective_input=projection.selected_reception)


@pytest.mark.parametrize('answer,answer_phrase', [
    ('その時は嬉しかった。', 'その時に嬉しかったという気持ち'),
    ('今は嬉しい。', '回答した時点で嬉しいという気持ち'),
    ('その時は嬉しかった。どう表したらいいかはまだ分からない。',
     'その時に嬉しかったという気持ち'),
])
@pytest.mark.parametrize('q3', [False, True])
def test_single_event_positive_add_keeps_both_independent_meanings(answer, answer_phrase, q3):
    from test_cmee_emlis_q1_thread import answered
    req = begin('褒められたのに、嬉しくなかった。') if q3 else initial()
    req = advance(req, answer) if q3 else answered(answer, req)
    prepared = prepare_emlis_meaning(req)
    assert not prepared.checkpoint.inactive_claim_refs
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    follow = result.artifact.reception
    assert '褒められたのに嬉しくなかったこと' in follow
    assert '褒められたことについて、' + answer_phrase in follow
    decisions = projection.selected_reception.decisions
    assert len(decisions) == 2 and all(d.branch == 'NORMAL' for d in decisions)
    assert len({d.projected_claim_ref for d in decisions}) == 2
    assert not set(decisions[0].selected_contribution_refs) & set(decisions[1].selected_contribution_refs)
    assert {d.reception_act for d in decisions} == {'stay_with_current_burden', 'recognize_lived_change'}
    if '分からない' in answer:
        assert prepared.checkpoint.assessment_status == 'PARTIAL'


def test_single_event_positive_add_inverse_rejects_lost_or_retimed_original_and_answer():
    from test_cmee_emlis_q1_thread import answered
    prepared = prepare_emlis_meaning(answered('今は嬉しい。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def valid(follow):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.reception, follow).encode(),
            plan=plan, sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    follow = result.artifact.reception
    assert valid(follow)
    mutations = [
        follow.split('。', 1)[1], follow.split('。', 1)[0] + '。',
        follow.replace('嬉しくなかったこと', '嬉しかったこと'),
        follow.replace('嬉しくなかったこと', '嬉しくないこと'),
        follow.replace('回答した時点で', 'その時に'),
        follow.replace('褒められたことについて', '誘われたことについて'),
        follow.replace('褒められたのに嬉しくなかったこと', '「褒められたのに嬉しくなかったこと」'),
    ]
    for changed in mutations:
        assert changed != follow and not valid(changed)


@pytest.mark.parametrize('answer,phrase', [
    ('その時は重かった。', 'その出来事へのその時の重さ'),
    ('今は怖い。', 'その出来事について、回答した時点で怖いこと'),
    ('今は怖くない。', 'その出来事について、回答した時点で怖くないこと'),
    ('その時は重かった。どう表したらいいかはまだ分からない。', 'その出来事へのその時の重さ'),
])
@pytest.mark.parametrize('q3', [False, True])
def test_single_event_negative_add_preserves_original_and_answer_in_body_and_selection(answer, phrase, q3):
    from test_cmee_emlis_q1_thread import answered
    req = advance(begin('褒められたのに、嬉しくなかった。'), answer) if q3 else answered(answer)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert not prepared.checkpoint.inactive_claim_refs
    assert '嬉しくなかった' in result.artifact.observation
    assert '褒められたのに嬉しくなかったこと' in result.artifact.reception
    assert phrase in result.artifact.reception
    move, = plan.response_plan.human_reception_plan.moves
    assert move.target_nucleus_ids == ('nucleus:s1:event',)
    assert move.support_nucleus_ids == ('nucleus:s1:reaction', prepared.accepted_nuclei[0].nucleus_id)
    decision, = projection.selected_reception.decisions
    assert decision.branch == 'NORMAL'
    assert len(decision.selected_contribution_refs) == 2
    assert set(decision.selected_contribution_refs) == set(decision.subjective_proposition.target_contribution_refs)
    if '分からない' in answer:
        assert prepared.checkpoint.assessment_status == 'PARTIAL'


@pytest.mark.parametrize('answer,phrase,retimed', [
    ('その時は重かった。', 'その出来事へのその時の重さ', 'その出来事への回答した時点の重さ'),
    ('今は怖い。', 'その出来事について、回答した時点で怖いこと', 'その出来事について、その時に怖いこと'),
    ('今はまだよく分からない。', 'その出来事について、回答した時点でまだよく分からないこと', 'その出来事について、その時にまだよく分からないこと'),
])
def test_single_negative_add_inverse_rejects_lost_swapped_or_retimed_meanings(answer, phrase, retimed):
    from test_cmee_emlis_q1_thread import answered
    from emlis_ai_grounded_observation_gate import _body_inverse_thread_received_group
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(answered(answer))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    follow = result.artifact.reception
    def valid(changed):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(follow, changed).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    assert valid(follow)
    move, = plan.response_plan.human_reception_plan.moves
    def parsed(changed):
        raw = result.artifact.text.replace(follow, changed).encode()
        witness = surface.parse_grounded_surface_body_bytes(raw)
        return tuple(_body_inverse_thread_received_group(raw, witness, row, move, plan, resolver)
                     for row in witness.sentences if row.section == 'reception')
    with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no replay')):
        assert any(row is not None for row in parsed(follow))
    original = '褒められたのに嬉しくなかったこと'
    mutations = [
        follow.replace(original + 'と、', ''), follow.replace('と、' + phrase, ''),
        follow.replace(original, '褒められたのに嬉しかったこと'),
        follow.replace(original, '褒められたのに嬉しくないこと'),
        follow.replace(phrase, retimed), follow.replace('褒められた', '誘われた'),
        follow.replace(original, '「' + original + '」'),
    ]
    if 'まだよく分からない' in follow:
        mutations.extend(follow.replace('まだよく分からない', changed)
                         for changed in ('もう分かった', 'まだよく分からなかった', '彼はまだよく分からない'))
    for changed in mutations:
        assert changed != follow and not valid(changed)
        with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no replay')):
            assert all(row is None for row in parsed(changed))


@pytest.mark.parametrize('answer,fragment', [
    ('今はまだよく分からない。', 'まだよく分からない'),
    ('現在は分からない。', '分からない'),
])
@pytest.mark.parametrize('q3', [False, True])
def test_current_unknown_answer_keeps_original_reaction_without_becoming_a_feeling(answer, fragment, q3):
    from test_cmee_emlis_q1_thread import answered
    req = advance(begin('褒められたのに、嬉しくなかった。'), answer) if q3 else answered(answer)
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert not prepared.checkpoint.inactive_claim_refs
    n, = prepared.accepted_nuclei
    assert (n.kind, n.semantic_frame.predicate_kind, n.semantic_frame.modality) == ('state', 'state', 'uncertain')
    assert n.semantic_frame.time_scope == 'present'
    plan = build_updated_grounded_plan(prepared)
    move, = plan.response_plan.human_reception_plan.moves
    assert move.target_nucleus_ids == ('nucleus:s1:event',)
    assert move.support_nucleus_ids == ('nucleus:s1:reaction', n.nucleus_id)
    result = realize_emlis_thread_body(prepared)
    assert '嬉しくなかった' in result.artifact.observation
    assert '褒められたのに嬉しくなかったこと' in result.artifact.reception
    assert 'その出来事について、回答した時点で' + fragment + 'こと' in result.artifact.reception
    assert '反映できていない' not in result.artifact.text


@pytest.mark.parametrize('q3', [False, True])
def test_unsupported_qualified_current_unknown_is_not_promoted_by_reception(q3):
    from test_cmee_emlis_q1_thread import answered
    answer = '今ははっきりわからない。'
    req = advance(begin('褒められたのに、嬉しくなかった。'), answer) if q3 else answered(answer)
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
    assert not prepared.checkpoint.inactive_claim_refs
    assert not prepared.accepted_nuclei


@pytest.mark.parametrize('memo', [
    '今はまだよく分からない。', '現在は分からない。', '現在もまだはっきりわからない。',
    '分からない。', 'わからない。', 'まだ分からない。', 'まだよくわからない。',
])
@pytest.mark.parametrize('q3', [False, True])
def test_initial_epistemic_unknown_reaches_actual_body_without_becoming_resolved(memo, q3):
    from cocolon_meaning_experience_engine import contracts as c
    req = begin(memo) if q3 else initial(memo)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    unknown, = (d for d in projection.graph.owner_dispositions if d.target_unknown_ref)
    carrier = c.source_explicit_epistemic_unknown_object_ref(projection.premeaning, unknown)
    assert carrier and projection.premeaning.material_unknown_refs
    assert unknown.source_owner_disposition is c.SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
    assert unknown.visible_authority is c.VisibleAuthority.NONE
    assert projection.meaning_plan.subjective_claim_rows
    assert all(d.user_fact_effect == 0 for d in projection.meaning_plan.subjective_claim_rows)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id))
    result = engine.generate(req)
    assert result.body_state == 'FINAL' and result.artifact and result.question is None
    assert memo.rstrip('。') in result.artifact.observation
    assert '結論を急がずに、' + memo.rstrip('。') + 'ことを小さくせずに受け止めています。' == result.artifact.reception
    source, = (n for n in plan.nuclei if n.source_fields == ('memo',))
    assert source.semantic_frame.time_scope == ('present' if memo.startswith(('今', '現在')) else 'current_input')
    assert source.kind == source.semantic_frame.predicate_kind == 'uncertainty'
    assert source.grounding_kind == 'explicit' and source.retention == 'required'
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def valid(body):
        return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=projection.selected_reception).passed
    assert valid(result.artifact.text)
    for changed in ('もう分かったことを受け止めています。', 'まだ分からなかったことを受け止めています。',
                    'まだ分からないことを小さくせずに受け止めています。'):
        assert not valid(result.artifact.text.replace(result.artifact.reception, changed))
    # The whole grammatical object must match. Matching its source as a
    # substring would incorrectly admit an added subject, time, or degree.
    from unittest.mock import patch
    nominal = memo.rstrip('。') + 'こと'
    mutations = [
        'まだ' + nominal, 'よく' + nominal, '今は' + nominal, '彼は' + nominal,
        nominal.replace('分からない', '分からなかった').replace('わからない', 'わからなかった'),
        nominal.replace('分からない', '分かった').replace('わからない', 'わかった'),
        '「' + nominal + '」', '『' + nominal + '』', nominal + 'と、' + nominal,
        '今ここに置かれた言葉',
        nominal.replace('現在も', '現在は').replace('まだ', '').replace('よく', '').replace('はっきり', ''),
    ]
    from types import SimpleNamespace
    def independent(follow):
        # Bypass only the existing writer replay equality. The body parser,
        # source/meaning checks and new whole-object matcher must still reject
        # each mutation independently of the writer's expected text.
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=follow)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return valid(result.artifact.text.replace(result.artifact.reception, follow))
    assert independent(result.artifact.reception)
    for changed in mutations:
        if changed != nominal:
            follow = result.artifact.reception.replace(nominal, changed)
            assert not valid(result.artifact.text.replace(result.artifact.reception, follow)), changed
            assert not independent(follow), changed
    assert not independent(result.artifact.reception + memo)
    assert not independent(result.artifact.reception.replace('ことを', 'ことに'))


@pytest.mark.parametrize('memo', ['分からない。', '今はまだよく分からない。', '現在もまだはっきりわからない。'])
@pytest.mark.parametrize('q3', [False, True])
def test_current_unknown_and_separate_action_keep_both_objects(memo, q3):
    from types import SimpleNamespace
    from unittest.mock import patch
    req = (begin if q3 else initial)(memo, 'メモを書いた。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    follow = result.artifact.reception
    nominal = memo.rstrip('。') + 'こと'
    assert follow == (nominal + 'を小さくせずに受け止めています。'
                      'メモを書いたことを大切に思っています。')
    # Exercise the actual Q1 engine as well as the modern thread projector.
    # Their initial contribution shapes differ before the shared partition.
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    current = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id))
    actual = engine.generate(current)
    assert actual.artifact, actual.reason_codes
    assert actual.body_state == 'FINAL' and actual.question is None
    assert actual.artifact.reception == follow
    assert memo.rstrip('。') in actual.artifact.observation
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.reception_act for m in moves] == ['stay_with_current_burden', 'honor_concrete_effort']
    assert all(m.required and not m.support_nucleus_ids for m in moves)
    assert not set(moves[0].source_evidence_span_ids) & set(moves[1].source_evidence_span_ids)
    left, right = projection.selected_reception.decisions
    if left.projected_claim_ref == right.projected_claim_ref:
        assert left.subjective_proposition == right.subjective_proposition
        assert not set(left.selected_contribution_refs) & set(right.selected_contribution_refs)
        assert set(left.selected_contribution_refs + right.selected_contribution_refs) == set(
            left.subjective_proposition.target_contribution_refs)
        from cocolon_meaning_experience_engine.emlis_stage1_response import (
            _partition_shared_reception_move_contributions, CMEEStage1ContractError)
        def partition(rows):
            return _partition_shared_reception_move_contributions(
                rows, plan.response_plan.human_reception_plan, projection.binding)
        assigned = [left, right]
        assert partition(assigned) is assigned
        complete = left.subjective_proposition.target_contribution_refs
        full = [replace(row, selected_contribution_refs=complete) for row in assigned]
        assert [r.selected_contribution_refs for r in partition(full)] == [
            r.selected_contribution_refs for r in assigned]
        for invalid in [
            [full[0], right],
            [replace(left, selected_contribution_refs=()), right],
            [replace(left, selected_contribution_refs=right.selected_contribution_refs),
             replace(right, selected_contribution_refs=left.selected_contribution_refs)],
            [replace(left, selected_contribution_refs=(*left.selected_contribution_refs, 'foreign')), right],
            [replace(left, basis_rows=left.basis_rows[:-1]), right],
        ]:
            with pytest.raises(CMEEStage1ContractError, match='CAUSAL_TRACE_GAP'):
                partition(invalid)
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def independent(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=changed)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(
                body=result.artifact.text.replace(follow, changed).encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver,
                selected_subjective_input=projection.selected_reception).passed
    assert independent(follow)
    for altered in ['まだ' + nominal, '今は' + nominal, '彼は' + nominal,
                    nominal.replace('ない', 'なかった'), '「' + nominal + '」',
                    nominal + 'と、' + nominal]:
        assert not independent(follow.replace(nominal, altered)), altered
    assert not independent(follow.split('。', 1)[1])
    assert not independent(follow.split('。', 1)[0] + '。')
    assert not independent(follow.replace('メモを書いた', 'メモを書かなかった'))


def test_independent_material_does_not_override_explicit_action_focus():
    import emlis_ai_grounded_observation_plan as gp
    from emlis_ai_safety_triage import classify_emlis_safety_triage_text
    prepared = prepare_emlis_meaning(begin('分からない。', 'メモを書いた。'))
    original = prepared.original_plan
    action, = (n for n in original.nuclei if n.source_fields == ('memo_action',))
    response, *_ = gp._build_response_and_policies(
        nuclei=original.nuclei, relations=original.relations,
        safety_decision=classify_emlis_safety_triage_text('分からない。 メモを書いた。'),
        complexity=original.input_profile.semantic_complexity,
        material_quality=original.input_profile.material_quality,
        include_reception_relation_support=True, final_source_fidelity=True,
        primary_focus_nucleus_ids=(action.nucleus_id,))
    assert response.human_follow_target_ids == (action.nucleus_id,)


@pytest.mark.parametrize('memo', [
    '彼は分からない。', '「分からない」と言われた。', '分からないと思った。',
    '分からない。寂しかった。', 'まだ分からない？',
])
def test_current_cognition_whole_field_witness_does_not_cover_other_source_forms(memo):
    plan = prepare_emlis_meaning(begin(memo, 'メモを書いた。')).original_plan
    for nucleus in plan.nuclei:
        if nucleus.kind == 'uncertainty':
            assert 'lexical:source_bounded_expression' not in nucleus.semantic_frame.attribute_codes


def test_initial_epistemic_unknown_requires_affected_source_and_complete_evidence():
    prepared = prepare_emlis_meaning(begin('今はまだよく分からない。'))
    boundary, = (b for b in prepared.original_plan.unknown_boundaries if b.dimension == 'source_explicit_epistemic_limit')
    for changed in (replace(boundary, evidence_span_ids=()),
                    replace(boundary, affected_nucleus_ids=()),
                    replace(boundary, affected_nucleus_ids=('nucleus:foreign',)),
                    replace(boundary, surface_policy='do_not_claim')):
        modified = replace(prepared, original_plan=replace(prepared.original_plan, unknown_boundaries=tuple(
            changed if b == boundary else b for b in prepared.original_plan.unknown_boundaries)))
        with pytest.raises(ValueError, match='emlis_thread_epistemic_unknown_source_unbound'):
            project_thread_meaning(modified, build_updated_grounded_plan(modified))


@pytest.mark.parametrize('memo', [
    '今はまだよく分からない。', '現在は分からない。', '現在もまだはっきりわからない。',
    '分からない。', 'わからない。', 'まだ分からない。', 'まだよくわからない。',
])
@pytest.mark.parametrize('q3', [False, True])
def test_current_cognition_observation_preserves_source_without_added_feeling_or_time(memo, q3):
    prepared = prepare_emlis_meaning(begin(memo) if q3 else initial(memo))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    observation = result.artifact.observation
    clause = memo.rstrip('。')
    assert observation == clause + 'のですね。'
    assert '感覚' not in observation and '気持ち' not in observation
    sentence = surface.build_grounded_sentence_plan(plan, prepared.thread.resolver(), recovery_stage='full')
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=prepared.thread.resolver(),
            selected_subjective_input=projection.selected_reception).passed
    assert valid(result.artifact.text)
    mutations = [
        '今は、' + observation,
        '彼は' + observation,
        observation.replace('分からない', '分かった').replace('わからない', 'わかった'),
        observation.replace('分からない', '分からなかった').replace('わからない', 'わからなかった'),
        clause + 'という感覚が前に出ています。',
        clause + 'のですか？',
        '「' + clause + '」という感覚が前に出ています。',
        '「' + clause + '」のですね。',
        observation + observation,
        observation.replace('現在も', '現在は').replace('まだ', '').replace('はっきり', '').replace('よく', ''),
    ]
    for changed in mutations:
        if changed != observation:
            assert not valid(result.artifact.text.replace(observation, changed)), changed


@pytest.mark.parametrize('q3', [False, True])
def test_bare_unknown_without_unfinished_source_proof_is_not_promoted_by_binding(q3):
    prepared = prepare_emlis_meaning(begin('分からない。') if q3 else initial('分からない。'))
    # The real bare source now has a final-OP proof. Remove that proof to keep
    # this negative test's original purpose: binding must not invent it.
    added = {'semantic_role:limiting_unknown', 'lexical:preserve_source_predicate',
             'lexical:no_new_sensation_family'}
    plan = prepared.original_plan
    prepared = replace(prepared, original_plan=replace(plan, nuclei=tuple(
        replace(n, kind='state', semantic_frame=replace(n.semantic_frame, predicate_kind='state',
            attribute_codes=tuple(code for code in n.semantic_frame.attribute_codes if code not in added)))
        if n.source_fields == ('memo',) else n for n in plan.nuclei)))
    with pytest.raises(ValueError, match='LIMITED_RECEPTION_CAPABILITY_GAP_STOP'):
        project_thread_meaning(prepared, build_updated_grounded_plan(prepared))


@pytest.mark.parametrize('clause', ['分からない', 'わからない'])
def test_bare_cognition_proof_requires_whole_source_and_keeps_legacy_low_information(clause):
    import emlis_ai_grounded_observation_plan as gp
    prepared = prepare_emlis_meaning(begin(clause + '。'))
    original = prepared.original_plan
    nucleus, = (n for n in original.nuclei if n.source_fields == ('memo',))
    raw = dict(memo=clause + '。', memo_action='', category=['仕事'], emotions=['不安'],
               emotion_details=[dict(type='不安', strength='medium')])
    legacy = gp.build_grounded_observation_plan(raw)
    labels = tuple(n for n in original.nuclei if n.allowed_claim_scope == 'selected_label_only')
    legacy_labels = tuple(n for n in legacy.nuclei if n.allowed_claim_scope == 'selected_label_only')
    assert labels and all(n.retention == 'required' for n in legacy_labels)
    assert labels == tuple(replace(n, retention='optional') for n in legacy_labels)
    assert original.input_profile.material_quality == legacy.input_profile.material_quality
    assert original.coverage_requirements.required_nucleus_ids == (nucleus.nucleus_id,)
    span = prepared.thread.resolver().resolve(nucleus.source_span_ids[0])
    # I5 still treats these short texts as limited; only final OP may prove
    # their complete source-owned finite predicate before meaning selection.
    assert not gp._is_substantive_text_span(span)
    added = {'semantic_role:limiting_unknown', 'lexical:preserve_source_predicate',
             'lexical:no_new_sensation_family'}
    before = replace(nucleus, kind='state', semantic_frame=replace(nucleus.semantic_frame,
        predicate_kind='state', attribute_codes=tuple(c for c in nucleus.semantic_frame.attribute_codes if c not in added)))
    def projected(source, evidence=span, owner=before):
        plan = replace(original, nuclei=(owner,))
        nuclei, _ = gp._final_stage1_typed_nuclei(plan, (evidence,), normalized_input={'memo': source})
        result, = nuclei
        return result
    proven = projected(clause + '。')
    assert proven == replace(before, kind='uncertainty', semantic_frame=replace(before.semantic_frame,
        predicate_kind='uncertainty', attribute_codes=before.semantic_frame.attribute_codes + (
            'semantic_role:limiting_unknown', 'lexical:preserve_source_predicate', 'lexical:no_new_sensation_family')))
    for source in (clause + '？', clause + 'なら待つ。', clause + '。続きがある。',
                   clause + '。。', '彼は' + clause + '。', '「' + clause + '。」'):
        start = source.index(clause)
        changed = replace(span, start_index=start, end_index=start + len(clause))
        assert projected(source, changed).kind == 'state', source
    for changed in (replace(span, start_index=1), replace(span, end_index=len(clause) - 1),
                    replace(span, raw_text=clause + '。'), replace(span, source_field='answer_text_private')):
        assert projected(clause + '。', changed).kind == 'state'
    for changed in (replace(before, retention='optional'), replace(before, grounding_kind='inferred'),
                    replace(before, allowed_claim_scope='selected_label_only'),
                    replace(before, semantic_frame=replace(before.semantic_frame, actor='other')),
                    replace(before, semantic_frame=replace(before.semantic_frame, time_scope='past'))):
        assert projected(clause + '。', owner=changed).kind == 'state'
    # The original low-information label obligations stay required when the
    # whole-field proof is absent or another text owner is present.
    legacy_text, = (n for n in legacy.nuclei if n.source_fields == ('memo',))
    for source in (clause + '？', '「' + clause + '。」'):
        start = source.index(clause)
        evidence = replace(span, start_index=start, end_index=start + len(clause))
        result, _ = gp._final_stage1_typed_nuclei(legacy, (evidence,), normalized_input={'memo': source})
        assert tuple(n for n in result if n.allowed_claim_scope == 'selected_label_only') == legacy_labels
    additional = replace(legacy_text, nucleus_id='other:text', source_span_ids=('other:span',), source_fields=('memo_action',))
    result, _ = gp._final_stage1_typed_nuclei(replace(legacy, nuclei=legacy.nuclei + (additional,)),
        (span,), normalized_input={'memo': clause + '。', 'memo_action': '待つ。'})
    assert tuple(n for n in result if n.allowed_claim_scope == 'selected_label_only') == legacy_labels


def test_initial_epistemic_unknown_view_independently_rejects_lost_or_rebound_unknown():
    from cocolon_meaning_experience_engine import contracts as c
    from cocolon_meaning_experience_engine.emlis_input_specific_meaning import (
        derive_grounded_situation_view, validate_grounded_situation_view)
    prepared = prepare_emlis_meaning(begin('今はまだよく分からない。'))
    projection = project_thread_meaning(prepared, build_updated_grounded_plan(prepared))
    pre, graph = projection.premeaning, projection.graph
    view = derive_grounded_situation_view(pre)
    validate_grounded_situation_view(view, pre, graph)
    basis, = (r for r in view.basis_rows if r.material_unknown_refs)
    compatibility, = (r for r in view.compatibility_rows if r.material_unknown_refs)
    unknown, = (d for d in graph.owner_dispositions if d.target_unknown_ref)
    bookkeeping = f'node:{unknown.target_unknown_ref}@{c.CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}'
    assert basis.scope_object_refs == basis.source_object_refs == (compatibility.scope_object_ref,)
    assert bookkeeping not in basis.scope_object_refs
    mutations = [replace(view, basis_rows=tuple(r for r in view.basis_rows if r != basis))]
    for altered in (replace(basis, scope_object_refs=(bookkeeping,)),
                    replace(basis, source_object_refs=(bookkeeping,)),
                    replace(basis, layer1_required_object_refs=(bookkeeping,)),
                    replace(basis, required_retention_duty_refs=('foreign:duty',)),
                    replace(basis, source_connected_relation_refs=('foreign:relation',)),
                    replace(basis, required_qualifier_refs=('actor:other',)),
                    replace(basis, source_evidence_refs=()), replace(basis, material_unknown_refs=())):
        mutations.append(replace(view, basis_rows=tuple(altered if r == basis else r for r in view.basis_rows)))
    mutations.append(replace(view, compatibility_rows=tuple(
        replace(r, material_unknown_refs=()) if r == compatibility else r for r in view.compatibility_rows)))
    for changed in mutations:
        with pytest.raises(c.CMEEStage1ContractError, match='unknown_'):
            validate_grounded_situation_view(changed, pre, graph)
    with pytest.raises(c.CMEEStage1ContractError):
        validate_grounded_situation_view(view, replace(pre, material_unknown_refs=()), graph)


def test_initial_epistemic_unknown_binding_does_not_accept_conflicting_or_missing_source_proof():
    from cocolon_meaning_experience_engine import contracts as c
    prepared = prepare_emlis_meaning(begin('今はまだよく分からない。'))
    projection = project_thread_meaning(prepared, build_updated_grounded_plan(prepared))
    pre = projection.premeaning
    unknown, = (d for d in pre.grounded_graph.owner_dispositions if d.target_unknown_ref)
    ref = c.source_explicit_epistemic_unknown_object_ref(pre, unknown)
    qualifier, = (q for q in pre.source_qualifier_rows if q.node_ref == ref)
    mutations = [replace(pre, material_unknown_refs=()),
                 replace(pre, grounded_graph=replace(pre.grounded_graph, required_owner_refs=()))]
    for extra in ('actor:other', 'time_scope:past', 'modality:asserted', 'polarity:positive', 'actor:current_user'):
        changed = replace(qualifier, qualifier_refs=qualifier.qualifier_refs + (extra,))
        mutations.append(replace(pre, source_qualifier_rows=tuple(
            changed if q == qualifier else q for q in pre.source_qualifier_rows)))
    for changed in mutations:
        assert c.source_explicit_epistemic_unknown_object_ref(changed, unknown) is None


@pytest.mark.parametrize('event_count', [1, 2, 3])
@pytest.mark.parametrize('q3', [False, True])
def test_event_withdrawal_keeps_independent_original_reaction_and_untouched_pairs(event_count, q3):
    from test_cmee_emlis_q1_thread import answered
    memo = '。'.join(MEMO.split('。')[:event_count]) + '。'
    request = begin(memo) if q3 else initial(memo)
    request = advance(request, '「褒められた」は誤りです。') if q3 else answered('「褒められた」は誤りです。', request)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert 'nucleus:s1:event' in prepared.checkpoint.inactive_claim_refs
    assert 'nucleus:s1:reaction' not in prepared.checkpoint.inactive_claim_refs
    assert '褒められた' not in result.artifact.text
    assert '嬉しくなかったこと' in result.artifact.reception
    assert 'その時の気持ちとして、「嬉しくなかった」が見えます' in result.artifact.observation
    for phrase in ('誘われたのに悲しかったこと', '頼まれたのに寂しかったこと')[:event_count-1]:
        assert phrase in result.artifact.reception
    assert not any('nucleus:s1:event' in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert any(m.target_nucleus_ids == ('nucleus:s1:reaction',) and not m.support_nucleus_ids
               for m in plan.response_plan.human_reception_plan.moves)


@pytest.mark.parametrize('answers,phrase', [
    (('その時は重かった。',), 'その時の重さ'),
    (('今は嬉しい。',), '回答した時点で嬉しいという気持ち'),
    (('その時は重かった。', '今は怖い。'), 'その時の重さ'),
])
def test_event_withdrawal_preserves_orphan_answer_time_and_other_event_answers(answers, phrase):
    request = begin()
    for answer in (*answers, '「褒められた」は誤りです。'):
        request = advance(request, answer)
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert '褒められた' not in result.artifact.text
    assert '嬉しくなかったこと' in result.artifact.reception and phrase in result.artifact.reception
    assert '誘われたのに悲しかったこと' in result.artifact.reception
    assert '頼まれたのに寂しかったこと' in result.artifact.reception
    if len(answers) == 2:
        assert 'その出来事について、回答した時点で怖いこと' in result.artifact.reception
        assert 'その時の気持ちとして、「重かった」が見えます' in result.artifact.observation
    answer_nucleus = next(n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    assert not any(answer_nucleus.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    selected = project_thread_meaning(prepared, plan).selected_reception
    assert len(selected.decisions) == 3
    sets = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert sum(map(len, sets)) == len(set().union(*sets))
    assert set().union(*sets) == set(selected.decisions[0].subjective_proposition.target_contribution_refs)


@pytest.mark.parametrize('prior,old,new', [
    ((), '嬉しくなかった', '苦しかった'),
    (('その時は重かった。',), '重かった', '苦しかった'),
])
def test_revising_a_detached_claim_keeps_withdrawal_and_other_source_meanings(prior, old, new):
    request = begin()
    for answer in (*prior, '「褒められた」は誤りです。', f'「{old}」ではなく「{new}」です。'):
        request = advance(request, answer)
    prepared = prepare_emlis_meaning(request)
    result = realize_emlis_thread_body(prepared)
    assert '褒められた' not in result.artifact.text and old not in result.artifact.text
    assert 'その時の苦しさ' in result.artifact.reception
    assert '誘われたのに悲しかったこと' in result.artifact.reception
    assert '頼まれたのに寂しかったこと' in result.artifact.reception
    assert 'nucleus:s1:event' in prepared.checkpoint.inactive_claim_refs


def test_withdrawal_duties_over_capacity_keep_checkpoint_without_partial_body():
    request = begin()
    for answer in ('その時は重かった。', '今は嬉しい。', '「褒められた」は誤りです。'):
        request = advance(request, answer)
    outcome = MeaningExperienceEngine().generate(request)
    assert outcome.meaning_checkpoint and 'nucleus:s1:event' in outcome.meaning_checkpoint.inactive_claim_refs
    assert outcome.body_state == 'MEANING_UPDATED_BODY_UNAVAILABLE' and outcome.artifact is None


@pytest.mark.parametrize('answer,phrase', [
    ('その時は重かった。', 'その時の重さ'),
    ('今は嬉しい。', '回答した時点で嬉しいという気持ち'),
])
def test_event_withdrawal_inverse_rejects_lost_retimed_or_rebound_independent_meaning(answer, phrase):
    from unittest.mock import patch
    from emlis_ai_grounded_observation_gate import _body_inverse_thread_received_group
    prepared = prepare_emlis_meaning(advance(advance(begin(), answer), '「褒められた」は誤りです。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    result = realize_emlis_thread_body(prepared)
    sentence_plan = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    follow = result.artifact.reception
    def valid(follow):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.reception, follow).encode(),
            plan=plan, sentence_plan=sentence_plan, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(follow)
    for changed in (
        follow.replace('嬉しくなかったこと', '嬉しかったこと'),
        follow.replace('嬉しくなかったこと', '嬉しくないこと'),
        follow.replace('嬉しくなかったこと', '「嬉しくなかったこと」'),
        follow.replace('嬉しくなかったこと', '褒められたのに嬉しくなかったこと'),
        follow.replace(phrase, ''),
        follow.replace(phrase, phrase.replace('その時の', '回答した時点の').replace('回答した時点で', 'その時に')),
        follow.replace('誘われたのに悲しかったこと', '誘われたのに嬉しくなかったこと'),
    ):
        assert changed != follow and not valid(changed)
    group = next(m for m in plan.response_plan.human_reception_plan.moves if m.support_nucleus_ids)
    def parsed(text):
        raw = text.encode()
        witness = surface.parse_grounded_surface_body_bytes(raw)
        return any(_body_inverse_thread_received_group(raw, witness, sentence, group, plan, resolver) is not None
                   for sentence in witness.sentences if sentence.section == 'reception')
    with patch('emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no replay')):
        assert parsed(result.artifact.text)
        assert not parsed(result.artifact.text.replace('と、頼まれたのに寂しかったこと', ''))


@pytest.mark.parametrize('memo,first_nominal', [
    ('何となく寂しい。なぜそう感じるのかは分からない。', '何となく寂しいこと'),
    ('私は少し怖い。その理由はまだよく分からない。', '少し怖いというあなたの気持ち'),
    ('僕はとても寂しい。その理由は分からない。', 'とても寂しいというあなたの気持ち'),
    ('人が近くにいても、自分だけ離れている感じがする。どうしてそう感じるのかがわからない。', '人が近くにいても、自分だけ離れている感じがすること'),
])
@pytest.mark.parametrize('q3', [False, True])
def test_current_feeling_and_its_reason_unknown_remain_one_reception_duty(memo, first_nominal, q3):
    req = (begin if q3 else initial)(memo, 'お茶を飲んだ。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    feeling, unknown = memo.rstrip('。').split('。')
    expected = first_nominal + 'と、' + unknown + 'ことを小さくせずに受け止めています。お茶を飲んだことを大切に思っています。'
    assert result.artifact.reception == expected
    assert unknown + 'のですね。' in result.artifact.observation
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    current = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id))
    actual = engine.generate(current)
    assert actual.artifact and actual.body_state == 'FINAL' and actual.question is None
    assert actual.artifact.reception == expected
    moves = plan.response_plan.human_reception_plan.moves
    assert [(m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids) for m in moves] == [
        ('stay_with_current_burden', ('nucleus:s1',), ('nucleus:s2',)),
        ('honor_concrete_effort', ('nucleus:s3',), ())]
    assert all(r.retention != 'required' and r.type == 'uncertain_connection' for r in plan.relations)
    left, right = projection.selected_reception.decisions
    if left.projected_claim_ref == right.projected_claim_ref:
        from cocolon_meaning_experience_engine.emlis_stage1_response import _partition_shared_reception_move_contributions, CMEEStage1ContractError
        assigned = [left, right]
        def partition(rows):
            return _partition_shared_reception_move_contributions(rows, plan.response_plan.human_reception_plan, projection.binding)
        assert partition(assigned) is assigned
        complete = left.subjective_proposition.target_contribution_refs
        assert not set(left.selected_contribution_refs) & set(right.selected_contribution_refs)
        assert set(left.selected_contribution_refs + right.selected_contribution_refs) == set(complete)
        full = [replace(r, selected_contribution_refs=complete) for r in assigned]
        assert [r.selected_contribution_refs for r in partition(full)] == [r.selected_contribution_refs for r in assigned]
        for bad in ([full[0], right], [replace(left, selected_contribution_refs=()), right],
                    [replace(left, selected_contribution_refs=right.selected_contribution_refs), replace(right, selected_contribution_refs=left.selected_contribution_refs)]):
            with pytest.raises(CMEEStage1ContractError, match='CAUSAL_TRACE_GAP'):
                partition(bad)


@pytest.mark.parametrize('memo', [
    '友達がつらい。その理由は分からない。',
    '私も少し怖い。その理由は分からない。',
    '私だけ少し怖い。その理由は分からない。',
    '私が一緒にいる友達は寂しい。その理由は分からない。',
    '私は仕事中だが彼女は寂しい。その理由は分からない。',
    '彼女は悲しい。なぜそう感じるのかは分からない。',
    '私は不安だ。その理由は分からない。',
    '「私は寂しい」と言われた。その理由は分からない。',
    '何となく寂しい？なぜそう感じるのかは分からない。',
    '何となく寂しかった。なぜそう感じるのかは分からない。',
    '何となく寂しい。その理由は分からなかった。',
    '何となく寂しい。彼がなぜそう感じるのかは分からない。',
    '何となく寂しい。少し怖い。その理由は分からない。',
])
def test_feeling_reason_group_requires_unique_current_self_owned_finite_host(memo):
    import emlis_ai_grounded_observation_plan as gp
    plan = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')).original_plan
    assert not gp._source_feeling_reason_group(plan.nuclei, plan.relations)


def test_feeling_reason_body_inverse_rejects_loss_rebinding_or_closed_reason_without_author_replay():
    from types import SimpleNamespace
    from unittest.mock import patch
    memo = '私は少し怖い。その理由はまだよく分からない。'
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    result = realize_emlis_thread_body(prepared)
    assert result.artifact
    resolver = prepared.thread.resolver()
    sentence_plan = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    follow = result.artifact.reception
    def independent(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=result.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence_plan, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(follow)
    for changed in (
        follow.replace('少し怖いというあなたの気持ちと、', ''), follow.replace('と、その理由はまだよく分からないこと', ''),
        follow.replace('あなたの気持ち', '私の気持ち'), follow.replace('まだよく', ''), follow.replace('分からない', '分かった'),
        follow.replace('分からない', '分からなかった'), follow.replace('その理由', '行動の理由'),
        follow.replace('気持ちと、', '気持ちが原因で、'), follow.replace('少し怖いというあなたの気持ち', '私は少し怖いこと'),
        follow.replace('あなたの気持ち', '彼女の気持ち'), follow.replace('少し怖いというあなたの気持ち', '「少し怖いというあなたの気持ち」'),
        follow.replace('お茶を飲んだこと', 'お茶を飲まなかったこと'),
    ):
        assert changed != follow and not independent(changed), changed


@pytest.mark.parametrize('q3', [False, True])
def test_feeling_reason_group_keeps_explicit_objects_without_a_supplementary_action(q3):
    req = (begin if q3 else initial)('何となく寂しい。なぜそう感じるのかは分からない。')
    prepared = prepare_emlis_meaning(req)
    result = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert result.artifact and actual.artifact
    expected = '何となく寂しいことと、なぜそう感じるのかは分からないことを小さくせずに受け止めています。'
    assert result.artifact.reception == actual.artifact.reception == expected


@pytest.mark.parametrize('memo', [
    '何となく寂しい。なぜそう感じるのかは分からない。',
    '私は少し怖い。その理由はまだよく分からない。',
    '僕はとても寂しい。その理由は分からない。',
])
@pytest.mark.parametrize('recovery_stage', surface.GROUND_RECOVERY_STAGES)
def test_limited_observation_keeps_finite_unknown_separate_from_neighboring_content(memo, recovery_stage):
    # The same admitted meaning can be rendered under limited observation.
    # Exercise every recovery stage; the existing minimal-stage rejection
    # must not collapse these three source duties into one.
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    original = build_updated_grounded_plan(prepared)
    plan = replace(original, input_profile=replace(original.input_profile, material_quality='limited_grounding'))
    resolver = prepared.thread.resolver()
    if recovery_stage == 'minimal_grounded':
        from emlis_ai_grounded_human_reception import GroundedHumanReceptionSurfaceError
        with pytest.raises(GroundedHumanReceptionSurfaceError, match='human_reception_minimal_grounded_not_allowed'):
            surface.build_grounded_sentence_plan(plan, resolver, recovery_stage=recovery_stage)
        return
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage=recovery_stage)
    observation_lines = [line for line in sentence.lines if line.binding.line_role != 'human_follow']
    assert [line.binding.nucleus_ids for line in observation_lines] == [
        ('nucleus:s1',), ('nucleus:s2',), ('nucleus:s3',)]
    assert sentence.covered_required_nucleus_ids == original.coverage_requirements.required_nucleus_ids
    assert sentence.covered_required_relation_ids == original.coverage_requirements.required_relation_ids
    assert [line.binding.sentence_id for line in sentence.lines] == [
        f'sentence:{i}' for i in range(1, len(sentence.lines) + 1)]
    ni = {n.nucleus_id: n for n in plan.nuclei}
    ri = {r.relation_id: r for r in plan.relations}
    texts = [surface._render_final_stage1_limited_scope(line.binding, ni, ri, resolver) for line in observation_lines]
    unknown = memo.rstrip('。').split('。')[1]
    assert texts[1] == unknown + 'のですね。'
    assert all(unknown not in text for text in (texts[0], texts[2]))
    assert 'お茶を飲んだ' not in texts[0] and 'お茶を飲んだ' in texts[2]
    assert sum(text.count('今の入力では、') for text in texts) == 1
    assert texts[2] == '「お茶を飲んだ」という行動も見えます。'
    # Existing Q3 body uses the same independent source duty for this nucleus.
    actual = realize_emlis_thread_body(prepared)
    assert actual.artifact and unknown + 'のですね。' in actual.artifact.observation
    if recovery_stage == 'full':
        from types import SimpleNamespace
        from unittest.mock import patch
        # Exercise the actual initial path, including its outer core guard.
        # This does not replace that guard or reception with a test double.
        req = initial(memo, 'お茶を飲んだ。')
        engine = MeaningExperienceEngine()
        checkpoint = engine.prepare_emlis_update(req)
        outcome = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
        assert outcome.artifact and outcome.body_state == 'FINAL' and outcome.question is None
        assert unknown + 'のですね。' in outcome.artifact.observation
        assert 'お茶を飲んだ' in outcome.artifact.observation
        selected = project_thread_meaning(prepared, original).selected_reception
        body = actual.artifact.text.replace(actual.artifact.observation, '\n'.join(texts))
        def valid(changed):
            # Keep the already-tested reception while isolating this changed
            # observation profile. Its selected meaning was not recomputed.
            with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                       return_value=SimpleNamespace(text=actual.artifact.reception)), patch(
                    'emlis_ai_grounded_sentence_surface._source_bound_current_cognition', side_effect=AssertionError('no author replay')):
                return evaluate_grounded_surface_body_inverse(body=changed.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
        assert valid(body)
        for changed in (
            body.replace(texts[1], ''),
            body.replace(texts[1], texts[1] + texts[1]),
            body.replace(texts[1], texts[1].replace('分からない', '分かった')),
            body.replace(texts[1], texts[1].replace('分からない', '分からなかった')),
            body.replace(texts[1], '「' + unknown + '」という、まだ分からない範囲があります。'),
            body.replace('\n'.join(texts), '\n'.join((texts[1], texts[0], texts[2]))),
        ):
            assert changed != body and not valid(changed)


def test_limited_observation_retains_unsplit_group_without_finite_unknown_proof():
    prepared = prepare_emlis_meaning(begin('何となく寂しい。なぜそう感じるのかは分からない。', 'お茶を飲んだ。'))
    original = build_updated_grounded_plan(prepared)
    plan = replace(original, input_profile=replace(original.input_profile, material_quality='limited_grounding'),
        nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame,
            attribute_codes=tuple(code for code in n.semantic_frame.attribute_codes
                if code != 'lexical:preserve_source_predicate'))) if n.nucleus_id == 'nucleus:s2' else n
            for n in original.nuclei))
    sentence = surface.build_grounded_sentence_plan(plan, prepared.thread.resolver())
    observations = [line for line in sentence.lines if line.binding.line_role != 'human_follow']
    assert len(observations) == 1
    assert observations[0].binding.nucleus_ids == ('nucleus:s1', 'nucleus:s2', 'nucleus:s3')


@pytest.mark.parametrize('memo', [
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。',
    '理由はうまく説明できないけれど、嬉しい感じと緊張する感じが同時にある。対象も一つではない気がする。',
    'わけをはっきり説明できないけど、怖い感じと安心した感じがどちらもある。対象は一つではない気がする。',
])
@pytest.mark.parametrize('q3', [False, True])
def test_coexisting_current_material_keeps_both_feelings_and_tentative_target(memo, q3):
    import emlis_ai_grounded_observation_plan as gp
    request = (begin if q3 else initial)(memo, 'お茶を飲んだ。')
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_current_material_group(plan.nuclei, plan.relations)
    assert len(group) == 3
    assert group[0].kind == 'reaction' and group[0].semantic_frame.polarity == 'mixed'
    assert group[1].semantic_frame.modality == 'uncertain'
    assert group[1].kind != 'uncertainty'  # An impression is not inability to know.
    assert not any(u.dimension == 'source_explicit_epistemic_limit'
                   and group[1].nucleus_id in u.affected_nucleus_ids for u in plan.unknown_boundaries)
    assert not any(r.retention == 'required' for r in plan.relations)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    first, second = memo.rstrip('。').split('。')
    assert first + 'ことと、' + second + 'ことを小さくせずに受け止めています。' in result.artifact.reception
    assert result.artifact.reception.index(first) < result.artifact.reception.index('お茶を飲んだ')
    assert 'お茶を飲んだことを大切に思っています。' in result.artifact.reception
    assert 'という制約' not in result.artifact.observation
    assert '対象は一つです' not in result.artifact.text
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(request)
    actual = engine.generate(replace(request, emlis_thread=replace(request.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    if not q3 and memo.startswith('わけを'):
        # The unchanged legacy first-person admission rejects this carrier.
        # Q3 and the common body above are independent of that older gate;
        # do not widen admission to make this capability test generate.
        assert actual.artifact is None and actual.body_state == 'UNAVAILABLE'
        assert actual.reason_codes == ('current_experiencer_or_time_scope_unsupported',)
    else:
        assert actual.artifact and actual.body_state == 'FINAL' and actual.question is None
        assert actual.artifact.reception == result.artifact.reception
    projection = project_thread_meaning(prepared, plan)
    decisions = projection.selected_reception.decisions
    assert len(decisions) == 2
    assigned = [set(d.selected_contribution_refs) for d in decisions]
    assert assigned[0] and assigned[1] and not assigned[0] & assigned[1]


@pytest.mark.parametrize('memo', [
    '友達が嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。',
    '彼には嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。',
    '昨日は嬉しい感じと怖い感じが同時にあった。対象は一つではない気がする。',
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がした。',
    '「嬉しい感じと怖い感じが同時にある」と言われた。対象は一つではない気がする。',
    '嬉しい感じと怖い感じが同時にあるか分からない。対象は一つではない気がする。',
    '嬉しい感じと怖い感じが同時にない。対象は一つではない気がする。',
    '嬉しい感じと怖い感じが同時にある。対象は一つではない。',
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がするが…',
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。まだ何かある。',
    '嬉しい感じと怖い感じと寂しい感じが同時にある。対象は一つではない気がする。',
    '嬉しい感じと怖い感じが同時にある。その理由も一つではない気がする。',
])
def test_current_material_does_not_borrow_unproved_owner_time_or_target(memo):
    import emlis_ai_grounded_observation_plan as gp
    plan = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')).original_plan
    assert not gp._source_current_material_group(plan.nuclei, plan.relations)


def test_current_material_inverse_reads_both_objects_without_author_replay():
    from types import SimpleNamespace
    from unittest.mock import patch
    memo = '理由はうまく説明できないけれど、嬉しい感じと緊張する感じが同時にある。対象も一つではない気がする。'
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = result.artifact.reception
    def independent(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=changed)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=result.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(follow)
    for changed in (
        follow.replace('嬉しい感じと', ''), follow.replace('緊張する感じ', '寂しい感じ'),
        follow.replace('嬉しい感じと緊張する感じ', '緊張する感じと嬉しい感じ'),
        follow.replace('説明できない', '説明できる'), follow.replace('同時にある', '同時にあった'),
        follow.replace('一つではない気がする', '一つではない'),
        follow.replace('対象も', '理由も'), follow.replace('気がする', '気がした'),
        follow.replace('ことと、対象', 'ことが原因で、対象'),
        follow.replace('と、対象も一つではない気がすること', ''),
        follow.replace('お茶を飲んだこと', 'お茶を飲まなかったこと'),
    ):
        assert changed != follow and not independent(changed), changed


@pytest.mark.parametrize('focus_slot', [0, 1, 2])
def test_current_material_preserves_explicit_focus(focus_slot):
    import emlis_ai_grounded_observation_plan as gp
    from emlis_ai_safety_triage import classify_emlis_safety_triage_text
    memo = '理由はうまく説明できないけれど、嬉しい感じと緊張する感じが同時にある。対象も一つではない気がする。'
    original = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')).original_plan
    group = gp._source_current_material_group(original.nuclei, original.relations)
    assert len(group) == 3
    focused = group[focus_slot]
    response, *_ = gp._build_response_and_policies(
        nuclei=original.nuclei, relations=original.relations,
        safety_decision=classify_emlis_safety_triage_text(memo + 'お茶を飲んだ。'),
        complexity=original.input_profile.semantic_complexity,
        material_quality=original.input_profile.material_quality,
        include_reception_relation_support=True, final_source_fidelity=True,
        primary_focus_nucleus_ids=(focused.nucleus_id,))
    assert response.human_follow_target_ids == (focused.nucleus_id,)
    assert focused.nucleus_id in response.human_reception_plan.moves[0].target_nucleus_ids


@pytest.mark.parametrize('q3', [False, True])
def test_current_material_without_action_keeps_both_explicit_objects(q3):
    memo = '嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。'
    req = (begin if q3 else initial)(memo)
    prepared = prepare_emlis_meaning(req)
    out = realize_emlis_thread_body(prepared)
    expected = '嬉しい感じと怖い感じが同時にあることと、対象は一つではない気がすることを小さくせずに受け止めています。'
    assert out.artifact and out.artifact.reception == expected
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert actual.artifact and actual.artifact.reception == expected and actual.question is None


def _current_material_with_requested_focus(monkeypatch, memo, action, q3, slot):
    """Exercise the existing internal focus contract before checkpoint sealing.

    There is no new public focus control. Only the selected focus is supplied;
    source recognition, meaning, sole body author, inverse and engine run live.
    """
    import emlis_ai_grounded_observation_plan as gp
    original = gp._build_response_and_policies
    def requested(**kwargs):
        group = gp._source_current_material_group(kwargs['nuclei'], kwargs['relations'])
        if group:
            kwargs['primary_focus_nucleus_ids'] = (group[slot].nucleus_id,)
        return original(**kwargs)
    monkeypatch.setattr(gp, '_build_response_and_policies', requested)
    return (begin if q3 else initial)(memo, action)


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('memo', [
    '嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。',
    '理由はうまく説明できないけれど、嬉しい感じと緊張する感じが同時にある。対象も一つではない気がする。',
])
def test_current_material_qualification_focus_reaches_both_layers(monkeypatch, q3, action, memo):
    req = _current_material_with_requested_focus(monkeypatch, memo, action, q3, 1)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    move = plan.response_plan.human_reception_plan.moves[0]
    index = {n.nucleus_id:n for n in plan.nuclei}
    assert plan.response_plan.human_follow_target_ids == move.target_nucleus_ids == ('nucleus:s2',)
    assert move.support_nucleus_ids == ('nucleus:s1',)
    target, support = index['nucleus:s2'], index['nucleus:s1']
    assert (target.semantic_frame.modality,target.semantic_frame.polarity) == ('uncertain','negative')
    assert (support.semantic_frame.modality,support.semantic_frame.polarity) == ('feeling','mixed')
    out = realize_emlis_thread_body(prepared)
    first, second = memo.rstrip('。').split('。')
    expected = second+'ことと、'+first+'ことを小さくせずに受け止めています。'
    assert out.artifact and out.artifact.reception.startswith(expected)
    assert first in out.artifact.observation and second in out.artifact.observation
    assert bool('お茶を飲んだこと' in out.artifact.reception) == bool(action)
    engine=MeaningExperienceEngine()
    checkpoint=engine.prepare_emlis_update(req)
    actual=engine.generate(replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert actual.artifact and actual.artifact.reception == out.artifact.reception
    assert actual.question is None


def test_current_material_qualification_inverse_rejects_changes_without_author_replay(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import patch
    memo='嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。'
    req=_current_material_with_requested_focus(monkeypatch,memo,'お茶を飲んだ。',True,1)
    prepared=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(prepared)
    out=realize_emlis_thread_body(prepared);follow=out.artifact.reception
    selected=project_thread_meaning(prepared,plan).selected_reception
    resolver=prepared.thread.resolver();sentence=surface.build_grounded_sentence_plan(plan,resolver)
    def independent(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=changed)),patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=out.artifact.text.replace(follow,changed).encode(),
                plan=plan,sentence_plan=sentence,resolver=resolver,selected_subjective_input=selected).passed
    assert independent(follow)
    for changed in (
        follow.replace('一つではない気がする','一つではない'),
        follow.replace('気がする','気がした'),
        follow.replace('対象は','理由は'),
        follow.replace('嬉しい感じと',''),
        follow.replace('怖い感じ','寂しい感じ'),
        follow.replace('同時にある','同時にあった'),
        follow.replace('と、嬉しい感じと怖い感じが同時にあること',''),
        follow.replace('対象は一つではない気がすることと、',''),
        follow.replace('ことと、嬉しい','ことが原因で、嬉しい'),
        follow.replace('お茶を飲んだこと','お茶を飲まなかったこと'),
    ):
        assert changed != follow and not independent(changed)


def test_current_material_focus_ir_cannot_swap_roles_or_status(monkeypatch):
    import emlis_ai_grounded_human_reception as hr
    memo='嬉しい感じと怖い感じが同時にある。対象は一つではない気がする。'
    req=_current_material_with_requested_focus(monkeypatch,memo,'お茶を飲んだ。',True,1)
    prepared=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(prepared)
    reception=plan.response_plan.human_reception_plan;move=reception.moves[0]
    ir=hr._project_source_grounded_reception_move_realization(reception,move,
        {n.nucleus_id:n for n in plan.nuclei},prepared.thread.resolver(),
        plan=plan,recovery_stage='full',clause_form='FINITE')
    assert hr._source_current_material_group_ir_text(ir)
    for bad in (
        replace(ir,modality='feeling',polarity='mixed'),
        replace(ir,nominalization_plan=(*ir.nominalization_plan[:-1],'source-current-material:0:1')),
        replace(ir,semantic_profiles=tuple(reversed(ir.semantic_profiles))),
        replace(ir,semantic_fragments=tuple(reversed(ir.semantic_fragments))),
        replace(ir,context_slots=()),
    ):
        with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
            hr._source_current_material_group_ir_text(bad)


def test_nominal_constraint_inverse_preserves_source_and_unfinished_tail_without_author_replay():
    from types import SimpleNamespace
    from unittest.mock import patch
    memo = '全部、ちょっと無理。どこからかというとまだ…'
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact, result.reason_codes
    follow = result.artifact.reception
    assert '全部、ちょっと無理という言葉を小さくせずに受け止めています。' in follow
    assert 'どこからかというとまだ…' in result.artifact.observation
    assert 'どこから' not in follow
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)

    def independent(changed_follow, changed_observation=None):
        body = result.artifact.text.replace(follow, changed_follow)
        if changed_observation is not None:
            body = body.replace(result.artifact.observation, changed_observation)
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=changed_follow)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed

    assert independent(follow)
    mutations = {
        'degree': follow.replace('ちょっと', 'とても'),
        'constraint_cancellation': follow.replace('無理という', '無理ではないという'),
        'foreign_owner': follow.replace('全部、ちょっと無理', '弟には全部、ちょっと無理'),
        'source_omission': follow.replace('全部、', ''),
        'unfinished_completion': follow.replace('という言葉を', 'という言葉と、どこからかはまだ分からないことを'),
        'new_cause': follow.replace('全部、ちょっと無理', 'お茶を飲んだことが原因で、全部、ちょっと無理'),
        'action_negation': follow.replace('お茶を飲んだこと', 'お茶を飲まなかったこと'),
    }
    for name, changed in mutations.items():
        assert changed != follow and not independent(changed), name
    completed = result.artifact.observation.replace('どこからかというとまだ…', 'どこからかはまだ分からない')
    assert completed != result.artifact.observation and not independent(follow, completed)


@pytest.mark.parametrize('memo', [
    '弟には全部、ちょっと無理。',
    '弟が全部、ちょっと無理と言った。',
    '「全部、ちょっと無理」と言われた。',
    '全部、ちょっと無理だった。',
    '全部、ちょっと無理ではない。',
    '全部、ちょっと無理かもしれない。',
    '無理の予定を見た。',
    '全部、ちょっと無理？',
    '全部、ちょっと無理…',
    '全部、ちょっと無理。と弟が言ったけど…',
    '全部、ちょっと無理。それは嘘だけど…',
    '全部、ちょっと無理。というのはまだ…',
    '全部、ちょっと無理。昨日はまだ…',
    '全部、ちょっと無理。彼には…',
    '全部、ちょっと無理。どこがつらいかはまだ…',
    '全部、ちょっと無理。どこからかというとまだ分からない。',
    '全部、ちょっと無理。どこからかというとまだ…？',
])
def test_nominal_constraint_source_proof_rejects_changed_scope_or_completion(memo):
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    assert not any('lexical:source_nominal_constraint_clause' in n.semantic_frame.attribute_codes
                   or 'lexical:source_unfinished_utterance_clause' in n.semantic_frame.attribute_codes
                   for n in plan.nuclei)


def _assert_nominal_constraint_actual_contract(first, with_tail, action, q3, plan, direct, actual):
    tail_text = 'どこからかというとまだ…'
    assert direct.artifact is not None, direct.reason_codes
    expected = first + 'という言葉を小さくせずに受け止めています。'
    if action:
        expected += 'お茶を飲んだことを大切に思っています。'
    assert direct.artifact.reception == expected
    assert actual.question is None
    if not q3 and first == 'どれも、もう限界':
        # The unchanged legacy Q1 first-person admission rejects this carrier.
        # Common body and Q3 coverage do not mean Q1 admission was widened.
        assert actual.artifact is None and actual.body_state == 'UNAVAILABLE'
        assert actual.reason_codes == ('current_experiencer_or_time_scope_unsupported',)
    else:
        assert actual.artifact is not None, actual.reason_codes
        assert actual.body_state == 'FINAL'
        assert actual.artifact.reception == direct.artifact.reception

    # Q1 may use its existing limited observation. Check both observations for
    # the complete source parts; do not require identical recovery-stage prose.
    artifacts = (direct.artifact,) + ((actual.artifact,) if actual.artifact else ())
    for artifact in artifacts:
        assert first in artifact.observation
        assert bool('お茶を飲んだ' in artifact.observation) == bool(action)
        assert bool('お茶を飲んだ' in artifact.reception) == bool(action)
        assert bool(tail_text in artifact.observation) == with_tail
        assert tail_text not in artifact.reception
        assert all(x not in artifact.text for x in (
            'どこからか分からない', '理由が分からない', 'まだ説明できない'))

    first_move = plan.response_plan.human_reception_plan.moves[0]
    first_nucleus = next(n for n in plan.nuclei
        if 'lexical:source_nominal_constraint_clause' in n.semantic_frame.attribute_codes)
    assert plan.response_plan.human_follow_target_ids == first_move.target_nucleus_ids == (first_nucleus.nucleus_id,)
    assert first_move.reception_act == 'stay_with_current_burden'
    assert not first_move.support_nucleus_ids
    assert len(plan.response_plan.human_reception_plan.moves) == 1 + bool(action)
    assert first_nucleus.kind == first_nucleus.semantic_frame.predicate_kind == 'constraint'
    assert (first_nucleus.semantic_frame.actor, first_nucleus.semantic_frame.modality,
            first_nucleus.semantic_frame.polarity, first_nucleus.semantic_frame.time_scope) == (
                'current_user', 'possibility', 'negative', 'current_input')
    tails = [n for n in plan.nuclei
        if 'lexical:source_unfinished_utterance_clause' in n.semantic_frame.attribute_codes]
    assert len(tails) == int(with_tail)
    if tails:
        tail = tails[0]
        assert tail.nucleus_id not in first_move.target_nucleus_ids + first_move.support_nucleus_ids
        assert tail.retention == 'required' and tail.grounding_kind == 'explicit'
        assert tail.kind != 'uncertainty'


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('with_tail', [False, True])
@pytest.mark.parametrize('first', ['全部、ちょっと無理', 'どれも、もう限界'])
def test_nominal_constraint_actual_body_keeps_complete_clause_and_unfinished_tail(first, with_tail, action, q3):
    memo = first + '。' + ('どこからかというとまだ…' if with_tail else '')
    req = (begin if q3 else initial)(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    _assert_nominal_constraint_actual_contract(first, with_tail, action, q3, plan, direct, actual)


# Public compositional grammar examples, independent of private product cases.
TEMPORAL_MEMOS = (
    '今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っている。',
    '現在は少し楽になり、今も緊張が残っています。今日のきっかけが同じかもまだ分からない。',
    '以前に疲れがあった時を思い出したけど、今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っている。',
)


@pytest.mark.parametrize('memo', TEMPORAL_MEMOS)
@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
def test_temporal_material_keeps_current_unknown_and_relief_residue(memo, q3, action):
    import emlis_ai_grounded_observation_plan as gp
    req = (begin if q3 else initial)(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_current_material_group(plan.nuclei, plan.relations)
    assert len(group) == 2 + bool(action)
    current, unknown = group[:2]
    assert (current.kind, current.semantic_frame.modality, current.semantic_frame.polarity) == ('change', 'fact', 'mixed')
    assert (unknown.kind, unknown.semantic_frame.modality, unknown.semantic_frame.polarity) == ('uncertainty', 'uncertain', 'negative')
    assert not any(u.dimension == 'source_explicit_epistemic_limit'
                   and current.nucleus_id in u.affected_nucleus_ids for u in plan.unknown_boundaries)
    assert all(r.type == 'uncertain_connection' and r.retention != 'required' for r in plan.relations)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    current_text, unknown_text = [resolver.resolve(n.source_span_ids[0]).raw_text for n in group[:2]]
    current_nominal = current_text.replace('残っています', '残っている')
    assert any(first + 'ことと、' + second + 'こと' in out.artifact.reception
               for first, second in ((current_nominal, unknown_text), (unknown_text, current_nominal)))
    assert 'いますこと' not in out.artifact.reception
    assert unknown_text + 'のですね。' in out.artifact.observation
    assert 'という感覚' not in out.artifact.observation
    assert bool('お茶を飲んだこと' in out.artifact.reception) == bool(action)
    selected = project_thread_meaning(prepared, plan).selected_reception
    assigned = [set(d.selected_contribution_refs) for d in selected.decisions]
    assert len(assigned) == 1 + bool(action) and all(assigned)
    if action:
        assert not assigned[0] & assigned[1]
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    if not q3 and memo != TEMPORAL_MEMOS[1]:
        # Preserve the existing first-person admission boundary. The common
        # body and Q3 capability do not bypass legacy Q1 source admission.
        assert actual.artifact is None and actual.body_state == 'UNAVAILABLE'
        assert actual.reason_codes == ('current_experiencer_or_time_scope_unsupported',)
    else:
        assert actual.artifact and actual.artifact.reception == out.artifact.reception
        assert actual.question is None and actual.body_state == 'FINAL'


@pytest.mark.parametrize('memo', [
    '友達は今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っている。',
    '今の原因が同じかはわからない。彼女は現在は横になると軽くなり、なお疲れも残っている。',
    '「今の原因が同じかはわからない」と言われた。現在は横になると軽くなり、なお疲れも残っている。',
    '今の原因が同じかはわかる。現在は横になると軽くなり、なお疲れも残っている。',
    '昨日の原因が同じかはわからなかった。現在は横になると軽くなり、なお疲れも残っている。',
    '今の原因が同じかはわからない。昨日は横になると軽くなり、なお疲れも残っていた。',
    '今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っていない。',
    '今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っているか分からない。',
    '今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っている。まだ続きがある。',
    '今の原因が同じかはわからない。現在は横になると軽くなり、なお疲れも残っているが…',
    '今の原因が同じかはわからない。',
    '現在は横になると軽くなり、なお疲れも残っている。',
])
def test_temporal_material_requires_complete_pair_and_explicit_scope(memo):
    import emlis_ai_grounded_observation_plan as gp
    plan = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')).original_plan
    assert not gp._source_temporal_material_group(plan.nuclei, plan.relations)
    assert not any(c.startswith('lexical:source_temporal_') for n in plan.nuclei
                   for c in n.semantic_frame.attribute_codes)


@pytest.mark.parametrize('slot', [1, 2])
def test_temporal_material_respects_existing_requested_focus(monkeypatch, slot):
    req = _current_material_with_requested_focus(monkeypatch, TEMPORAL_MEMOS[0], 'お茶を飲んだ。', True, slot)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    first = plan.response_plan.human_reception_plan.moves[0]
    assert first.target_nucleus_ids == (('nucleus:s1',) if slot == 1 else ('nucleus:s3',))
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    if slot == 1:
        assert out.artifact.reception.startswith('今の原因が同じかはわからないことと、現在は横になると軽くなり、なお疲れも残っていること')
    else:
        assert out.artifact.reception.startswith('お茶を飲んだこと')


@pytest.mark.parametrize('unknown_focus', [False, True])
def test_temporal_material_inverse_rejects_scope_changes_without_author_replay(monkeypatch, unknown_focus):
    from types import SimpleNamespace
    from unittest.mock import patch
    memo = TEMPORAL_MEMOS[2]
    req = (_current_material_with_requested_focus(monkeypatch, memo, 'お茶を飲んだ。', True, 1)
           if unknown_focus else begin(memo, 'お茶を飲んだ。'))
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    def independent(body):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=out.artifact.reception)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(out.artifact.text)
    for old, new in (
        ('以前に疲れがあった時', '現在も疲れている時'),
        ('思い出した', '想像した'), ('今の原因が同じかはわからない', '今の原因は分からない'),
        ('わからない', 'わかる'), ('横になると', '横になったから'),
        ('軽くなり', '軽くならず'), ('なお疲れも残っている', '疲れはもうない'),
        ('ことと、', 'ことが原因で、'), ('お茶を飲んだ', 'お茶を飲まなかった'),
    ):
        changed = out.artifact.text.replace(old, new)
        assert changed != out.artifact.text and not independent(changed), (old, new)


def test_temporal_material_polite_attributive_is_checked_without_author_replay():
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(TEMPORAL_MEMOS[1]))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact and '今も緊張が残っていること' in out.artifact.reception
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    selected = project_thread_meaning(prepared, plan).selected_reception
    def independent(follow):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=follow)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(
                body=out.artifact.text.replace(out.artifact.reception, follow).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(out.artifact.reception)
    for ending in ('残っていますこと', '残っていたこと', '残っていないこと'):
        assert not independent(out.artifact.reception.replace('残っていること', ending))


# A tentative comparison and the negative degree of asserting a conclusion
# have different hosts. Neither permits recovery certainty or a new unknown.
PROVISIONAL_DEGREE_MEMOS = (
    '以前より軽くなった気がするけれど、まだ平気と言えるほどではない。',
    'さっきより楽になった気もするけど、すっかり回復したと言えるほどではない。',
    '昨日より楽になった気はしますけれど、もう元気と言えるほどではありません。',
    'さっきより軽くなった気がするけど、もう大丈夫と言い切れるほどではない。',
)


@pytest.mark.parametrize('memo', PROVISIONAL_DEGREE_MEMOS)
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('q3', [False, True])
def test_provisional_degree_actual_body_keeps_both_hosts_before_separate_action(memo, action, q3):
    import re
    req = (begin if q3 else initial)(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert direct.artifact and actual.artifact, (direct.reason_codes, actual.reason_codes)
    assert actual.question is None and actual.body_state == 'FINAL'
    raw = memo.rstrip('。')
    finite = re.sub(r'(気[がはも])します', r'\1する', raw)
    finite = re.sub(r'ありません$', 'ない', finite)
    expected = raw + 'という言葉を小さくせずに受け止めています。'
    if action:
        expected += 'お茶を飲んだことを大切に思っています。'
    for artifact in (direct.artifact, actual.artifact):
        assert artifact.reception == expected
        assert finite + 'のですね。' in artifact.observation
        assert bool('お茶を飲んだ' in artifact.observation) == bool(action)
        assert all(value not in artifact.text for value in (
            'という感覚', 'という変化', '理由が分からない', 'もう大丈夫です', '回復しました'))
    target = next(n for n in plan.nuclei if 'memo' in n.source_fields)
    frame = target.semantic_frame
    assert (target.kind, target.grounding_kind, target.retention) == ('change', 'explicit', 'required')
    assert (frame.actor, frame.modality, frame.polarity, frame.time_scope) == (
        'current_user', 'fact', 'mixed', 'current_input')
    assert not any(n.kind == 'uncertainty' and 'memo' in n.source_fields for n in plan.nuclei)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 1 + bool(action)
    assert moves[0].target_nucleus_ids == (target.nucleus_id,)
    assert moves[0].reception_act == 'stay_with_current_burden'
    assert not any(move.support_nucleus_ids for move in moves)
    if action:
        action_target = next(n for n in plan.nuclei if 'memo_action' in n.source_fields)
        assert moves[1].target_nucleus_ids == (action_target.nucleus_id,)
        assert not any(r.retention == 'required' and r.type != 'uncertain_connection'
                       and {r.from_nucleus_id, r.to_nucleus_id} == {target.nucleus_id, action_target.nucleus_id}
                       for r in plan.relations)


@pytest.mark.parametrize('memo', [
    '私は以前より静かになった気がするけれど、もう安心だと言えるほどではない。',
    '弟は以前より軽くなった気がするけど、もう平気と言えるほどではない。',
    '「以前より軽くなった気がするけど、もう平気と言えるほどではない」と言われた。',
    '以前より軽くなった気がしたけど、もう平気と言えるほどではない。',
    '以前より軽くなったけど、もう平気と言えるほどではない。',
    '以前より軽くなった気がするけど、もう平気と言える。',
    '以前より軽くなった気がするけど、もう平気と言えるほどではなかった。',
    '以前より軽くなった気がするけど、もう平気と言えるほどではないかもしれない。',
    '以前より軽くなった気がするけど、もう平気と言えるほどではない？',
    '以前より軽くなった気がするけど、もう平気と言えるほどではない…',
    '以前より軽くなった気がするけど、もう平気と言えるほどではない。と弟が言った。',
    '以前より軽くなった気がするけど、もう平気と言えるほどではない。どこからかはまだ…',
    '前より楽な気はするけど、まだ重さが残っている。',
    '明日は以前より軽くなった気がするけど、もう平気と言えるほどではない。',
])
def test_provisional_degree_requires_complete_current_user_and_host_scopes(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')))
    assert not any('lexical:source_provisional_degree' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('memo', [PROVISIONAL_DEGREE_MEMOS[2], PROVISIONAL_DEGREE_MEMOS[3]])
def test_provisional_degree_inverse_rejects_host_changes_without_author_replay(memo):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    selected = project_thread_meaning(prepared, plan).selected_reception
    def independent(body):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=out.artifact.reception)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(out.artifact.text)
    # Mutate either observation or reception independently; the other layer
    # cannot compensate for a missing hedge, negation, owner or comparison.
    for section in ('observation', 'reception'):
        original = getattr(out.artifact, section)
        for old, new in (
            ('より', 'と同じくらい'), ('気がする', ''), ('気はする', ''), ('気はします', ''),
            ('ではない', 'です'), ('ではありません', 'です'),
            ('気がする', '気がした'), ('気はする', '気はした'),
            ('気はします', '気はしました'), ('という言葉', 'という確かな事実'),
            ('お茶を飲んだ', 'お茶を飲まなかった'),
        ):
            if old in original:
                changed = out.artifact.text.replace(original, original.replace(old, new))
                assert not independent(changed), (section, old, new)
        changed = out.artifact.text.replace(original, '弟は' + original)
        assert not independent(changed), section


def test_provisional_degree_does_not_exempt_assurances_outside_negative_source(monkeypatch):
    import cocolon_meaning_experience_engine.emlis_thread_surface as thread_surface
    import emlis_ai_grounded_observation_gate as gate
    captured = {}
    original_gate = thread_surface.evaluate_grounded_observation_gate
    def capture(**kwargs):
        captured.update(kwargs)
        return original_gate(**kwargs)
    monkeypatch.setattr(thread_surface, 'evaluate_grounded_observation_gate', capture)
    out = realize_emlis_thread_body(prepare_emlis_meaning(begin(PROVISIONAL_DEGREE_MEMOS[3])))
    assert out.artifact and original_gate(**captured).public_observation_status == 'passed'
    for assurance in ('もう大丈夫です。', '安全です。'):
        raw = captured['surface_result']
        changed = replace(raw, text=raw.text + assurance)
        result = gate.evaluate_grounded_observation_gate(**{**captured, 'surface_result': changed})
        assert result.public_observation_status == 'rejected'
        assert 'reception_safety_or_resolution_guarantee_added' in result.rejection_reasons


# A tentative target appraisal and an explicit evaluation of an alternative
# retain their contrast. Neither is a new unknown or a performed action.
APPRAISAL_CONTRAST_MEMOS = (
    '説明が長かったかもしれない。でも省くのも違う。',
    '判断が厳しかったかも知れない。でも引き下がるのは違う。',
)


@pytest.mark.parametrize('memo', APPRAISAL_CONTRAST_MEMOS)
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('q3', [False, True])
def test_appraisal_contrast_preserves_two_evaluations_and_independent_action(memo, action, q3):
    import emlis_ai_grounded_observation_plan as gp
    req = (begin if q3 else initial)(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_appraisal_contrast_group(plan.nuclei, plan.relations)
    assert len(group) == 2 + bool(action)
    assert (group[0].semantic_frame.modality, group[1].semantic_frame.modality) == ('uncertain', 'fact')
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 1 + bool(action)
    assert (moves[0].target_nucleus_ids, moves[0].support_nucleus_ids) == (
        (group[0].nucleus_id,), (group[1].nucleus_id,))
    contrast = next(r for r in plan.relations if r.type == 'contrast')
    assert contrast.retention == 'required' and contrast.grounding_kind == 'user_stated_relation'
    assert contrast.relation_id in plan.coverage_requirements.required_relation_ids
    if action:
        assert moves[1].target_nucleus_ids == (group[2].nucleus_id,)
        assert not moves[1].support_nucleus_ids
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert direct.artifact and actual.artifact, (direct.reason_codes, actual.reason_codes)
    assert actual.question is None
    first, second = memo.rstrip('。').split('。でも')
    for artifact in (direct.artifact, actual.artifact):
        assert all(part in section for part in (first, second)
                   for section in (artifact.observation, artifact.reception))
        assert bool('お茶を飲んだ' in artifact.reception) == bool(action)
        assert not any(x in artifact.reception for x in ('結論を急がず', '分からない', 'あなたの説明', 'あなたの判断'))


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('focus', [0, 1, 2])
def test_appraisal_contrast_respects_existing_explicit_focus(monkeypatch, q3, focus):
    req = _current_material_with_requested_focus(monkeypatch, APPRAISAL_CONTRAST_MEMOS[0], 'お茶を飲んだ。', q3, focus)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    expected = ('nucleus:s1', 'nucleus:s3', 'nucleus:s4')[focus]
    assert plan.response_plan.human_follow_target_ids == (expected,)
    assert plan.response_plan.human_reception_plan.moves[0].target_nucleus_ids == (expected,)
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert direct.artifact and actual.artifact, (direct.reason_codes, actual.reason_codes)
    for part in ('説明が長かったかもしれない', '省くのも違う', 'お茶を飲んだ'):
        assert part in direct.artifact.reception and part in actual.artifact.reception


@pytest.mark.parametrize('memo', [
    '弟の説明が長かったかもしれない。でも省くのも違う。',
    '「説明が長かったかもしれない。でも省くのも違う」と聞いた。',
    '説明が長かったかもしれないと思った。でも省くのも違う。',
    '説明が長かった。でも省くのも違う。',
    '説明が長かったかもしれない。でも省くのも違うかもしれない。',
    '説明が長かったかもしれない。でも省くのも違った。',
    '説明が長かったかもしれない。でも省くのも…',
    '説明が長かったかもしれない。でも省くのも違う。転居の時期も迷う。',
    '説明が長かったかもしれない。でも省くのも違うと弟は言った。',
    '説明が長かったかもしれない。でも弟は省くのも違うと思う。',
    '声が高かったかもしれない。でも友人が断るのも違う。',
    '声が高かったかもしれない。でも彼が受け入れるのも違う。',
    '声が高かったかもしれない。でも聞かれたら帰るのも違う。',
    '彼の声が高かったかもしれない。でも黙って受け入れるのも違う。',
])
def test_appraisal_contrast_does_not_promote_other_hosts_or_incomplete_material(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')))
    assert not any('lexical:source_appraisal_tentative' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('memo', APPRAISAL_CONTRAST_MEMOS)
def test_appraisal_contrast_inverse_rejects_changed_evaluation_relation_and_action(memo):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    selected = project_thread_meaning(prepared, plan).selected_reception
    def independent(body):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=out.artifact.reception)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(out.artifact.text)
    for section in ('observation', 'reception'):
        original = getattr(out.artifact, section)
        for old, new in (('かもしれない', ''), ('かも知れない', ''), ('違う', '同じだ'),
                         ('違う', '違った'), ('違う', '違わない'), ('との違い', 'が原因'),
                         ('お茶を飲んだ', 'お茶を飲まなかった')):
            if old in original:
                assert not independent(out.artifact.text.replace(original, original.replace(old, new))), (section, old)
        second = memo.rstrip('。').split('。でも')[1]
        assert not independent(out.artifact.text.replace(original, original.replace(second, '')))


# An unresolved choice and an independently unresolved time for starting
# consideration keep their nested objects. Neither proposal is performed.
INDEPENDENT_DECISION_MEMOS = (
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められない。',
    '今の講座を続けるか迷っています。それとは別に、読む資料を替えることを考え始める時期は決められません。',
)


@pytest.mark.parametrize('memo', INDEPENDENT_DECISION_MEMOS)
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('q3', [False, True])
def test_independent_decision_preserves_two_unknown_objects_and_separate_action(memo, action, q3):
    import emlis_ai_grounded_observation_plan as gp
    req = (begin if q3 else initial)(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_independent_decision_group(plan.nuclei, plan.relations)
    assert len(group) == 2 + bool(action)
    assert [n.kind for n in group[:2]] == ['uncertainty', 'uncertainty']
    assert [n.semantic_frame.modality for n in group[:2]] == ['uncertain', 'uncertain']
    assert [n.semantic_frame.polarity for n in group[:2]] == ['neutral', 'negative']
    limits = [u for u in plan.unknown_boundaries if u.dimension == 'source_explicit_epistemic_limit']
    assert len(limits) == 2
    assert {(u.affected_nucleus_ids, u.evidence_span_ids, u.surface_policy) for u in limits} == {
        ((n.nucleus_id,), n.source_span_ids, 'hedge_only') for n in group[:2]}
    assert not plan.coverage_requirements.required_relation_ids
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 1 + bool(action)
    assert (moves[0].target_nucleus_ids, moves[0].support_nucleus_ids) == (
        (group[0].nucleus_id,), (group[1].nucleus_id,))
    if action:
        assert moves[1].target_nucleus_ids == (group[2].nucleus_id,)
        assert not moves[1].support_nucleus_ids
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert direct.artifact and actual.artifact, (direct.reason_codes, actual.reason_codes)
    assert actual.question is None
    hosts = memo.rstrip('。').replace('迷っています', '迷っている').replace('決められません', '決められない').split('。')
    for artifact in (direct.artifact, actual.artifact):
        for section in (artifact.observation, artifact.reception):
            assert all(host in section for host in hosts)
            assert section.index(hosts[0]) < section.index(hosts[1])
        assert bool('お茶を飲んだ' in artifact.reception) == bool(action)
        if action:
            assert '。' in artifact.reception[artifact.reception.index(hosts[1]) + len(hosts[1]):artifact.reception.index('お茶を飲んだ')]
        assert not any(x in artifact.text for x in ('迷っていますこと', '決められませんこと', '使いました', '続けました', '変える時期', '替える時期'))


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('focus', [0, 1, 2])
def test_independent_decision_keeps_explicit_focus_and_independence(monkeypatch, q3, focus):
    import emlis_ai_grounded_observation_plan as gp
    req = _current_material_with_requested_focus(monkeypatch, INDEPENDENT_DECISION_MEMOS[1], 'お茶を飲んだ。', q3, focus)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_independent_decision_group(plan.nuclei, plan.relations)
    expected = group[focus].nucleus_id
    assert plan.response_plan.human_follow_target_ids == (expected,)
    assert plan.response_plan.human_reception_plan.moves[0].target_nucleus_ids == (expected,)
    direct = realize_emlis_thread_body(prepared)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(req)
    actual = engine.generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert direct.artifact and actual.artifact, (direct.reason_codes, actual.reason_codes)
    for artifact in (direct.artifact, actual.artifact):
        follow = artifact.reception
        first = '今の講座を続けるか迷っている'
        second = '読む資料を替えることを考え始める時期は決められない'
        assert all(part in follow for part in (first, second, 'お茶を飲んだ'))
        if focus == 1:
            assert second + 'ことと、それとは別に、' + first in follow
        else:
            assert first + 'ことと、それとは別に、' + second in follow


@pytest.mark.parametrize('memo', [
    '弟が教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められない。',
    '弟の教材を使うか迷っている。それとは別に、弟が通う時間を変えることを考え始める時期も決められない。',
    '「今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められない」と聞いた。',
    '今の教材を使うか迷っていると思った。それとは別に、通う時間を変えることを考え始める時期も決められない。',
    '今の教材を使うか迷っていた。それとは別に、通う時間を変えることを考え始める時期も決められない。',
    '今の教材を使うことにした。それとは別に、通う時間を変えることを考え始める時期も決められない。',
    '今の教材を使うか迷っている。それとは別に、通う時間を変える時期も決められない。',
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始めた時期も決められない。',
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められなかった。',
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められないと弟は言った。',
    '今の教材を使うか迷っている。それとは別に、聞かれたら帰ることを考え始める時期も決められない。',
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も…',
    '今の教材を使うか迷っている。それとは別に、通う時間を変えることを考え始める時期も決められない。昼寝した。',
    '今の教材を使うか迷っている。だから通う時間を変えることを考え始める時期も決められない。',
])
def test_independent_decision_does_not_promote_other_owners_hosts_or_timing(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。')))
    assert not any('lexical:source_independent_decision_choice' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('memo', INDEPENDENT_DECISION_MEMOS)
def test_independent_decision_inverse_rejects_changed_host_nested_scope_and_action(memo):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(memo, 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    selected = project_thread_meaning(prepared, plan).selected_reception
    def independent(body):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=out.artifact.reception)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert independent(out.artifact.text)
    for section in ('observation', 'reception'):
        original = getattr(out.artifact, section)
        for old, new in (('か迷っている', 'ことに決めた'), ('迷っている', '迷っていた'),
                         ('決められない', '決められる'), ('決められない', '決められなかった'),
                         ('ことを考え始める時期', '時期'), ('考え始める', '考え始めた'),
                         ('それとは別に、', 'そのため、'), ('それとは別に、', ''),
                         ('お茶を飲んだ', 'お茶を飲まなかった')):
            assert old in original
            assert not independent(out.artifact.text.replace(original, original.replace(old, new))), (section, old)


@pytest.mark.parametrize('memo', INDEPENDENT_DECISION_MEMOS)
def test_independent_decision_neutral_unknown_carrier_requires_complete_host_and_owner(memo):
    from cocolon_meaning_experience_engine import contracts as c
    prepared = prepare_emlis_meaning(begin(memo))
    pre = project_thread_meaning(prepared, build_updated_grounded_plan(prepared)).premeaning
    unknowns = [d for d in pre.grounded_graph.owner_dispositions if d.target_unknown_ref]
    assert len(unknowns) == 2
    for unknown in unknowns:
        ref = c.source_explicit_epistemic_unknown_object_ref(pre, unknown)
        assert ref is not None
        qualifier, = (q for q in pre.source_qualifier_rows if q.node_ref == ref)
        for extra in ('actor:other', 'time_scope:past', 'modality:asserted', 'polarity:positive'):
            changed = replace(qualifier, qualifier_refs=qualifier.qualifier_refs + (extra,))
            assert c.source_explicit_epistemic_unknown_object_ref(replace(pre, source_qualifier_rows=tuple(
                changed if q == qualifier else q for q in pre.source_qualifier_rows)), unknown) is None
        if 'polarity:neutral' in qualifier.qualifier_refs:
            node, = (n for n in pre.grounded_graph.nodes if c._graph_object_ref(n) == ref)
            for value in ('迷っている', node.value.replace('迷っている', '決めた').replace('迷っています', '決めました'),
                          '弟が' + node.value):
                graph = replace(pre.grounded_graph, nodes=tuple(
                    replace(n, value=value) if n == node else n for n in pre.grounded_graph.nodes))
                assert c.source_explicit_epistemic_unknown_object_ref(replace(pre, grounded_graph=graph), unknown) is None


@pytest.mark.parametrize('focus', [0, 1])
def test_independent_decision_ir_cannot_swap_roles_or_promote_proposed_actions(monkeypatch, focus):
    import emlis_ai_grounded_human_reception as hr
    req = _current_material_with_requested_focus(monkeypatch, INDEPENDENT_DECISION_MEMOS[1], '', True, focus)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    reception = plan.response_plan.human_reception_plan
    ir = hr._project_source_grounded_reception_move_realization(reception, reception.moves[0],
        {n.nucleus_id: n for n in plan.nuclei}, prepared.thread.resolver(),
        plan=plan, recovery_stage='full', clause_form='FINITE')
    assert hr._source_current_material_group_ir_text(ir)
    mutations = [replace(ir, modality='fact'), replace(ir, polarity='mixed'),
        replace(ir, context_slots=()), replace(ir, semantic_fragments=tuple(reversed(ir.semantic_fragments))),
        replace(ir, nominalization_plan=(*ir.nominalization_plan[:-1], 'source-independent-decision:' + ('1:0' if focus == 0 else '0:1')))]
    for slot, profile in enumerate(ir.semantic_profiles):
        for changes in ({'actor_kind': 'OTHER'}, {'performed_action': True}, {'future_action': True},
                        {'quoted_boundary': True}, {'modality': 'fact'}):
            mutations.append(replace(ir, semantic_profiles=tuple(
                replace(p, **changes) if i == slot else p for i, p in enumerate(ir.semantic_profiles))))
    for bad in mutations:
        with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
            hr._source_current_material_group_ir_text(bad)


ACTION_CHANGE_CONTRAST_MEMO = (
    '窓辺の鉢を棚へ移したら、机の上が広くなってうれしかった。'
    '一方で、いつも見ていた葉が遠くなり、手元に緑がない寂しさも残っている。'
)


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('unfinished', ['', 'まだ配置は見つかっていない。'])
def test_action_change_contrast_receives_both_duties_in_actual_body(q3, action, unfinished):
    import emlis_ai_grounded_observation_plan as gp
    req = (begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + unfinished, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_action_change_contrast(plan.nuclei, plan.relations)
    assert len(group) == 3
    moves = plan.response_plan.human_reception_plan.moves
    assert [(m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids) for m in moves] == [
        ('honor_concrete_effort', (group[0],), (group[1],)),
        ('stay_with_current_burden', (group[2],), ()),
    ]
    output = MeaningExperienceEngine().generate(req)
    assert output.artifact, output.reason_codes
    assert '窓辺の鉢を棚へ移したこと' in output.artifact.reception
    assert '机の上が広くなってうれしかったこと' in output.artifact.reception
    assert 'いつも見ていた葉が遠くなり、手元に緑がない寂しさも残っていること' in output.artifact.reception
    assert 'とで、' not in output.artifact.reception
    if unfinished:
        assert unfinished[:-1] in output.artifact.observation
        remaining = next(n for n in plan.nuclei if 'semantic_role:present_unfinished' in n.semantic_frame.attribute_codes)
        assert (remaining.kind, remaining.semantic_frame.modality, remaining.semantic_frame.polarity) == ('event', 'fact', 'negative')
        assert remaining.nucleus_id in plan.coverage_requirements.required_nucleus_ids
        assert all(remaining.nucleus_id not in u.affected_nucleus_ids for u in plan.unknown_boundaries
                   if u.dimension == 'source_explicit_epistemic_limit')


@pytest.mark.parametrize('q3', [False, True])
def test_action_change_contrast_whole_contribution_partition_cannot_be_swapped(q3):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    prepared = prepare_emlis_meaning((begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    selected = projection.selected_reception
    left, right = selected.decisions
    assert left.projected_claim_ref == right.projected_claim_ref
    assert set(left.selected_contribution_refs).isdisjoint(right.selected_contribution_refs)
    assert set(left.selected_contribution_refs) | set(right.selected_contribution_refs) == set(left.subjective_proposition.target_contribution_refs)
    wrong = hr.identify_selected_subjective_reception_decision(replace(left, decision_ref='',
        selected_contribution_refs=right.selected_contribution_refs))
    altered = hr.identify_selected_subjective_reception_input(replace(selected, input_ref='', decisions=(wrong, right)))
    resolver = prepared.thread.resolver()
    reception = plan.response_plan.human_reception_plan
    expressions = tuple(_bind_expression(plan, resolver, replace(projection, selected_reception=altered), m, 'FINITE') for m in reception.moves)
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    clauses = next(l.reception_clause_plans for l in sentence.lines if l.binding.line_role == 'human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception, expressions, {n.nucleus_id: n for n in plan.nuclei},
            resolver, plan=plan, recovery_stage='full', clause_plans=clauses, selected_subjective_input=altered)


@pytest.mark.parametrize('change', ['actor', 'polarity', 'modality', 'retention', 'relation_grounding', 'relation_retention'])
def test_action_change_contrast_requires_the_complete_explicit_source_graph(change):
    import emlis_ai_grounded_observation_plan as gp
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO)))
    group = gp._source_action_change_contrast(plan.nuclei, plan.relations)
    assert group
    nuclei, relations = plan.nuclei, plan.relations
    burden = next(n for n in nuclei if n.nucleus_id == group[2])
    if change in {'actor', 'polarity', 'modality', 'retention'}:
        if change == 'retention':
            changed = replace(burden, retention='should')
        else:
            changed = replace(burden, semantic_frame=replace(burden.semantic_frame,
                **{change: {'actor': 'other_person', 'polarity': 'positive', 'modality': 'possibility'}[change]}))
        nuclei = tuple(changed if n == burden else n for n in nuclei)
    else:
        relations = tuple(replace(r, **({'grounding_kind': 'bounded_structural_inference'}
            if change == 'relation_grounding' else {'retention': 'should'}))
            if r.type == 'contrast' else r for r in relations)
    assert not gp._source_action_change_contrast(nuclei, relations)


@pytest.mark.parametrize('suffix', [
    '友人の話では、まだ配置は見つかっていない。',
    '伝聞では、まだ方法は決まっていない。',
    'まだ配置は見つかっていないと言われた。',
    'まだ配置は見つかっていないかもしれない。',
    'もしまだ配置は見つかっていないなら。',
    'まだ配置は見つかっていないわけではない。',
    '「まだ配置は見つかっていない」。',
    'まだ配置は見つかっていなかった。',
])
def test_unfinished_result_duty_does_not_promote_other_finite_hosts(suffix):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO + suffix)))
    assert not any('semantic_role:present_unfinished' in n.semantic_frame.attribute_codes for n in plan.nuclei)


def test_action_change_contrast_inverse_rejects_missing_or_changed_source_without_author_replay():
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO))
    plan = build_updated_grounded_plan(prepared)
    output = realize_emlis_thread_body(prepared)
    assert output.artifact, output.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = output.artifact.reception
    def passes(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan',
                   return_value=SimpleNamespace(text=changed)), patch(
                   'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses',
                   side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=output.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    for changed in (follow.split('。')[0] + '。', follow.split('。', 1)[1],
                    follow.replace('いつも見ていた葉が遠くなり、', ''),
                    follow.replace('寂しさも残っている', '寂しさも残っていた'),
                    follow.replace('寂しさも残っている', '寂しさは残っていない'),
                    follow.replace('うれしかった', 'うれしくなかった'),
                    follow.replace('窓辺の鉢を棚へ移した', '弟が窓辺の鉢を棚へ移した')):
        assert changed != follow and not passes(changed)


@pytest.mark.parametrize('change', ['field', 'offset', 'prefix'])
def test_split_contrast_clause_requires_adjacent_original_connector(monkeypatch, change):
    import emlis_ai_grounded_human_reception as hr
    import emlis_ai_grounded_observation_plan as gp
    prepared = prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO))
    plan = build_updated_grounded_plan(prepared)
    group = gp._source_action_change_contrast(plan.nuclei, plan.relations)
    burden = next(n for n in plan.nuclei if n.nucleus_id == group[2])
    resolver = prepared.thread.resolver()
    assert hr._source_grounded_split_contrast_fragment(burden, resolver).startswith('いつも見ていた葉')
    original = resolver.resolve_many
    def changed(ids):
        return tuple(replace(s, **({'source_field': 'memo_action'} if change == 'field' else
                                  {'end_index': s.end_index - 1} if change == 'offset' else {'raw_text': '一緒'}))
                     if s.raw_text == '一方' else s for s in original(ids))
    monkeypatch.setattr(resolver, 'resolve_many', changed)
    assert hr._source_grounded_split_contrast_fragment(burden, resolver) is None


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('ending', ['まだ配置は見つかっていない。', 'まだ配置は見つかっていません。'])
def test_mixed_unfinished_fact_survives_actual_reception_as_a_separate_duty(q3, ending):
    import emlis_ai_grounded_observation_plan as gp
    req = (begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + ending)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    unfinished = gp._source_action_change_contrast_unfinished(plan.nuclei, plan.relations)
    assert len(unfinished) == 1
    group = gp._source_action_change_contrast(plan.nuclei, plan.relations)
    moves = plan.response_plan.human_reception_plan.moves
    assert [(m.move_role, m.reception_act, m.target_nucleus_ids, m.support_nucleus_ids) for m in moves] == [
        ('attention', 'honor_concrete_effort', (group[0],), (group[1],)),
        ('attention', 'stay_with_current_burden', (group[2],), ()),
        ('felt_response', 'stay_with_current_burden', unfinished, ()),
    ]
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact, result.reason_codes
    assert ending[:-1] in result.artifact.observation
    nominal = ending[:-1] + ('という言葉' if ending.endswith('ません。') else 'こと')
    assert nominal + 'を小さくせずに受け止めています。' in result.artifact.reception
    assert result.artifact.reception.count(ending[:-1]) == 1
    assert '手元に緑がない寂しさも残っている' in result.artifact.reception
    assert '机の上が広くなってうれしかった' in result.artifact.reception
    assert result.artifact.reception.endswith(nominal + 'を小さくせずに受け止めています。')


@pytest.mark.parametrize('support', [False, True])
@pytest.mark.parametrize('complexity', ['multi', 'long_arc'])
def test_mixed_unfinished_selection_keeps_all_source_duties_across_existing_adapters(support, complexity):
    import emlis_ai_grounded_observation_plan as gp
    prepared = prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO + 'まだ配置は見つかっていない。', 'お茶を飲んだ。'))
    plan = build_updated_grounded_plan(prepared)
    rp = plan.response_plan
    reception = gp.build_grounded_human_reception_plan(required=True,
        human_follow_target_ids=rp.human_follow_target_ids, primary_nucleus_ids=rp.primary_nucleus_ids,
        supporting_nucleus_ids=rp.supporting_nucleus_ids, required_nucleus_ids=rp.required_nucleus_ids,
        fact_boundary_nucleus_ids=rp.fact_boundary_nucleus_ids, nuclei=plan.nuclei, relations=plan.relations,
        safety_kind=plan.safety_policy.safety_kind, material_quality='grounded', semantic_complexity=complexity,
        include_relation_support=support, final_source_fidelity=True)
    assert reception.moves == rp.human_reception_plan.moves
    assert reception.depth_policy.selected_move_count == reception.depth_policy.min_realized_moves == 3


@pytest.mark.parametrize('mutation', ['actor', 'time', 'polarity', 'modality', 'retention', 'scope', 'fragment', 'required_relation', 'duplicate'])
def test_mixed_unfinished_fact_requires_one_independent_current_source_witness(mutation):
    import emlis_ai_grounded_observation_plan as gp
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO + 'まだ配置は見つかっていない。')))
    unfinished, = gp._source_action_change_contrast_unfinished(plan.nuclei, plan.relations)
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == unfinished)
    nuclei, relations = plan.nuclei, plan.relations
    if mutation in {'actor', 'time', 'polarity', 'modality'}:
        change = {'actor': {'actor': 'other_person'}, 'time': {'time_scope': 'past'},
                  'polarity': {'polarity': 'positive'}, 'modality': {'modality': 'uncertain'}}[mutation]
        altered = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame, **change))
    elif mutation == 'retention':
        altered = replace(nucleus, retention='should')
    elif mutation == 'scope':
        altered = replace(nucleus, allowed_claim_scope='explicit_supplemental_answer')
    elif mutation == 'fragment':
        altered = replace(nucleus, semantic_frame=replace(nucleus.semantic_frame,
            attribute_codes=(*nucleus.semantic_frame.attribute_codes, 'source_fragment_start:1')))
    elif mutation == 'duplicate':
        nuclei = (*nuclei, replace(nucleus, nucleus_id='duplicate_unfinished'))
        altered = nucleus
    else:
        relations = (*relations, replace(relations[0], relation_id='unfinished_required',
            type='uncertain_connection', retention='required', from_nucleus_id=unfinished))
        altered = nucleus
    nuclei = tuple(altered if n == nucleus else n for n in nuclei)
    assert not gp._source_action_change_contrast_unfinished(nuclei, relations)


@pytest.mark.parametrize('q3', [False, True])
def test_mixed_unfinished_whole_claim_partition_rejects_partial_or_cross_duty_consumption(q3):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine import emlis_stage1_response as owner
    prepared = prepare_emlis_meaning((begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + 'まだ配置は見つかっていない。'))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    rows = projection.selected_reception.decisions
    assert len(rows) == 3 and len({r.projected_claim_ref for r in rows}) == 1
    complete = rows[0].subjective_proposition.target_contribution_refs
    assert sum(len(r.selected_contribution_refs) for r in rows) == len(complete)
    assert {c for r in rows for c in r.selected_contribution_refs} == set(complete)
    assert owner._partition_shared_reception_move_contributions(rows, plan.response_plan.human_reception_plan, projection.binding) == list(rows)
    for index, selected in ((0, complete), (1, rows[2].selected_contribution_refs), (2, ())):
        altered = hr.identify_selected_subjective_reception_decision(replace(rows[index], decision_ref='', selected_contribution_refs=selected))
        changed = tuple(altered if i == index else row for i, row in enumerate(rows))
        with pytest.raises(owner.CMEEStage1ContractError):
            owner._partition_shared_reception_move_contributions(changed, plan.response_plan.human_reception_plan, projection.binding)


@pytest.mark.parametrize('ending', ['まだ配置は見つかっていない。', 'まだ配置は見つかっていません。'])
def test_mixed_unfinished_inverse_reads_complete_fact_without_author_replay(ending):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO + ending))
    plan = build_updated_grounded_plan(prepared)
    output = realize_emlis_thread_body(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = output.artifact.reception
    def passes(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=output.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    source = ending[:-1]
    for changed in ('弟が' + source, '以前は' + source, 'そのため、' + source,
                    'まだ配置は見つかっていなかった', '配置は見つかった', '配置を探している',
                    '「' + source + '」', ''):
        assert not passes(follow.replace(source, changed)), changed


@pytest.mark.parametrize('recovery_stage', ['full', 'integrated', 'hedged'])
@pytest.mark.parametrize('separate_material', [False, True])
def test_mixed_unfinished_observation_does_not_name_the_fact_as_a_future_action(recovery_stage, separate_material):
    prepared = prepare_emlis_meaning(begin(ACTION_CHANGE_CONTRAST_MEMO + 'まだ配置は見つかっていない。', '明日、棚を動かす。'))
    original = build_updated_grounded_plan(prepared)
    plan = replace(original, input_profile=replace(original.input_profile, material_quality='limited_grounding'))
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage=recovery_stage)
    ni, ri = {n.nucleus_id: n for n in plan.nuclei}, {r.relation_id: r for r in plan.relations}
    bindings = [line.binding for line in sentence.lines if line.binding.line_role == 'limited_scope']
    if separate_material:
        bindings = [replace(binding, relation_ids=(), functional_atom_ids=(*binding.functional_atom_ids, 'limited_scope:additional_material')) for binding in bindings]
    texts = [surface._render_final_stage1_limited_scope(binding, ni, ri, resolver) for binding in bindings]
    text = ' '.join(texts)
    fact_sentence, = (part for part in text.split('。') if 'まだ配置は見つかっていない' in part)
    assert '明日、棚を動かす' not in fact_sentence and 'これからの行動' not in fact_sentence
    assert '明日、棚を動かす' in text and 'これからの行動' in text


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('unfinished', ['', 'まだ配置は見つかっていない。', 'まだ配置は見つかっていません。'])
def test_completed_relation_attention_governs_one_object_in_actual_reception(q3, unfinished):
    request = (begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + unfinished)
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request))
    output = MeaningExperienceEngine().generate(request)
    assert output.artifact, output.reason_codes
    follow = output.artifact.reception
    clauses = follow.rstrip('。').split('。')
    moves = plan.response_plan.human_reception_plan.moves
    assert len(clauses) == len(moves) == (3 if unfinished else 2)
    assert '窓辺の鉢を棚へ移したことが机の上が広くなってうれしかったことを支えていること' in clauses[0]
    if unfinished:
        assert clauses[1] == '机の上が広くなってうれしかった一方で、いつも見ていた葉が遠くなり、手元に緑がない寂しさも残っていることを見過ごさず、小さくせずに受け止めています'
    else:
        assert '机の上が広くなってうれしかったことといつも見ていた葉が遠くなり、手元に緑がない寂しさも残っていること' in clauses[1]
        assert '違い' in clauses[1]
    assert clauses[0].endswith('を見過ごさず、大切に思っています')
    assert '目が留まり、それを' not in follow
    for move, clause in zip(moves, clauses):
        if move.move_role == 'attention':
            assert clause.count('を見過ごさず、') == 1 and 'それを' not in clause
        else:
            assert '見過ごさず' not in clause
    if unfinished:
        nominal = unfinished[:-1] + ('という言葉' if unfinished.endswith('ません。') else 'こと')
        assert clauses[-1] == nominal + 'を小さくせずに受け止めています'


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('source_attention_word', [False, True])
def test_completed_relation_attention_inverse_rejects_changed_grammar_without_author_replay(q3, source_attention_word):
    from types import SimpleNamespace
    from unittest.mock import patch
    memo = ACTION_CHANGE_CONTRAST_MEMO
    if source_attention_word:
        memo = memo.replace('窓辺の鉢', '見過ごしていた窓辺の鉢')
    prepared = prepare_emlis_meaning((begin if q3 else initial)(memo + 'まだ配置は見つかっていない。'))
    plan = build_updated_grounded_plan(prepared)
    output = realize_emlis_thread_body(prepared)
    assert output.artifact, output.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = output.artifact.reception
    def passes(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=output.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    clauses = follow.rstrip('。').split('。')
    for index in (0, 1):
        for old, new in [('を見過ごさず、', 'を'), ('を見過ごさず、', 'を見過ごして、'),
                         ('を見過ごさず、', 'に見過ごさず、'), ('を見過ごさず、', 'を見過ごさず、それを'),
                         ('ています', 'ていません')]:
            changed = list(clauses)
            changed[index] = changed[index].replace(old, new)
            assert changed[index] != clauses[index]
            assert not passes('。'.join(changed) + '。'), (index, old, new)
    for old, new in [('を支えていること', 'を支えていないこと'), ('一方で、', 'ので、'),
                     ('寂しさも残っている', '寂しさも残っていた'), ('うれしかった', 'うれしくなかった'),
                     ('大切に思っています', '小さくせずに受け止めています'),
                     ('小さくせずに受け止めています', '大切に思っています'),
                     ('窓辺の鉢を棚へ移した', '弟が窓辺の鉢を棚へ移した')]:
        assert not passes(follow.replace(old, new)), (old, new)


@pytest.mark.parametrize('q3', [False, True])
def test_finite_contrast_inverse_binds_complete_ordered_objects_and_left_edge(q3):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning((begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + 'まだ配置は見つかっていない。'))
    plan = build_updated_grounded_plan(prepared)
    output = realize_emlis_thread_body(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    clauses = output.artifact.reception.rstrip('。').split('。')
    left = '机の上が広くなってうれしかった'
    right = 'いつも見ていた葉が遠くなり、手元に緑がない寂しさも残っていること'
    tail = 'を見過ごさず、小さくせずに受け止めています'
    assert clauses[1] == left + '一方で、' + right + tail
    def passes(middle):
        changed = '。'.join((clauses[0], middle, clauses[2])) + '。'
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=output.artifact.text.replace(output.artifact.reception, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(clauses[1])
    for changed in (
        *(prefix + clauses[1] for prefix in ('弟が', '以前は', '今も、', 'そのため、')),
        *(left + link + right + tail for link in ('ので、', 'そして、', 'ことと', '一方で、さらに、')),
        right[:-2] + '一方で、' + left + 'こと' + tail,
        right + tail, left + '一方で、' + tail,
        left + 'こと一方で、' + right + tail,
        left + '一方で、' + right + right + tail,
        left + '一方で、それ' + tail,
        left + '一方で、' + right.replace('、', '') + tail,
        left + '一方で、' + right + 'との違い' + tail,
    ):
        assert changed != clauses[1] and not passes(changed), changed


NOMINAL_COGNITION_FEELING = '課題を終えるように急がなくても、もう一度話せると思えたことがうれしい'


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('memo', [NOMINAL_COGNITION_FEELING,
    '片付けが終わった。背伸びをしなくても、少しずつ取り組めると思えたことが嬉しい'])
def test_nominal_cognition_feeling_keeps_background_and_potential_as_one_response_object(q3, memo):
    from emlis_ai_grounded_observation_plan import is_grounded_positive_feeling
    prepared = prepare_emlis_meaning((begin if q3 else initial)(memo + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    positives = [n for n in plan.nuclei if is_grounded_positive_feeling(n)]
    assert len(positives) == 1
    feeling = positives[0]
    host = memo.split('。')[-1]
    assert resolver.resolve(feeling.source_span_ids[0]).raw_text == host
    assert feeling.source_fields == ('memo',) and feeling.retention == 'required'
    assert 'operator:negation' in feeling.semantic_frame.attribute_codes
    assert 'operator:performed_action' not in feeling.semantic_frame.attribute_codes
    selected = project_thread_meaning(prepared, plan).selected_reception
    duties = plan.response_plan.human_reception_plan.moves
    assert {m.reception_act for m in duties} == {'honor_concrete_effort', 'recognize_lived_change'}
    assert all(not m.support_nucleus_ids for m in duties)
    assert all(r.type == 'uncertain_connection' and r.retention != 'required'
               for r in plan.relations if feeling.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id))
    consumed = [ref for d in selected.decisions for ref in d.selected_contribution_refs]
    assert len(consumed) == len(set(consumed))
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    assert host + 'という気持ちを受け止めています。' in out.artifact.reception
    assert '机を拭いたことを見過ごさず、大切に受け止めています。' in out.artifact.reception
    assert 'を背景に' not in out.artifact.reception and 'を支えている' not in out.artifact.reception


@pytest.mark.parametrize('memo', [
    '弟は' + NOMINAL_COGNITION_FEELING,
    '友人によると、' + NOMINAL_COGNITION_FEELING,
    '友人の感想です。' + NOMINAL_COGNITION_FEELING,
    '友人はこう言った。' + NOMINAL_COGNITION_FEELING,
    '同僚の記録です。' + NOMINAL_COGNITION_FEELING,
    '友人の気持ちです。' + NOMINAL_COGNITION_FEELING,
    '「' + NOMINAL_COGNITION_FEELING + '」',
    '「' + NOMINAL_COGNITION_FEELING,
    NOMINAL_COGNITION_FEELING + 'と友人は言った',
    NOMINAL_COGNITION_FEELING + 'とは限らない',
    NOMINAL_COGNITION_FEELING + 'わけではない',
    NOMINAL_COGNITION_FEELING.replace('うれしい', 'うれしくない'),
    NOMINAL_COGNITION_FEELING.replace('うれしい', 'うれしいかもしれない'),
    NOMINAL_COGNITION_FEELING.replace('うれしい', 'うれしかったら'),
    NOMINAL_COGNITION_FEELING + '？',
    '明日は' + NOMINAL_COGNITION_FEELING,
    NOMINAL_COGNITION_FEELING.replace('もう一度話せる', '弟がもう一度話せる'),
])
def test_nominal_cognition_scope_does_not_promote_foreign_report_or_nonaffirmative_host(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(initial(memo + '。')))
    assert not any('lexical:source_nominal_cognition_feeling' in n.semantic_frame.attribute_codes
                   for n in plan.nuclei)


@pytest.mark.parametrize('q3', [False, True])
def test_nominal_cognition_inverse_requires_whole_feeling_object_without_author_replay(q3):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning((begin if q3 else initial)(NOMINAL_COGNITION_FEELING + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = out.artifact.reception
    def passes(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=out.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    for old, new in [
        ('課題を終えるように急がなくても、', ''),
        ('もう一度話せると思えたことが', ''),
        ('話せると思えた', '話した'),
        ('うれしい', 'うれしくない'),
        ('という気持ち', 'という変化'),
        ('という気持ち', 'という弟の気持ち'),
        ('課題を終える', '弟が課題を終える'),
        ('受け止めています', '受け止めていません'),
        (NOMINAL_COGNITION_FEELING + 'という気持ち', 'その気持ち'),
    ]:
        changed = follow.replace(old, new)
        assert changed != follow and not passes(changed), (old, new)


RECEIVED_PAST_FEELING = '連絡できなかったけれど、訪ねたときに急かさず待ってもらえて安心した'


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('past', [RECEIVED_PAST_FEELING,
    '話したときに否定せず受け入れてくれて嬉しかった',
    '私は話を聞いてもらえて少し落ち着いた'])
def test_received_past_feeling_and_current_cognition_keep_independent_duties(q3, past):
    from emlis_ai_grounded_observation_plan import is_grounded_positive_feeling
    prepared = prepare_emlis_meaning((begin if q3 else initial)(
        past + '。' + NOMINAL_COGNITION_FEELING + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    feelings = [n for n in plan.nuclei if is_grounded_positive_feeling(n)]
    assert len(feelings) == 2
    assert [resolver.resolve(n.source_span_ids[0]).raw_text for n in feelings] == [past, NOMINAL_COGNITION_FEELING]
    assert [n.semantic_frame.time_scope for n in feelings] == ['past', 'current_input']
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.reception_act for m in moves] == ['recognize_lived_change', 'recognize_lived_change', 'honor_concrete_effort']
    assert all(not m.support_nucleus_ids for m in moves)
    assert [m.target_nucleus_ids for m in moves[:2]] == [(n.nucleus_id,) for n in feelings]
    selected = project_thread_meaning(prepared, plan).selected_reception
    consumed = [ref for d in selected.decisions for ref in d.selected_contribution_refs]
    assert len(consumed) == len(set(consumed)) and all(d.selected_contribution_refs for d in selected.decisions)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    assert past + 'という気持ちを見過ごさず、受け止めています。' in out.artifact.reception
    assert NOMINAL_COGNITION_FEELING + 'という気持ちを受け止めています。' in out.artifact.reception
    assert '机を拭いたことを大切に思っています。' in out.artifact.reception
    assert out.artifact.reception.index(past) < out.artifact.reception.index(NOMINAL_COGNITION_FEELING) < out.artifact.reception.index('机を拭いた')
    assert '一つの状態' not in out.artifact.observation
    assert 'を背景に' not in out.artifact.reception and 'を支えている' not in out.artifact.reception


@pytest.mark.parametrize('memo', [
    '弟は' + RECEIVED_PAST_FEELING,
    '友人によると、' + RECEIVED_PAST_FEELING,
    '友人の感想です。' + RECEIVED_PAST_FEELING,
    '「' + RECEIVED_PAST_FEELING + '」',
    '「' + RECEIVED_PAST_FEELING,
    RECEIVED_PAST_FEELING + 'と友人は言った',
    RECEIVED_PAST_FEELING + 'とは限らない',
    RECEIVED_PAST_FEELING + 'わけではない',
    RECEIVED_PAST_FEELING.replace('安心した', '安心しなかった'),
    RECEIVED_PAST_FEELING.replace('安心した', '安心したかもしれない'),
    RECEIVED_PAST_FEELING.replace('安心した', '安心したら'),
    RECEIVED_PAST_FEELING.replace('安心した', '安心している'),
    RECEIVED_PAST_FEELING + '？',
    '明日は' + RECEIVED_PAST_FEELING,
])
def test_received_past_feeling_does_not_promote_foreign_report_or_nonaffirmative_host(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(initial(memo + '。')))
    assert not any('lexical:source_received_past_feeling' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('q3', [False, True])
def test_received_past_pair_inverse_requires_each_complete_object_without_author_replay(q3):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning((begin if q3 else initial)(
        RECEIVED_PAST_FEELING + '。' + NOMINAL_COGNITION_FEELING + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    follow = out.artifact.reception
    def passes(changed):
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=changed)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=out.artifact.text.replace(follow, changed).encode(),
                plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    for old, new in [
        ('連絡できなかったけれど、', ''),
        ('急かさず', '急かして'),
        ('安心した', '安心している'),
        ('安心した', '安心しなかった'),
        (RECEIVED_PAST_FEELING + 'という気持ち', 'その気持ち'),
        (RECEIVED_PAST_FEELING, '弟が' + RECEIVED_PAST_FEELING),
        ('話せると思えた', '話した'),
        (RECEIVED_PAST_FEELING + 'という気持ちを見過ごさず、受け止めています。', ''),
        (NOMINAL_COGNITION_FEELING + 'という気持ちを受け止めています。', ''),
        ('机を拭いたことを大切に思っています。', ''),
    ]:
        changed = follow.replace(old, new)
        assert changed != follow and not passes(changed), (old, new)


@pytest.mark.parametrize('action', ['', '机を拭いた。'])
def test_received_past_single_observation_does_not_promote_time_to_now(action):
    out = realize_emlis_thread_body(prepare_emlis_meaning(initial(RECEIVED_PAST_FEELING + '。', action)))
    assert out.artifact, out.reason_codes
    assert RECEIVED_PAST_FEELING in out.artifact.observation
    assert '今は' not in out.artifact.observation


@pytest.mark.parametrize('action', ['', '机を拭いた。'])
def test_received_past_pair_direct_projection_consumes_each_duty_once(action):
    from test_cmee_final_stage1_generic_move_projection import _full_surface_artifacts
    result = _full_surface_artifacts({'case_id': 'synthetic-independent-positive-pair', 'input': {
        'thought_text': RECEIVED_PAST_FEELING + '。' + NOMINAL_COGNITION_FEELING + '。',
        'action_text': action, 'categories': ['仕事'], 'emotions': [{'type': '不安', 'strength': 'medium'}]}})
    assert result.inverse.passed and result.gate.passed
    assert len(result.selected_subjective_input.decisions) == (3 if action else 2)
    refs = [ref for d in result.selected_subjective_input.decisions for ref in d.selected_contribution_refs]
    assert len(refs) == len(set(refs))
    assert RECEIVED_PAST_FEELING + 'という気持ち' in result.surface.text
    assert NOMINAL_COGNITION_FEELING + 'という気持ち' in result.surface.text


DENIED_RESOLUTION_COGNITION = '不安が消えたわけではないけれど、別の方法もありそうだと思えた'


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('clause', [DENIED_RESOLUTION_COGNITION,
    '緊張がなくなったわけではありませんが、他の手順もありそうだと思いました',
    '痛みが取れたわけじゃないけど、休む以外の過ごし方もありそうだと思えました'])
def test_denied_resolution_keeps_each_host_and_prior_context(q3, clause):
    import re
    request = (begin if q3 else initial)(
        '昨日は会議だった。' + clause + '。', '机を拭いた。')
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    target = next(n for n in plan.nuclei if 'lexical:source_denied_resolution' in n.semantic_frame.attribute_codes)
    frame = target.semantic_frame
    assert (frame.predicate_kind, frame.modality, frame.polarity, frame.time_scope) == ('change', 'fact', 'mixed', 'current_input')
    codes = frame.attribute_codes
    assert 'operator:positive_change' not in codes and 'operator:performed_action' not in codes
    assert any(c.endswith(':under_present_denial') for c in codes)
    assert any(c.endswith(':under_past_cognition') for c in codes)
    assert prepared.thread.resolver().resolve(target.source_span_ids[0]).raw_text == clause
    moves = plan.response_plan.human_reception_plan.moves
    assert moves[0].target_nucleus_ids == (target.nucleus_id,)
    assert all(not m.support_nucleus_ids for m in moves)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(request)
    actual = engine.generate(replace(request, emlis_thread=replace(
        request.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert actual.artifact, actual.reason_codes
    assert actual.question is None and actual.body_state == 'FINAL'
    finite = re.sub(r'思いました$', '思った', clause)
    finite = re.sub(r'思えました$', '思えた', finite)
    for artifact in (out.artifact, actual.artifact):
        assert finite + 'のですね。' in artifact.observation
        assert '昨日は会議だった' in artifact.observation
        assert clause + 'という言葉' in artifact.reception
        assert artifact.reception.index(clause) < artifact.reception.index('机を拭いた')
        assert '実際の行動' not in artifact.reception and 'という変化' not in artifact.observation
        assert '思いましたのですね' not in artifact.observation
        assert '思えましたのですね' not in artifact.observation


@pytest.mark.parametrize('memo', [
    '弟は' + DENIED_RESOLUTION_COGNITION,
    '友人によると、' + DENIED_RESOLUTION_COGNITION,
    '友人の感想です。' + DENIED_RESOLUTION_COGNITION,
    '友人の説明です。' + DENIED_RESOLUTION_COGNITION,
    '弟が説明した。' + DENIED_RESOLUTION_COGNITION,
    '昨日の自分の気持ちです。' + DENIED_RESOLUTION_COGNITION,
    '同僚が答えました。' + DENIED_RESOLUTION_COGNITION,
    '以前の自分の感想でした。' + DENIED_RESOLUTION_COGNITION,
    '父が自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '父の要望を伝えた。' + DENIED_RESOLUTION_COGNITION,
    '私は次のように話した。' + DENIED_RESOLUTION_COGNITION,
    '自分の意見をこう伝えた。' + DENIED_RESOLUTION_COGNITION,
    '兄こそ自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '兄自身、自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '兄本人、自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '兄まで自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '兄だって自分の意見を述べた。' + DENIED_RESOLUTION_COGNITION,
    '「' + DENIED_RESOLUTION_COGNITION + '」',
    '「' + DENIED_RESOLUTION_COGNITION,
    DENIED_RESOLUTION_COGNITION + 'と弟が言った',
    DENIED_RESOLUTION_COGNITION.replace('わけではない', 'わけではなかった'),
    DENIED_RESOLUTION_COGNITION.replace('消えた', '消えない'),
    DENIED_RESOLUTION_COGNITION.replace('わけではない', 'わけではないかもしれない'),
    DENIED_RESOLUTION_COGNITION.replace('思えた', '思えなかった'),
    DENIED_RESOLUTION_COGNITION.replace('思えた', '思えれば'),
    DENIED_RESOLUTION_COGNITION.replace('ありそうだと思えた', 'あった'),
    DENIED_RESOLUTION_COGNITION + '？',
    '明日は' + DENIED_RESOLUTION_COGNITION,
])
def test_denied_resolution_does_not_borrow_foreign_or_nonfinite_hosts(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(initial(memo + '。')))
    assert not any('lexical:source_denied_resolution' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('q3', [False, True])
def test_denied_resolution_inverse_retains_both_scopes_without_author_replay(q3):
    from types import SimpleNamespace
    from unittest.mock import patch
    prepared = prepare_emlis_meaning((begin if q3 else initial)(
        '昨日は会議だった。' + DENIED_RESOLUTION_COGNITION + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = surface.build_grounded_sentence_plan(plan, resolver)
    def passes(observation, reception):
        body = out.artifact.text.replace(out.artifact.observation, observation).replace(out.artifact.reception, reception)
        with patch('emlis_ai_grounded_observation_gate.replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=reception)), patch(
            'emlis_ai_grounded_human_reception._author_source_grounded_reception_clauses', side_effect=AssertionError('no author replay')):
            return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
                sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert passes(out.artifact.observation, out.artifact.reception)
    for old, new in [
        ('わけではない', ''), ('わけではない', 'わけではなかった'),
        ('消えた', '消えない'), ('ありそうだと思えた', 'あった'),
        ('思えた', '思えなかった'), ('不安が', '弟の不安が'),
        ('不安が消えたわけではないけれど、', ''),
        ('別の方法もありそうだと思えた', ''),
    ]:
        observation = out.artifact.observation.replace(old, new)
        reception = out.artifact.reception.replace(old, new)
        assert observation != out.artifact.observation and reception != out.artifact.reception
        assert not passes(observation, out.artifact.reception), (old, new, 'observation')
        assert not passes(out.artifact.observation, reception), (old, new, 'reception')
    assert not passes(out.artifact.observation, out.artifact.reception + 'もう大丈夫です。')


@pytest.mark.parametrize('action', ['', '机を拭いた。'])
def test_denied_resolution_direct_projection_preserves_context_and_unique_duties(action):
    from test_cmee_final_stage1_generic_move_projection import _full_surface_artifacts
    result = _full_surface_artifacts({'case_id': 'synthetic-scoped-denial', 'input': {
        'thought_text': '昨日は会議だった。' + DENIED_RESOLUTION_COGNITION + '。',
        'action_text': action, 'categories': ['仕事'], 'emotions': [{'type': '不安', 'strength': 'medium'}]}})
    assert result.inverse.passed and result.gate.passed
    assert DENIED_RESOLUTION_COGNITION + 'という言葉' in result.surface.text
    refs = [ref for d in result.selected_subjective_input.decisions for ref in d.selected_contribution_refs]
    assert len(refs) == len(set(refs))


@pytest.mark.parametrize('scope_case', ['no_resolver', 'missing_scope', 'forged_scope', 'unbound_source'])
def test_denied_resolution_outer_requires_complete_source_scope_proof(scope_case):
    from cocolon_meaning_experience_engine import emlis_v1a
    prepared = prepare_emlis_meaning(initial(DENIED_RESOLUTION_COGNITION + '。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    target = next(n for n in plan.nuclei if 'lexical:source_denied_resolution' in n.semantic_frame.attribute_codes)
    kwargs = {'stage1_response_schema_version': emlis_v1a.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
              'resolver': resolver}
    check = emlis_v1a._cmee_assert_current_first_person_scope_supported
    check(DENIED_RESOLUTION_COGNITION + '。', plan, **kwargs)
    value = DENIED_RESOLUTION_COGNITION + '。'
    if scope_case == 'no_resolver':
        kwargs['resolver'] = None
    elif scope_case in {'missing_scope', 'forged_scope'}:
        codes = tuple(c for c in target.semantic_frame.attribute_codes
                      if not c.startswith('source_clause_scope:assertion:'))
        if scope_case == 'forged_scope':
            codes += ('source_clause_scope:assertion:999:1000:under_present_denial',)
        changed = replace(target, semantic_frame=replace(target.semantic_frame, attribute_codes=codes))
        plan = replace(plan, nuclei=tuple(changed if n.nucleus_id == target.nucleus_id else n for n in plan.nuclei))
    else:
        value = '不安が消えた。'
    with pytest.raises(emlis_v1a.CMEEVerticalError, match='current_experiencer_or_time_scope_unsupported'):
        check(value, plan, **kwargs)


@pytest.mark.parametrize('other_sentence', [
    '不安が消えた。',
    '弟は不安を感じている。',
    '昨日は不安だった。',
])
@pytest.mark.parametrize('before', [False, True])
def test_denied_resolution_outer_exemption_does_not_cover_other_sentences(other_sentence, before):
    from cocolon_meaning_experience_engine import emlis_v1a
    prepared = prepare_emlis_meaning(initial(DENIED_RESOLUTION_COGNITION + '。'))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    kwargs = {'stage1_response_schema_version': emlis_v1a.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
              'resolver': resolver}
    check = emlis_v1a._cmee_assert_current_first_person_scope_supported
    original = DENIED_RESOLUTION_COGNITION + '。'
    check(original, plan, **kwargs)
    value = other_sentence + original if before else original + other_sentence
    with pytest.raises(emlis_v1a.CMEEVerticalError, match='current_experiencer_or_time_scope_unsupported'):
        check(value, plan, **kwargs)


@pytest.mark.parametrize('prefix', [
    '私の要望を伝えた。', '面談では、自分の意見を述べた。', '父には自分の意見を伝えた。',
])
def test_denied_resolution_does_not_treat_completed_self_expression_as_report(prefix):
    prepared = prepare_emlis_meaning(initial(prefix + DENIED_RESOLUTION_COGNITION + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    assert any('lexical:source_denied_resolution' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    assert prefix.rstrip('。') in out.artifact.observation
    assert DENIED_RESOLUTION_COGNITION + 'という言葉' in out.artifact.reception


@pytest.mark.parametrize('action', ['', '机を拭いた。'])
def test_denied_resolution_outer_negative_reception_requires_owned_whole_source(action):
    from unittest.mock import patch
    from cocolon_meaning_experience_engine import emlis_v1a
    source_clause = '痛みが取れたわけじゃないけど、休む以外の過ごし方もありそうだと思えました'
    request = initial(source_clause + '。', action)
    engine = MeaningExperienceEngine()
    checkpoint = engine.prepare_emlis_update(request)
    check = emlis_v1a._validate_reception_semantic_compatibility
    captured = []
    def capture(source, lines, projection):
        captured.append((source, lines, projection))
        return check(source, lines, projection)
    with patch.object(emlis_v1a, '_validate_reception_semantic_compatibility', side_effect=capture):
        actual = engine.generate(replace(request, emlis_thread=replace(
            request.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint.checkpoint_id)))
    assert actual.artifact and captured, actual.reason_codes
    source, lines, projection = captured[-1]
    target = next(line for line in lines if line.binding.line_role == 'human_follow')
    for extra in ('そのつらさも受け止めています。', 'ほかの痛みも受け止めています。'):
        changed = replace(target, text=target.text + extra)
        with pytest.raises(emlis_v1a.CMEEVerticalError, match='reception_negative_meaning_promotion'):
            check(source, tuple(changed if line is target else line for line in lines), projection)


def test_denied_resolution_keeps_independent_finite_line_beside_required_relation():
    prepared = prepare_emlis_meaning(initial(
        '昨日は会議だった。でも午後は休憩だった。' + DENIED_RESOLUTION_COGNITION + '。', '机を拭いた。'))
    plan = build_updated_grounded_plan(prepared)
    assert plan.coverage_requirements.required_relation_ids
    out = realize_emlis_thread_body(prepared)
    assert out.artifact, out.reason_codes
    assert '昨日は会議だった' in out.artifact.observation and '午後は休憩だった' in out.artifact.observation
    assert DENIED_RESOLUTION_COGNITION + 'のですね。' in out.artifact.observation
    assert 'という変化' not in out.artifact.observation
