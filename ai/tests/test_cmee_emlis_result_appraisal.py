"""Original appraisals own their objects; semantic checks are not Product Read."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_plan import source_owned_result_appraisal
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
from emlis_ai_grounded_sentence_surface import build_grounded_sentence_plan


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('basis', ['探しやすくなった', '見た目がすっきりした', '資料を使いやすい'])
@pytest.mark.parametrize('target,event', [('資料を分類したことに', '資料を分類した'),
    ('資料を分類できて', '資料を分類できた'), ('案を選んで', '案を選んだ')])
def test_reason_and_received_keep_both_experiences_in_limited_body(reverse, evaluation, basis, target, event):
    reason = basis + 'ので、' + target + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*( (received, reason) if reverse else (reason, received) ))
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    assert projection.meaning_plan.projection_branch == 'LIMITED'
    assert all(d.branch == 'LIMITED' and d.subjective_proposition.focal_relation_ref is None
               for d in projection.selected_reception.decisions)
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    body = outcome.artifact
    assert basis + 'という理由に目を向けています' in body.reception
    assert ('当時の満足について' if evaluation == '満足した'
            else '入力した時点での満足について') in body.reception
    assert event + 'ことへの' in body.reception
    assert evaluation + 'のですね' not in body.reception
    assert '褒められたことは、嬉しさにはつながらなかった' in body.reception
    assert '拠り所' not in body.reception
    assert basis in body.observation and '褒められた' in body.observation


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('target,event', [('資料を分類したことに', '資料を分類した'),
    ('資料を分類できて', '資料を分類できた'), ('案を選んで', '案を選んだ')])
def test_limited_reason_reader_preserves_roles_and_time_without_author(monkeypatch, reverse, evaluation, target, event):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    from emlis_ai_grounded_observation_plan import source_owned_relational_focus
    source = '探しやすくなったので、' + target + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, source) if reverse else (source, received)))
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    artifact = MeaningExperienceEngine().generate(req).artifact
    assert artifact is not None
    clause = next(part + '。' for part in artifact.reception.split('。') if 'という理由に' in part)
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if (focus := source_owned_relational_focus(m, plan)) and focus[0] == 'reasoned_result_appraisal')
    wrongs = (
        clause.replace('探しやすくなったという理由に', ''),
        clause.replace('探しやすくなった', '探しにくくなった'),
        clause.replace('探しやすくなった', '探しやすくしたかった'),
        clause.replace('探しやすくなった', '褒められた'),
        clause.replace(event + 'ことへの', '褒められたことへの'),
        clause.replace(event, '資料を分類しなかった'),
        clause.replace('満足', '納得'),
        clause.replace('満足について', '不満について'),
        clause.replace('当時の' if evaluation == '満足した' else '入力した時点での', '回答した時点では'),
        clause.replace('という理由に', 'ことの原因に'),
        clause.replace('という理由に', 'という唯一の理由に'),
        clause.replace('という理由に', 'という最も大切な理由に'),
        clause.replace('目を向けています', '成長を感じています'),
        clause.replace('という理由に目を向けています', 'のですね'),
        ('探しやすくなったことを理由に、' + event + 'ことについて、'
         + ('当時は' if evaluation == '満足した' else '入力した時点では')
         + evaluation + 'のですね。'),
    )
    def valid(body):
        return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(artifact.text)
    for wrong in wrongs:
        assert wrong != clause and not valid(artifact.text.replace(clause, wrong))
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence',
        lambda *_a, **_k: pytest.fail('independent LIMITED reader called the author'))
    assert read_source_owned_discourse(clause, move, plan, resolver, selected) is not None
    for wrong in wrongs:
        assert read_source_owned_discourse(wrong, move, plan, resolver, selected) is None


@pytest.mark.parametrize('reverse', [False, True])
def test_limited_reason_selected_ownership_cannot_drop_or_borrow_contributions(reverse):
    import emlis_ai_grounded_human_reception as hr
    source = '探しやすくなったので、資料を分類したことに満足した。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, source) if reverse else (source, received)))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    selected = project_thread_meaning(p, plan).selected_reception
    reason, = (d for d in selected.decisions if len(d.support_nucleus_ids) == 2)
    other, = (d for d in selected.decisions if d != reason)
    variants = [replace(reason, selected_contribution_refs=reason.selected_contribution_refs[:1]),
                replace(reason, selected_contribution_refs=other.selected_contribution_refs),
                replace(reason, selected_contribution_refs=(*reason.selected_contribution_refs, *other.selected_contribution_refs)),
                replace(reason, branch='NORMAL')]
    for field, value in [('subjective_mode', 'PERSONAL_APPRAISAL'), ('subjective_operator', 'VALUE_AS')]:
        variants.append(replace(reason, subjective_proposition=replace(reason.subjective_proposition, **{field: value})))
    for row in variants:
        row = hr.identify_selected_subjective_reception_decision(row)
        changed = hr.identify_selected_subjective_reception_input(replace(selected,
            decisions=tuple(row if d == reason else d for d in selected.decisions)))
        with pytest.raises(hr.GroundedHumanReceptionSurfaceError, match='MEANING_REALIZATION_CAUSAL_TRACE_GAP'):
            hr.validate_selected_subjective_reception_input(changed,
                plan.response_plan.human_reception_plan, plan, p.thread.resolver())


def test_limited_reason_removal_or_replacement_does_not_reassign_received_experience():
    engine = MeaningExperienceEngine()
    received = '褒められたのに、嬉しくなかった。'
    sources = ['探しやすくなったので、資料を分類したことに満足した。',
               '見た目がすっきりしたので、資料を分類したことに満足した。',
               '資料を分類したことに満足した。']
    bodies = [engine.generate(request(source, received)).artifact for source in sources]
    assert all(bodies)
    assert '探しやすくなったという理由に' in bodies[0].reception
    assert '見た目がすっきりしたという理由に' in bodies[1].reception
    assert '探しやすくなった' not in bodies[1].reception
    assert '理由' not in bodies[2].reception and '探しやすくなった' not in bodies[2].reception
    for body in bodies:
        assert '褒められたことは、嬉しさにはつながらなかったのですね。' in body.reception
    assert all('資料を分類したことへの当時の満足について' in b.reception for b in bodies[:2])
    assert '資料を分類したことについて、当時は満足したのですね。' in bodies[2].reception


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
    if '満足' in memo:
        assert 'ご自身の中に' in outcome.artifact.reception
        assert '満たされた感覚が' in outcome.artifact.reception
    else:
        assert 'ご自身の理解の中で' in outcome.artifact.reception
        assert '筋が通って' in outcome.artifact.reception
    assert ('経験として受け取りました' if polarity == 'positive'
            else 'ことの両方を受け取りました') in outcome.artifact.reception


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
                    body.replace("資料を分類できたこと", "資料を分類できなかったこと")):
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
    if kind == 'thinking': assert '案を考えたこと' in reception
    if kind == 'manual_action': assert '机を拭いたこと' in reception
    if still: assert 'ご自身の理解の中でまだ筋が通っていない' in reception and '今も' not in reception
    if degree == 'slight': assert '少し満たされた感覚がある' in reception
    if degree == 'not_much': assert 'あまり満たされた感覚がなかった' in reception
    assert 'ご自身にも' not in reception and '状態に表れた変化' not in reception
    assert '感じられなかった' not in reception


def test_confirmed_meanings_distinguish_fulfilment_from_personal_intelligibility():
    rows = []
    for evaluation in ('満足した', '満足しなかった', '納得した', '納得しなかった'):
        req = request('案を選んで' + evaluation + '。')
        prepared = prepare_emlis_meaning(req)
        plan = build_updated_grounded_plan(prepared)
        selected = project_thread_meaning(prepared, plan).selected_reception
        content = selected.decisions[0].subjective_proposition.appraisal_content
        body = MeaningExperienceEngine().generate(req).artifact.reception
        rows.append((content.reception_configuration, body))
    assert len({kind for kind, _ in rows}) == len({body for _, body in rows}) == 4
    for index, (_, body) in enumerate(rows):
        assert '案を選んだこと' in body
        assert ('満たされた感覚' in body) == (index < 2)
        assert ('ご自身の理解の中で筋が通って' in body) == (index >= 2)
        assert ('ことの両方を受け取りました' in body) == (index % 2 == 1)
        assert not any(word in body for word in ('目標', '基準', '成功', '成長', '正しい', 'いずれ', '追いつ'))


@pytest.mark.parametrize('evaluation', [
    '満足した', 'あまり満足しなかった', '少し満足している',
    '納得した', '納得しなかった', 'まだ納得していない',
    '少し納得した', 'とても納得している', 'あまり納得しなかった',
])
def test_source_owned_appraisal_reader_rejects_semantic_mutations_without_author(monkeypatch, evaluation):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    req = request('資料を分類したことに' + evaluation + '。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    artifact = MeaningExperienceEngine().generate(req).artifact
    assert artifact is not None
    def whole_valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert whole_valid(artifact.text)
    reception = artifact.reception
    changes = [
        reception.replace('資料を分類したこと', '資料を分類しなかったこと'),
        reception.replace('ご自身の中に', '客観的に').replace('ご自身の理解の中で', '客観的に'),
        reception.replace('当時', '回答した時点').replace('入力した時点', '回答した時点'),
        reception.replace('満たされた感覚', '筋の通った感覚') if '満足' in evaluation else
            reception.replace('筋が通って', '満たされて').replace('納得', '満足'),
    ]
    if 'まだ' in evaluation:
        changes.append(reception.replace('まだ', ''))
    if any(degree in evaluation for degree in ('少し', 'とても', 'あまり')):
        changes.append(reception.replace('少し', 'とても').replace('とても', '本当に').replace('あまり', 'まったく'))
    if 'それについて' in reception:
        changes.append(reception.replace('それについて', ''))
    if '納得' in reception:
        changes.append(reception.replace('納得した', '筋が通っていた')
            .replace('納得している', '筋が通っている').replace('納得しなかった', '筋が通っていなかった'))
    for wrong in changes:
        assert wrong != reception
        assert not whole_valid(artifact.text.replace(reception, wrong))
    # The complete inverse also keeps the required plan-only replay check.
    # Only this source reader is independent of the author.
    move, = plan.response_plan.human_reception_plan.moves
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence',
        lambda *_a, **_k: pytest.fail('source reader must not invoke the author'))
    def valid(text):
        return read_source_owned_discourse(text, move, plan, resolver, selected) is not None
    assert valid(reception)
    for wrong in changes:
        assert wrong != reception
        assert not valid(wrong)


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
    assert '資料を分類できたこと' in outcome.artifact.reception
    assert '満たされた感覚があった経験' in outcome.artifact.reception
    appraisal_sentence=next(sentence for sentence in outcome.artifact.reception.split('。') if '満たされた' in sentence)
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


@pytest.mark.parametrize('source,evaluation', [
    ('資料を分類できて満足した', '満足した'),
    ('資料を分類したことにまだ納得していない', 'まだ納得していない'),
])
@pytest.mark.parametrize('whole', [False, True])
def test_appraisal_withdrawal_preserves_only_the_remaining_source_meaning(source, evaluation, whole):
    from test_cmee_emlis_q3_thread import begin, advance
    req = begin('褒められたのに、嬉しくなかった。', source + '。植木に水をやった。')
    original = prepare_emlis_meaning(req).original_plan
    relation, = (r for r in original.relations if source_owned_result_appraisal(r, original.nuclei))
    target = source if whole else evaluation
    req = advance(req, f'「{target}」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update, = prepared.checkpoint.answer_update.updates
    removed = {relation.to_nucleus_id, relation.from_nucleus_id} if whole else {relation.to_nucleus_id}
    assert update.operation == 'WITHDRAW'
    assert set(update.superseded_claim_refs) == removed
    plan = build_updated_grounded_plan(prepared)
    assert not removed & {n.nucleus_id for n in plan.nuclei}
    assert relation.relation_id not in {r.relation_id for r in plan.relations}
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    body = outcome.artifact.text
    assert '植木に水をやった' in body and '褒められた' in body
    assert evaluation not in body
    if whole:
        assert '資料を分類' not in body
    else:
        event = next(n for n in plan.nuclei if n.nucleus_id == relation.from_nucleus_id)
        assert (event.kind, event.semantic_frame.predicate_kind, event.semantic_frame.modality,
                event.semantic_frame.time_scope) == ('event', 'event', 'fact', 'past')
        line = next(line for line in outcome.artifact.observation.splitlines() if '資料を分類' in line)
        assert 'という出来事がありました。' in line
        assert '今は' not in line and '感覚' not in line
        projection = project_thread_meaning(prepared, plan)
        sentence = build_grounded_sentence_plan(plan, prepared.thread.resolver(), recovery_stage='full')
        def valid(value):
            return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
                sentence_plan=sentence, resolver=prepared.thread.resolver(),
                selected_subjective_input=projection.selected_reception).passed
        assert valid(body)
        for ending in ('という感覚が前に出ています。', 'という出来事があります。',
                       'という出来事に満足しました。'):
            changed = body.replace('という出来事がありました。', ending)
            assert changed != body and not valid(changed)


@pytest.mark.parametrize('quoted', ['資料を分類', '資料を分類できて満足', '他人を分類できて満足した'])
def test_partial_or_foreign_appraisal_quote_cannot_withdraw_the_whole_source(quoted):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
                  f'「{quoted}」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
    assert not prepared.checkpoint.inactive_claim_refs


def test_repeated_whole_appraisal_cannot_be_resolved_by_source_order():
    from test_cmee_emlis_q1_thread import answered
    req = answered('「資料を分類できて満足した」は誤りです。',
        initial('褒められたのに、嬉しくなかった。',
                '資料を分類できて満足した。資料を分類できて満足した。'))
    prepared = prepare_emlis_meaning(req)
    assert sum(source_owned_result_appraisal(r, prepared.original_plan.nuclei)
               for r in prepared.original_plan.relations) == 2
    assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
    assert not prepared.checkpoint.inactive_claim_refs
    assert not prepared.checkpoint.answer_update.updates
    assert tuple(row.reason_code for row in prepared.checkpoint.unresolved_parts) == ('correction_target_unresolved',)


@pytest.mark.parametrize('whole', [False, True])
def test_saved_appraisal_withdrawal_uses_updated_body_and_no_author_on_reopen(qcase, qdb, whole):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent,
        '褒められたのに、嬉しくなかった。', '資料を分類できて満足した。植木に水をやった。'])
    initial_dto = run(service.start(user, parent))
    target = '資料を分類できて満足した' if whole else '満足した'
    dto = run(answer(service, user, initial_dto, f'「{target}」は誤りです。'))
    assert dto['body_state'] == 'REFINED', dto
    current = dto['current_observation']
    assert current['event_id'] != initial_dto['current_observation']['event_id']
    assert '満足した' not in current['text'] and '植木に水をやった' in current['text']
    assert ('資料を分類' not in current['text']) if whole else ('という出来事がありました。' in current['text'])
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved withdrawal read attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == dto
    assert run(restarted.start(user, parent)) == dto


# Captured by the unmodified c458 baseline, including its genuine question.
# These are not current checkpoints with IDs substituted to simulate history.
LEGACY_CHECKPOINTS = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_pre_appraisal_checkpoint_v1.json').read_text())['rows']


def _legacy_fixture_request(row, *, checkpoint=True):
    from cocolon_meaning_experience_engine.emlis_thread_contracts import (
        EmlisClarificationV1, EmlisQuestionDecisionV1, EmlisQuestionControlV1, SupplementalAnswerSource)
    req = initial(row['memo'], row['action'])
    thread = replace(req.emlis_thread, capability_snapshot=row['capability'])
    if 'answer' in row:
        def question(value):
            q = dict(value)
            d = dict(q.pop('decision'))
            for key in ('supporting_evidence_refs', 'affected_meaning_refs', 'affected_reception_refs', 'asked_target_refs'):
                d[key] = tuple(d[key])
            return EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d), **q)
        control = dict(row['question_control'])
        control['pending_question'] = question(control['pending_question'])
        control['issued_questions'] = tuple(question(q) for q in control['issued_questions'])
        control['asked_target_refs'] = tuple(control['asked_target_refs'])
        answers = tuple(SupplementalAnswerSource(**a) for a in (
            row['supplemental_answers'] if 'supplemental_answers' in row else [row['supplemental_answer']]))
        thread = replace(thread, current_round=len(answers),
            answers=answers,
            question_control_context=EmlisQuestionControlV1(**control))
    return replace(req, emlis_thread=replace(thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id'] if checkpoint else None))


@pytest.mark.parametrize('row', LEGACY_CHECKPOINTS, ids=lambda r: r['case_id'])
def test_saved_pre_appraisal_checkpoint_is_rederived_exactly_before_body(row):
    from dataclasses import asdict
    from hashlib import sha256
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_result_appraisal
    assert _json(prepared.checkpoint) == row['checkpoint']
    for attr in ('nuclei', 'relations'):
        value = json.dumps([asdict(n) for n in getattr(prepared.original_plan, attr)],
            sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        assert sha256(value).hexdigest() == row['original_' + attr + '_sha256']
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert _json(outcome.meaning_checkpoint) == row['checkpoint']
    assert outcome.body_state == row['baseline_body_state']
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)


def test_new_answer_to_a_genuine_legacy_question_revalidates_the_question_before_preparing():
    from emlis_thread_service import _json
    row = next(r for r in LEGACY_CHECKPOINTS if r['case_id'] == 'q2_answered_appraisal_action')
    req = _legacy_fixture_request(row, checkpoint=False)
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_result_appraisal
    assert _json(prepared.checkpoint) == row['checkpoint']
    control = req.emlis_thread.question_control_context
    wrong = replace(control.pending_question, prompt_private='別の質問')
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        question_control_context=replace(control, pending_question=wrong)))
    with pytest.raises(ValueError, match='emlis_question_noncanonical'):
        prepare_emlis_meaning(req)


def test_current_appraisal_does_not_select_the_legacy_projection():
    req = request('資料を分類できて満足した。')
    prepared = prepare_emlis_meaning(req)
    assert not prepared.legacy_result_appraisal
    bound = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    assert prepare_emlis_meaning(bound).checkpoint == prepared.checkpoint
    assert not prepare_emlis_meaning(bound).legacy_result_appraisal


@pytest.mark.parametrize('memo,action,expected_state', [
    ('資料を分類できて満足した。', '植木に水をやった。', 'FINAL'),
    ('探しやすくなったので、資料を分類したことに満足した。' * 2,
     '褒められたのに、嬉しくなかった。', 'PRE_QUESTION'),
    ('褒められたのに、嬉しくなかった。',
     '探しやすくなったので、資料を分類したことに満足した。' * 2, 'PRE_QUESTION'),
])
def test_current_appraisal_body_save_retry_reuses_the_same_meaning(qcase, qdb, monkeypatch, memo, action, expected_state):
    import httpx
    import emlis_thread_store
    from test_emlis_q2_application import run
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1',
        [parent, memo, action])
    failed = False
    async def fail_body_once(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_body_once)
    pending = run(service.start(user, parent))
    assert pending['can_retry'] and pending['current_observation'] is None
    before = run(service.store.read(user, input_id=parent))
    meaning = next(e for e in before['events'] if e['kind'] == 'MEANING_UPDATE')
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', lambda *_: pytest.fail('checkpoint must be reused'))
    done = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='retry-appraisal', operation_id=pending['operation_id']))
    assert done['body_state'] == expected_state and done['current_observation']
    assert done['operation_id'] == pending['operation_id'] and done['attempt_id'] != pending['attempt_id']
    after = run(service.store.read(user, input_id=parent))
    assert [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE'] == [meaning]
    observation, = (e for e in after['events'] if e['kind'] == 'OBSERVATION')
    assert observation['payload']['meaning_checkpoint_ref'] == meaning['payload']['checkpoint_id']
    assert observation['payload']['effective_plan_ref'] == meaning['payload']['base_meaning_ref']


@pytest.mark.parametrize('memo,action', [
    ('資料を分類できて満足した。', '植木に水をやった。'),
    ('資料を分類したことにまだ納得していない。', ''),
    ('褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
])
def test_q2_appraisal_initial_body_uses_the_same_prepared_meaning(memo, action):
    req = initial(memo, action)
    prepared = prepare_emlis_meaning(req)
    assert not prepared.legacy_result_appraisal
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert out.meaning_checkpoint == prepared.checkpoint
    assert '資料を分類' in out.artifact.text
    if '褒められた' in memo:
        from test_cmee_emlis_q1_thread import answered, prepared_request
        assert out.question is not None
        for text in ('その時は重かった。', '分からない。'):
            revised = answered(text, req)
            assert revised.emlis_thread.question_control_context.pending_question == out.question
            revised, cp = prepared_request(revised)
            after = MeaningExperienceEngine().generate(revised)
            assert after.artifact is not None, after.reason_codes
            assert after.meaning_checkpoint == cp
            assert after.body_state == ('REFINED' if '重' in text else 'UNCHANGED')
            assert '資料を分類' in after.artifact.text and '満足' in after.artifact.text


def test_q2_legacy_no_change_answer_keeps_the_legacy_original_meaning():
    row = next(r for r in LEGACY_CHECKPOINTS if r['case_id'] == 'q2_answered_appraisal_action')
    req = _legacy_fixture_request(row, checkpoint=False)
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        answers=(replace(req.emlis_thread.answers[0], answer_text_private='分からない。'),)))
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_result_appraisal
    assert prepared.checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE'
    bound = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    out = MeaningExperienceEngine().generate(bound)
    assert out.artifact is not None, out.reason_codes
    assert out.body_state == 'UNCHANGED'
    assert out.meaning_checkpoint == prepared.checkpoint
    assert '資料を分類できて満足した' in out.artifact.observation
    assert not any(source_owned_result_appraisal(r, prepared.original_plan.nuclei)
                   for r in prepared.original_plan.relations)


@pytest.mark.parametrize('old,new,polarity,time,degree,continuing', [
    ('満足した', '満足しなかった', 'negative', 'past', 'unmarked', False),
    ('満足しなかった', '満足した', 'positive', 'past', 'unmarked', False),
    ('まだ納得していない', '納得している', 'positive', 'present', 'unmarked', False),
    ('納得している', 'まだ納得していない', 'negative', 'present', 'unmarked', True),
    ('とても満足した', '少し満足しています', 'positive', 'present', 'slight', False),
    ('満足した', '全然満足しませんでした', 'negative', 'past', 'not_at_all', False),
    ('満足していない', 'その時は本当に納得しました', 'positive', 'past', 'truly', False),
])
def test_appraisal_revision_reads_only_new_source_operators_and_body_time(old, new, polarity, time, degree, continuing):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。',
        f'資料を分類できて{old}。植木に水をやった。'), f'「{old}」ではなく「{new}」です。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update, = prepared.checkpoint.answer_update.updates
    assert update.operation == 'REVISE' and len(update.changed_claim_refs) == 1
    plan = build_updated_grounded_plan(prepared)
    relation, = [r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == relation.to_nucleus_id)
    assert nucleus.source_fields == ('answer_text_private',)
    frame = nucleus.semantic_frame
    assert (frame.polarity, frame.time_scope) == (polarity, time)
    assert {c for c in frame.attribute_codes if c.startswith('source_appraisal_degree:')} == {'source_appraisal_degree:' + degree}
    assert ('source_appraisal_continuing:still' in frame.attribute_codes) == continuing
    assert ('operator:negation' in frame.attribute_codes) == (polarity == 'negative')
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    body = outcome.artifact.text
    assert f'「{new}」' in outcome.artifact.observation
    assert '資料を分類できたことについて' in outcome.artifact.reception
    assert '植木に水をやった' in outcome.artifact.observation
    expected_time = '当時' if time == 'past' else '入力した時点'
    assert expected_time + 'の評価' in outcome.artifact.observation
    assert expected_time + ('は' if time == 'past' else 'では') in outcome.artifact.reception
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def valid(value):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    for changed in (body.replace(expected_time, '回答した時点'),
                    body.replace(new, old), body.replace('資料を分類できたことについて', '植木に水をやったことについて')):
        assert changed != body and not valid(changed)


@pytest.mark.parametrize('evaluation,time', [
    ('満足した', 'past'), ('満足しなかった', 'past'),
    ('少し満足しています', 'present'), ('まだ納得していない', 'present'),
])
def test_event_only_withdrawal_keeps_evaluation_without_inventing_its_object(evaluation, time):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。',
        f'資料を分類できて{evaluation}。植木に水をやった。'), '「資料を分類できて」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    from emlis_ai_grounded_observation_plan import _thread_withdrawn_result_appraisal
    surviving, = [n for n in plan.nuclei if _thread_withdrawn_result_appraisal(n, plan.relations)]
    assert surviving.semantic_frame.time_scope == time
    assert not any(surviving.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    body = outcome.artifact.text
    assert '資料を分類' not in body and f'「{evaluation}」' in body
    assert '褒められた' in body and '植木に水をやった' in body
    when = '当時' if time == 'past' else '入力した時点'
    assert when + 'の評価として' in body
    projection = project_thread_meaning(prepared, plan)
    sentence = build_grounded_sentence_plan(plan, prepared.thread.resolver(), recovery_stage='full')
    def valid(value):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=prepared.thread.resolver(),
            selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    for changed in (body.replace(when, '回答した時点'), body.replace(evaluation, '満足しなかった' if evaluation != '満足しなかった' else '満足した'),
                    body.replace(when + 'の評価として', '資料を分類できたことへの評価として')):
        assert changed != body and not valid(changed)


@pytest.mark.parametrize('new', ['今は満足した', '同僚が満足した', '満足したかもしれない', '満足したら'])
def test_revision_does_not_turn_foreign_uncertain_or_conflicting_time_into_appraisal(new):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
                  f'「満足した」ではなく「{new}」です。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'


@pytest.mark.parametrize('evaluation', ['嬉しかった', '重かった'])
def test_existing_nonappraisal_correction_keeps_its_accepted_meaning(evaluation):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
                  f'「満足した」ではなく「{evaluation}」です。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert prepared.accepted_nuclei
    assert all('thread_subject:revised_result_appraisal' not in n.semantic_frame.attribute_codes for n in prepared.accepted_nuclei)


@pytest.mark.parametrize('withdraw_first', [False, True])
def test_revision_and_event_withdrawal_compose_without_reattaching_the_evaluation(withdraw_first):
    from test_cmee_emlis_q3_thread import begin, advance
    req = begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。',
                '資料を分類できて満足した。')
    changes = ['「満足した」ではなく「まだ納得していない」です。', '「資料を分類できて」は誤りです。']
    if withdraw_first:
        changes.reverse()
    for change in changes:
        req = advance(req, change)
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert '資料を分類' not in outcome.artifact.text
    assert '満足した' not in outcome.artifact.text
    assert '入力した時点の評価として、「まだ納得していない」' in outcome.artifact.observation


LEGACY_CORRECTIONS = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_pre_appraisal_correction_checkpoint_v1.json').read_text())['rows']


@pytest.mark.parametrize('row', LEGACY_CORRECTIONS, ids=lambda r: r['case_id'])
def test_saved_u254_partial_correction_keeps_full_checkpoint_but_new_answer_uses_new_meaning(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_appraisal_correction and not prepared.legacy_result_appraisal
    assert _json(prepared.checkpoint) == row['checkpoint']
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert outcome.body_state == row['baseline_body_state'] == 'PARTIALLY_REFINED'
    assert outcome.artifact.text == row['baseline_body']
    fresh = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
    assert not fresh.legacy_appraisal_correction and fresh.checkpoint.assessment_status == 'RESOLVED'
    assert fresh.checkpoint.checkpoint_id != prepared.checkpoint.checkpoint_id
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)
    control = req.emlis_thread.question_control_context
    wrong = replace(control.pending_question, prompt_private='別の質問')
    with pytest.raises(ValueError, match='emlis_question_noncanonical'):
        prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread,
            question_control_context=replace(control, pending_question=wrong, issued_questions=(wrong,)))))


@pytest.mark.parametrize('response,expected,absent', [
    ('「満足した」ではなく「満足しなかった」です。', '当時は満足しなかった', None),
    ('「満足した」ではなく「少し満足しています」です。', '入力した時点では少し満足している', None),
    ('「資料を分類できて」は誤りです。', '当時は満足した', '資料を分類'),
])
def test_saved_revision_or_event_withdrawal_reopens_without_generation(qcase, qdb, response, expected, absent):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE, _request, _json
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent,
        '褒められたのに、嬉しくなかった。', '資料を分類できて満足した。植木に水をやった。'])
    initial_dto = run(service.start(user, parent))
    dto = run(answer(service, user, initial_dto, response))
    assert dto['body_state'] == 'REFINED' and dto['answer_saved'] and dto['meaning_updated'], dto
    current = dto['current_observation']
    assert expected in current['text'] and '植木に水をやった' in current['text']
    if absent:
        assert absent not in current['text']
    bundle = run(service.store.read(user, input_id=parent))
    meaning = next(e['payload'] for e in bundle['events'] if e['id'] == bundle['thread']['current_meaning_event_id'])
    assert _json(prepare_emlis_meaning(_request(bundle, checkpoint_ref=meaning['checkpoint_id'])).checkpoint) == meaning
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved update read attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == dto
    assert run(restarted.start(user, parent)) == dto
    replay = run(answer(restarted, user, initial_dto, response))
    assert replay['current_observation'] == current and replay['timeline'] == dto['timeline']
    assert replay['operation_id'] == dto['operation_id'] and replay['attempt_id'] == dto['attempt_id']
    assert replay['requested_attempt_id'] == dto['attempt_id']


@pytest.mark.parametrize('legacy_mode', ['legacy_appraisal_correction', 'legacy_appraisal_answer_time'])
def test_saved_partial_checkpoint_retry_preserves_meaning_event_and_operation(qcase, qdb, monkeypatch, legacy_mode):
    import httpx
    import emlis_thread_store
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import _json
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    from cocolon_meaning_experience_engine.emlis_answer_update import _prepare_emlis_meaning_from_plan
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent,
        '褒められたのに、嬉しくなかった。', '資料を分類できて満足した。植木に水をやった。'])
    initial_dto = run(service.start(user, parent))
    def old_prepare(req):
        thread = admit_emlis_thread(req)
        return _prepare_emlis_meaning_from_plan(req, thread, original_meaning_plan(thread),
            **{legacy_mode: True}).checkpoint
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    failed = False
    async def fail_body_once(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_body_once)
    new = '満足しなかった' if legacy_mode == 'legacy_appraisal_correction' else '今は満足していない'
    pending = run(answer(service, user, initial_dto, f'「満足した」ではなく「{new}」です。'))
    assert pending['can_retry'] and pending['answer_saved'] and pending['meaning_updated'], pending
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert meanings[-1]['payload']['assessment_status'] == 'PARTIAL'
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', lambda *_: pytest.fail('saved meaning must be reused'))
    done = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='retry-u254-correction', operation_id=pending['operation_id']))
    assert done['body_state'] == 'PARTIALLY_REFINED' and done['current_observation'], done
    assert done['operation_id'] == pending['operation_id'] and done['attempt_id'] != pending['attempt_id']
    after = run(service.store.read(user, input_id=parent))
    assert [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE'] == meanings
    observation = next(e for e in after['events'] if e['id'] == after['thread']['last_observation_event_id'])
    assert observation['payload']['meaning_checkpoint_ref'] == meanings[-1]['payload']['checkpoint_id']


MULTIPLE_APPRAISALS = (
    ('満足した', '納得した'),
    ('満足した', 'まだ納得していない'),
    ('あまり満足しなかった', '少し納得しています'),
    ('満足した', '満足した'),
)


@pytest.mark.parametrize('evaluations', MULTIPLE_APPRAISALS)
@pytest.mark.parametrize('in_memo', [False, True])
def test_multiple_original_appraisals_keep_each_object_and_time(evaluations, in_memo):
    from test_cmee_emlis_q3_thread import begin
    first, second = evaluations
    pair = f'資料を分類できて{first}。案を選んで{second}。'
    received = '褒められたのに、嬉しくなかった。'
    req = begin(pair, received) if in_memo else begin(received, pair)
    plan = build_updated_grounded_plan(prepare_emlis_meaning(req))
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    links = [r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(links) == 2 and len(moves) == 3
    assert all(any(m.target_nucleus_ids == (r.to_nucleus_id,)
                   and m.support_nucleus_ids == (r.from_nucleus_id,) for m in moves) for r in links)
    for target, evaluation in zip(('資料を分類できて', '案を選んで'), evaluations, strict=True):
        when = '入力した時点' if evaluation.endswith(('いない', 'います')) else '当時'
        assert f'「{target}」という出来事に対する{when}の評価は「{evaluation}」' in out.artifact.observation
    assert out.artifact.observation.index('資料を分類') < out.artifact.observation.index('案を選んで')
    assert '資料を分類できたことについて' in out.artifact.reception
    assert '案を選んだことについて' in out.artifact.reception
    assert '褒められた' in out.artifact.reception and '嬉しさにはつながらなかった' in out.artifact.reception


@pytest.mark.parametrize('evaluations', MULTIPLE_APPRAISALS)
@pytest.mark.parametrize('both', [False, True])
def test_multiple_appraisal_withdrawal_keeps_each_surviving_evaluation(evaluations, both):
    from test_cmee_emlis_q3_thread import begin, advance
    first, second = evaluations
    req = advance(begin('褒められたのに、嬉しくなかった。',
        f'資料を分類できて{first}。案を選んで{second}。'),
        '「資料を分類できて」は誤りです。' + ('「案を選んで」は誤りです。' if both else ''))
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    plan = build_updated_grounded_plan(prepared)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert '資料を分類' not in out.artifact.text
    assert ('案を選ん' not in out.artifact.text) == both
    assert len([r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]) == (0 if both else 1)
    for evaluation in evaluations:
        assert f'「{evaluation}」' in out.artifact.observation
    assert '入力した時点では' in out.artifact.reception if second.endswith(('いない', 'います')) else '当時は' in out.artifact.reception
    if both and first == second:
        assert '二つの評価とも、当時は満足したのですね。' in out.artifact.reception
        assert out.artifact.reception.count('満足した') == 1


@pytest.mark.parametrize('withdraw_first', [False, True])
def test_multiple_appraisal_revision_and_withdrawal_in_one_answer_preserve_remaining_duties(withdraw_first):
    from test_cmee_emlis_q3_thread import begin, advance
    req = begin('褒められたのに、嬉しくなかった。',
                '資料を分類できて満足した。案を選んで納得した。')
    changes = ['「満足した」ではなく「まだ納得していない」です。',
               '「資料を分類できて」は誤りです。「案を選んで」は誤りです。']
    if withdraw_first:
        changes.reverse()
    req = advance(req, ''.join(changes))
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert prepare_emlis_meaning(req).checkpoint.assessment_status == 'RESOLVED'
    assert '満足した' not in out.artifact.text and '資料を分類' not in out.artifact.text and '案を選ん' not in out.artifact.text
    assert '入力した時点の評価「まだ納得していない」' in out.artifact.observation
    assert '当時の評価「納得した」' in out.artifact.observation
    assert '褒められた' in out.artifact.reception


@pytest.mark.parametrize('withdraw', [False, True])
def test_multiple_appraisal_body_reader_rejects_source_time_and_scope_edits(withdraw):
    from test_cmee_emlis_q3_thread import begin, advance
    req = begin('褒められたのに、嬉しくなかった。',
                '資料を分類できて満足した。案を選んでまだ納得していない。')
    if withdraw:
        req = advance(req, '「資料を分類できて」は誤りです。「案を選んで」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    body = MeaningExperienceEngine().generate(req).artifact.text
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan, sentence_plan=sentence,
            resolver=resolver, selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    changes = [body.replace('満足した', '満足しなかった'), body.replace('入力した時点', '回答した時点'),
               body.replace('まだ納得していない', '納得している'),
               body.replace('当時', '入力した時点'), body.replace('書かれています。', '書かれているので成長しました。')]
    if withdraw:
        changes += [body.replace('と、入力した時点の評価「まだ納得していない」', ''),
                    body.replace('当時は満足したのですね。', '資料を分類できたことについて、当時は満足したのですね。')]
    else:
        changes += [body.replace('資料を分類できて', 'SWAP').replace('案を選んで', '資料を分類できて').replace('SWAP', '案を選んで'),
                    body.replace('、また「案を選んで」という出来事に対する入力した時点の評価は「まだ納得していない」', '')]
    for changed in changes:
        assert changed != body
        assert not valid(changed)


@pytest.mark.parametrize('second,response', [
    ('まだ納得していない', '「資料を分類できて」は誤りです。'),
    ('まだ納得していない', '「資料を分類できて」は誤りです。「案を選んで」は誤りです。'),
    ('納得した', '「満足した」ではなく「納得している」です。'),
    ('満足した', '「資料を分類できて」は誤りです。「案を選んで」は誤りです。'),
])
def test_saved_multiple_appraisals_reopen_and_replay_without_author(qcase, qdb, second, response):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE, _request, _json
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent,
        '褒められたのに、嬉しくなかった。', f'資料を分類できて満足した。案を選んで{second}。'])
    initial_dto = run(service.start(user, parent))
    assert initial_dto['current_observation'] and initial_dto['pending_question'], initial_dto
    dto = run(answer(service, user, initial_dto, response))
    assert dto['body_state'] == 'REFINED' and dto['answer_saved'] and dto['meaning_updated'], dto
    bundle = run(service.store.read(user, input_id=parent))
    meaning = next(e['payload'] for e in bundle['events'] if e['id'] == bundle['thread']['current_meaning_event_id'])
    assert _json(prepare_emlis_meaning(_request(bundle, checkpoint_ref=meaning['checkpoint_id'])).checkpoint) == meaning
    current = dto['current_observation']
    event = next(e for e in bundle['events'] if e['id'] == current['event_id'])
    assert event['payload']['text'] == current['text']
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved multiple-appraisal read attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == run(restarted.start(user, parent)) == dto
    replay = run(answer(restarted, user, initial_dto, response))
    assert replay['current_observation'] == current and replay['timeline'] == dto['timeline']
    assert replay['operation_id'] == dto['operation_id'] and replay['attempt_id'] == dto['attempt_id']


@pytest.mark.parametrize('new', ['今は満足していない', '今は少し満足しています',
                               '今はまだ納得していません', '今は納得している'])
@pytest.mark.parametrize('withdraw', ['', 'before', 'after'])
def test_appraisal_now_revision_keeps_answer_source_time_and_detached_body(new, withdraw):
    from test_cmee_emlis_q3_thread import begin, advance
    changes = [f'「満足した」ではなく「{new}」です。']
    if withdraw:
        changes.insert(0 if withdraw == 'before' else 1, '「資料を分類できて」は誤りです。')
    req = advance(begin('褒められたのに、嬉しくなかった。',
        '資料を分類できて満足した。植木に水をやった。'), ''.join(changes))
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update, = [u for u in prepared.checkpoint.answer_update.updates if u.operation == 'REVISE']
    assert update.temporal_binding.about_time == 'ANSWER_TIME'
    assert update.temporal_binding.anchor_source_ref == prepared.thread.answers[-1].envelope.envelope_id
    assert update.temporal_binding.time_expression_evidence_refs == update.evidence_refs
    assert update.temporal_binding.relative_relation == 'answer_deictic_now'
    plan = build_updated_grounded_plan(prepared)
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == update.changed_claim_refs[0])
    assert {c for c in nucleus.semantic_frame.attribute_codes if c.startswith('thread_time:')} == {'thread_time:answer_time'}
    assert nucleus.semantic_frame.time_scope == 'present'
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    body = out.artifact.text
    assert new in out.artifact.observation
    assert '回答した時点の評価' in out.artifact.observation
    assert '回答した時点では' in out.artifact.reception
    assert '植木に水をやった' in body
    assert ('資料を分類' not in body) if withdraw else ('資料を分類できたことについて' in out.artifact.reception)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def valid(value):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    for when in ('入力した時点', '当時', '先の回答時点'):
        changed = body.replace('回答した時点', when)
        assert changed != body and not valid(changed)


@pytest.mark.parametrize('explicit_now', [False, True])
def test_revising_a_previous_now_appraisal_preserves_or_explicitly_reanchors_time(explicit_now):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。',
        '資料を分類できて満足した。'), '「満足した」ではなく「今は満足していない」です。')
    first = prepare_emlis_meaning(req)
    first_anchor = first.thread.answers[-1].envelope.envelope_id
    new = ('今は' if explicit_now else '') + '少し満足している'
    req = advance(req, f'「今は満足していない」ではなく「{new}」です。')
    prepared = prepare_emlis_meaning(req)
    update, = prepared.checkpoint.answer_update.updates
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert update.temporal_binding.about_time == 'ANSWER_TIME'
    assert update.temporal_binding.anchor_source_ref == (
        prepared.thread.answers[-1].envelope.envelope_id if explicit_now else first_anchor)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    when = '回答した時点' if explicit_now else '先の回答時点'
    assert when + 'の評価' in out.artifact.observation
    assert when + 'では少し満足している' in out.artifact.reception


LEGACY_ANSWER_TIME = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_pre_appraisal_answer_time_checkpoint_v1.json').read_text())['rows']


@pytest.mark.parametrize('row', LEGACY_ANSWER_TIME, ids=lambda r: r['case_id'])
def test_saved_u256_now_partial_is_exact_but_fresh_revision_uses_answer_time(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert _json(prepared.checkpoint) == row['checkpoint']
    old = MeaningExperienceEngine().generate(req)
    assert old.artifact is not None, old.reason_codes
    assert (old.artifact.observation, old.artifact.reception) == (row['observation'], row['reception'])
    fresh = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
    assert fresh.checkpoint.assessment_status == 'RESOLVED'
    assert fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    fresh_req = _legacy_fixture_request(row, checkpoint=False)
    fresh_req = replace(fresh_req, emlis_thread=replace(fresh_req.emlis_thread,
        prepared_meaning_checkpoint_ref=fresh.checkpoint.checkpoint_id))
    new = MeaningExperienceEngine().generate(fresh_req)
    assert new.artifact is not None, new.reason_codes
    assert '回答した時点では満足していない' in new.artifact.reception
    if row['case_id'] == 'mixed_corrections':
        assert '当時は納得しなかった' in new.artifact.reception
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)


@pytest.mark.parametrize('response,absent', [
    ('「満足した」ではなく「今は満足していない」です。', None),
    ('「資料を分類できて」は誤りです。「満足した」ではなく「今はまだ納得していません」です。', '資料を分類'),
])
def test_saved_now_revision_reopens_without_author(qcase, qdb, response, absent):
    test_saved_revision_or_event_withdrawal_reopens_without_generation(
        qcase, qdb, response,
        '回答した時点では' + ('まだ納得していない' if absent else '満足していない'), absent)


@pytest.mark.parametrize('withdraw_first', [False, True])
def test_now_appraisal_and_separate_target_withdrawal_keep_answer_time(withdraw_first):
    from test_cmee_emlis_q3_thread import begin, advance
    changes = ['「満足した」ではなく「今は満足していない」です。', '「資料を分類できて」は誤りです。']
    if withdraw_first:
        changes.reverse()
    req = begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。', '資料を分類できて満足した。')
    for change in changes:
        req = advance(req, change)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert '資料を分類' not in out.artifact.text
    assert '回答した時点の評価として、「今は満足していない」' in out.artifact.observation
    assert '回答した時点では満足していない' in out.artifact.reception


@pytest.mark.parametrize('withdraw', [False, True])
def test_appraisal_recorrection_explicit_original_time_overrides_prior_answer(withdraw):
    from test_cmee_emlis_q3_thread import begin, advance
    req = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。',
        '資料を分類できて満足した。'),
        '「満足した」ではなく「今は満足していない」です。')
    response = '「今は満足していない」ではなく「その時は納得した」です。'
    if withdraw:
        response += '「資料を分類できて」は誤りです。'
    req = advance(req, response)
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update = next(u for u in prepared.checkpoint.answer_update.updates if u.operation == 'REVISE')
    assert update.temporal_binding.about_time == 'ORIGINAL_OCCASION'
    assert update.temporal_binding.anchor_source_ref == prepared.thread.original.envelope.envelope_id
    assert update.temporal_binding.time_expression_evidence_refs == update.evidence_refs
    nucleus, = prepared.accepted_nuclei
    assert {c for c in nucleus.semantic_frame.attribute_codes if c.startswith('thread_time:')} == {'thread_time:original_occasion'}
    assert not any(c.startswith('thread_time_anchor:') for c in nucleus.semantic_frame.attribute_codes)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert '当時の評価' in out.artifact.observation
    assert '当時は納得した' in out.artifact.reception
    assert '先の回答時点' not in out.artifact.text and '回答した時点' not in out.artifact.text
    assert ('資料を分類' in out.artifact.text) == (not withdraw)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    selected = project_thread_meaning(prepared, plan).selected_reception
    changed = out.artifact.text.replace('当時', '先の回答時点')
    assert changed != out.artifact.text
    assert not evaluate_grounded_surface_body_inverse(body=changed.encode(), plan=plan,
        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed


LEGACY_ORIGINAL_TIMES = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_pre_appraisal_original_time_checkpoint_v1.json').read_text())['rows']


@pytest.mark.parametrize('row', LEGACY_ORIGINAL_TIMES, ids=lambda r: r['case_id'])
def test_saved_u257_partial_original_time_checkpoint_keeps_its_complete_meaning(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert _json(prepared.checkpoint) == row['checkpoint']
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.text == row['baseline_body']
    assert out.body_state == row['baseline_body_state'] == 'PARTIALLY_REFINED'
    fresh = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
    assert fresh.checkpoint.assessment_status == 'RESOLVED'
    assert fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch|emlis_q3_unresolved_predecessor'):
        prepare_emlis_meaning(foreign)


def _unfinished_appraisal_source(plan):
    from emlis_ai_grounded_observation_plan import source_owned_result_appraisal_context
    index = {n.nucleus_id: n for n in plan.nuclei}
    rows = [(context, index[relation.from_nucleus_id], index[relation.to_nucleus_id], relation)
            for relation in plan.relations
            if (context := source_owned_result_appraisal_context(
                relation, plan.nuclei, plan.relations)) is not None]
    return rows


@pytest.mark.parametrize('event,action,evaluation', [
    ('考えを言葉にできて', '', '満足した'),
    ('考えを言葉にできて', '植木に水をやった。', '満足した'),
    ('資料を分類できて', '机を拭いた。', '満足した'),
    ('考えを言葉にできて', '植木に水をやった。', '満足している'),
])
def test_unfinished_appraisal_owns_three_sources_and_scoped_selected_content(event, action, evaluation):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine import contracts as c
    req = request('結論は出ていないが、' + event + evaluation + '。', action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    (context, target, feeling, about), = _unfinished_appraisal_source(plan)
    index = {n.nucleus_id: n for n in plan.nuclei}
    resolver = prepared.thread.resolver()
    assert tuple(hr.final_reception_source_anchor_text(n.nucleus_id, index, resolver)
                 for n in (context, target, feeling)) == ('結論は出ていない', event, evaluation)
    assert (context.kind, context.semantic_frame.modality, context.semantic_frame.polarity,
            context.semantic_frame.time_scope) == ('state', 'fact', 'negative', 'present')
    assert 'semantic_role:appraisal_unfinished_context' in context.semantic_frame.attribute_codes
    assert target.semantic_frame.modality == 'fact'
    assert (feeling.semantic_frame.modality, feeling.semantic_frame.polarity,
            feeling.semantic_frame.time_scope) == (
                'feeling', 'positive', 'present' if evaluation.endswith('している') else 'past')
    source_ids = {n.nucleus_id for n in (context, target, feeling)}
    assert source_ids <= set(plan.coverage_requirements.required_nucleus_ids)
    assert len({n.source_span_ids for n in (context, target, feeling)}) == 1
    contrast, = (r for r in plan.relations if r.type == 'contrast'
                 and r.from_nucleus_id == context.nucleus_id and r.to_nucleus_id == feeling.nucleus_id)
    assert {about.relation_id, contrast.relation_id} <= set(plan.coverage_requirements.required_relation_ids)
    # Missing causes or personal standards can remain do-not-claim boundaries.
    # The stated unfinished fact itself must not become an epistemic unknown.
    assert not any(boundary.dimension == 'source_explicit_epistemic_limit'
                   and set(boundary.affected_nucleus_ids) & source_ids
                   for boundary in plan.unknown_boundaries)

    projection = project_thread_meaning(prepared, plan)
    selected = projection.structure.meaning_decision_outcome
    assert type(selected) is c.SelectedEmlisProvisionalReading
    candidate = next(row for row in projection.structure.candidate_records
                     if row.candidate_id == selected.selected_candidate_ref)
    assert set(candidate.requirement_bundle_refs) == {
        row.bundle_id for row in projection.structure.requirement_bundles}
    reception = projection.selected_reception
    decision, = (d for d in reception.decisions if d.target_nucleus_ids == (feeling.nucleus_id,))
    assert decision.branch == 'NORMAL'
    assert set(decision.support_nucleus_ids) == {context.nucleus_id, target.nucleus_id}
    content = decision.subjective_proposition.appraisal_content
    assert type(content) is c.EmlisAppraisalContent
    assert (content.dimension, content.operation) == (
        c.AppraisalDimension.RELATIONAL_NONCOLLAPSE, c.AppraisalOperation.PRESERVE_BOTH_ENDPOINTS)
    assert len(content.appraised_bindings) == 3 and content.protected_bindings == ()
    bases = {row.binding_ref: row for row in decision.basis_rows}
    semantic_to_nucleus = dict(reception.semantic_nucleus_pairs)
    assert {semantic_to_nucleus[bases[ref].semantic_ref] for ref in content.appraised_bindings} == source_ids
    assert dict(reception.relation_pairs)[content.focal_relation_ref] == contrast.relation_id

    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    text = outcome.artifact.reception
    assert '同時' not in outcome.artifact.text
    assert '結論' in text and event[:-1] + 'た' in text
    assert '満たされた感覚' in text or '充足' in text
    assert '植木' not in text and '机を拭' not in text
    assert not any(word in text for word in (
        '目標', '基準', '成長', '成功', '進歩', 'いずれ', '追いつ', '理解が深ま', '伝わった'))


@pytest.mark.parametrize('memo', [
    '結論は出ていないが、考えを言葉にできて満足しなかった。',
    '結論は出ていないが、考えを言葉にできて納得した。',
    '結論は出ていないが、考えを言葉にできて少し満足した。',
    '同僚は結論が出ていないが、考えを言葉にできて満足した。',
    '「結論は出ていないが、考えを言葉にできて満足した」と聞いた。',
    '結論は出ていないが、考えを言葉にできて満足したかもしれない。',
    '結論が出ていないなら、考えを言葉にできて満足した。',
    '結論は出ていないが、考えを言葉にできて満足したら。',
    '結論は出ていないが、考えを言葉にできて満足し',
    '結論は出ていない。考えを言葉にできて満足した。',
])
def test_unfinished_appraisal_does_not_extend_its_approved_source_scope(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request(memo)))
    assert not _unfinished_appraisal_source(plan)


def test_removing_unfinished_source_removes_the_three_point_reading():
    from cocolon_meaning_experience_engine import contracts as c
    req = request('考えを言葉にできて満足した。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert not _unfinished_appraisal_source(plan)
    relation, = (r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei))
    selected = project_thread_meaning(prepared, plan).selected_reception
    decision, = (d for d in selected.decisions if d.target_nucleus_ids == (relation.to_nucleus_id,))
    content = decision.subjective_proposition.appraisal_content
    assert type(content) is c.EmlisEvaluatedExperienceAppraisalContent
    assert len(content.appraised_bindings) == 2
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert '考えを言葉にできた' in outcome.artifact.reception
    assert '結論' not in outcome.artifact.text


def test_independent_action_does_not_replace_unfinished_appraisal_reception():
    memo = '結論は出ていないが、考えを言葉にできて満足した。'
    artifacts = []
    for action in ('', '植木に水をやった。', '机を拭いた。'):
        result = MeaningExperienceEngine().generate(request(memo, action))
        assert result.artifact is not None, result.reason_codes
        artifacts.append(result.artifact)
        if action:
            assert action.rstrip('。') in result.artifact.observation
    assert len({body.reception for body in artifacts}) == 1
    assert len({body.observation for body in artifacts}) == 3


@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
def test_unfinished_appraisal_reader_preserves_limit_target_and_time_without_author(monkeypatch, evaluation):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    req = request('結論は出ていないが、考えを言葉にできて' + evaluation + '。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    (_, _, feeling, _), = _unfinished_appraisal_source(plan)
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    artifact = outcome.artifact
    reception = artifact.reception
    expected_time = '当時の満足' if evaluation == '満足した' else '入力した時点での満足'
    wrong_time = '入力した時点での満足' if evaluation == '満足した' else '当時の満足'
    assert expected_time in reception
    mutations = (
        reception.replace('結論は出ていないという点と切り分けて、', ''),
        reception.replace('結論は出ていない', '結論は出ている'),
        reception.replace('結論は出ていない', '結論は出ていなかった'),
        reception.replace('考えを言葉にできたこと', '結論が出たこと'),
        reception.replace('考えを言葉にできたこと', '考えを言葉にできなかったこと'),
        reception.replace(expected_time, wrong_time),
        reception.replace('という点と切り分けて', 'のですが'),
        reception.replace('という点と切り分けて', 'という点と同時に'),
    )
    def whole_valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert whole_valid(artifact.text)
    for wrong in mutations:
        assert wrong != reception
        assert not whole_valid(artifact.text.replace(reception, wrong))
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.target_nucleus_ids == (feeling.nucleus_id,))
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence',
        lambda *_a, **_k: pytest.fail('source reader must not invoke the author'))
    assert read_source_owned_discourse(reception, move, plan, resolver, selected) is not None
    for wrong in mutations:
        assert read_source_owned_discourse(wrong, move, plan, resolver, selected) is None


# Complete initial checkpoints captured from unmodified dc90d70 before the
# connected-source grammar was added. No current IDs stand in for old meaning.
_PRE_CONNECTED_CHECKPOINTS = (
    ('', {
        'checkpoint_id': 'emlis-checkpoint-e39d1005b18507b54062bd0418becc7be8ad12caa8d8527f602b2fd544e34506',
        'source_prefix_ref': 'emlis-q3-source-prefix-3f919cfd78553ee5f573387870220ab88c75cf24e9e17599c869bfc0e5769c5b',
        'base_meaning_ref': 'emlis-base-meaning-fdb9763f513d2eec5c5fd8945c8cda36c7d6d89f2c7287c8ab5e447dec283bdd',
        'answer_update': None,
        'assessment_status': 'RESOLVED',
        'accepted_update_refs': [],
        'inactive_claim_refs': [],
        'unresolved_parts': [],
        'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1',
    }),
    ('植木に水をやった。', {
        'checkpoint_id': 'emlis-checkpoint-c006386b2e13e85733cb382ac29407abb74d5f17d355531ca2e96ce3a0fbe0f6',
        'source_prefix_ref': 'emlis-q3-source-prefix-0ba6b972362a507bc1ea776d0464a50469d015263967407c0c59fe62e7513da5',
        'base_meaning_ref': 'emlis-base-meaning-fbdfb141956d425c4bb7c21acfc89bdaaa9b7a0d95d8fdabe43db6480076f296',
        'answer_update': None,
        'assessment_status': 'RESOLVED',
        'accepted_update_refs': [],
        'inactive_claim_refs': [],
        'unresolved_parts': [],
        'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1',
    }),
)


@pytest.mark.parametrize('action,expected', _PRE_CONNECTED_CHECKPOINTS, ids=['without_action', 'with_action'])
def test_saved_u261_checkpoint_stays_exact_while_fresh_meaning_owns_connected_appraisal(action, expected):
    from emlis_thread_service import _json
    req = request('結論は出ていないが、考えを言葉にできて満足した。', action)
    saved_req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=expected['checkpoint_id']))
    restored = prepare_emlis_meaning(saved_req)
    assert _json(restored.checkpoint) == expected
    assert restored.legacy_result_appraisal
    assert not _unfinished_appraisal_source(build_updated_grounded_plan(restored))
    old_outcome = MeaningExperienceEngine().generate(saved_req)
    assert old_outcome.artifact is None
    assert old_outcome.reason_codes == ('emlis_q3_initial_body_unavailable',)

    fresh = prepare_emlis_meaning(req)
    assert not fresh.legacy_result_appraisal
    assert fresh.checkpoint.source_prefix_ref == expected['source_prefix_ref']
    assert fresh.checkpoint.base_meaning_ref != expected['base_meaning_ref']
    assert fresh.checkpoint.checkpoint_id != expected['checkpoint_id']
    assert len(_unfinished_appraisal_source(build_updated_grounded_plan(fresh))) == 1
    current_req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=fresh.checkpoint.checkpoint_id))
    current = MeaningExperienceEngine().generate(current_req)
    assert current.artifact is not None, current.reason_codes
    assert current.meaning_checkpoint == fresh.checkpoint
    assert '結論は出ていない' in current.artifact.reception
    assert '考えを言葉にできたこと' in current.artifact.reception
    assert '同時' not in current.artifact.text
    foreign = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)


def test_appraisal_relation_qualifiers_match_after_direct_source_projection():
    from cocolon_meaning_experience_engine import contracts as c
    version = c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    left = ('semantic_role:present_unfinished', 'operator:unfinished', 'operator:negation')
    base = ('semantic_dependency:explicit_result_appraisal',
            'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked')
    def reconstructed(attrs):
        return tuple(value.removeprefix('qualifier:') for value in
            c.project_stage1_source_contract_qualifiers(source_attribute_codes=attrs,
                source_explicit_shift_relation_endpoint=False, stage1_response_schema_version=version))
    def relation(source, target):
        return c.project_stage1_relation_source_contract_qualifiers(
            candidate_kind=c.InterpretationKind.TENSION,
            source_attribute_codes=source, target_attribute_codes=target,
            stage1_response_schema_version=version)
    carried = {'right_qualifier:' + code for code in base}
    for right, expected in (
        (base, carried),
        (base + ('operator:negation',), carried),
        (base + ('source_appraisal_continuing:still',), set()),
        (tuple(code.replace('satisfaction', 'acceptance') for code in base), set()),
        (tuple(code.replace('unmarked', 'slight') for code in base), set()),
    ):
        raw = relation(left, right)
        assert raw == relation(reconstructed(left), reconstructed(right)), right
        assert set(raw) == expected


def _reasoned_appraisal_source(plan):
    from emlis_ai_grounded_observation_plan import source_owned_result_appraisal_reason
    return tuple((r, reason) for r in plan.relations
                 if (reason := source_owned_result_appraisal_reason(r, plan.nuclei, plan.relations)) is not None)


@pytest.mark.parametrize('reason,evaluation,action', [
    ('探しやすくなった', '満足した', ''),
    ('必要な資料を探しやすくなった', '満足した', ''),
    ('必要な資料を探しやすくなった', '満足した', '植木に水をやった。'),
    ('必要な資料を探しやすくなった', '満足している', '机を拭いた。'),
    ('資料を探しやすい', '満足している', ''),
    ('資料を探しやすかった', '満足した', ''),
    ('資料を使いやすくなっている', '満足した', ''),
    ('見た目がすっきりした', '満足した', ''),
    ('見た目がはっきりしている', '満足している', ''),
])
def test_explicit_reason_owns_selected_scope_and_actual_reception(reason, evaluation, action):
    from cocolon_meaning_experience_engine import contracts as c
    req = request(reason + 'ので、資料を分類したことに' + evaluation + '。', action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    (about, reason_node), = _reasoned_appraisal_source(plan)
    projection = project_thread_meaning(prepared, plan)
    assert type(projection.structure.meaning_decision_outcome) is c.SelectedEmlisProvisionalReading
    configurations = projection.structure.configurations
    directions = {d.relation_kind: d for config in configurations if isinstance(config, c.RelationalConfiguration)
                  for d in config.direction_rows}
    cause = directions[c.EmlisThreadScopeRelationKind.SATISFACTION_REASON]
    target = directions[c.EmlisThreadScopeRelationKind.ABOUT_TARGET]
    assert cause.schema_version == '1.1' and target.schema_version == '1.0'
    assert cause.target_endpoint_ref == target.target_endpoint_ref
    assert cause.source_endpoint_ref != target.source_endpoint_ref
    assert {d for d in c.ForegroundScopeRelationKind} == {
        c.ForegroundScopeRelationKind.CONTRAST, c.ForegroundScopeRelationKind.COEXISTENCE,
        c.ForegroundScopeRelationKind.CONTINUATION, c.ForegroundScopeRelationKind.CORRECTION}
    selected = projection.selected_reception
    decision, = selected.decisions
    content = decision.subjective_proposition.appraisal_content
    assert type(content) is c.EmlisAppraisalContent
    assert content.dimension == c.AppraisalDimension.MATERIAL_WEIGHT
    assert content.operation == c.AppraisalOperation.RECEIVE_AS_MATERIAL
    assert len(content.appraised_bindings) == 3 and not content.protected_bindings
    assert content.focal_relation_ref == cause.relation_ref
    basis = {b.binding_ref: b.semantic_ref for b in decision.basis_rows}
    semantic_map = dict(selected.semantic_nucleus_pairs)
    assert {semantic_map[basis[ref]] for ref in content.appraised_bindings} == {
        reason_node.nucleus_id, about.from_nucleus_id, about.to_nucleus_id}
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    body = outcome.artifact
    assert reason + '点に' in body.reception
    assert '資料を分類したことへの' in body.reception
    assert ('当時の満足' if evaluation == '満足した' else '入力した時点での満足') in body.reception
    assert '拠り所' in body.reception and '植木' not in body.reception and '机を拭' not in body.reception
    assert not any(word in body.reception for word in ('成功', '成長', '目的', '目標', '唯一', '最も', 'おかげ'))
    if action:
        assert action.rstrip('。') in body.observation


@pytest.mark.parametrize('memo', [
    '必要な資料を探しやすくなったので、資料を分類したことに満足しなかった。',
    '必要な資料を探しやすくなったので、資料を分類したことに少し満足した。',
    '必要な資料を探しやすくなったので、資料を分類したことに納得した。',
    '必要な資料を探しやすくしたかったので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなる予定なので、資料を分類したことに満足した。',
    '必要な資料を探しやすくならなかったので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったからではなく、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったなら、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったら、資料を分類したことに満足した。',
    '同僚が必要な資料を探しやすくなったので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったので、同僚が資料を分類したことに満足した。',
    '同僚は仕事を終えた。必要な資料を探しやすくなったので、資料を分類したことに満足した。',
    '「必要な資料を探しやすくなったので、資料を分類したことに満足した」と聞いた。',
    '必要な資料を探しやすくなったらしいので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったので、資料を分類したことに満足したかもしれない。',
    '必要な資料を探しやすくなったので、資料を分類したことに満足した？',
    '必要な資料を探しやすくなったので、資料を分類したことに満足し',
    '資料を分類できて満足した。必要な資料を探しやすくなったからだ。',
    '必要な資料を探しやすくなり、見た目がすっきりしたので、資料を分類したことに満足した。',
    '結論は出ていないが、必要な資料を探しやすくなったので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったので、嬉しかった。資料を分類したことに満足した。',
])
def test_reason_scope_does_not_admit_nonfact_foreign_unbound_or_multiple_reasons(memo):
    from cocolon_meaning_experience_engine import contracts as c
    p = prepare_emlis_meaning(request(memo))
    plan = build_updated_grounded_plan(p)
    assert not _reasoned_appraisal_source(plan)
    # The unchanged pre-reason engine also stops for this uncertain appraisal.
    # Exclusion does not imply every out-of-scope input has a body.
    if memo.endswith('満足したかもしれない。'):
        from cocolon_meaning_experience_engine.emlis_stage1_composition import Stage1CompositionError
        with pytest.raises(Stage1CompositionError, match='LIMITED_RECEPTION_CAPABILITY_GAP_STOP'):
            project_thread_meaning(p, plan)
        return
    projection = project_thread_meaning(p, plan)
    assert all(row.relation_kind is not c.EmlisThreadScopeRelationKind.SATISFACTION_REASON
               for row in projection.premeaning.source_relation_rows)


def test_reason_removal_and_replacement_change_the_received_aspect_without_action_bias():
    first = '必要な資料を探しやすくなったので、資料を分類したことに満足した。'
    second = '見た目がすっきりしたので、資料を分類したことに満足した。'
    artifacts = [MeaningExperienceEngine().generate(request(first, action)).artifact
                 for action in ('', '植木に水をやった。', '机を拭いた。')]
    assert all(artifacts) and len({a.reception for a in artifacts}) == 1
    changed = MeaningExperienceEngine().generate(request(second, '')).artifact
    removed = MeaningExperienceEngine().generate(request('資料を分類したことに満足した。', '')).artifact
    assert changed and removed
    assert '探しやす' not in changed.reception and '見た目がすっきりした' in changed.reception
    assert '拠り所' not in removed.reception
    assert len({artifacts[0].reception, changed.reception, removed.reception}) == 3


@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
def test_reason_reader_rejects_role_polarity_time_and_invented_cause_without_author(monkeypatch, evaluation):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    req = request('必要な資料を探しやすくなったので、資料を分類したことに' + evaluation + '。')
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    selected = project_thread_meaning(p, plan).selected_reception
    resolver = p.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    artifact = MeaningExperienceEngine().generate(req).artifact
    assert artifact is not None
    reception = artifact.reception
    time = '当時の' if evaluation == '満足した' else '入力した時点での'
    mutations = (
        reception.replace('必要な資料を探しやすくなった点に、', ''),
        reception.replace('探しやすくなった', '探しにくくなった'),
        reception.replace('探しやすくなった', '探しやすくしたかった'),
        reception.replace('資料を分類したことへの', '資料を探しやすくなったことへの'),
        reception.replace('資料を分類したことへの', '資料を分類しなかったことへの'),
        reception.replace(time, '回答した時点での'),
        reception.replace('満足', '納得'),
        reception.replace('拠り所', '唯一の拠り所'),
        reception.replace('拠り所が見えます', '理由は分類が探しやすさを生んだことです'),
    )
    def whole_valid(body):
        return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert whole_valid(artifact.text)
    for wrong in mutations:
        assert wrong != reception and not whole_valid(artifact.text.replace(reception, wrong))
    move, = plan.response_plan.human_reception_plan.moves
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence',
        lambda *_a, **_k: pytest.fail('independent reason reader invoked author'))
    assert read_source_owned_discourse(reception, move, plan, resolver, selected) is not None
    for wrong in mutations:
        assert read_source_owned_discourse(wrong, move, plan, resolver, selected) is None


def test_reason_private_scope_rejects_missing_markers_wrong_direction_and_old_row_version():
    from cocolon_meaning_experience_engine import contracts as c
    from cocolon_meaning_experience_engine.emlis_input_specific_meaning import (
        derive_grounded_situation_view, validate_grounded_situation_view)
    p = prepare_emlis_meaning(request('必要な資料を探しやすくなったので、資料を分類したことに満足した。'))
    pre = project_thread_meaning(p, build_updated_grounded_plan(p)).premeaning
    view = derive_grounded_situation_view(pre)
    reason, = (r for r in view.source_connected_relations
               if r.relation_kind is c.EmlisThreadScopeRelationKind.SATISFACTION_REASON)
    for wrong in (replace(reason, schema_version='1.0'),
                  replace(reason, source_object_ref=reason.target_object_ref, target_object_ref=reason.source_object_ref)):
        with pytest.raises(c.CMEEStage1ContractError):
            validate_grounded_situation_view(replace(view, source_connected_relations=tuple(
                wrong if r == reason else r for r in view.source_connected_relations)), pre, pre.grounded_graph)
    missing = replace(pre, source_qualifier_rows=tuple(replace(row, qualifier_refs=tuple(
        code for code in row.qualifier_refs if code != 'qualifier:semantic_role:appraisal_explicit_reason'))
        for row in pre.source_qualifier_rows))
    with pytest.raises(c.CMEEStage1ContractError):
        derive_grounded_situation_view(missing)


# Full initial checkpoints and bodies captured from unmodified 70030c8.
_PRE_REASON_CHECKPOINTS = [{'memo': '必要な資料を探しやすくなったので、資料を分類したことに満足した。', 'action': '', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-b597ecbecc340a9963e14b6b47c3b0b286a59d90a3a2f7f7544c5d5b7c90b537', 'source_prefix_ref': 'emlis-q3-source-prefix-930c34231cc163f6ba2efc307f61ea68a9d173d7b7659b0abb8e6aaf4cd64b10', 'base_meaning_ref': 'emlis-base-meaning-9a80755822363f8a16207487a9fb85409b0e7859813d4e2cd585c71195869020', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n今の入力には、「必要な資料を探しやすくなったので、資料を分類したことに満足した」という変化があります。\n\nEmlisから：\nその変化を感じています。', 'reason_codes': ['no_bound_personal_meaning_target']}, {'memo': '必要な資料を探しやすくなったので、資料を分類したことに満足した。', 'action': '植木に水をやった。', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-b45aa68e607fcb3b758407edf780e37005b9dbf723a87acc011fa0c4542a81c6', 'source_prefix_ref': 'emlis-q3-source-prefix-e2e7412d98c7e57cf0468d1be18b1287c0244ce66fc494fa457a15c3afe944b5', 'base_meaning_ref': 'emlis-base-meaning-b03ae1451d179bcb6574231c0fc6394e61e5b1aeaa18b4fe426bc22c8866f63a', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n今の入力には、「必要な資料を探しやすくなったので、資料を分類したことに満足した」という変化があります。\n今の入力には、「植木に水をやった」という行動があります。\n\nEmlisから：\n必要な資料を探しやすくなったので、資料を分類したことに満足したという変化を見過ごさず、受け止めています。植木に水をやったことを大切に思っています。', 'reason_codes': ['no_bound_personal_meaning_target']}, {'memo': '見た目がすっきりしたので、資料を分類したことに満足した。', 'action': '', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-dd767d841877d2c9842d5a6dafd9c78608fea5a5823d72a5623d57d96ef519c7', 'source_prefix_ref': 'emlis-q3-source-prefix-b3844a7b9c54869587232d52f59e54714fec97dd3222ce2df5b6ce6308b9baff', 'base_meaning_ref': 'emlis-base-meaning-c1b80f865e8e57dde46598acfff86a072cdbee258ac48fbb110b5d29fa76f567', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n今の入力には、「見た目がすっきりしたので、資料を分類したことに満足した」という行動があります。\n\nEmlisから：\n実際の行動に目が留まり、それを大切に思っています。', 'reason_codes': ['no_bound_personal_meaning_target']}, {'memo': '見た目がすっきりしたので、資料を分類したことに満足した。', 'action': '植木に水をやった。', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-54f78d378cc08a8cd9622ba177c88b7fd0d1e993f898a4329e54ad0783a00c36', 'source_prefix_ref': 'emlis-q3-source-prefix-91584b3aed2d492e14bc7887a80778eb75ad07f888a18146b229e415482891c9', 'base_meaning_ref': 'emlis-base-meaning-0caed104231c7eef3efd571a8d18ca0d0ca77c98d820a50899b972076d8300f6', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': None, 'reason_codes': ['emlis_q3_initial_body_unavailable']}]


@pytest.mark.parametrize('row', _PRE_REASON_CHECKPOINTS)
def test_saved_pre_reason_checkpoint_retains_complete_meaning_and_body(row):
    from emlis_thread_service import _json
    req = request(row['memo'], row['action'])
    saved = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(saved)
    assert p.legacy_appraisal_reason and not p.legacy_result_appraisal
    assert _json(p.checkpoint) == row['checkpoint']
    assert not _reasoned_appraisal_source(build_updated_grounded_plan(p))
    old = MeaningExperienceEngine().generate(saved)
    assert (old.artifact.text if old.artifact else None) == row['body']
    assert list(old.reason_codes) == row['reason_codes']
    fresh = prepare_emlis_meaning(req)
    assert not fresh.legacy_appraisal_reason
    assert fresh.checkpoint.source_prefix_ref == row['checkpoint']['source_prefix_ref']
    assert fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    assert len(_reasoned_appraisal_source(build_updated_grounded_plan(fresh))) == 1
    current = MeaningExperienceEngine().generate(req)
    assert current.artifact and '満足の拠り所' in current.artifact.reception
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)


@pytest.mark.parametrize('memo', [
    '必要な資料を探しやすくなったので、資料を分類したことに満足した。',
    '必要な資料を探しやすくなったから、資料を分類したことに満足している。',
    '見た目がすっきりしたので、資料を分類したことに満足した。',
    '資料を探しやすいので、資料を分類したことに満足している。',
])
def test_reason_appraisal_saved_body_reopens_without_author(qcase, qdb, memo):
    test_selected_appraisal_saved_body_is_read_without_regeneration(qcase, qdb, memo)


def test_reason_relation_qualifiers_survive_direct_projection_without_widening_generic_cause():
    from cocolon_meaning_experience_engine import contracts as c
    version = c.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    common = ('semantic_dependency:explicit_result_appraisal', 'semantic_dependency:reasoned_result_appraisal')
    reason = (*common, 'semantic_role:appraisal_explicit_reason')
    evaluation = (*common, 'source_appraisal_kind:satisfaction', 'source_appraisal_degree:unmarked')
    def direct(codes):
        return tuple(value.removeprefix('qualifier:') for value in
            c.project_stage1_source_contract_qualifiers(source_attribute_codes=codes,
                source_explicit_shift_relation_endpoint=False, stage1_response_schema_version=version))
    def relation(left, right):
        return c.project_stage1_relation_source_contract_qualifiers(candidate_kind=c.InterpretationKind.SOURCE_STATED_CAUSE,
            source_attribute_codes=left, target_attribute_codes=right, stage1_response_schema_version=version)
    assert relation(reason, evaluation) == relation(direct(reason), direct(evaluation))
    assert 'cause_qualifier:semantic_role:appraisal_explicit_reason' in relation(reason, evaluation)
    assert 'effect_qualifier:source_appraisal_kind:satisfaction' in relation(reason, evaluation)
    assert relation((), evaluation) == ()
    assert c.project_foreground_scope_relation_kind('user_stated_cause',
        relation_operators=(c.RelationOperator.SOURCE_EXPLICIT_CAUSE,)) is None


@pytest.mark.parametrize('memo,admitted', [
    ('同僚は仕事を終えた。必要な資料を探しやすくなったので、私は資料を分類したことに満足した。', False),
    ('同僚は仕事を終えた。私は必要な資料を探しやすくなったので、資料を分類したことに満足した。', True),
])
def test_reason_owner_reset_must_start_at_the_reason(memo, admitted):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request(memo)))
    assert bool(_reasoned_appraisal_source(plan)) is admitted


def test_reason_scope_rejects_conflicting_owner_and_different_evidence():
    from cocolon_meaning_experience_engine import contracts as c
    from cocolon_meaning_experience_engine.emlis_input_specific_meaning import derive_grounded_situation_view
    p = prepare_emlis_meaning(request('必要な資料を探しやすくなったので、資料を分類したことに満足した。'))
    pre = project_thread_meaning(p, build_updated_grounded_plan(p)).premeaning
    reason_row, = (row for row in pre.source_qualifier_rows
        if 'qualifier:semantic_role:appraisal_explicit_reason' in row.qualifier_refs)
    conflicting = replace(pre, source_qualifier_rows=tuple(
        replace(row, qualifier_refs=(*row.qualifier_refs, 'actor:other')) if row == reason_row else row
        for row in pre.source_qualifier_rows))
    graph = pre.grounded_graph
    cause, = (edge for edge in graph.edges if edge.relation == 'user_stated_cause')
    wrong_evidence = replace(pre, grounded_graph=replace(graph, edges=tuple(
        replace(edge, evidence_ids=('foreign-evidence',)) if edge == cause else edge for edge in graph.edges)))
    for wrong in (conflicting, wrong_evidence):
        with pytest.raises(c.CMEEStage1ContractError):
            derive_grounded_situation_view(wrong)


def test_reason_reader_requires_selected_three_bindings_and_reason_focal_relation():
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    req = request('必要な資料を探しやすくなったので、資料を分類したことに満足した。')
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    selected = project_thread_meaning(p, plan).selected_reception
    decision, = selected.decisions
    proposition = decision.subjective_proposition
    content = proposition.appraisal_content
    body = MeaningExperienceEngine().generate(req).artifact.reception
    move, = plan.response_plan.human_reception_plan.moves
    for wrong in (replace(content, appraised_bindings=content.appraised_bindings[:2]),
                  replace(content, focal_relation_ref='foreign-relation')):
        mutated = replace(selected, decisions=(replace(decision,
            subjective_proposition=replace(proposition, appraisal_content=wrong)),))
        assert read_source_owned_discourse(body, move, plan, p.thread.resolver(), mutated) is None


_PRE_REASON_MIXED_CHECKPOINT = {'memo': '必要な資料を探しやすくなったので、資料を分類したことに満足した。', 'action': '案を選んで満足した。', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-17c6594cf23755894ededf9f93314b31c9da8f3deaf67ba539c4944a924c7aed', 'source_prefix_ref': 'emlis-q3-source-prefix-350e912098136659fd71db4a23eed2ddd00c8d4fae0e746ab8225fe7ef686b6c', 'base_meaning_ref': 'emlis-base-meaning-575eb2a22adf8c93ab7ddb527146549366b7fa7a41bcf7d7a5ecae0075347772', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}}


def test_saved_pre_reason_checkpoint_keeps_other_existing_appraisals():
    from emlis_thread_service import _json
    row = _PRE_REASON_MIXED_CHECKPOINT
    req = request(row['memo'], row['action'])
    saved = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(saved)
    assert p.legacy_appraisal_reason and not p.legacy_result_appraisal
    assert _json(p.checkpoint) == row['checkpoint']
    plan = build_updated_grounded_plan(p)
    assert not _reasoned_appraisal_source(plan)
    assert len([r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]) == 1


_PRE_REASON_Q1_CHECKPOINT = {'memo': '必要な資料を探しやすくなったので、資料を分類したことに満足した。', 'action': '', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-34cd00df38498f1a09299486c83af58bb766d68f5198e69e954035088cd34657', 'source_prefix_ref': 'emlis-source-prefix-ac530874d05fd82f25ed755333fd0b1d1641f1ecb58b105009a973c1e487ca01', 'base_meaning_ref': 'emlis-base-meaning-9a80755822363f8a16207487a9fb85409b0e7859813d4e2cd585c71195869020', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n今の入力には、「必要な資料を探しやすくなったので、資料を分類したことに満足した」という変化があります。\n\nEmlisから：\nその変化を感じています。', 'reason_codes': ['no_bound_personal_meaning_target']}


def test_saved_q1_pre_reason_checkpoint_uses_its_prepared_plan():
    from emlis_thread_service import _json
    row = _PRE_REASON_Q1_CHECKPOINT
    req = initial(row['memo'], row['action'])
    saved = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(saved)
    assert p.legacy_appraisal_reason and _json(p.checkpoint) == row['checkpoint']
    old = MeaningExperienceEngine().generate(saved)
    assert (old.artifact.text if old.artifact else None) == row['body']
    assert list(old.reason_codes) == row['reason_codes']
    fresh = MeaningExperienceEngine().generate(req)
    assert fresh.artifact and '満足の拠り所' in fresh.artifact.reception


@pytest.mark.parametrize('received,appraisal,polarity,time', [
    ('褒められたのに、嬉しくなかった。', '資料を分類できて満足した。', 'positive', 'past'),
    ('先生に褒められたのに、嬉しくなかった。', '資料を分類できて満足しなかった。', 'negative', 'past'),
    ('私は先生に褒められたのに、嬉しくなかった。', '資料を分類したことに少し満足しています。', 'positive', 'present'),
    ('誘われたのに、悲しかった。', '資料を分類したことにまだ納得していない。', 'negative', 'present'),
])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_received_context_keeps_same_field_appraisal_in_actual_body(received, appraisal, polarity, time, field):
    req = request(received + appraisal if field == 'memo' else '',
                  '植木に水をやった。' if field == 'memo' else received + appraisal)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    relation, = (r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei))
    index = {n.nucleus_id: n for n in plan.nuclei}
    target, evaluation = (index[nid] for nid in (relation.from_nucleus_id, relation.to_nucleus_id))
    assert target.source_fields == evaluation.source_fields == (field,)
    assert target.source_span_ids == evaluation.source_span_ids
    assert (evaluation.semantic_frame.polarity, evaluation.semantic_frame.time_scope) == (polarity, time)
    assert prepared.thread.resolver().resolve(target.source_span_ids[0]).raw_text == appraisal.rstrip('。')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert '資料を分類' in out.artifact.reception
    assert ('納得' if '納得' in appraisal else '満足') in out.artifact.reception
    assert received.split('のに')[0].replace('私は', 'あなたは') in out.artifact.reception
    assert ('当時は' if time == 'past' else '入力した時点では') in out.artifact.reception
    assert ('満足しなかった' in out.artifact.reception) == ('満足しなかった' in appraisal)
    assert ('まだ納得していない' in out.artifact.reception) == ('まだ納得していない' in appraisal)
    assert out.question is not None and out.question.decision.target_kind == 'PERSONAL_RECEIVED_MEANING'
    if field == 'memo':
        assert '植木に水をやった' in out.artifact.observation


@pytest.mark.parametrize('prefix,suffix', [
    ('同僚が褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('同僚は私に褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('同僚が私に褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('同僚も先生に褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('同僚は仕事を終えた。褒められたのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。', '資料を分類できて満足した。'),
    ('褒められたのに、嬉しくなかったけど、悲しかった。', '資料を分類できて満足した。'),
    ('「褒められたのに、嬉しくなかった。」', '資料を分類できて満足した。'),
    ('褒められたら、嬉しくなかった。', '資料を分類できて満足した。'),
    ('褒められなかったのに、嬉しくなかった。', '資料を分類できて満足した。'),
    ('褒められたのに、嬉しくなかった。', '探しやすくなったので、資料を分類したことに満足した。'),
    ('褒められたのに、嬉しくなかった。', '結論はまだ出ていないけど、資料を分類したことに満足した。'),
])
def test_received_context_does_not_erase_foreign_or_add_another_semantic_scope(prefix, suffix):
    plan = prepare_emlis_meaning(request(prefix + suffix)).original_plan
    assert not any(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations)


@pytest.mark.parametrize('giver', ['私', '自分', '自分自身', '私たち', '先生と私'])
def test_received_context_self_giver_does_not_prove_self_receiver(giver):
    plan = prepare_emlis_meaning(request(giver + 'に褒められたのに、嬉しくなかった。資料を分類できて満足した。')).original_plan
    assert not any(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations)


@pytest.mark.parametrize('answer,operation,retained,absent', [
    ('その時は重かった。', 'ADD', '満足した', '今は満足'),
    ('「満足した」ではなく「満足しなかった」です。', 'REVISE', '満足しなかった', '「満足した」'),
    ('「満足した」ではなく「今は満足していない」です。', 'REVISE', '回答した時点', '当時は満足した'),
    ('「満足した」は誤りです。', 'WITHDRAW', '資料を分類', '満足'),
    ('「資料を分類できて満足した」は誤りです。', 'WITHDRAW', '褒められた', '資料を分類'),
])
def test_received_context_current_question_answer_keeps_appraisal_correction_and_withdrawal(answer, operation, retained, absent):
    from test_cmee_emlis_q3_thread import advance
    req = advance(request('褒められたのに、嬉しくなかった。資料を分類できて満足した。'), answer)
    p = prepare_emlis_meaning(req)
    assert not p.legacy_received_appraisal_context
    assert p.checkpoint.assessment_status == 'RESOLVED'
    assert any(u.operation == operation for u in p.checkpoint.answer_update.updates)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert retained in out.artifact.text and absent not in out.artifact.text
    assert '植木に水をやった' in out.artifact.observation
    assert '褒められた' in out.artifact.text


def test_received_context_actual_body_inverse_rejects_swapped_target_or_appraisal():
    req = request('褒められたのに、嬉しくなかった。資料を分類できて満足した。')
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    projection = project_thread_meaning(p, plan)
    sentence = build_grounded_sentence_plan(plan, p.thread.resolver(), recovery_stage='full')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    body = out.artifact.text
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=p.thread.resolver(),
            selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    reception = out.artifact.reception
    for changed in (reception.replace('資料を分類できた', '植木に水をやった'),
                    reception.replace('満足した', '満足しなかった'),
                    reception.replace('当時は', '回答した時点では'),
                    reception.split('。', 1)[1]):
        assert changed != reception and not valid(body.replace(reception, changed))


# Full initial/answered checkpoints captured from unmodified ba6a7ad.
_PRE_RECEIVED_CONTEXT_CHECKPOINTS = [{'case_id': 'Q1_INTERNAL', 'memo': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'action': '植木に水をやった。', 'capability': 'FREE_Q1', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-50298d28282168d1862a9660d3aa22be40c402c58f5dbd72592be34207f335eb', 'source_prefix_ref': 'emlis-source-prefix-3922745fbbb1982bdb2c39e78a7098756df54561d397281a5afa634a6cfd6529', 'base_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n今の入力では、「褒められた」と「嬉しくなかった」の異なる向きが確認できます。 あわせて、「資料を分類できて満足した」と「植木に水をやった」という行動も今の状態として見えます。\n\nEmlisから：\n植木に水をやったことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_question_candidate_ready'], 'question': {'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s3'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'body_state': 'PRE_QUESTION'}, {'case_id': 'Q3_FREE', 'memo': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'action': '植木に水をやった。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-b9744c701ebcbf9fe66592aaa9fbba84731556b304252c7c88254e1bb26f9a00', 'source_prefix_ref': 'emlis-q3-source-prefix-6d5370305e436d8f59d32084768e1c51cd4a62e07ef8394c02b3bc1011025331', 'base_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n今回の中心には、「資料を分類できて満足した」があります。\n今の入力には、「植木に水をやった」という行動があります。\n\nEmlisから：\n植木に水をやったことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_question_candidate_ready'], 'question': {'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'body_state': 'PRE_QUESTION'}, {'case_id': 'Q3_FREE_answer0', 'memo': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'action': '植木に水をやった。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-94712ae2777b847a97f2e23e058a2ed5aa562313037c732568a06cbe40b71a0e', 'source_prefix_ref': 'emlis-q3-source-prefix-ecfa09274bc4d9759de0c6f1bf7364e673c3fc2cf70ab4f59edc1ce08d812ac3', 'base_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'answer_update': {'answer_source_ref': 'src-032fc6927f68fd4f4455b8fd', 'question_ref': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'prior_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'updates': [{'update_ref': 'emlis-update-7c7e0349f9149ab96a96406b80e745c1345047c4297bb517dea11e21a863d7f9', 'binding_kind': 'QUESTION_FOCUS', 'target_meaning_refs': ['nucleus:s1:event'], 'evidence_refs': ['ev-9f5ac1de3b536110aed18571'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'time_expression_evidence_refs': ['ev-9f5ac1de3b536110aed18571'], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'ADD', 'changed_claim_refs': ['answer:s7'], 'superseded_claim_refs': [], 'affected_dependency_refs': []}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-3ef37cb5eb2b0f20d48f7ffc7b2687bfe7c981e585207507b310a54b4e66bc27'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-7c7e0349f9149ab96a96406b80e745c1345047c4297bb517dea11e21a863d7f9'], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n「褒められた」のに「嬉しくなかった」、その時は「重かった」とあります。\n今回の中心には、「資料を分類できて満足した」があります。\n今の入力には、「植木に水をやった」という行動があります。\n\nEmlisから：\n褒められたことについて、その時の重さを小さくせずに受け止めています。植木に水をやったことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_thread_body_generated'], 'question': None, 'body_state': 'REFINED', 'answer': 'その時は重かった。', 'question_control': {'pending_question': {'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'round_index': 1, 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'answer_text_private': 'その時は重かった。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}]}, {'case_id': 'Q3_FREE_answer1', 'memo': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'action': '植木に水をやった。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-08c95d2d5c1784701c250563bc7cf781dadd8a4eb67d97000f7f341935dead95', 'source_prefix_ref': 'emlis-q3-source-prefix-c86e825bd93e27eb8ff1729f1e14528521cde206afc880374b2aca9241ce2ed8', 'base_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'answer_update': {'answer_source_ref': 'src-581c243fb5194eb6e31ca3b1', 'question_ref': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'prior_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'updates': [{'update_ref': 'emlis-update-8e3f1c0486cec94cd3e52c9f8ed3736133c45360fd47edefa43b617e8c8e09d7', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2'], 'evidence_refs': ['ev-fd57614809f3e6bff3a007b6'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s2'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-bf26f278add3084b2ef75d1e921bb5cdf35ed00badba213a21d2b3f03dd0819b'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-8e3f1c0486cec94cd3e52c9f8ed3736133c45360fd47edefa43b617e8c8e09d7'], 'inactive_claim_refs': ['nucleus:s2', 'relation:r1'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n今の入力には、「植木に水をやった」という行動があります。\n\nEmlisから：\n褒められたことは、嬉しさにはつながらなかったのですね。植木に水をやったことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_thread_body_generated'], 'question': None, 'body_state': 'REFINED', 'answer': '「資料を分類できて満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'round_index': 1, 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'answer_text_private': '「資料を分類できて満足した」は誤りです。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}]}, {'case_id': 'Q3_PREMIUM', 'memo': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'action': '植木に水をやった。', 'capability': 'Q3_PREMIUM', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-c3ebc7741b46f12ad1c37153626063b821bc8a94b5648096cf90f4a59dd236f2', 'source_prefix_ref': 'emlis-q3-source-prefix-ad188b31a428f5796dd1eda7425b8a6241cdfda81c25bcf2d2fd88b1b61501d8', 'base_meaning_ref': 'emlis-base-meaning-7c4d3523fb1277f37792806b61f8891bfd4e5d62573c5d28067e1e7e61544d6a', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n今回の中心には、「資料を分類できて満足した」があります。\n今の入力には、「植木に水をやった」という行動があります。\n\nEmlisから：\n植木に水をやったことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_question_candidate_ready'], 'question': {'question_id': 'emlis-question-7c4d75bb689070364534ff37d4849c624d4044a5b026c95794afb05932129862', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-ca09d181c2f7df9b29f2277d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-5aa8fd0d07b51875f61dfc1e0dd46405d7c0a6beccb9f418dfa07d9f295c850e', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-06d0b9689a43c6e022f872c9'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'body_state': 'PRE_QUESTION'}, {'case_id': 'same_action', 'memo': '', 'action': '褒められたのに、嬉しくなかった。資料を分類できて満足した。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-ed9d2d8650f1587e5762fa86ab796056f3ac307e1a1a68ebc2e93ba6328c374e', 'source_prefix_ref': 'emlis-q3-source-prefix-a71b4314e8b04d1a74601ed6adb71fd3b92f1c5ddd28e88efa0db4d0d0af48f3', 'base_meaning_ref': 'emlis-base-meaning-bf0658d4bd65b7cfc1a65406bc446ecd2d966b418e1eb3cc6e34010826f10889', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n今の入力には、「資料を分類できて満足した」という行動があります。\n\nEmlisから：\n褒められたことは、嬉しさにはつながらなかったのですね。資料を分類できて満足したことを見過ごさず、大切に受け止めています。', 'reason_codes': ['emlis_question_candidate_ready'], 'question': {'question_id': 'emlis-question-0870f2eab94823fe803ecbcb84a61c01db199ac8a479ca05029de1d712177d47', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-908efa402a4ba2a38fddd42c', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-6b81c5bd74e53b320e15a5fbe49bbd18d12f161f291c77340698d1f493eb4bcd', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-c2e96a60cfd0500c91719499'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'body_state': 'PRE_QUESTION'}]


@pytest.mark.parametrize('row', _PRE_RECEIVED_CONTEXT_CHECKPOINTS, ids=lambda row: row['case_id'])
def test_received_context_saved_checkpoint_body_and_question_are_rederived_exactly(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    p = prepare_emlis_meaning(req)
    assert p.legacy_received_appraisal_context and not p.legacy_appraisal_reason
    assert _json(p.checkpoint) == row['checkpoint']
    out = MeaningExperienceEngine().generate(req)
    if row['capability'] == 'FREE_Q1':
        # Q1 previously used the generic observation surface. A restored
        # checkpoint must now render its old prepared meaning, rather than
        # rebuild current appraisal meaning under that old checkpoint ID.
        assert out.artifact and out.artifact.reception == row['body'].split('Emlisから：\n')[1]
        assert not any(source_owned_result_appraisal(r, p.original_plan.nuclei) for r in p.original_plan.relations)
        assert all(text in out.artifact.observation for text in
            ('褒められた', '嬉しくなかった', '資料を分類できて満足した', '植木に水をやった'))
    else:
        assert (out.artifact.text if out.artifact else None) == row['body']
    assert _json(out.meaning_checkpoint) == row['checkpoint']
    assert _json(out.question) == row['question']
    assert list(out.reason_codes) == row['reason_codes'] and out.body_state == row['body_state']
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)


@pytest.mark.parametrize('row', [r for r in _PRE_RECEIVED_CONTEXT_CHECKPOINTS if 'answer' in r],
                         ids=lambda row: row['case_id'])
def test_received_context_old_issued_question_is_revalidated_before_new_answer(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row, checkpoint=False)
    p = prepare_emlis_meaning(req)
    # This question's full source-bound focus is unchanged and is canonical
    # under the current plan too. A new, unsaved answer uses current meaning;
    # only a complete old checkpoint selects legacy reconstruction.
    assert not p.legacy_received_appraisal_context
    assert _json(p.checkpoint) != row['checkpoint']
    assert any(source_owned_result_appraisal(r, p.original_plan.nuclei) for r in p.original_plan.relations)
    out = MeaningExperienceEngine().generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=p.checkpoint.checkpoint_id)))
    assert out.artifact is not None and _json(out.meaning_checkpoint) == _json(p.checkpoint)
    control = req.emlis_thread.question_control_context
    wrong = replace(control.pending_question, prompt_private='別の質問')
    tampered = replace(req, emlis_thread=replace(req.emlis_thread, question_control_context=replace(
        control, pending_question=wrong, issued_questions=(wrong,))))
    with pytest.raises(ValueError, match='emlis_question_noncanonical'):
        prepare_emlis_meaning(tampered)


# Captured on unmodified 26d8ccc7, with genuine issued questions and the entire
# unresolved/partially accepted checkpoint; never substitute a historical ID.
_PRE_REASON_WITHDRAWAL_CHECKPOINTS = [{'case_id': 'u266-reason-False-False', 'memo': '探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-43ee2060c472935c54b42d58'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'affected_reception_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-43ee2060c472935c54b42d58'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'affected_reception_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'round_index': 1, 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-4536c98d652156a44859e4cfc8369e5371397c17cac5fdb90e8be6124d3ed208', 'source_prefix_ref': 'emlis-q3-source-prefix-de1d11aee9e1016a8b106a323f0473467a5feacf309822518fa4a16241adce0a', 'base_meaning_ref': 'emlis-base-meaning-134bb4523c89421ce1bec0b36930797d7ee8d50accec6c42fbed431cf1ee9195', 'answer_update': {'answer_source_ref': 'src-27616755bf66f298cfc725b5', 'question_ref': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'prior_meaning_ref': 'emlis-base-meaning-134bb4523c89421ce1bec0b36930797d7ee8d50accec6c42fbed431cf1ee9195', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-8260e14dd182f0a3eb0d3815'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-134bb4523c89421ce1bec0b36930797d7ee8d50accec6c42fbed431cf1ee9195'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-8260e14dd182f0a3eb0d3815'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved']}, {'case_id': 'u266-reason-False-True', 'memo': '探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-43ee2060c472935c54b42d58'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'affected_reception_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-9620cf9a29241334fe20ce15067be7392840155bbef5be533041d192fb65ed32', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-43ee2060c472935c54b42d58'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'affected_reception_refs': ['nucleus:s2:event', 'nucleus:s2:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'round_index': 1, 'original_source_ref': 'src-86bd0775dfe56d124598f10b', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-7b5fe8958df3a8812299a969bb0df8f8818794b1f4c1e28c3041a1ce6e4d869d', 'source_prefix_ref': 'emlis-q3-source-prefix-fafc7d905190e2c906fb7dbffe36d3d8abe1be97b5bf28b6be3656b2c943cafc', 'base_meaning_ref': 'emlis-base-meaning-134bb4523c89421ce1bec0b36930797d7ee8d50accec6c42fbed431cf1ee9195', 'answer_update': {'answer_source_ref': 'src-1300ecea976ee2a2c146080a', 'question_ref': 'emlis-question-bb17c8b3bd21dfb31976aa91c20224864d3ebb77e57298875b91aff25dfb3d22', 'prior_meaning_ref': 'emlis-base-meaning-134bb4523c89421ce1bec0b36930797d7ee8d50accec6c42fbed431cf1ee9195', 'updates': [{'update_ref': 'emlis-update-b4294de54053f6db66b0d30c89eaeb29e0c29ccaeed01a48292fd43f91664dd4', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2:reaction'], 'evidence_refs': ['ev-f5dbb0a39bb671f94b6abe4b'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-86bd0775dfe56d124598f10b', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s7'], 'superseded_claim_refs': ['nucleus:s2:reaction'], 'affected_dependency_refs': ['relation:r3']}], 'unresolved_parts': [{'evidence_refs': ['ev-d6615882011a15ef952a445f'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-a5bd6339b016db11cdb35136bb04d689efb2226753eae460e79ffd62c21692f1'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-b4294de54053f6db66b0d30c89eaeb29e0c29ccaeed01a48292fd43f91664dd4'], 'inactive_claim_refs': ['nucleus:s2:reaction', 'relation:r3'], 'unresolved_parts': [{'evidence_refs': ['ev-d6615882011a15ef952a445f'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable']}, {'case_id': 'u266-reason-True-False', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-52027c5fbafbb058988f546f'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-52027c5fbafbb058988f546f'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'round_index': 1, 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-52af18cefb6900e570f011c40c6caecfb95fa72f867408c547ef8a6bde164d40', 'source_prefix_ref': 'emlis-q3-source-prefix-683d56568d31cf3615ccdea2a3493acd20f34ecc8758c6e994a7a96e7bb284a5', 'base_meaning_ref': 'emlis-base-meaning-ae03eb02b2f577ce6cf6bfa956d0c41642e37eabc46ca065995cfc430af19d18', 'answer_update': {'answer_source_ref': 'src-23cd787329f7f2a42ea3bc4d', 'question_ref': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'prior_meaning_ref': 'emlis-base-meaning-ae03eb02b2f577ce6cf6bfa956d0c41642e37eabc46ca065995cfc430af19d18', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-3169e286bdae2996b7240261'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-ae03eb02b2f577ce6cf6bfa956d0c41642e37eabc46ca065995cfc430af19d18'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-3169e286bdae2996b7240261'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved']}, {'case_id': 'u266-reason-True-True', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-52027c5fbafbb058988f546f'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-a4d7a70520df16803fce4ba0b274f49831ecd966e81daa56036baea632179dc7', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-52027c5fbafbb058988f546f'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'answer-1', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'round_index': 1, 'original_source_ref': 'src-d46c89684fb1148689dc3b2d', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T01:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-071010a3fee003ff6bd069cd10474133809b5fbd525b1013c7de17d811ff59b2', 'source_prefix_ref': 'emlis-q3-source-prefix-3064dd6b5e9da7e3b0fee52a60c98ebe35a54a26f64d0e101fb1a574444ecb57', 'base_meaning_ref': 'emlis-base-meaning-ae03eb02b2f577ce6cf6bfa956d0c41642e37eabc46ca065995cfc430af19d18', 'answer_update': {'answer_source_ref': 'src-12ccb18183d8df6e2a078b9e', 'question_ref': 'emlis-question-1e505b83a539b80dd82c997d052bbbb19d0fd047fb0bb21d1668568e9aba7e04', 'prior_meaning_ref': 'emlis-base-meaning-ae03eb02b2f577ce6cf6bfa956d0c41642e37eabc46ca065995cfc430af19d18', 'updates': [{'update_ref': 'emlis-update-db9941f2c5cab1a8191d646b6654d1558ba4f043ef46a8ae7ff47c9026f09110', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s1:reaction'], 'evidence_refs': ['ev-3625ec857b521a0741f71feb'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-d46c89684fb1148689dc3b2d', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s7'], 'superseded_claim_refs': ['nucleus:s1:reaction'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [{'evidence_refs': ['ev-38dff1e4cc25cbbefcfee76f'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-bbad88ac26010459da5ea0b29d138bc3299451cc8c6c3e7fb4030528a594e7b7'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-db9941f2c5cab1a8191d646b6654d1558ba4f043ef46a8ae7ff47c9026f09110'], 'inactive_claim_refs': ['nucleus:s1:reaction', 'relation:r1'], 'unresolved_parts': [{'evidence_refs': ['ev-38dff1e4cc25cbbefcfee76f'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable']}]

@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('basis', ['探しやすくなった', '見た目がすっきりした'])
def test_whole_reason_withdrawal_removes_exactly_its_three_owners(reverse, evaluation, basis):
    from test_cmee_emlis_q3_thread import advance
    from emlis_ai_grounded_observation_plan import source_owned_result_appraisal_reason
    source = basis + 'ので、資料を分類したことに' + evaluation
    received = '褒められたのに、嬉しくなかった。植木に水をやった。'
    req = request(*((received, source + '。') if reverse else (source + '。', received)))
    original = prepare_emlis_meaning(req).original_plan
    relation, = (r for r in original.relations if source_owned_result_appraisal(r, original.nuclei))
    reason = source_owned_result_appraisal_reason(relation, original.nuclei, original.relations)
    assert reason is not None
    removed = {relation.from_nucleus_id, relation.to_nucleus_id, reason.nucleus_id}
    remaining = {n.nucleus_id for n in original.nuclei} - removed
    req = advance(req, f'「{source}」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update, = prepared.checkpoint.answer_update.updates
    assert update.operation == 'WITHDRAW'
    assert set(update.superseded_claim_refs) == removed
    plan = build_updated_grounded_plan(prepared)
    assert {n.nucleus_id for n in plan.nuclei} == remaining
    assert {r.relation_id for r in plan.relations} == {
        r.relation_id for r in original.relations
        if r.from_nucleus_id not in removed and r.to_nucleus_id not in removed}
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert '褒められた' in outcome.artifact.text and '植木に水をやった' in outcome.artifact.text
    for absent in (basis, '資料を分類', '満足'):
        assert absent not in outcome.artifact.text


@pytest.mark.parametrize('quoted', ['資料を分類したことに', '探しやすく',
    '探しやすくなったので、資料を分類したことに満足',
    '見つけやすくなったので、資料を分類したことに満足した'])
def test_reason_withdrawal_does_not_expand_partial_or_foreign_quotes(quoted):
    from test_cmee_emlis_q3_thread import advance
    req = advance(request('探しやすくなったので、資料を分類したことに満足した。',
        '褒められたのに、嬉しくなかった。'), f'「{quoted}」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
    assert not prepared.checkpoint.inactive_claim_refs
    assert not prepared.checkpoint.answer_update.updates


@pytest.mark.parametrize('target', ['資料を分類した', '満足した', '探しやすくなった'])
def test_single_reason_owner_withdrawal_keeps_other_owner_nuclei(target):
    from test_cmee_emlis_q3_thread import advance
    req = advance(request('探しやすくなったので、資料を分類したことに満足した。',
        '褒められたのに、嬉しくなかった。'), f'「{target}」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update, = prepared.checkpoint.answer_update.updates
    assert len(update.superseded_claim_refs) == 1
    plan = build_updated_grounded_plan(prepared)
    assert {n.nucleus_id for n in plan.nuclei} == (
        {n.nucleus_id for n in prepared.original_plan.nuclei} - set(update.superseded_claim_refs))


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('reason', ['探しやすくなった', '見た目がすっきりした', '資料を使いやすい'])
@pytest.mark.parametrize('received_count', [1, 2])
def test_withdrawn_target_keeps_reason_and_appraisal_in_finite_attention(reverse, evaluation, reason, received_count):
    from test_cmee_emlis_q3_thread import advance
    from emlis_ai_grounded_observation_plan import source_owned_relational_focus
    source = reason + 'ので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    if received_count == 2:
        received += '誘われたのに、悲しかった。'
    req = advance(request(*((received, source) if reverse else (source, received))),
                  '「資料を分類した」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert out.meaning_checkpoint == prepared.checkpoint
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    at = '当時の' if evaluation == '満足した' else '入力した時点での'
    expected = reason + 'という理由と、' + at + '満足とのつながりに目を向けています。'
    if received_count == 1:
        expected += '褒められたことは、嬉しさにはつながらなかったのですね。'
    assert out.artifact.reception == expected
    assert '資料を分類' not in out.artifact.text
    assert evaluation in out.artifact.observation
    assert '褒められた' in out.artifact.observation
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.reception_act == "recognize_lived_change")
    kind, basis, feeling = source_owned_relational_focus(move, plan)
    assert kind == 'withdrawn_target_appraisal_reason'
    assert move.target_nucleus_ids == (feeling.nucleus_id,) and move.support_nucleus_ids == (basis.nucleus_id,)
    decision, = (d for d in selected.decisions if d.reception_act == "recognize_lived_change")
    assert decision.branch == 'LIMITED'
    assert decision.subjective_proposition.subjective_mode == 'ATTENTION'
    if received_count == 1:
        assert len(selected.decisions) == 2
        assert decision.subjective_proposition.appraisal_content.operation == 'RECEIVE_AS_MATERIAL'
        assert decision.subjective_proposition.focal_relation_ref is None
        assert len({d.projected_claim_ref for d in selected.decisions}) == 1
        assert not set(selected.decisions[0].selected_contribution_refs) & set(selected.decisions[1].selected_contribution_refs)
    else:
        # Two received pairs remain outside this bounded retention repair.
        assert len(selected.decisions) == 1
        assert decision.subjective_proposition.appraisal_content.operation == 'PRESERVE_BOTH_ENDPOINTS'
        assert dict(selected.relation_pairs)[decision.subjective_proposition.focal_relation_ref] == next(
            r.relation_id for r in plan.relations if r.type == 'user_stated_cause')
        assert '誘われた' in out.artifact.observation and '悲しかった' in out.artifact.observation


@pytest.mark.parametrize('reverse', [False, True])
def test_withdrawn_target_retention_does_not_admit_an_extra_action(reverse):
    from test_cmee_emlis_q3_thread import advance
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    source = '探しやすくなったので、資料を分類したことに満足した。'
    received = '褒められたのに、嬉しくなかった。植木に水をやった。'
    req = advance(request(*((received, source) if reverse else (source, received))),
                  '「資料を分類した」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert _thread_retained_reaction_groups(plan.nuclei, plan.relations) == ()
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is None
    assert out.reason_codes == ('emlis_refined_body_unavailable',)
    assert out.meaning_checkpoint == prepared.checkpoint


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
def test_withdrawn_target_reason_reader_is_independent_and_rejects_changed_meaning(monkeypatch, reverse, evaluation):
    from test_cmee_emlis_q3_thread import advance
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    source = '私は探しやすくなったので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = advance(request(*((received, source) if reverse else (source, received))),
                  '「資料を分類した」は誤りです。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    clause = out.artifact.reception.split("。", 1)[0] + "。"
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.reception_act == "recognize_lived_change")
    at = '当時の' if evaluation == '満足した' else '入力した時点での'
    wrongs = (
        clause.replace('あなたは探しやすくなったという理由と、', ''),
        clause.replace('探しやすくなった', '探しにくくなった'),
        clause.replace('探しやすくなった', '探しやすくしたかった'),
        clause.replace('あなたは探しやすくなった', '褒められた'),
        clause.replace('あなたは', '上司は'),
        clause.replace('満足', '納得'),
        clause.replace('満足', '不満'),
        clause.replace(at, '回答した時点での'),
        clause.replace(at, '入力した時点での' if at == '当時の' else '当時の'),
        clause.replace('という理由と、', 'という唯一の理由と、'),
        clause.replace('という理由と、', 'という最も大切な理由と、'),
        clause.replace('という理由と、', 'という原因で生じた、'),
        clause.replace('満足とのつながり', '資料を分類したことへの満足とのつながり'),
        clause.replace('目を向けています', '成長を感じています'),
        '満足したという理由と、' + at + '探しやすさとのつながりに目を向けています。',
    )
    def valid(body):
        return evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(out.artifact.text)
    for wrong in wrongs:
        assert wrong != clause and not valid(out.artifact.text.replace(clause, wrong))
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence',
        lambda *_a, **_k: pytest.fail('independent withdrawn-target reader called the author'))
    assert read_source_owned_discourse(clause, move, plan, resolver, selected) is not None
    for wrong in wrongs:
        assert read_source_owned_discourse(wrong, move, plan, resolver, selected) is None


def test_withdrawn_target_reason_focus_requires_the_surviving_source_pair():
    from test_cmee_emlis_q3_thread import advance
    from emlis_ai_grounded_observation_plan import source_owned_relational_focus
    prepared = prepare_emlis_meaning(advance(request(
        '探しやすくなったので、資料を分類したことに満足した。',
        '褒められたのに、嬉しくなかった。'), '「資料を分類した」は誤りです。'))
    plan = build_updated_grounded_plan(prepared)
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.reception_act == "recognize_lived_change")
    _, reason, evaluation = source_owned_relational_focus(move, plan)
    edge, = (r for r in plan.relations if r.type == 'user_stated_cause')
    def without(node, code):
        return replace(node, semantic_frame=replace(node.semantic_frame,
            attribute_codes=tuple(c for c in node.semantic_frame.attribute_codes if c != code)))
    variants = [without(evaluation, 'thread_subject:withdrawn_source_event'),
        without(reason, 'semantic_role:appraisal_explicit_reason'),
        replace(reason, source_fields=('memo_action',)),
        replace(reason, semantic_frame=replace(reason.semantic_frame, modality='hypothetical')),
        replace(evaluation, semantic_frame=replace(evaluation.semantic_frame, actor='other')),
        replace(evaluation, semantic_frame=replace(evaluation.semantic_frame, polarity='negative'))]
    for changed in variants:
        mutated = replace(plan, nuclei=tuple(changed if n.nucleus_id == changed.nucleus_id else n for n in plan.nuclei))
        assert source_owned_relational_focus(move, mutated) is None
    restored = next(n for n in prepared.original_plan.nuclei if n.nucleus_id in
                    prepared.checkpoint.answer_update.updates[0].superseded_claim_refs)
    assert source_owned_relational_focus(move, replace(plan, nuclei=(*plan.nuclei, restored))) is None
    reversed_edge = replace(edge, from_nucleus_id=edge.to_nucleus_id, to_nucleus_id=edge.from_nucleus_id)
    assert source_owned_relational_focus(move, replace(plan,
        relations=tuple(reversed_edge if r == edge else r for r in plan.relations))) is None
    # Naming a finite surface focus must not rewrite pre-selection/reference-mode decisions.
    assert source_owned_relational_focus(move, nuclei=plan.nuclei, relations=plan.relations) is None


def test_withdrawn_target_reason_selected_focal_cannot_borrow_another_experience():
    from test_cmee_emlis_q3_thread import advance
    import emlis_ai_grounded_human_reception as hr
    prepared = prepare_emlis_meaning(advance(request(
        '探しやすくなったので、資料を分類したことに満足した。',
        '褒められたのに、嬉しくなかった。'), '「資料を分類した」は誤りです。'))
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    decision, = (d for d in selected.decisions if d.reception_act == "recognize_lived_change")
    proposition = decision.subjective_proposition
    other = next(ref for ref, rid in selected.relation_pairs if rid == next(
        r.relation_id for r in plan.relations if r.type == 'contrast'))
    other_decision, = (d for d in selected.decisions if d != decision)
    variants = [replace(decision, selected_contribution_refs=()),
        replace(decision, subjective_proposition=replace(proposition, subjective_mode='PERSONAL_APPRAISAL')),
        replace(decision, subjective_proposition=replace(proposition, subjective_operator='VALUE_AS')),
        replace(decision, selected_contribution_refs=other_decision.selected_contribution_refs),
        replace(decision, selected_contribution_refs=(*decision.selected_contribution_refs, *other_decision.selected_contribution_refs)),
        replace(decision, branch='NORMAL'), replace(decision, subjective_proposition=replace(
        proposition, focal_relation_ref=other, appraisal_content=replace(proposition.appraisal_content,
                                                                       focal_relation_ref=other)))]
    for row in variants:
        row = hr.identify_selected_subjective_reception_decision(row)
        changed = hr.identify_selected_subjective_reception_input(replace(selected, decisions=tuple(row if d == decision else d for d in selected.decisions)))
        with pytest.raises(hr.GroundedHumanReceptionSurfaceError, match='MEANING_REALIZATION_CAUSAL_TRACE_GAP'):
            hr.validate_selected_subjective_reception_input(changed,
                plan.response_plan.human_reception_plan, plan, prepared.thread.resolver())


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('also_correct', [False, True])
def test_repeated_reason_withdrawal_does_not_choose_the_generic_occurrence(reverse, also_correct):
    from test_cmee_emlis_q1_thread import answered
    source = '探しやすくなったので、資料を分類したことに満足した'
    received = '褒められたのに、嬉しくなかった。'
    memo, action = (received, source + '。' + source + '。') if reverse else (source + '。' + source + '。', received)
    response = f'「{source}」は誤りです。' + ('「嬉しくなかった」ではなく「重かった」です。' if also_correct else '')
    req = answered(response, initial(memo, action))
    prepared = prepare_emlis_meaning(req)
    # Both complete occurrences retain their own reason, event, and evaluation.
    assert sum(source_owned_result_appraisal(r, prepared.original_plan.nuclei)
               for r in prepared.original_plan.relations) == 2
    assert prepared.checkpoint.assessment_status == ('PARTIAL' if also_correct else 'UNRESOLVED')
    assert [u.reason_code for u in prepared.checkpoint.unresolved_parts] == ['correction_target_unresolved']
    updates = prepared.checkpoint.answer_update.updates
    assert len(updates) == int(also_correct)
    assert all(u.operation == 'REVISE' for u in updates)
    source_field = 'memo_action' if reverse else 'memo'
    kept = {n.nucleus_id for n in prepared.original_plan.nuclei if n.source_fields == (source_field,)}
    assert len(kept) == 6
    assert not kept.intersection(prepared.checkpoint.inactive_claim_refs)
    plan = build_updated_grounded_plan(prepared)
    assert kept <= {n.nucleus_id for n in plan.nuclei}
    if not also_correct:
        assert not prepared.checkpoint.inactive_claim_refs
        assert plan.nuclei == prepared.original_plan.nuclei
        assert plan.relations == prepared.original_plan.relations
        req = replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
        outcome = MeaningExperienceEngine().generate(req)
        assert outcome.body_state == 'ANSWER_UNREFLECTED' and outcome.artifact is None
        assert outcome.meaning_checkpoint == prepared.checkpoint
        assert outcome.reason_codes == ('correction_target_unresolved',)


@pytest.mark.parametrize('row', _PRE_REASON_WITHDRAWAL_CHECKPOINTS, ids=lambda r: r['case_id'])
def test_saved_reason_withdrawal_rederives_complete_old_checkpoint(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    restored = prepare_emlis_meaning(req)
    assert _json(restored.checkpoint) == row['checkpoint']
    assert not restored.legacy_appraisal_reason and not restored.legacy_result_appraisal
    result = MeaningExperienceEngine().generate(req)
    assert result.body_state == row['baseline_body_state']
    assert result.artifact is None
    assert list(result.reason_codes) == row['baseline_reason_codes']
    assert _json(result.meaning_checkpoint) == row['checkpoint']
    fresh = _legacy_fixture_request(row, checkpoint=False)
    changed = prepare_emlis_meaning(fresh)
    assert changed.checkpoint.assessment_status == 'RESOLVED'
    assert changed.checkpoint.checkpoint_id != restored.checkpoint.checkpoint_id
    fresh = replace(fresh, emlis_thread=replace(fresh.emlis_thread,
        prepared_meaning_checkpoint_ref=changed.checkpoint.checkpoint_id))
    result = MeaningExperienceEngine().generate(fresh)
    assert result.artifact is not None, result.reason_codes
    assert '資料を分類' not in result.artifact.text and '探しやすく' not in result.artifact.text
    assert '褒められた' in result.artifact.text
    if len(changed.checkpoint.answer_update.updates) == 2:
        assert '重かった' in result.artifact.text and '嬉しくなかった' not in result.artifact.text
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(foreign)
    control = req.emlis_thread.question_control_context
    wrong = replace(control.pending_question, prompt_private='別の質問')
    tampered = replace(req, emlis_thread=replace(req.emlis_thread,
        question_control_context=replace(control, pending_question=wrong,
            issued_questions=(*control.issued_questions[:-1], wrong))))
    with pytest.raises(ValueError, match='emlis_question_noncanonical'):
        prepare_emlis_meaning(tampered)


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('also_correct', [False, True])
def test_saved_whole_reason_withdrawal_preserves_exact_body_without_author(qcase, qdb, reverse, also_correct):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    source = '探しやすくなったので、資料を分類したことに満足した'
    received = '褒められたのに、嬉しくなかった。'
    memo, action = (received, source + '。') if reverse else (source + '。', received)
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    before = run(service.start(user, parent))
    response = f'「{source}」は誤りです。' + ('「嬉しくなかった」ではなく「重かった」です。' if also_correct else '')
    dto = run(answer(service, user, before, response, key='reason-withdrawal'))
    assert dto['body_state'] == 'REFINED', dto
    current = dto['current_observation']
    assert current['event_id'] != before['current_observation']['event_id']
    assert '資料を分類' not in current['text'] and '探しやすく' not in current['text']
    assert '褒められた' in current['text']
    if also_correct:
        assert '重かった' in current['text'] and '嬉しくなかった' not in current['text']
    snapshot = run(service.store.read(user, input_id=parent))
    event, = (e for e in snapshot['events'] if e['id'] == current['event_id'])
    assert event['payload']['text'] == current['text']
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved reason withdrawal attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == dto
    assert run(restarted.start(user, parent)) == dto
    replay = run(answer(restarted, user, before, response, key='reason-withdrawal'))
    assert replay['current_observation'] == current and replay['timeline'] == dto['timeline']


# Captured from unmodified u267 66613bc5; complete old meanings, not new approvals.
_PRE_DUPLICATE_WITHDRAWAL_CHECKPOINTS = [{'case_id': 'u267-duplicate-False-False', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s1:appraisal'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-b8653afdfb74088180b49a20f23ff0e1b5f0e5e363c423e124c4d0306f1b0fd4', 'source_prefix_ref': 'emlis-source-prefix-e7ac5a54a24c9d877af79b07716bf2f25300ac79a83bd0beab1bdbbe761fdb7d', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-a0b6347964bf91b08d4052c2', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-375a268ee2eb6d1ec898c444ccbe38053fa7a9895705a10fd39bf4ce858112df', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2'], 'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s2'], 'affected_dependency_refs': []}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-e24d2199cd423a0e1381856f1ed01605dc199239953dbfe278f0078dca2b3dea'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-375a268ee2eb6d1ec898c444ccbe38053fa7a9895705a10fd39bf4ce858112df'], 'inactive_claim_refs': ['nucleus:s2'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'REFINED', 'baseline_body': '見えたこと：\n「探しやすくなった」を理由として、「満足した」へつながっています。 「資料を分類した」という出来事に対する評価は、「満足した」とあります。\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n\nEmlisから：\n探しやすくなったことを理由に、資料を分類したことについて、当時は満足したのですね。褒められたことは、嬉しさにはつながらなかったのですね。', 'baseline_reason_codes': ['emlis_thread_body_generated'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u267-duplicate-False-True', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s1:appraisal'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-eec15299666d0e979a9f4c2791fefe3eec0feaa7feba057e4f762a61abe6f551', 'source_prefix_ref': 'emlis-source-prefix-b7bdfc43c582881d3fd806587f5f3d2a63d1e93babd80d9602a2a32072cf510c', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-393f3f3081f8db2c092a8bae', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-bb893a4325bb7f687041162333dc1517c74a499b17677dfb4eb5e7b64a8afec0', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2'], 'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s2'], 'affected_dependency_refs': []}, {'update_ref': 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3:reaction'], 'evidence_refs': ['ev-687caba37596997f8258a79c'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s3:reaction'], 'affected_dependency_refs': ['relation:r3']}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-9754eebf9371564c94afecc3e608d2c1b6490b0efde35b85db1bde9ff9afc841'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-bb893a4325bb7f687041162333dc1517c74a499b17677dfb4eb5e7b64a8afec0', 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c'], 'inactive_claim_refs': ['nucleus:s2', 'nucleus:s3:reaction', 'relation:r3'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u267-duplicate-True-False', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s3'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-bffed829308ccb8818916aabac97334867c2741079b055877ef89fdb145a7bc2', 'source_prefix_ref': 'emlis-source-prefix-69e985fa590c8b2161d516b4bd616239725c06fb8684af98d132ac1e797fb99f', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-3c579db386d39a15ccd16ebe', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-38b9f9bacc232ed9ef31d14910885af0ef5ac03ff28ee0545c0fa3ab7ec2a6e4', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3'], 'evidence_refs': ['ev-a1a081f59b51505580834433'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s3'], 'affected_dependency_refs': []}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-dea7ace221a7ca2aa5f521f891464bd9e99eb4e1340c321281d4e7b72c114e90'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-38b9f9bacc232ed9ef31d14910885af0ef5ac03ff28ee0545c0fa3ab7ec2a6e4'], 'inactive_claim_refs': ['nucleus:s3'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'REFINED', 'baseline_body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n「探しやすくなった」を理由として、「満足した」へつながっています。 「資料を分類した」という出来事に対する評価は、「満足した」とあります。\n\nEmlisから：\n探しやすくなったことを理由に、資料を分類したことについて、当時は満足したのですね。褒められたことは、嬉しさにはつながらなかったのですね。', 'baseline_reason_codes': ['emlis_thread_body_generated'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u267-duplicate-True-True', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s3'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-d774078807be397a447b7b9b54f529616508ceb8906422c78ded0f6812572051', 'source_prefix_ref': 'emlis-source-prefix-e0c01e43c4db9de5aa8f4c2200f4f886db0150b9c525de0f842c0d366264b8e5', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-4c346ef3c5546c1ac510dd2a', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-d4f8cda8e370d0cca853d6b3abb10d1c3e3c704549f48c0175b3cc263ce836c6', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3'], 'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s3'], 'affected_dependency_refs': []}, {'update_ref': 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s1:reaction'], 'evidence_refs': ['ev-04d33938ac9888e25d75e5cf'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s1:reaction'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-8694db4336955f455828deb1a8ee3132c9be0ef0730cc4005c05777ae28543dc'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-d4f8cda8e370d0cca853d6b3abb10d1c3e3c704549f48c0175b3cc263ce836c6', 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123'], 'inactive_claim_refs': ['nucleus:s3', 'nucleus:s1:reaction', 'relation:r1'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u267-duplicate-False-False-q3', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-e6dac27f823406dd4fe9925ccba45d1ca23497b19ecd11b00deb90f1fd26e82b', 'source_prefix_ref': 'emlis-q3-source-prefix-5ba8e7d42379f31ae33da1c8e922c817341e98b9d478ed7b10aaf617fbb548ff', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-a0b6347964bf91b08d4052c2', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-375a268ee2eb6d1ec898c444ccbe38053fa7a9895705a10fd39bf4ce858112df', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2'], 'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s2'], 'affected_dependency_refs': []}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-e24d2199cd423a0e1381856f1ed01605dc199239953dbfe278f0078dca2b3dea'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-375a268ee2eb6d1ec898c444ccbe38053fa7a9895705a10fd39bf4ce858112df'], 'inactive_claim_refs': ['nucleus:s2'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'REFINED', 'baseline_body': '見えたこと：\n「探しやすくなった」を理由として、「満足した」へつながっています。 「資料を分類した」という出来事に対する評価は、「満足した」とあります。\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n\nEmlisから：\n探しやすくなったことを理由に、資料を分類したことについて、当時は満足したのですね。褒められたことは、嬉しさにはつながらなかったのですね。', 'baseline_reason_codes': ['emlis_thread_body_generated'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u267-duplicate-False-True-q3', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-8a8a006518f5fe686f3e28c1a352a32fec01aa868c21d9636ff6d6abef8c87be', 'source_prefix_ref': 'emlis-q3-source-prefix-770f125d85ef71c6ec48ab855d7eee27e192f7060f36965d716db080324aac9f', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-393f3f3081f8db2c092a8bae', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-bb893a4325bb7f687041162333dc1517c74a499b17677dfb4eb5e7b64a8afec0', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s2'], 'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s2'], 'affected_dependency_refs': []}, {'update_ref': 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3:reaction'], 'evidence_refs': ['ev-687caba37596997f8258a79c'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s3:reaction'], 'affected_dependency_refs': ['relation:r3']}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-9754eebf9371564c94afecc3e608d2c1b6490b0efde35b85db1bde9ff9afc841'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-bb893a4325bb7f687041162333dc1517c74a499b17677dfb4eb5e7b64a8afec0', 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c'], 'inactive_claim_refs': ['nucleus:s2', 'nucleus:s3:reaction', 'relation:r3'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u267-duplicate-True-False-q3', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-79672096f42156b7567c02ab7945c0c26ab4c5c6e3e0886e3b1656d31a54c1fe', 'source_prefix_ref': 'emlis-q3-source-prefix-601c0c85a297c2d63bbcb2ffad1a49f0d561e003eaebc3bfd9223db48d257b1a', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-3c579db386d39a15ccd16ebe', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-38b9f9bacc232ed9ef31d14910885af0ef5ac03ff28ee0545c0fa3ab7ec2a6e4', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3'], 'evidence_refs': ['ev-a1a081f59b51505580834433'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s3'], 'affected_dependency_refs': []}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-dea7ace221a7ca2aa5f521f891464bd9e99eb4e1340c321281d4e7b72c114e90'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-38b9f9bacc232ed9ef31d14910885af0ef5ac03ff28ee0545c0fa3ab7ec2a6e4'], 'inactive_claim_refs': ['nucleus:s3'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'REFINED', 'baseline_body': '見えたこと：\n「褒められた」と「嬉しくなかった」が、異なる向きのまま同時にあります。\n「探しやすくなった」を理由として、「満足した」へつながっています。 「資料を分類した」という出来事に対する評価は、「満足した」とあります。\n\nEmlisから：\n探しやすくなったことを理由に、資料を分類したことについて、当時は満足したのですね。褒められたことは、嬉しさにはつながらなかったのですね。', 'baseline_reason_codes': ['emlis_thread_body_generated'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u267-duplicate-True-True-q3', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-51f9831b0718e1d0ac41053bd83fa38cc3dadbd66a5f6c988ea68acb3a81e9d3', 'source_prefix_ref': 'emlis-q3-source-prefix-040c7e95ee829e0c500612c7c0b2a3e3479fec82ecc3da6b4ceffadd6c303b22', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-4c346ef3c5546c1ac510dd2a', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-d4f8cda8e370d0cca853d6b3abb10d1c3e3c704549f48c0175b3cc263ce836c6', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3'], 'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'WITHDRAW', 'changed_claim_refs': [], 'superseded_claim_refs': ['nucleus:s3'], 'affected_dependency_refs': []}, {'update_ref': 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s1:reaction'], 'evidence_refs': ['ev-04d33938ac9888e25d75e5cf'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s1:reaction'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-8694db4336955f455828deb1a8ee3132c9be0ef0730cc4005c05777ae28543dc'}, 'assessment_status': 'RESOLVED', 'accepted_update_refs': ['emlis-update-d4f8cda8e370d0cca853d6b3abb10d1c3e3c704549f48c0175b3cc263ce836c6', 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123'], 'inactive_claim_refs': ['nucleus:s3', 'nucleus:s1:reaction', 'relation:r1'], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}]


@pytest.mark.parametrize('row', _PRE_DUPLICATE_WITHDRAWAL_CHECKPOINTS, ids=lambda r: r['case_id'])
def test_saved_duplicate_withdrawal_rederives_complete_old_checkpoint(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert _json(prepared.checkpoint) == row['checkpoint']
    result = MeaningExperienceEngine().generate(req)
    assert _json(result.meaning_checkpoint) == row['checkpoint']
    assert result.body_state == row['baseline_body_state']
    assert (result.artifact.text if result.artifact else None) == row['baseline_body']
    assert list(result.reason_codes) == row['baseline_reason_codes']
    fresh = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
    assert fresh.checkpoint.checkpoint_id != prepared.checkpoint.checkpoint_id
    assert fresh.checkpoint.assessment_status == ('PARTIAL' if len(row['checkpoint']['answer_update']['updates']) > 1 else 'UNRESOLVED')
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match=row['foreign_error']):
        prepare_emlis_meaning(foreign)
    control = req.emlis_thread.question_control_context
    wrong = replace(control.pending_question, prompt_private='別の質問')
    tampered = replace(req, emlis_thread=replace(req.emlis_thread,
        question_control_context=replace(control, pending_question=wrong,
            issued_questions=(*control.issued_questions[:-1], wrong) if control.issued_questions else ())))
    with pytest.raises(ValueError, match='emlis_question_noncanonical'):
        prepare_emlis_meaning(tampered)


# Full synthetic checkpoints captured from unmodified u268 (05d3040709e9648b666bab037096fe821092e422).
_PRE_REPEATED_REASON_SOURCE_CHECKPOINTS = [{'case_id': 'u268-duplicate-False-False', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s1:appraisal'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-b7a39eec73c7346ff38a49e0b0bb95f8231a40e07e07b0d933a61a68528a388f', 'source_prefix_ref': 'emlis-source-prefix-e7ac5a54a24c9d877af79b07716bf2f25300ac79a83bd0beab1bdbbe761fdb7d', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-a0b6347964bf91b08d4052c2', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u268-duplicate-False-True', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s1:appraisal'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-287d71bbde73de4d3ac7685f480282319f956d57a881c0fc7a5e6a81dbbc33b0', 'source_prefix_ref': 'emlis-source-prefix-b7bdfc43c582881d3fd806587f5f3d2a63d1e93babd80d9602a2a32072cf510c', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-393f3f3081f8db2c092a8bae', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3:reaction'], 'evidence_refs': ['ev-687caba37596997f8258a79c'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s3:reaction'], 'affected_dependency_refs': ['relation:r3']}], 'unresolved_parts': [{'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-999de6bcda9d7cd6ad8ffc7ba9a0883de4f3b0bb3cc99f5825bd9fa9fe894a0e'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c'], 'inactive_claim_refs': ['nucleus:s3:reaction', 'relation:r3'], 'unresolved_parts': [{'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u268-duplicate-True-False', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s3'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-9cd68c57606f06ff53f56f58631329281a9a3fab679cfa3ae4798250fe5f8228', 'source_prefix_ref': 'emlis-source-prefix-69e985fa590c8b2161d516b4bd616239725c06fb8684af98d132ac1e797fb99f', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-3c579db386d39a15ccd16ebe', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-a1a081f59b51505580834433'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-a1a081f59b51505580834433'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u268-duplicate-True-True', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'FREE_Q1', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s3'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-a2e0934c011bb5bcc4c7b8086992100367e54b7e555284d4bdf9002eea999235', 'source_prefix_ref': 'emlis-source-prefix-e0c01e43c4db9de5aa8f4c2200f4f886db0150b9c525de0f842c0d366264b8e5', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-4c346ef3c5546c1ac510dd2a', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s1:reaction'], 'evidence_refs': ['ev-04d33938ac9888e25d75e5cf'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s1:reaction'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [{'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-3e68b823a54f6804a87ee7df039def366f65d73e4ff8078e7ba051e76a9c3f49'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123'], 'inactive_claim_refs': ['nucleus:s1:reaction', 'relation:r1'], 'unresolved_parts': [{'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_question_noncanonical'}, {'case_id': 'u268-duplicate-False-False-q3', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-2402ee3a9b5ecda137fba648ac21ac84f3ec6bf976a6e8d68ee54b62e7587160', 'source_prefix_ref': 'emlis-q3-source-prefix-5ba8e7d42379f31ae33da1c8e922c817341e98b9d478ed7b10aaf617fbb548ff', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-a0b6347964bf91b08d4052c2', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-31f15627a433f4c729b300dd'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-duplicate-False-True-q3', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-8752ab78f3ea147c4af18304cf8c64e4d1df92a64dbd5f9158c5e836be9f16cf', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-f79541ec1045a5ace3254fd1'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'affected_reception_refs': ['nucleus:s3:event', 'nucleus:s3:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'round_index': 1, 'original_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-97aea927b08dbf0f48cfc055b9205d1d9ab3b50c61d4b50cb359b61010b9e9e0', 'source_prefix_ref': 'emlis-q3-source-prefix-770f125d85ef71c6ec48ab855d7eee27e192f7060f36965d716db080324aac9f', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': {'answer_source_ref': 'src-393f3f3081f8db2c092a8bae', 'question_ref': 'emlis-question-2bbc61e3caec966ee79dd9783bfd06bfb417a34390eee7fcea267589b0055cc8', 'prior_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'updates': [{'update_ref': 'emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s3:reaction'], 'evidence_refs': ['ev-687caba37596997f8258a79c'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-9d1e2d05b7230377a5a41f47', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s3:reaction'], 'affected_dependency_refs': ['relation:r3']}], 'unresolved_parts': [{'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-999de6bcda9d7cd6ad8ffc7ba9a0883de4f3b0bb3cc99f5825bd9fa9fe894a0e'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-808465ea2e128f849a698653c5bb22d0e140907dc4887cf2511fecee0e69e36c'], 'inactive_claim_refs': ['nucleus:s3:reaction', 'relation:r3'], 'unresolved_parts': [{'evidence_refs': ['ev-7b644437cd64777ffbcc2b7d'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-duplicate-True-False-q3', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-1593f14e2211e788d1ba4fdc06edd57034bc1d1262256198dc0eb599e0c8d31e', 'source_prefix_ref': 'emlis-q3-source-prefix-601c0c85a297c2d63bbcb2ffad1a49f0d561e003eaebc3bfd9223db48d257b1a', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-3c579db386d39a15ccd16ebe', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [], 'unresolved_parts': [{'evidence_refs': ['ev-a1a081f59b51505580834433'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'UNRESOLVED', 'new_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11'}, 'assessment_status': 'UNRESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [{'evidence_refs': ['ev-a1a081f59b51505580834433'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'ANSWER_UNREFLECTED', 'baseline_body': None, 'baseline_reason_codes': ['correction_target_unresolved'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-duplicate-True-True-q3', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'answer': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'question_control': {'pending_question': {'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}, 'asked_target_refs': ['emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231'], 'issued_count': 1, 'stop': False, 'issued_questions': [{'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'parent_request_id': 'q1-synthetic', 'thread_id': 'q1-thread', 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'decision': {'disposition': 'ASK', 'target_ref': 'emlis-target-43600dfdff9540fb13582f49a89e184ad63a482320cc294dd132e506bc54f231', 'target_kind': 'PERSONAL_RECEIVED_MEANING', 'supporting_evidence_refs': ['ev-d4fbf8200a2b483ca37a5557'], 'missing_dimension': 'personal_received_meaning', 'affected_meaning_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'affected_reception_refs': ['nucleus:s1:event', 'nucleus:s1:reaction'], 'asked_target_refs': [], 'decision_reason': 'source_bound_event_personal_meaning_missing'}, 'prompt_private': '「褒められた」は、あなたにはどんな意味として届きましたか。', 'skip_allowed': True, 'answer_limit': 1, 'answer_source_role': 'SUPPLEMENTAL_ANSWER', 'schema_version': 'cocolon.cmee.emlis_clarification.v1'}], 'question_limit': 1}, 'supplemental_answers': [{'answer_id': 'q1-answer', 'thread_id': 'q1-thread', 'question_id': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'round_index': 1, 'original_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'answer_text_private': '「探しやすくなったので、資料を分類したことに満足した」は誤りです。「嬉しくなかった」ではなく「重かった」です。', 'recorded_at': '2026-09-11T00:00:00Z', 'authored_at': None, 'source_version': 'cocolon.cmee.supplemental_answer.v1', 'source_role': 'SUPPLEMENTAL_ANSWER'}], 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-bf5867cb5a55cc58f5765623154f332e4be6f2b72d9eb0451cb6f80630125803', 'source_prefix_ref': 'emlis-q3-source-prefix-040c7e95ee829e0c500612c7c0b2a3e3479fec82ecc3da6b4ceffadd6c303b22', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': {'answer_source_ref': 'src-4c346ef3c5546c1ac510dd2a', 'question_ref': 'emlis-question-c7687e04370687aec2765102840ec3d88c07740a41b14af45e180c667ddd4fb9', 'prior_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'updates': [{'update_ref': 'emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123', 'binding_kind': 'EXPLICIT_CORRECTION', 'target_meaning_refs': ['nucleus:s1:reaction'], 'evidence_refs': ['ev-04d33938ac9888e25d75e5cf'], 'temporal_binding': {'about_time': 'ORIGINAL_OCCASION', 'anchor_source_ref': 'src-0249f760c226a7f96a0e5b1e', 'time_expression_evidence_refs': [], 'relative_relation': None, 'resolved_interval': None, 'timezone_basis': None}, 'operation': 'REVISE', 'changed_claim_refs': ['answer:s8'], 'superseded_claim_refs': ['nucleus:s1:reaction'], 'affected_dependency_refs': ['relation:r1']}], 'unresolved_parts': [{'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'reason_code': 'correction_target_unresolved'}], 'disposition': 'MATERIAL_UPDATE', 'new_meaning_ref': 'emlis-meaning-3e68b823a54f6804a87ee7df039def366f65d73e4ff8078e7ba051e76a9c3f49'}, 'assessment_status': 'PARTIAL', 'accepted_update_refs': ['emlis-update-da28055fae84c60b1e435e30287e23f476ab3fa35f2f355b80a72c2b0069d123'], 'inactive_claim_refs': ['nucleus:s1:reaction', 'relation:r1'], 'unresolved_parts': [{'evidence_refs': ['ev-0830ec2a86b73c3c0af4a879'], 'reason_code': 'correction_target_unresolved'}], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'MEANING_UPDATED_BODY_UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_refined_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-initial-FREE_Q1-False', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'FREE_Q1', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-24a45fb3c65169c31a5ac3c3721aadcdf4d906a2fcb2a619566205a801a62917', 'source_prefix_ref': 'emlis-source-prefix-e8c3729aaa0997f32e99011e5c81aed42dd04757c638504de646530b45e6654c', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_q3_initial_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-initial-FREE_Q1-True', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'FREE_Q1', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-20f08aebd33912237a15c895ba034466cd2728ee038301f0c75d9a904e9d6740', 'source_prefix_ref': 'emlis-source-prefix-74202e382fa73db296921fa36e8c4a9186670837df6d5800bf50660c440c7ec4', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_q3_initial_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-initial-Q3_FREE-False', 'memo': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'action': '褒められたのに、嬉しくなかった。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-06b443d7a470355c5e38706a53d65289a0d37482ca6387822ca8b5cf024bc19d', 'source_prefix_ref': 'emlis-q3-source-prefix-b4776cc3143b25c5df3a6a3cc2b39fc2c6a3d96019609a90af69f93e5f5dacff', 'base_meaning_ref': 'emlis-base-meaning-5ce6437f5d6e74e56564b756b62fcfdb5a1d8376a6e1d77f194ddf1f3b91826b', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_q3_initial_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}, {'case_id': 'u268-initial-Q3_FREE-True', 'memo': '褒められたのに、嬉しくなかった。', 'action': '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。', 'capability': 'Q3_FREE', 'checkpoint': {'checkpoint_id': 'emlis-checkpoint-c9c6c5155fbf18fe66d8523136d0a66898b9374157a86703955ab23ccc3d90ca', 'source_prefix_ref': 'emlis-q3-source-prefix-9405b056ba8a3bac1c3f7c2f210bf9ebdb7ca7ef157750bdfdda8e8a18e81481', 'base_meaning_ref': 'emlis-base-meaning-91d6c3a5807cbaca28ebc66f78174f1b899d65b21315041aac76efc644a6ef11', 'answer_update': None, 'assessment_status': 'RESOLVED', 'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [], 'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1'}, 'baseline_body_state': 'UNAVAILABLE', 'baseline_body': None, 'baseline_reason_codes': ['emlis_q3_initial_body_unavailable'], 'foreign_error': 'emlis_checkpoint_source_prefix_mismatch'}]


@pytest.mark.parametrize('capability', ['FREE_Q1', 'Q3_FREE'])
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('basis', ['探しやすくなった', '見た目がすっきりした'])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
def test_exact_repeated_reason_initial_body_keeps_both_source_occurrences(capability, reverse, basis, evaluation):
    source = basis + 'ので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = initial(*((received, source * 2) if reverse else (source * 2, received)))
    req = replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot=capability))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    field = 'memo_action' if reverse else 'memo'
    owned = tuple(n for n in plan.nuclei if n.source_fields == (field,))
    assert len(owned) == len({n.nucleus_id for n in owned}) == 6
    assert len({n.source_span_ids for n in owned}) == 2
    resolver = p.thread.resolver()
    spans = sorted((resolver.resolve(s[0]) for s in {n.source_span_ids for n in owned}), key=lambda s: s.start_index)
    assert [(s.start_index, s.end_index, s.raw_text) for s in spans] == [
        (0, len(source) - 1, source[:-1]), (len(source), 2 * len(source) - 1, source[:-1])]
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    merged, = (line for line in sentence.lines if len(line.binding.nucleus_ids) == 6)
    assert set(merged.binding.nucleus_ids) == {n.nucleus_id for n in owned}
    assert len(merged.binding.relation_ids) == 4
    selected = project_thread_meaning(p, plan).selected_reception
    assert len(selected.decisions) == 3 and all(d.branch == 'LIMITED' for d in selected.decisions)
    assert sorted(len(d.support_nucleus_ids) for d in selected.decisions) == [1, 2, 2]
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None and outcome.body_state == 'PRE_QUESTION'
    assert outcome.question is not None and not outcome.automatic_progression
    body = outcome.artifact
    assert body.observation.count('「' + basis + '」を理由に、') == 1
    assert body.observation.count('「資料を分類した」という出来事への評価') == 1
    assert body.observation.count('「' + evaluation + '」') == 1
    assert '褒められた' in body.observation and '嬉しくなかった' in body.observation
    assert basis + 'という理由に目を向けています' in body.reception
    assert ('当時の満足について' if evaluation == '満足した' else '入力した時点での満足について') in body.reception
    assert not any(word in body.text for word in ('という変化があります', '二度', '二回', '繰り返し', 'より強く'))
    assert evaluate_grounded_surface_body_inverse(body=body.text.encode(), plan=plan,
        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed


@pytest.mark.parametrize('memo', [
    '同僚が話した。探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足した。',
    '探しやすくなったので、資料を分類したことに満足した。見た目がすっきりしたので、資料を分類したことに満足した。',
    '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、文章を整理したことに満足した。',
    '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足している。',
    '探しやすくなったので、資料を分類したことに満足した。探しやすくなったので、資料を分類したことに満足しなかった。',
    '探しやすくなったので、資料を分類したことに満足した。休んだ。探しやすくなったので、資料を分類したことに満足した。',
    '「探しやすくなったので、資料を分類したことに満足した」と同僚が言った。「探しやすくなったので、資料を分類したことに満足した」と同僚が言った。',
])
def test_repeated_reason_owner_does_not_spread_to_different_or_foreign_context(memo):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    p = prepare_emlis_meaning(request(memo, '褒められたのに、嬉しくなかった。'))
    prior = original_meaning_plan(p.thread, _legacy_repeated_appraisal_context=True)
    assert p.original_plan.nuclei == prior.nuclei and p.original_plan.relations == prior.relations


@pytest.mark.parametrize('second', [
    '私は見た目がすっきりしたので、資料を分類したことに満足した。',
    '私は探しやすくなったので、文章を整理したことに満足した。',
    '私は探しやすくなったので、資料を分類したことに満足している。',
    '私は探しやすくなったので、資料を分類したことに満足した。',
])
def test_nonidentical_reason_groups_are_not_visibly_coalesced(second):
    req = request('探しやすくなったので、資料を分類したことに満足した。' + second,
        '褒められたのに、嬉しくなかった。')
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    assert sum(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations) == 2
    sentence = build_grounded_sentence_plan(plan, p.thread.resolver(), recovery_stage='full')
    assert not any(len(line.binding.nucleus_ids) == 6 and len(line.binding.relation_ids) == 4
                   for line in sentence.lines)


def test_shared_reason_observation_reader_checks_every_role_without_author(monkeypatch):
    import emlis_ai_grounded_sentence_surface as surface
    import emlis_ai_grounded_human_reception as hr
    req = request('探しやすくなったので、資料を分類したことに満足した。' * 2,
        '褒められたのに、嬉しくなかった。')
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    selected = project_thread_meaning(p, plan).selected_reception
    sentence = build_grounded_sentence_plan(plan, p.thread.resolver(), recovery_stage='full')
    body = MeaningExperienceEngine().generate(req).artifact.text
    def forbidden(*_a, **_k):
        pytest.fail('independent body reader called author')
    monkeypatch.setattr(surface, '_render_relation', forbidden)
    def read(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=p.thread.resolver(), selected_subjective_input=selected)
    assert read(body).passed
    reason = '「探しやすくなった」を理由に、'
    about = '「資料を分類した」という出来事への評価は「満足した」とあります。'
    variants = [body.replace(reason, ''), body.replace(about, ''),
        body.replace('「探しやすくなった」を理由に', '「褒められた」を理由に'),
        body.replace('「資料を分類した」という出来事', '「褒められた」という出来事'),
        body.replace('当時の満足について', '回答した時点での満足について'),
        body.replace('という理由に', 'という唯一の理由に'),
        body.replace(about, about.replace('満足した', '二度満足した'))]
    for wrong in variants:
        assert wrong != body and not read(wrong).passed
    # Full inverse also performs the established author replay. Separately
    # prove its discourse reader accepts the HR clause without the author.
    from emlis_ai_grounded_observation_gate import read_source_owned_discourse
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence', forbidden)
    move = next(m for m in plan.response_plan.human_reception_plan.moves if len(m.support_nucleus_ids) == 2)
    clause = next(part + '。' for part in body.split('Emlisから：\n', 1)[1].split('。') if 'という理由に' in part)
    assert read_source_owned_discourse(clause, move, plan, p.thread.resolver(), selected) is not None
    assert read_source_owned_discourse(clause.replace('という理由に', 'という唯一の理由に'),
        move, plan, p.thread.resolver(), selected) is None


@pytest.mark.parametrize('row', _PRE_REPEATED_REASON_SOURCE_CHECKPOINTS, ids=lambda r: r['case_id'])
def test_saved_repeated_reason_source_keeps_complete_old_checkpoint_and_body(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    p = prepare_emlis_meaning(req)
    assert p.legacy_repeated_appraisal_context
    assert _json(p.checkpoint) == row['checkpoint']
    result = MeaningExperienceEngine().generate(req)
    assert _json(result.meaning_checkpoint) == row['checkpoint']
    assert result.body_state == row['baseline_body_state']
    assert (result.artifact.text if result.artifact else None) == row['baseline_body']
    assert list(result.reason_codes) == row['baseline_reason_codes']
    pending = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
    if pending.legacy_repeated_appraisal_context:
        # An already issued old question must keep its own canonical plan.
        assert pending.checkpoint == p.checkpoint
    fresh_request = initial(row['memo'], row['action'])
    fresh_request = replace(fresh_request, emlis_thread=replace(fresh_request.emlis_thread,
        capability_snapshot=row['capability']))
    fresh = prepare_emlis_meaning(fresh_request)
    assert not fresh.legacy_repeated_appraisal_context
    assert fresh.checkpoint.checkpoint_id != p.checkpoint.checkpoint_id
    assert sum(source_owned_result_appraisal(r, fresh.original_plan.nuclei)
               for r in fresh.original_plan.relations) == 2
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match=row['foreign_error']):
        prepare_emlis_meaning(foreign)


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('also_correct', [False, True])
def test_saved_duplicate_reason_withdrawal_keeps_ambiguity_and_body(qcase, qdb, reverse, also_correct):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE, _request, _json
    user, parent, service = qcase
    source = '探しやすくなったので、資料を分類したことに満足した'
    repeated = (source + '。') * 2
    received = '褒められたのに、嬉しくなかった。'
    memo, action = (received, repeated) if reverse else (repeated, received)
    qdb.query("update public.profiles set subscription_tier='free' where id=$1", [user])
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    before = run(service.start(user, parent))
    assert before['state'] == 'AWAITING_ANSWER' and before['body_state'] == 'PRE_QUESTION', before
    initial_body = before['current_observation']
    assert initial_body and all(s in initial_body['text'] for s in (
        '探しやすくなった', '資料を分類した', '満足した', '褒められた'))
    initial_saved = run(service.store.read(user, input_id=parent))
    assert _request(initial_saved).emlis_thread.capability_snapshot == 'Q3_FREE'
    initial_event = next(e for e in initial_saved['events'] if e['id'] == initial_body['event_id'])
    assert initial_event['payload']['text'] == initial_body['text']
    response = f'「{source}」は誤りです。' + ('「嬉しくなかった」ではなく「重かった」です。' if also_correct else '')
    dto = run(answer(service, user, before, response, key='duplicate-reason'))
    assert dto['answer_saved'] and dto['meaning_updated'] == also_correct, dto
    assert dto['answer_assessment'] == ('PARTIAL' if also_correct else 'UNRESOLVED')
    assert dto['body_state'] == ('PARTIALLY_REFINED' if also_correct else 'ANSWER_UNREFLECTED'), dto
    assert not dto['can_retry'] and dto['pending_question'] is None and dto['issued_count'] == 1
    saved = run(service.store.read(user, input_id=parent))
    meaning = next(e['payload'] for e in saved['events'] if e['id'] == saved['thread']['current_meaning_event_id'])
    prepared = prepare_emlis_meaning(_request(saved, checkpoint_ref=meaning['checkpoint_id']))
    assert _json(prepared.checkpoint) == meaning
    assert meaning['assessment_status'] == dto['answer_assessment']
    assert [p['reason_code'] for p in meaning['unresolved_parts']] == ['correction_target_unresolved']
    updates = meaning['answer_update']['updates']
    assert [u['operation'] for u in updates] == (['REVISE'] if also_correct else [])
    if also_correct:
        assert updates[0]['target_meaning_refs'] == ['nucleus:s1:reaction' if reverse else 'nucleus:s3:reaction']
    else:
        assert meaning['inactive_claim_refs'] == []
    plan = build_updated_grounded_plan(prepared)
    assert sum(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations) == 2
    current = dto['current_observation']
    if also_correct:
        assert current and current['text'] != initial_body['text']
        assert 'その時の受け止めは「重かった」' in current['text']
        assert '嬉しくなかった' not in current['text']
        assert '今回の観測に反映できていない部分があります' in current['text']
        assert current['text'].count('資料を分類したことへの当時の満足について') == 1
    else:
        assert current is None and not any(e.get('is_current') for e in dto['timeline'])
    assert len([e for e in saved['events'] if e['kind'] == 'ANSWER']) == 1
    assert len([e for e in saved['events'] if e['kind'] == 'MEANING_UPDATE']) == 2
    assert len([e for e in saved['events'] if e['kind'] == 'OBSERVATION']) == (2 if also_correct else 1)
    assert all(k not in json.dumps(dto) for k in ('source_prefix_ref', 'checkpoint_id', 'meaning_graph', 'artifact', 'raw_utf8'))
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved duplicate read attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == dto
    assert run(restarted.start(user, parent)) == dto
    replay = run(answer(restarted, user, before, response, key='duplicate-reason'))
    for key in ('revision', 'current_observation', 'timeline', 'body_state', 'answer_assessment', 'operation_id', 'attempt_id'):
        assert replay[key] == dto[key]
    assert replay['requested_attempt_id'] == dto['attempt_id']
    assert run(restarted.store.read(user, input_id=parent))['events'] == saved['events']


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('basis', ['探しやすくなった', '見た目がすっきりした'])
@pytest.mark.parametrize('correction', ['重かった', '怖かった'])
def test_duplicate_reason_independent_correction_keeps_body_and_ambiguous_withdrawal(
        reverse, evaluation, basis, correction):
    from test_cmee_emlis_q3_thread import advance
    source = basis + 'ので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, source * 2) if reverse else (source * 2, received)))
    reply = '「' + source[:-1] + '」は誤りです。「嬉しくなかった」ではなく「' + correction + '」です。'
    updated = advance(req, reply)
    prepared = prepare_emlis_meaning(updated)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    outcome = MeaningExperienceEngine().generate(updated)
    assert outcome.artifact is not None, outcome.reason_codes
    assert outcome.body_state == 'PARTIALLY_REFINED' and not outcome.automatic_progression
    body = outcome.artifact
    assert 'その時の受け止めは「' + correction + '」' in body.observation
    assert '嬉しくなかった' not in body.text
    assert '今回の観測に反映できていない部分があります' in body.observation
    assert body.reception.count(basis + 'という理由に目を向けています') == 1
    assert ('当時の' if evaluation == '満足した' else '入力した時点での') + '満足について' in body.reception
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    def valid(value):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(body.text)
    for wrong in (body.text.replace(basis + 'という理由に', ''),
                  body.text.replace('資料を分類したことへの', '褒められたことへの'),
                  body.text.replace('当時の' if evaluation == '満足した' else '入力した時点での', '回答した時点では'),
                  body.text.replace('その時の受け止めは「' + correction + '」', 'その時の受け止めは「嬉しくなかった」')):
        assert wrong != body.text and not valid(wrong)


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('correction', ['満足した', '満足している'])
def test_plain_appraisal_correction_preserves_both_received_pairs_in_source_order(reverse, correction):
    from test_cmee_emlis_q3_thread import advance
    first = '褒められたのに、嬉しくなかった。資料を分類したことに満足した。'
    second = '誘われたのに、悲しかった。文章を直したことに納得した。'
    req = request(*((second, first) if reverse else (first, second)))
    updated = advance(req, '「納得した」ではなく「' + correction + '」です。')
    prepared = prepare_emlis_meaning(updated)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    outcome = MeaningExperienceEngine().generate(updated)
    assert outcome.artifact is not None, outcome.reason_codes
    assert outcome.body_state == 'REFINED' and not outcome.automatic_progression
    body = outcome.artifact
    assert all(token in body.observation and token in body.reception for token in
               ('資料を分類した', '文章を直した', '褒められた', '誘われた'))
    assert '嬉しさにはつながら' in body.reception and '悲しさを感じ' in body.reception
    assert '納得した' not in body.text
    time = '当時は' if correction == '満足した' else '入力した時点では'
    assert '文章を直したことについて、' + time + correction in body.reception
    sentence = build_grounded_sentence_plan(plan, prepared.thread.resolver(), recovery_stage='full')
    def valid(value):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=prepared.thread.resolver(), selected_subjective_input=selected).passed
    assert valid(body.text)
    for wrong in (body.text.replace('資料を分類したことについて、当時は満足したのですね。', ''),
                  body.text.replace('文章を直したことについて', '褒められたことについて'),
                  body.text.replace('誘われたのに、悲しさを感じ', '誘われたので、嬉しさを感じ')):
        assert wrong != body.text and not valid(wrong)


@pytest.mark.parametrize('reverse', [False, True])
def test_corrected_source_components_still_reject_a_split_of_the_same_arc(monkeypatch, reverse):
    from test_cmee_emlis_q3_thread import advance
    from cocolon_meaning_experience_engine import emlis_thread_surface as thread_surface
    import emlis_ai_grounded_sentence_surface as surface
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    source = '探しやすくなったので、資料を分類したことに満足した。' * 2
    received = '褒められたのに、嬉しくなかった。'
    updated = advance(request(*((received, source) if reverse else (source, received))),
        '「嬉しくなかった」ではなく「重かった」です。')
    captured = {}
    gate = thread_surface.evaluate_grounded_observation_gate
    def record(**kwargs):
        captured.update(kwargs)
        return gate(**kwargs)
    monkeypatch.setattr(thread_surface, 'evaluate_grounded_observation_gate', record)
    outcome = MeaningExperienceEngine().generate(updated)
    assert outcome.artifact is not None, outcome.reason_codes
    assert gate(**captured).public_observation_status == 'passed'
    plan, sentence = captured['plan'], captured['sentence_plan']
    owner = next(line for line in sentence.lines if len(line.binding.nucleus_ids) == 6)
    split = surface._make_line(sentence_number=len(sentence.lines) + 1,
        line_role=owner.binding.line_role, surface_function='observe_nuclei',
        nucleus_ids=owner.binding.nucleus_ids[:1], relation_ids=(),
        nucleus_index={n.nucleus_id: n for n in plan.nuclei},
        relation_index={r.relation_id: r for r in plan.relations},
        claim_scope=owner.binding.claim_scope, recovery_stage='full')
    arcs = lambda line: {a for a in line.binding.functional_atom_ids if a.startswith('semantic_arc:')}
    assert arcs(owner) & arcs(split)
    assert 'semantic_arc_fragment:justified' not in split.binding.functional_atom_ids
    fragmented = replace(sentence, lines=(*sentence.lines, split))
    reasons = _semantic_subcheck_reasons(plan=plan, sentence_plan=fragmented,
        surface_result=captured['surface_result'], resolver=captured['resolver'])
    assert 'required_arc_fragmented_without_reason' in reasons[2]
    assert gate(**{**captured, 'sentence_plan': fragmented}).public_observation_status != 'passed'


_U269_DUPLICATE_SOURCE_CHECKPOINTS = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u269_duplicate_source_checkpoints.json').read_text())


@pytest.mark.parametrize('row', _U269_DUPLICATE_SOURCE_CHECKPOINTS, ids=lambda r: r['case_id'])
def test_u269_duplicate_source_checkpoint_rederives_complete_historical_state(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_duplicate_appraisal_source
    assert _json(prepared.checkpoint) == row['checkpoint']
    outcome = MeaningExperienceEngine().generate(req)
    assert _json(outcome.meaning_checkpoint) == row['checkpoint']
    assert outcome.body_state == row['baseline_body_state']
    assert (outcome.artifact.text if outcome.artifact else None) == row['baseline_body']
    assert list(outcome.reason_codes) == row['baseline_reason_codes']
    with pytest.raises(ValueError, match=row['foreign_error']):
        prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref='foreign')))


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('basis', ['探しやすくなった', '見た目がすっきりした', '資料を使いやすい'])
def test_duplicate_reason_initial_body_shares_words_but_keeps_both_occurrences(reverse, evaluation, basis):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_plan import source_owned_duplicate_reason_appraisals
    source = basis + 'ので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, source * 2) if reverse else (source * 2, received)))
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    groups = source_owned_duplicate_reason_appraisals(plan.nuclei, plan.relations, resolver)
    assert len(groups) == 2 and len({n.nucleus_id for group in groups for n in group}) == 6
    assert groups[0][0].source_span_ids != groups[1][0].source_span_ids
    spans = [resolver.resolve(g[0].source_span_ids[0]) for g in groups]
    assert spans[0].raw_text == spans[1].raw_text
    assert spans[0].end_index <= spans[1].start_index
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert outcome.body_state == 'PRE_QUESTION'
    assert outcome.artifact.observation.count('を理由に、') == 1
    assert outcome.artifact.observation.count('という出来事への評価は') == 1
    assert outcome.artifact.observation.count('「' + evaluation + '」') == 1
    assert outcome.artifact.reception.count(basis + 'という理由に目を向けています') == 1
    assert ('当時の' if evaluation == '満足した' else '入力した時点での') + '満足について' in outcome.artifact.reception
    assert '褒められたことは、嬉しさにはつながらなかった' in outcome.artifact.reception
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    shared, = (line for line in sentence.lines if len(line.binding.nucleus_ids) == 6)
    assert len(shared.binding.relation_ids) == 4
    clauses = hr.build_grounded_reception_clause_plans(plan.response_plan.human_reception_plan,
        'full', plan=plan, resolver=resolver)
    assert sorted(len(c.move_ids) for c in clauses) == [1, 2]
    assert len(plan.response_plan.human_reception_plan.moves) == 3


@pytest.mark.parametrize('source', [
    '探しやすくなったので、資料を分類したことに満足した。' * 3,
    '探しやすくなったので、資料を分類したことに満足した。見つけやすくなったので、資料を分類したことに満足した。',
    '友人の話です。' + '探しやすくなったので、資料を分類したことに満足した。' * 2,
    '「探しやすくなったので、資料を分類したことに満足した。」' * 2,
    '探しやすくなったので、資料を分類したことに満足しなかった。' * 2,
    '探しやすくなったので、資料を分類したことに少し満足した。' * 2,
    '探しやすくなったので、資料を分類したことに納得した。' * 2,
])
def test_duplicate_reason_scope_does_not_expand_other_sources(source):
    from emlis_ai_grounded_observation_plan import source_owned_duplicate_reason_appraisals
    p = prepare_emlis_meaning(request(source, '褒められたのに、嬉しくなかった。'))
    assert not source_owned_duplicate_reason_appraisals(p.original_plan.nuclei,
        p.original_plan.relations, p.thread.resolver())
    assert not any('semantic_dependency:duplicated_reason_appraisal_exact2' in n.semantic_frame.attribute_codes
                   for n in p.original_plan.nuclei)


@pytest.mark.parametrize('reverse', [False, True])
def test_duplicate_reason_shared_body_inverse_checks_roles_and_each_selected_owner(monkeypatch, reverse):
    import emlis_ai_grounded_human_reception as hr
    import emlis_ai_grounded_sentence_surface as ss
    from emlis_ai_grounded_observation_gate import read_detached_feeling_pair
    source = '探しやすくなったので、資料を分類したことに満足した。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, source * 2) if reverse else (source * 2, received)))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    resolver = p.thread.resolver()
    selected = project_thread_meaning(p, plan).selected_reception
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    body = MeaningExperienceEngine().generate(req).artifact.text
    def forbidden(*_a, **_k):
        pytest.fail('independent reader called an author')
    monkeypatch.setattr(ss, '_render_relation', forbidden)
    def valid(value, selection=selected):
        return evaluate_grounded_surface_body_inverse(body=value.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selection).passed
    assert valid(body)
    wrongs = [body.replace('を理由に、', 'の結果として、'),
              body.replace('評価は「満足した」', '評価は「資料を分類した」'),
              body.replace('探しやすくなったという理由に', ''),
              body.replace('資料を分類したことへの', '褒められたことへの'),
              body.replace('当時の', '回答した時点での'),
              body.replace('満足について', '不満について')]
    assert all(value != body and not valid(value) for value in wrongs)
    clauses = hr.build_grounded_reception_clause_plans(plan.response_plan.human_reception_plan,
        'full', plan=plan, resolver=resolver)
    pair_clause, = (c for c in clauses if len(c.move_ids) == 2)
    moves = tuple(m for mid in pair_clause.move_ids for m in plan.response_plan.human_reception_plan.moves if m.move_id == mid)
    raw, = (part + '。' for part in body.split('Emlisから：')[1].strip().split('。') if 'という理由に' in part)
    monkeypatch.setattr(hr, '_source_owned_relational_focus_sentence', forbidden)
    assert read_detached_feeling_pair(raw, moves, plan, resolver, selected) is not None
    first, second = (next(d for d in selected.decisions if d.move_id == m.move_id) for m in moves)
    for changed in (replace(first, selected_contribution_refs=first.selected_contribution_refs[:1]),
                    replace(first, selected_contribution_refs=second.selected_contribution_refs)):
        changed = hr.identify_selected_subjective_reception_decision(changed)
        selection = hr.identify_selected_subjective_reception_input(replace(selected,
            decisions=tuple(changed if d == first else d for d in selected.decisions)))
        assert read_detached_feeling_pair(raw, moves, plan, resolver, selection) is None




@pytest.mark.parametrize('capability', ['FREE_Q1', 'Q3_FREE'])
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('target,evaluation', [
    ('資料を分類した', '満足した'), ('机を拭いた', '満足している'),
    ('資料を分類した', '満足しなかった')])
def test_plain_appraisal_retention_keeps_two_received_and_two_evaluations(capability, reverse, target, evaluation):
    first = '褒められたのに、嬉しくなかった。' + target + 'ことに' + evaluation + '。'
    second = '誘われたのに、悲しかった。文章を直したことに納得した。'
    req = initial(*((second, first) if reverse else (first, second)))
    req = replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot=capability))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    text = tuple(n for n in plan.nuclei if n.source_fields in {('memo',), ('memo_action',)})
    assert len(text) == 8 and all(n.retention == 'required' for n in text)
    if capability == 'FREE_Q1':
        # Q1's existing Observation contribution budget remains a separate
        # limitation; restoring source ownership must not enlarge it.
        with pytest.raises(ValueError, match='stage1_required_observation_unrealizable'):
            project_thread_meaning(p, plan)
        assert MeaningExperienceEngine().generate(req).artifact is None
        return
    selected = project_thread_meaning(p, plan).selected_reception
    assert len(selected.decisions) == 3 and all(d.branch == 'LIMITED' for d in selected.decisions)
    assert {nid for d in selected.decisions for nid in (*d.target_nucleus_ids, *d.support_nucleus_ids)} == {
        n.nucleus_id for n in text}
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.body_state == 'PRE_QUESTION' and outcome.artifact and outcome.question
    assert not outcome.automatic_progression
    body = outcome.artifact
    for token in (target, evaluation, '文章を直した', '納得した', '褒められた', '誘われた'):
        assert token in body.observation and token in body.reception
    assert '嬉しさにはつながら' in body.reception and '悲しさを感じ' in body.reception
    assert '入力した時点では' in body.reception if evaluation == '満足している' else '当時は' in body.reception
    sentence = build_grounded_sentence_plan(plan, p.thread.resolver(), recovery_stage='full')
    def passes(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=p.thread.resolver(), selected_subjective_input=selected).passed
    assert passes(body.text)
    # Each appraisal still belongs to its own object; each received reaction
    # must survive independently of the two positive/negative evaluations.
    for wrong in (body.text.replace(target + 'ことについて', '文章を直したことについて'),
                  body.text.replace('文章を直したことについて、当時は納得したのですね。', ''),
                  body.text.replace('誘われたのに、悲しさを感じ', '誘われたので、嬉しさを感じ')):
        assert wrong != body.text and not passes(wrong)


@pytest.mark.parametrize('extra', ['植木に水をやった。', '私は不安だった。',
    '私は探しやすくなったので、資料を分類したことに満足した。',
    'まだ結果が出ていないけれど、文章を直したことに満足した。'])
def test_appraisal_retention_does_not_drop_extra_owners_to_fit_capacity(extra):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    req = request('褒められたのに、嬉しくなかった。資料を分類したことに満足した。' + extra,
        '誘われたのに、悲しかった。文章を直したことに納得した。')
    p = prepare_emlis_meaning(req)
    old = original_meaning_plan(p.thread, _legacy_appraisal_retention=True)
    assert p.original_plan.nuclei == old.nuclei and p.original_plan.relations == old.relations


# Captured from unmodified u268 05d3040; identical on the independently
# validated u269 source snapshot. These are synthetic historical meanings.
_PRE_APPRAISAL_RETENTION = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_plain_appraisal_retention_u268.json').read_text())


@pytest.mark.parametrize('row', _PRE_APPRAISAL_RETENTION, ids=lambda r: r['case_id'])
def test_saved_plain_appraisal_retention_restores_complete_checkpoint_and_result(row):
    from emlis_thread_service import _json
    req = _legacy_fixture_request(row)
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_appraisal_retention
    assert _json(prepared.checkpoint) == row['checkpoint']
    outcome = MeaningExperienceEngine().generate(req)
    assert _json(outcome.meaning_checkpoint) == row['checkpoint']
    assert outcome.body_state == row['baseline_body_state']
    assert (outcome.artifact.text if outcome.artifact else None) == row['baseline_body']
    assert list(outcome.reason_codes) == row['baseline_reason_codes']
    foreign = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref='foreign'))
    with pytest.raises(ValueError, match=row['foreign_error']):
        prepare_emlis_meaning(foreign)
    if 'answer' in row:
        issued = prepare_emlis_meaning(_legacy_fixture_request(row, checkpoint=False))
        # Some issued questions are still canonical under the repaired plan.
        # Without a saved checkpoint they may create a new complete meaning;
        # the old checkpoint above must still re-derive exactly.
        assert issued.thread.control.question_control_context == prepared.thread.control.question_control_context
        assert (issued.checkpoint == prepared.checkpoint) == issued.legacy_appraisal_retention


@pytest.mark.parametrize('reverse', [False, True])
def test_saved_plain_appraisal_retention_reopens_without_author(qcase, qdb, reverse):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    first = '褒められたのに、嬉しくなかった。資料を分類したことに満足した。'
    second = '誘われたのに、悲しかった。文章を直したことに納得した。'
    memo, action = (second, first) if reverse else (first, second)
    qdb.query("update public.profiles set subscription_tier='free' where id=$1", [user])
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    before = run(service.start(user, parent))
    assert before['body_state'] == 'PRE_QUESTION' and before['current_observation']
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved appraisal retention attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == before
    assert run(restarted.start(user, parent)) == before
    response = '「納得した」ではなく「満足している」です。'
    after = run(answer(service, user, before, response, key='appraisal-retention'))
    assert after['body_state'] == 'REFINED', after
    assert after['answer_assessment'] == 'RESOLVED' and after['meaning_updated']
    assert after['current_observation'] and after['current_observation'] != before['current_observation']
    text = after['current_observation']['text']
    assert '納得した' not in text and '入力した時点では満足している' in text
    assert all(token in text for token in ('資料を分類した', '文章を直した', '褒められた', '誘われた'))
    assert run(restarted.get(user, parent)) == after
    assert run(restarted.start(user, parent)) == after
    saved = run(service.store.read(user, input_id=parent))
    replay = run(answer(restarted, user, before, response, key='appraisal-retention'))
    assert replay['current_observation'] == after['current_observation'] and replay['timeline'] == after['timeline']
    assert run(restarted.store.read(user, input_id=parent))['events'] == saved['events']


@pytest.mark.parametrize('target', ['資料を分類したことに', '資料を分類できて', '案を選んで'])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
def test_reason_configuration_reads_all_three_roles_without_repeating_evaluation(monkeypatch, target, evaluation):
    import emlis_ai_grounded_sentence_surface as surface
    basis = '探しやすくなった'
    req = request(basis + 'ので、' + target + evaluation + '。', '褒められたのに、嬉しくなかった。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    selected = project_thread_meaning(prepared, plan).selected_reception
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    artifact = result.artifact
    event = target.removesuffix('ことに')
    expected = f'「{basis}」を理由に、「{event}」という出来事への評価は「{evaluation}」とあります。'
    assert expected in artifact.observation
    assert artifact.observation.count('「' + evaluation + '」') == 1
    assert '褒められた' in artifact.observation and '嬉しくなかった' in artifact.observation
    def forbidden(*_a, **_k):
        pytest.fail('independent Observation reader called the author')
    monkeypatch.setattr(surface, '_render_relation', forbidden)
    def valid(observation):
        return evaluate_grounded_surface_body_inverse(body=artifact.text.replace(artifact.observation, observation).encode(),
            plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(artifact.observation)
    wrongs = [
        expected.replace(f'「{basis}」を理由に、', ''),
        expected.replace(f'「{basis}」', '「褒められた」'),
        expected.replace(f'「{event}」', '「褒められた」'),
        f'「{event}」を理由に、「{basis}」という出来事への評価は「{evaluation}」とあります。',
        expected.replace('を理由に、', 'の結果として、'),
        expected.replace('を理由に、', 'だけを理由に、'),
        expected.replace(evaluation, '満足しなかった'),
        expected.replace(evaluation, '満足している' if evaluation == '満足した' else '満足した'),
        expected + 'これからも満足できそうです。',
        expected + f'「{event}」という出来事に対する評価は、「{evaluation}」とあります。',
    ]
    for wrong in wrongs:
        assert wrong != expected
        assert not valid(artifact.observation.replace(expected, wrong))


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('target', ['資料を分類したことに', '資料を分類できて', '案を選んで'])
def test_saved_single_reason_sentence_survives_correction_and_reopen(qcase, qdb, reverse, target):
    from test_emlis_q2_application import run, answer
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    source = '探しやすくなったので、' + target + '満足した。'
    received = '褒められたのに、嬉しくなかった。'
    memo, action = (received, source) if reverse else (source, received)
    qdb.query("update public.profiles set subscription_tier='free' where id=$1", [user])
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1', [parent, memo, action])
    before = run(service.start(user, parent))
    assert before['body_state'] == 'PRE_QUESTION', before
    event = target.removesuffix('ことに')
    expected = f'「探しやすくなった」を理由に、「{event}」という出来事への評価は「満足した」とあります。'
    assert expected in before['current_observation']['text']
    assert run(service.get(user, parent)) == before
    response = '「嬉しくなかった」ではなく「重かった」です。'
    dto = run(answer(service, user, before, response, key='single-reason-body'))
    assert dto['body_state'] == 'REFINED', dto
    assert dto['answer_saved'] and dto['meaning_updated'] and dto['answer_assessment'] == 'RESOLVED'
    assert expected in dto['current_observation']['text']
    assert 'その時の受け止めは「重かった」' in dto['current_observation']['text']
    assert '嬉しくなかった' not in dto['current_observation']['text']
    saved = run(service.store.read(user, input_id=parent))
    observations = [e for e in saved['events'] if e['kind'] == 'OBSERVATION']
    assert [e['payload']['text'] for e in observations] == [before['current_observation']['text'], dto['current_observation']['text']]
    assert [e['text'] for e in dto['timeline'] if e['kind'] == 'OBSERVATION'] == [e['payload']['text'] for e in observations]
    assert [e['is_current'] for e in dto['timeline'] if e['kind'] == 'OBSERVATION'] == [False, True]
    assert len([e for e in saved['events'] if e['kind'] == 'ANSWER']) == 1
    assert len([e for e in saved['events'] if e['kind'] == 'MEANING_UPDATE']) == 2
    class NoAuthor:
        def __getattr__(self, name):
            raise AssertionError('saved single-reason read attempted generation: ' + name)
    restarted = EmlisThreadService(engine=NoAuthor(), runtime_profile=Q3_PROFILE)
    assert run(restarted.get(user, parent)) == dto
    assert run(restarted.start(user, parent)) == dto
    replay = run(answer(restarted, user, before, response, key='single-reason-body'))
    for key in ('revision', 'current_observation', 'timeline', 'body_state', 'answer_assessment', 'operation_id', 'attempt_id'):
        assert replay[key] == dto[key]
    assert run(restarted.store.read(user, input_id=parent))['events'] == saved['events']


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('correction', ['重かった', '怖かった'])
def test_single_reason_and_corrected_received_keep_distinct_complete_source_arcs(monkeypatch, reverse, evaluation, correction):
    from test_cmee_emlis_q3_thread import advance
    from cocolon_meaning_experience_engine import emlis_thread_surface as thread_surface
    import emlis_ai_grounded_sentence_surface as surface
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    reason = '探しやすくなったので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    req = request(*((received, reason) if reverse else (reason, received)))
    updated = advance(req, '「嬉しくなかった」ではなく「' + correction + '」です。')
    prepared = prepare_emlis_meaning(updated)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    captured = {}
    gate = thread_surface.evaluate_grounded_observation_gate
    def record(**kwargs):
        captured.update(kwargs)
        return gate(**kwargs)
    monkeypatch.setattr(thread_surface, 'evaluate_grounded_observation_gate', record)
    outcome = MeaningExperienceEngine().generate(updated)
    assert outcome.artifact is not None and outcome.body_state == 'REFINED', outcome.reason_codes
    assert not outcome.automatic_progression
    body = outcome.artifact
    assert body.observation.count('「' + evaluation + '」') == 1
    assert 'その時の受け止めは「' + correction + '」' in body.observation
    assert '嬉しくなかった' not in body.text
    plan, sentence, resolver = captured['plan'], captured['sentence_plan'], captured['resolver']
    assert len(plan.coverage_requirements.required_nucleus_ids) == 5
    assert len(plan.coverage_requirements.required_relation_ids) == 3
    assert set(sentence.covered_required_nucleus_ids) == set(plan.coverage_requirements.required_nucleus_ids)
    assert set(sentence.covered_required_relation_ids) == set(plan.coverage_requirements.required_relation_ids)
    observations = tuple(line for line in sentence.lines if line.binding.line_role in {'primary_observation', 'supporting_observation'})
    assert len(observations) == 2
    arcs = lambda line: {a for a in line.binding.functional_atom_ids if a.startswith('semantic_arc:')}
    assert all(len(arcs(line)) == 1 for line in observations)
    assert not arcs(observations[0]) & arcs(observations[1])
    owner, = (line for line in observations if len(line.binding.nucleus_ids) == 3)
    split = surface._make_line(sentence_number=len(sentence.lines) + 1,
        line_role=owner.binding.line_role, surface_function='observe_nuclei',
        nucleus_ids=owner.binding.nucleus_ids[:1], relation_ids=(),
        nucleus_index={n.nucleus_id: n for n in plan.nuclei},
        relation_index={r.relation_id: r for r in plan.relations},
        claim_scope=owner.binding.claim_scope, recovery_stage='full', plan=plan, resolver=resolver)
    assert arcs(owner) & arcs(split)
    assert 'semantic_arc_fragment:justified' not in split.binding.functional_atom_ids
    fragmented = replace(sentence, lines=(*sentence.lines, split))
    reasons = _semantic_subcheck_reasons(plan=plan, sentence_plan=fragmented,
        surface_result=captured['surface_result'], resolver=resolver)
    assert 'required_arc_fragmented_without_reason' in reasons[2]
    assert gate(**{**captured, 'sentence_plan': fragmented}).public_observation_status != 'passed'
    selected = project_thread_meaning(prepared, build_updated_grounded_plan(prepared)).selected_reception
    def forbidden(*_a, **_k):
        pytest.fail('independent reader called Observation author')
    monkeypatch.setattr(surface, '_render_relation', forbidden)
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(body.text)
    for wrong in (body.text.replace('「探しやすくなった」', '「褒められた」'),
                  body.text.replace('「資料を分類した」', '「褒められた」'),
                  body.text.replace('「' + correction + '」', '「嬉しくなかった」'),
                  body.text.replace('評価は「' + evaluation + '」', '評価は「満足しなかった」')):
        assert wrong != body.text and not valid(wrong)


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('evaluation', ['満足した', '満足している'])
@pytest.mark.parametrize('reason', ['探しやすくなった', '見た目がすっきりした', '資料を使いやすい'])
@pytest.mark.parametrize('operation', ['revise', 'withdraw'])
def test_detached_appraisal_reason_remains_an_original_fact(reverse, evaluation, reason, operation):
    from test_cmee_emlis_q3_thread import advance
    source = reason + 'ので、資料を分類したことに' + evaluation + '。'
    received = '褒められたのに、嬉しくなかった。'
    correction = '満足しなかった' if evaluation == '満足した' else '満足していない'
    answer = ('「' + evaluation + '」ではなく「' + correction + '」です。'
              if operation == 'revise' else '「' + evaluation + '」は誤りです。')
    req = advance(request(*((received, source) if reverse else (source, received))), answer)
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    reason_node, = (n for n in plan.nuclei
        if 'semantic_role:appraisal_explicit_reason' in n.semantic_frame.attribute_codes)
    assert reason_node.kind == reason_node.semantic_frame.predicate_kind == 'state'
    assert reason_node.semantic_frame.modality == 'fact'
    assert not any(reason_node.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    assert result.meaning_checkpoint == p.checkpoint
    when = '入力した時点' if reason == '資料を使いやすい' else '当時'
    assert f'{when}の状態として、「{reason}」と書かれています。' in result.artifact.observation
    assert f'今は、「{reason}」という感覚' not in result.artifact.text
    if operation == 'revise':
        assert correction in result.artifact.observation
        assert correction in result.artifact.reception
    else:
        assert evaluation not in result.artifact.text
        assert '「資料を分類した」という出来事がありました。' in result.artifact.observation
    assert '褒められた' in result.artifact.observation and '嬉しくなかった' in result.artifact.observation


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('reason', ['私は探しやすくなった', '私は資料を使いやすい'])
@pytest.mark.parametrize('operation', ['revise', 'withdraw'])
def test_detached_reason_reader_rejects_changed_fact_time_and_link_without_author(monkeypatch, reverse, reason, operation):
    from test_cmee_emlis_q3_thread import advance
    import emlis_ai_grounded_sentence_surface as surface
    import emlis_ai_grounded_observation_gate as gate
    source = reason + 'ので、資料を分類したことに満足した。'
    received = '褒められたのに、嬉しくなかった。'
    answer = ('「満足した」ではなく「満足しなかった」です。'
              if operation == 'revise' else '「満足した」は誤りです。')
    req = advance(request(*((received, source) if reverse else (source, received))), answer)
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    selected = project_thread_meaning(p, plan).selected_reception
    resolver = p.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    body = result.artifact.text
    reason_node = next(n for n in plan.nuclei if 'semantic_role:appraisal_explicit_reason' in n.semantic_frame.attribute_codes)
    planned = tuple(l for l in sentence.lines if l.binding.line_role != 'human_follow')
    index = next(i for i,l in enumerate(planned) if l.binding.nucleus_ids == (reason_node.nucleus_id,))
    when = '当時' if reason_node.semantic_frame.time_scope == 'past' else '入力した時点'
    original = f'{when}の状態として、「{reason}」と書かれています。'
    assert original in body
    wrongs = [f'今は、「{reason}」という感覚が前に出ています。',
        original.replace('状態', '気持ち'), original.replace('状態', '出来事'),
        original.replace(when, '回答した時点'),
        original.replace(when, '入力した時点' if when == '当時' else '当時'),
        original.replace(reason, '褒められた'), original.replace('私は', '上司は'),
        original.replace('と書かれています', 'ことが満足しなかった理由です'),
        original.replace('探しやすくなった', '探しにくくなった') if '探しやすくなった' in reason
        else original.replace('使いやすい', '使いにくい')]
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed
    assert valid(body)
    for wrong in wrongs:
        assert wrong != original and not valid(body.replace(original, wrong))
    def forbidden(*_a, **_k):
        pytest.fail('independent original fact reader called author')
    monkeypatch.setattr(surface, '_render_observation', forbidden)
    def independent(text):
        raw = text.encode(); witness = gate.parse_grounded_surface_body_bytes(raw)
        line = tuple(l for l in witness.lines if l.section == 'observation')[index]
        return gate._body_inverse_intervening_events(raw, witness, line, planned[index], plan, resolver)
    assert independent(body)
    for wrong in wrongs:
        assert not independent(body.replace(original, wrong))
