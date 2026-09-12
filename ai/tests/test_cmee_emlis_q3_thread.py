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
