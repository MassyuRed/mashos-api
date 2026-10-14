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
        thread = replace(thread, current_round=1,
            answers=(SupplementalAnswerSource(**row['supplemental_answer']),),
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


def test_current_appraisal_body_save_retry_reuses_the_same_meaning(qcase, qdb, monkeypatch):
    import httpx
    import emlis_thread_store
    from test_emlis_q2_application import run
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2,memo_action=$3 where id=$1',
        [parent, '資料を分類できて満足した。', '植木に水をやった。'])
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
    assert done['body_state'] == 'FINAL' and done['current_observation']
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
