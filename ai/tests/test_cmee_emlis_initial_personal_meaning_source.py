"""Complete source, sealed selection and delivered bytes are independent gates."""
from dataclasses import fields, replace
from unittest.mock import patch
import pytest
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_observation_gate as gate
from cocolon_meaning_experience_engine import contracts as c
from test_cmee_emlis_initial_personal_meaning import request, ROWS, update
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_cmee_emlis_q1_thread import initial

@pytest.fixture(scope='module')
def context():
    return actual(request=request('pair_received_unknown'))

@pytest.mark.parametrize('before,after',[
    ('嬉しくなかったし、期待されているように感じて、重かったのですね。','嬉しくなかったのですね。'),
    ('期待されているように感じて','期待されていて'),
    ('重かったのですね','重いのですね'),
    ('重かったのですね。','重かったから、'),
    ('と、それぞれ書かれています。','が、同じ入力の中で一つの流れになっています。'),
    ('のに「嬉しくなかった」という経験が書かれています。','と「嬉しくなかった」が、異なる向きのまま同時にあります。'),
    ('「褒められた」のに「嬉しくなかった」という経験が書かれています。',
     '「褒められた」の一方で「嬉しくなかった」、また「褒められた」の一方で「嬉しくなかった」という、それぞれ異なる向きが並んでいます。'),
    ('「褒められた」のに「嬉しくなかった」という経験が書かれています。',
     '「褒められた」のに「嬉しくなかった」という経験が書かれています。「褒められた」の一方で「嬉しくなかった」とあります。'),
    ('その寂しさにも、今、耳を傾けていたいです。',''),
    ('何が不安なのか、あなたにもまだわからないのですね。',''),
])
def test_delivered_loss_fact_promotion_time_cause_and_independent_loss_fail(context,before,after):
    body=context[0].artifact.text
    changed=body.replace(before,after)
    assert changed!=body
    with patch.object(hr,'_source_grounded_initial_personal_meaning_discourse',side_effect=AssertionError('author forbidden')):
        assert read_body(context,body).passed
        assert not read_body(context,changed).passed

@pytest.mark.parametrize('mutation',['time','modality','argument','swap','checkpoint','source','duplicate_unknown','downgrade'])
def test_resealed_local_or_selected_cannot_forge_source_roles(context,mutation):
    _,plan,_,resolver,selected=context
    decision=selected.decisions[0];local=decision.initial_received_personal_meaning
    rest=selected.decisions[1:]
    if mutation in {'time','modality','argument'}:
        meaning_basis=next(b for b in local.basis_rows if b.semantic_ref==local.initial_meaning_ref)
        key,value={'time':('time_scope','present'),'modality':('modality','fact'),'argument':('source_argument_role','EFFECT')}[mutation]
        local=replace(local,qualifier_rows=tuple(replace(q,**{key:value}) if q.basis_binding_ref==meaning_basis.binding_ref else q for q in local.qualifier_rows))
    elif mutation=='swap':
        local=replace(local,initial_meaning_ref=local.reaction_ref,reaction_ref=local.initial_meaning_ref)
    elif mutation in {'checkpoint','source'}:
        local=replace(local,eligibility=replace(local.eligibility,**{('checkpoint_ref' if mutation=='checkpoint' else 'original_source_ref'):'foreign'}))
    elif mutation=='duplicate_unknown':
        rest=(*rest[:-1],hr.identify_selected_subjective_reception_decision(replace(rest[-1],selected_contribution_refs=decision.selected_contribution_refs)))
    if mutation=='downgrade':
        rows=tuple(hr.identify_selected_subjective_reception_decision(hr.SelectedSubjectiveReceptionDecisionV1(
            **{f.name:getattr(d,f.name) for f in fields(hr.SelectedSubjectiveReceptionDecisionV1)})) for d in selected.decisions)
        forged=hr.identify_selected_subjective_reception_input(replace(selected,decisions=rows))
        body=context[0].artifact.text
        changed=(context[0],plan,context[2],resolver,forged)
        assert not read_body(changed,body).passed
        return
    local=replace(local,seal_ref=c.initial_personal_meaning_seal(local))
    decision=hr.identify_selected_subjective_reception_decision(replace(decision,initial_received_personal_meaning=local))
    forged=hr.identify_selected_subjective_reception_input(replace(selected,decisions=(decision,*rest)))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.validate_selected_subjective_reception_input(forged,plan.response_plan.human_reception_plan,plan,resolver)

@pytest.mark.parametrize('mutation',['polarity','time','scope','actor','relation'])
def test_new_source_witness_is_not_authority(context,mutation):
    _,plan,_,resolver,_=context
    group=gp._source_initial_personal_meaning_from_resolver(plan.nuclei,plan.relations,resolver)
    meaning=group[5];nuclei=plan.nuclei;relations=plan.relations
    if mutation=='relation':
        relations=(*relations,replace(group[-1],relation_id='invented',type='uncertain_connection',from_nucleus_id=meaning.nucleus_id,to_nucleus_id=group[0].nucleus_id))
    else:
        change={'polarity':dict(polarity='positive'),'time':dict(time_scope='present'),
                'scope':dict(attribute_codes=tuple(x for x in meaning.semantic_frame.attribute_codes if not x.startswith('source_initial_meaning_scope:'))),
                'actor':dict(actor='other_person')}[mutation]
        nuclei=tuple(replace(n,semantic_frame=replace(n.semantic_frame,**change)) if n==meaning else n for n in nuclei)
    assert not gp._source_initial_personal_meaning_from_resolver(nuclei,relations,resolver)

@pytest.mark.parametrize('memo,action',[
    (ROWS['received']['memo'].replace('期待されて','友達は期待されて'),''),
    (ROWS['received']['memo'].replace('期待されて','彼女は期待されて'),''),
    (ROWS['received']['memo'].replace('期待されて','今は期待されて'),''),
    (ROWS['received']['memo'],'机を片付けた。'),
    (ROWS['received']['memo']+'これは友人の話でした。',''),
    ('期待されているように感じて、重かった。褒められたのに、嬉しくなかった。',''),
])
def test_unapproved_source_orders_actors_times_and_extra_fields_excluded(memo,action):
    p=update.prepare_emlis_meaning(initial(memo,memo_action=action))
    plan=update.build_updated_grounded_plan(p)
    assert not gp._source_initial_personal_meaning_from_resolver(plan.nuclei,plan.relations,p.thread.resolver())


def test_initial_private_contract_inventory_preserves_answer_free_boundary():
    from cocolon_meaning_experience_engine.emlis_stage1_composition import _contract_manifest
    manifest=dict(_contract_manifest());assert manifest['logical_contract_count']==90
    rows={dict(row)['type_name']:dict(row) for row in manifest['logical_contract_descriptors']}
    for contract in (c.InitialReceivedPersonalMeaningEligibilityV1,c.InitialReceivedPersonalMeaningContentV1,c.InitialReceivedPersonalMeaningPairContentV1):
        row=rows[contract.__name__]
        assert row['logical_version']=='initial-personal-meaning-v1'
        assert tuple(dict(f)['field_name'] for f in row['fields'])==tuple(f.name for f in fields(contract))
        assert not any(f.name in {'answer_ref','answer_nucleus_ref','answer_relation_ref','update','answer_source_ref'} for f in fields(contract))


def test_initial_personal_source_does_not_replace_existing_self_denial_owner():
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    thread=admit_emlis_thread(initial('褒められたのに、嬉しくなかった。自分は価値がないと思って、重かった。'))
    old=original_meaning_plan(thread,_legacy_initial_personal_meaning=True)
    current=original_meaning_plan(thread)
    assert old.input_profile.safety_kind=='self_denial_safe_state_answer'
    assert current==old
    assert not gp._source_initial_personal_meaning_from_resolver(current.nuclei,current.relations,thread.resolver())
