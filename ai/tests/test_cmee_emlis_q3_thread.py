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
