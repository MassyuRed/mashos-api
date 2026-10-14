"""Original appraisals own their objects; semantic checks are not Product Read."""
from dataclasses import replace

import pytest

from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_plan import source_owned_result_appraisal
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
from emlis_ai_grounded_sentence_surface import build_grounded_sentence_plan


def request(memo, action="植木に水をやった。"):
    req = initial(memo, action)
    return replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot="Q3_FREE"))


@pytest.mark.parametrize("memo,polarity,time", [
    ("資料を分類できて満足した。", "positive", "past"),
    ("予定を決められて納得しました。", "positive", "past"),
    ("文章を直せたことに満足している。", "positive", "present"),
    ("案を選んで納得した。", "positive", "past"),
    ("意見をまとめて満足しなかった。", "negative", "past"),
    ("資料を分類したことにまだ納得していない。", "negative", "present"),
    ("昨日は私は資料を分類できてとても満足しました。", "positive", "past"),
    ("資料を分類したことにはあまり満足しませんでした。", "negative", "past"),
])
def test_appraisal_keeps_its_object_outer_polarity_and_time_in_actual_body(memo, polarity, time):
    req = request(memo)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    about = [r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]
    assert len(about) == 1
    index = {n.nucleus_id: n for n in plan.nuclei}
    event, feeling = (index[nid] for nid in (about[0].from_nucleus_id, about[0].to_nucleus_id))
    assert event.kind == "event" and event.semantic_frame.modality == "fact"
    assert (feeling.kind, feeling.semantic_frame.predicate_kind, feeling.semantic_frame.modality,
            feeling.semantic_frame.polarity, feeling.semantic_frame.time_scope) == ("reaction", "feeling", "feeling", polarity, time)
    assert event.source_span_ids == feeling.source_span_ids
    assert plan.response_plan.human_follow_target_ids == (feeling.nucleus_id,)
    projection = project_thread_meaning(prepared, plan)
    assert any(str(row.relation_kind).endswith("ABOUT_TARGET") for row in projection.premeaning.source_relation_rows)
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert "植木" in outcome.artifact.observation
    assert "植木" not in outcome.artifact.reception
    assert "状態に表れた変化" not in outcome.artifact.reception
    assert "努力" not in outcome.artifact.reception
    assert "満足" in outcome.artifact.reception or "納得" in outcome.artifact.reception


@pytest.mark.parametrize("memo", [
    "同僚は資料を分類できて満足したと言った。",
    "同僚が資料を分類できて満足した。",
    "同僚が話した。資料を分類できて満足した。",
    "『資料を分類できて満足した』と聞いた。",
    "資料を分類できたら満足できそう。",
    "資料を分類できて満足したかもしれない。",
    "資料を分類できて満足した？",
    "資料を分類できて満足したら。",
    "資料を分類できて満足し",
    "満足度調査の項目を分類した。",
    "資料を分類しなくて満足した。",
    "資料を分類しないで満足した。",
    "資料を分類した。嬉しかったのは友人からの返事だ。",
    "資料を準備中で満足した。",
    "資料を分類する予定で満足した。",
    "資料を分類したつもりで満足した。",
    "山田さんは仕事を終えた。資料を分類できて満足した。",
    "ともこは仕事を終えた。資料を分類できて満足した。",
    "同僚たちが仕事を終えた。資料を分類できて満足した。",
])
def test_nonasserted_foreign_nominal_or_unfinished_text_does_not_acquire_appraisal_proof(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request(memo)))
    assert not any(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations)


def test_changing_an_independent_action_does_not_replace_the_appraisal():
    bodies = [MeaningExperienceEngine().generate(request("資料を分類できて満足した。", action)).artifact
              for action in ("植木に水をやった。", "机を拭いた。", "")]
    assert all(bodies)
    assert len({body.reception for body in bodies}) == 1
    assert bodies[0].observation != bodies[1].observation


def test_body_reader_rejects_swapped_object_polarity_and_invented_answer_time():
    req = request("資料を分類できて満足した。")
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage="full")
    body = MeaningExperienceEngine().generate(req).artifact.text
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    for changed in (body.replace("満足した", "満足しなかった"),
                    body.replace("資料を分類でき", "植木に水をやっ"),
                    body.replace("出来事に対する評価は", "回答した時点の評価は"),
                    body.replace("資料を分類できたという", "資料を分類できなかったという")):
        assert changed != body
        assert not valid(changed)


@pytest.mark.parametrize('memo,kind,evaluation,polarity,time,still,degree', [
    ('案を考えて満足した。', 'thinking', 'satisfaction', 'positive', 'past', False, 'unmarked'),
    ('机を拭いて満足した。', 'manual_action', 'satisfaction', 'positive', 'past', False, 'unmarked'),
    ('案を考えたことに少し満足している。', 'thinking', 'satisfaction', 'positive', 'present', False, 'slight'),
    ('意見をまとめて満足しなかった。', 'unspecified_action', 'satisfaction', 'negative', 'past', False, 'unmarked'),
    ('資料を分類したことにまだ納得していない。', 'unspecified_action', 'acceptance', 'negative', 'present', True, 'unmarked'),
    ('資料を分類したことにあまり満足しなかった。', 'unspecified_action', 'satisfaction', 'negative', 'past', False, 'not_much'),
])
def test_experience_is_selected_before_authoring_and_survives_in_body(memo,kind,evaluation,polarity,time,still,degree):
    from cocolon_meaning_experience_engine.contracts import EmlisEvaluatedExperienceAppraisalContent
    req = request(memo)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared,plan)
    decision = projection.selected_reception.decisions[0]
    content = decision.subjective_proposition.appraisal_content
    assert type(content) is EmlisEvaluatedExperienceAppraisalContent
    assert (content.target_kind,content.evaluation_kind,content.polarity,content.evaluation_time,
            content.continuing,content.degree) == (kind,evaluation,polarity,time,still,degree)
    assert {content.event_binding_ref,content.evaluation_binding_ref} == set(content.appraised_bindings)
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None,outcome.reason_codes
    reception = outcome.artifact.reception
    if kind == 'thinking': assert 'という内側の営み' in reception
    if kind == 'manual_action': assert '実際の作業' in reception
    if still: assert 'まだご自身が納得していない' in reception and '今も' not in reception
    if degree == 'slight': assert '少し満足を感じている' in reception
    if degree == 'not_much': assert 'あまり満足を感じなかった' in reception
    assert 'ご自身にも' not in reception and '状態に表れた変化' not in reception
    assert '感じられなかった' not in reception


@pytest.mark.parametrize('changes', [dict(target_kind='thinking'),dict(evaluation_kind='acceptance'),
    dict(polarity='negative'),dict(evaluation_time='present'),dict(continuing=True),
    dict(explicit_ability=False),dict(degree='slight'),dict(schema_version='legacy'),
    dict(protected_bindings=('forged',))])
def test_reidentified_selected_experience_cannot_change_source_meaning(changes):
    import emlis_ai_grounded_human_reception as hr
    req=request('資料を分類できて満足した。')
    prepared=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(prepared)
    selected=project_thread_meaning(prepared,plan).selected_reception
    decision=selected.decisions[0]
    if 'protected_bindings' in changes:
        changes = dict(protected_bindings=(decision.subjective_proposition.appraisal_content.event_binding_ref,))
    proposition=replace(decision.subjective_proposition,
        appraisal_content=replace(decision.subjective_proposition.appraisal_content,**changes))
    changed=hr.identify_selected_subjective_reception_decision(replace(decision,subjective_proposition=proposition))
    forged=hr.identify_selected_subjective_reception_input(replace(selected,decisions=(changed,)))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.validate_selected_subjective_reception_input(forged,plan.response_plan.human_reception_plan,plan,prepared.thread.resolver())


@pytest.mark.parametrize('action',['彼は植木に水をやった。','今日は彼が植木に水をやった。','彼は外出した。植木に水をやった。','寂しかった。'])
def test_independent_foreign_or_non_action_does_not_acquire_component_admission(action):
    prepared=prepare_emlis_meaning(request('資料を分類できて満足した。',action))
    projection=project_thread_meaning(prepared,build_updated_grounded_plan(prepared))
    assert projection.structure.schema_version != '1.2'


@pytest.mark.parametrize('memo',[
    '資料を分類してもらって満足した。','資料を分類させられて満足した。',
    '資料を分類する予定だったことに満足した。','資料を分類するつもりだったことに満足した。',
    '資料を分類したことにその時は納得していない。'])
def test_unperformed_or_unbound_time_does_not_acquire_original_appraisal(memo):
    plan=build_updated_grounded_plan(prepare_emlis_meaning(request(memo)))
    assert not any(source_owned_result_appraisal(r,plan.nuclei) for r in plan.relations)


def test_all_independent_required_components_owned_by_one_selected_reading():
    from cocolon_meaning_experience_engine import contracts as c
    prepared=prepare_emlis_meaning(request('資料を分類できて満足した。'))
    projection=project_thread_meaning(prepared,build_updated_grounded_plan(prepared))
    structure=projection.structure
    selected=structure.meaning_decision_outcome
    assert type(selected) is c.SelectedEmlisProvisionalReading and selected.schema_version=='1.2'
    assert len(structure.requirement_bundles)==2
    candidate=next(row for row in structure.candidate_records if row.candidate_id==selected.selected_candidate_ref)
    assert set(candidate.requirement_bundle_refs)=={row.bundle_id for row in structure.requirement_bundles}
    assert selected.primary_reading_focus_ref==candidate.candidate_id and selected.supporting_facet_refs==()
    assert all(edge.relation=='evaluation_about_event' for edge in projection.graph.edges)

# Reuse the actual Q2/Q3 migration fixture; no live user data or database.
from test_emlis_q3_application import qdb, qcase

@pytest.mark.parametrize('memo', ['資料を分類できて満足した。','資料を分類したことにまだ納得していない。'])
def test_selected_appraisal_saved_body_is_read_without_regeneration(qcase,qdb,memo):
    from test_emlis_q2_application import run
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user,parent,service=qcase
    qdb.query("update public.profiles set subscription_tier='free' where id=$1",[user])
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1',[parent,memo,'植木に水をやった。'])
    dto=run(service.start(user,parent))
    assert dto['current_observation'] is not None,dto
    snapshot=run(service.store.read(user,input_id=parent))
    current=snapshot['thread']['last_observation_event_id']
    observation=next(event for event in snapshot['events'] if event['id']==current)
    assert observation['kind']=='OBSERVATION'
    assert dto['current_observation']['text']==observation['payload']['text']
    assert dto['current_observation']['event_id']==current
    class NoAuthor:
        def __getattr__(self,name): raise AssertionError('saved read attempted generation: '+name)
    restarted=EmlisThreadService(engine=NoAuthor(),runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user,parent))==dto
    assert run(restarted.start(user,parent))==dto

@pytest.mark.parametrize('memo,action',[
    ('', '植木に水をやった。資料を分類できて満足した。'),
    ('', '資料を分類できて満足した。植木に水をやった。'),
    ('植木に水をやった。資料を分類できて満足した。',''),
    ('資料を分類できて満足した。植木に水をやった。',''),
])
def test_independent_action_order_and_field_do_not_mask_appraisal_difference(memo,action):
    outcome=MeaningExperienceEngine().generate(request(memo,action))
    assert outcome.artifact is not None,outcome.reason_codes
    assert '植木に水をやった' in outcome.artifact.observation
    assert '資料を分類できたというご自身での実現' in outcome.artifact.reception
    assert '満足を感じた' in outcome.artifact.reception
    appraisal_sentence=next(sentence for sentence in outcome.artifact.reception.split('。') if '満足' in sentence)
    assert '植木' not in appraisal_sentence


def test_versioned_appraisal_is_in_current_manifest_without_changing_legacy_fields():
    from dataclasses import fields
    from cocolon_meaning_experience_engine.contracts import EmlisAppraisalContent
    from cocolon_meaning_experience_engine.emlis_stage1_composition import _contract_manifest
    manifest = dict(_contract_manifest())
    assert manifest['logical_contract_count'] == 70
    assert any(dict(row)['type_name'] == 'EmlisEvaluatedExperienceAppraisalContent'
               for row in manifest['logical_contract_descriptors'])
    assert tuple(field.name for field in fields(EmlisAppraisalContent)) == (
        'dimension', 'operation', 'appraised_bindings',
        'focal_relation_ref', 'protected_bindings', 'basis_contribution_refs')
