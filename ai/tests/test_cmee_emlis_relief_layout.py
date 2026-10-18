"""A retained pair stays a complete Observation unit after one other answer.

The baseline is the unmodified u344 public Q1/Q3 route, including all initial
bodies. Sentence layout may change; meaning, decisions and question cannot.
"""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u344_relief_layout_v1.json').read_text())
ROWS = {r['case']:r for r in BASELINE['cases']}
SHORTENED = {'add_now_positive','add_past_positive','add_now_negative','add_past_burden',
             'self_pair','degree_pair','revise_other','withdraw_other_event','kana','relief'}

@lru_cache(None)
def request(case, profile, updated):
    r=ROWS[case]; req=(initial if profile=='q1' else begin)(r['memo'])
    return advance(req,r['answer']) if updated else req

@lru_cache(None)
def generated(case, profile, updated):
    out=MeaningExperienceEngine().generate(request(case,profile,updated))
    folder=os.environ.get('CMEE_RELIEF_LAYOUT_BODY_DIR')
    if folder and profile=='q3' and updated:
        Path(folder).mkdir(parents=True,exist_ok=True)
        Path(folder,case+'.json').write_text(json.dumps(dict(case=case,
            memo=ROWS[case]['memo'],reply=ROWS[case]['answer'],
            body=out.artifact.text if out.artifact else None,
            reasons=list(out.reason_codes),status=out.status.value,body_state=out.body_state),
            ensure_ascii=False,indent=2)+'\n')
    return out

@pytest.mark.parametrize('case',ROWS)
@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('updated',[False,True],ids=['initial','one_answer'])
def test_same_meaning_and_questions_with_complete_source_units(case,profile,updated):
    assert BASELINE['source_commit'] == 'fc3bc92841b44950ba7cf73b905fbef024a30559'
    row=ROWS[case][profile]
    if updated and 'answer_error' in row:
        with pytest.raises(AssertionError) as exc: request(case,profile,True)
        # Pytest appends assertion diagnostics; the original failure reason is first.
        assert str(exc.value).splitlines()[0] == row['answer_error']
        return
    frozen=row['updated' if updated else 'initial']
    req=request(case,profile,updated); p=prepare_emlis_meaning(req)
    assert digest(p.checkpoint)==frozen['checkpoint_sha']
    assert p.thread.source_prefix_ref==frozen['source_prefix']
    if 'plan_error' in frozen:
        with pytest.raises(ValueError,match=frozen['plan_error']): build_updated_grounded_plan(p)
    else:
        plan=build_updated_grounded_plan(p)
        assert digest(plan)==frozen['plan_sha']
        if 'projection_error' in frozen:
            with pytest.raises(ValueError,match=frozen['projection_error']): project_thread_meaning(p,plan)
        else:
            assert digest(project_thread_meaning(p,plan).selected_reception)==frozen['selected_sha']
    out=generated(case,profile,updated)
    assert encoded(out.question)==frozen['question']
    assert encoded(out.question_decision)==frozen['question_decision']
    assert list(out.reason_codes)==frozen['reasons']
    assert out.status.value==frozen['status'] and out.body_state==frozen['body_state']
    old=frozen['artifact']
    if not updated or case not in SHORTENED | {'ambiguous'}:
        assert encoded(out.artifact)==old
    elif case in SHORTENED:
        assert out.artifact
        body=out.artifact
        assert body.observation.splitlines()[0].endswith('とあります。')
        assert len(body.observation.splitlines())>=2
        assert 'の一方で' in body.observation.splitlines()[0]
        assert 'かもしれな' in body.observation
        assert 'かもしれな' not in body.reception
        assert 'と聞いて、私も少し安心しましたが、その' in body.reception
        assert '今、耳を傾けていたいです。' in body.reception
        assert len(body.reception)<len(old['reception'])
        # No unmodified or withdrawn experience is lost when the first move shortens.
        prior_tail=old['reception'].split('耳を傾けていたいです。',1)[1]
        assert body.reception.endswith(prior_tail)
        assert encoded(replace(body,artifact_id=old['artifact_id'],
            observation=old['observation'],reception=old['reception']))==old
    else:
        # Another loneliness host still requires the complete original reference.
        assert out.artifact and out.artifact.reception==old['reception']
        assert 'その寂しさにも' not in out.artifact.reception
        assert encoded(replace(out.artifact,artifact_id=old['artifact_id'],
            observation=old['observation'],reception=old['reception']))==old
    saved=replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=frozen['checkpoint_id']))
    assert MeaningExperienceEngine().generate(saved).artifact==out.artifact


CAPTURED = {}

@pytest.fixture(scope='module')
def current_context():
    from cocolon_meaning_experience_engine import emlis_thread_surface
    original = emlis_thread_surface.evaluate_grounded_observation_gate
    def capture(**kwargs):
        CAPTURED.update(kwargs)
        return original(**kwargs)
    with patch.object(emlis_thread_surface, 'evaluate_grounded_observation_gate', capture):
        return actual(request=request('degree_pair','q3',True))

@pytest.mark.parametrize('mutation',['missing_pair','missing_other','possibility','degree','self',
    'time','contrast','duplicate','join','reaction','listening','other_time','other_value'])
def test_independent_reader_rejects_loss_or_ambiguous_joint_reference(current_context,mutation):
    out,plan,sentence,resolver,selected=current_context
    body=out.artifact.text
    obs=out.artifact.observation; follow=out.artifact.reception
    if mutation=='missing_pair': changed=body.replace(obs.splitlines()[0]+'\n','')
    elif mutation=='missing_other': changed=body.replace(obs.splitlines()[1],'')
    elif mutation=='possibility': changed=body.replace('かもしれない','に違いない')
    elif mutation=='degree': changed=body.replace('とても寂しい','少し寂しい')
    elif mutation=='self': changed=body.replace('一人で休めたこと','友達が一人で休めたこと')
    elif mutation=='time': changed=body.replace('ほっとした','ほっとする',1)
    elif mutation=='contrast': changed=body.replace('の一方で','が原因で')
    elif mutation=='duplicate': changed=body.replace(obs,obs+'\n'+obs.splitlines()[0])
    elif mutation=='join': changed=body.replace(obs,obs.replace('\n',' '))
    elif mutation=='reaction': changed=body.replace('私も少し安心しましたが、','')
    elif mutation=='listening': changed=body.replace('今、耳を傾けていたいです','違いを感じています')
    elif mutation=='other_time': changed=body.replace('回答した時点','その時')
    else: changed=body.replace('少し悲しい','少し嬉しい').replace('少し悲しさ','少し嬉しさ')
    assert changed!=body
    with patch.object(surface,'_realize_line',side_effect=AssertionError('no author oracle')):
        assert read_body(current_context,body).passed
        assert not read_body(current_context,changed).passed


def test_same_component_fragmentation_is_still_rejected(current_context):
    # The two genuine components own different arcs; no nucleus/relation was
    # discarded or reclassified to make the split pass.
    _,plan,sentence,resolver,_=current_context
    lines=[l for l in sentence.lines if l.binding.line_role!='human_follow']
    assert len(lines)==2
    assert set(n for l in lines for n in l.binding.nucleus_ids)==set(sentence.required_nucleus_ids)
    assert set(r for l in lines for r in l.binding.relation_ids)==set(sentence.required_relation_ids)
    arcs=[{a for a in l.binding.functional_atom_ids if a.startswith('semantic_arc:')} for l in lines]
    assert all(arcs) and not arcs[0]&arcs[1]
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    owner = lines[0]
    split = surface._make_line(sentence_number=len(sentence.lines)+1,
        line_role=owner.binding.line_role, surface_function='observe_nuclei',
        nucleus_ids=owner.binding.nucleus_ids[:1], relation_ids=(),
        nucleus_index={n.nucleus_id:n for n in plan.nuclei},
        relation_index={r.relation_id:r for r in plan.relations},
        claim_scope=owner.binding.claim_scope, recovery_stage='full', plan=plan, resolver=resolver)
    assert split.binding.sentence_id not in {l.binding.sentence_id for l in sentence.lines}
    assert arcs[0] & set(split.binding.functional_atom_ids)
    reasons = _semantic_subcheck_reasons(plan=plan,
        sentence_plan=replace(sentence,lines=(*sentence.lines,split)),
        surface_result=CAPTURED['surface_result'],resolver=resolver)
    assert 'required_arc_fragmented_without_reason' in reasons[2]


@pytest.mark.parametrize('case',['add_now_positive','revise_other','withdraw_other_event'])
def test_saved_delivery_setup_matches_untouched_u344(case):
    # The SQL tests persist this prior behavior, not a fabricated saved string.
    with patch.object(surface,'_retained_relief_observation_pair',return_value=frozenset()):
        old=MeaningExperienceEngine().generate(request(case,'q3',True))
    assert encoded(old.artifact)==ROWS[case]['q3']['updated']['artifact']
