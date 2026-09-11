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
    assert '褒められたことへのその時の重さ' in follow
    assert '誘われたこと' in follow and fragment in follow
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
    from emlis_ai_grounded_observation_gate import _body_inverse_thread_answer_group
    from unittest.mock import patch
    r=advance(advance(begin(),'その時は重かった。'),'その時は怖かった。')
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
    r=advance(advance(begin(),'その時は重かった。'),'その時は怖かった。')
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
