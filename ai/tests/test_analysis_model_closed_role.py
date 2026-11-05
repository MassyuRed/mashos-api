"""An exact written role is a closed sentence, never a forward report host."""
import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from test_analysis_model_observed_actions import OWNER, sample, build


@pytest.mark.parametrize('self_word',['私','僕','自分'])
@pytest.mark.parametrize('copula',['だった','でした'])
@pytest.mark.parametrize('negative',[False,True])
@pytest.mark.parametrize('swap',[False,True])
def test_complete_positive_role_does_not_hide_a_separate_explicit_self_action(self_word,copula,negative,swap):
    role=self_word+'の役割は案内係'+copula+'。'
    action=self_word+'は費用を記録'+('しなかった。' if negative else 'した。')
    snap=sample();snap['members'][0]['original'].update(memo=action if swap else role,
        memo_action=role if swap else action)
    assert compiler._written_role_proposition(role) is not None
    assert not compiler._analysis_prefix_opens_report(role)
    snap,value,a,c=build(snap)
    normal,nc=service.build_cumulative_map(OWNER,snap)
    assert a is not None and len(a.graph.nodes)==2
    node=next(n for n in a.graph.nodes if n.node_kind=='ACTION_OR_NONACTION')
    finite=normal.graph.nodes[0]
    assert node.proposition==finite.proposition
    e,=node.evidence_refs;old,=finite.evidence_refs
    assert (e.field_path,e.scalar_start,e.scalar_end,e.utf8_start,e.utf8_end,e.literal_sha256)==(
        old.field_path,old.scalar_start,old.scalar_end,old.utf8_start,old.utf8_end,old.literal_sha256)
    assert node.node_kind=='ACTION_OR_NONACTION' and node.visible_label==action.rstrip('。')
    assert node.proposition.actor=='SELF' and node.polarity==('negative' if negative else 'positive')
    assert c['mapped_count']==1 and c['unparsed_count']==0 and a.graph.edges==()
    assert nc['unparsed_count']==1 and len(normal.graph.nodes)==1
    assert any(g.missing_scope=='ROUTE_CONNECTION' for g in a.graph.unknown_gaps)
    assert '案内係' in a.safe_text_projection(authenticated_owner_scope=OWNER)['text']


@pytest.mark.parametrize('host',['友人は言った。','聞いた内容は、','夢を見た。'])
@pytest.mark.parametrize('before',[False,True])
def test_closed_role_does_not_close_an_earlier_or_later_report(host,before):
    role='僕の役割は案内係だった。'
    text=host+role if before else role+host
    snap=sample();snap['members'][0]['original']['memo']=text
    _,_,a,c=build(snap)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('memo',['「僕の役割は案内係だった」と聞いた。',
    '友人は「僕の役割は案内係だった」と言った。',
    '夢では僕の役割は案内係だった。',
    '姉の役割は案内係だった。','僕の役割は何係だった。'])
def test_nonmatching_role_scope_never_uses_the_new_closure_exception(memo):
    assert compiler._written_role_proposition(memo) is None
    snap=sample();snap['members'][0]['original']['memo']=memo
    _,_,a,c=build(snap)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_conditional_role_keeps_the_existing_report_policy_without_a_closure_witness():
    text='僕の役割は案内係だったなら、'
    assert compiler._written_role_proposition(text) is None
    assert compiler._analysis_prefix_opens_report(text)==compiler._source_prefix_opens_report(text)


def test_uncertain_role_keeps_only_action_but_proved_negative_role_is_now_included():
    for role in ['僕の役割は案内係だったかもしれない。','僕の役割は案内係ではなかった。']:
        snap=sample();snap['members'][0]['original']['memo']=role
        _,_,a,c=build(snap)
        uncertain='かもしれない' in role
        assert a is not None and len(a.graph.nodes)==(1 if uncertain else 2)
        assert c['unparsed_count']==int(uncertain)
        assert any(n.node_kind=='ACTION_OR_NONACTION' for n in a.graph.nodes)


def test_closed_role_never_supplies_an_actor_to_an_omitted_action():
    snap=sample();snap['members'][0]['original'].update(memo='僕の役割は案内係だった。',memo_action='費用を記録した。')
    _,_,a,c=build(snap)
    normal,nc=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==nc
    assert c['mapped_count']==c['unparsed_count']==1
    node,=a.graph.nodes
    assert node.node_kind=='ACTION_OR_NONACTION' and node.proposition.actor=='UNSPECIFIED'
    assert node.visible_label=='費用を記録した' and not a.graph.edges
    assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '誰の行動かは未確定' in text and '案内係' not in text
