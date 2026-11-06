"""Existing model-unit input reaches ordinary maps only with whole-source proof."""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisSemanticError, canonical, generate_analysis_model_observed_actions,
    prepare_analysis_model_quoted_parent_units)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, freeze_analysis_sources, source_field_text)
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_quoted_parent_units import call


ERRORS=(AnalysisSemanticError,AnalysisSourceError)


def sample(negative=False, swap=False):
    snap=source_snapshot(1)
    role='僕の役割は案内係だったかもしれない。'
    action='僕は費用を記録'+('しなかった。' if negative else 'した。')
    snap['members'][0]['original'].update(memo=action if swap else role,
        memo_action=role if swap else action)
    return snap


def prepared(snap,prompt='selected_material.v4'):
    return service.prepare_cumulative_category_units(OWNER,snap,prompt_version=prompt)


def packet(p):
    fields=json.loads(p.messages()[1]['content'])['fields']
    return dict(fields=[dict(field=f['field'],units=[dict(quote=f['text'].rstrip('。'),
        node_kind='ROLE' if '役割は' in f['text'] else 'ACTION_OR_NONACTION',
        parent_quote=None,scope_role=None,qualifiers=[])]) for f in fields])


def build(snap=None, *, prompt='selected_material.v4', change=None):
    snap=sample() if snap is None else snap
    p=prepared(snap,prompt);data=packet(p)
    if change:change(data)
    value=call(p,data)
    artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=value)
    return snap,value,artifact,coverage


@pytest.mark.parametrize('prompt',['selected_material.v2','selected_material.v4'])
@pytest.mark.parametrize('negative',[False,True])
@pytest.mark.parametrize('swap',[False,True])
def test_model_entry_keeps_normal_action_proof_and_leaves_the_other_field_unread(prompt,negative,swap):
    snap,value,a,c=build(sample(negative,swap),prompt=prompt)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    UUID(a.artifact_id[9:])
    node,=a.graph.nodes
    assert node.node_kind=='ACTION_OR_NONACTION' and node.proposition.actor=='SELF'
    assert node.polarity==('negative' if negative else 'positive')
    assert node.modality=='fact' and node.temporal_scope=='past'
    assert node.selected_categories==('仕事',) and not a.graph.edges
    assert c['source_count']==c['processed_count']==c['mapped_count']==c['unparsed_count']==1
    assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert 'かもしれない' not in text and 'まだ読み取れていない' in text
    assert text==normal.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    frozen=freeze_analysis_sources(value.request); source,=frozen.sources; e,=node.evidence_refs
    assert a.source_set_ref==frozen.source_set_ref and a.source_members==frozen.members
    field=source_field_text(source,e.field_path)
    assert field[e.scalar_start:e.scalar_end]==node.visible_label
    assert source.envelope.raw_utf8[e.utf8_start:e.utf8_end].decode()==node.visible_label
    assert e.field_sha256==hashlib.sha256(field.encode()).hexdigest()
    candidate,counts=service.build_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value)
    assert counts['mapped_count']==0 and counts['unparsed_count']==1
    assert all(u.actor=='UNRESOLVED_NOT_OWNER_DERIVED' for f in candidate.graph.fields for u in f.units)


def test_single_complete_action_field_has_no_invented_unread_scope():
    snap=sample();snap['members'][0]['original']['memo']=''
    _,_,a,c=build(snap)
    assert a is not None and c['mapped_count']==1 and c['unparsed_count']==0
    assert not any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)


@pytest.mark.parametrize('memo', ['友人は「準備ができた」と言った。',
    '友人は「準備ができた」と言う。','友人は「準備ができた」と言わなかった。',
    '友人は「準備ができた。','友人は言う。','友人は言わなかった。',
    '夢を見た。','聞いた話だ。','読んだ内容は、'])
def test_other_field_report_or_dream_never_disappears_from_the_source_check(memo):
    snap=sample();snap['members'][0]['original']['memo']=memo
    _,_,a,c=build(snap)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('action',['姉は費用を記録した。',
    '僕は費用を記録したかもしれない。','僕は費用を記録したと思った。',
    '僕は費用を記録したという話だった。','僕は費用を記録している。',
    '僕は費用を記録した。まだ分からない。','昨日、僕は費用を記録した。',
    '僕は費用を記録したい。','僕は費用を記録した。その後、僕は資料を見た。'])
def test_model_root_cannot_prove_other_actor_embedded_or_incomplete_action(action):
    snap=sample();snap['members'][0]['original']['memo_action']=action
    _,_,a,c=build(snap)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('change',['kind','child_under_thought','false_actor','false_negation',
    'modifier','extra_root','unread_root'])
def test_model_units_must_match_the_complete_source_proved_action(change):
    def edit(data):
        units=data['fields'][1]['units'];u=units[0]
        if change=='kind':u['node_kind']='ROLE'
        if change=='child_under_thought':
            parent=copy.deepcopy(u);parent['node_kind']='ATTENTION_OR_THOUGHT';parent['quote']+='。'
            u.update(node_kind=None,parent_quote=parent['quote'],scope_role='CONTENT_TARGET')
            units.append(parent)
        if change=='false_actor':u['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='費用')]
        if change=='false_negation':u['qualifiers']=[dict(kind='NEGATION',quote='した')]
        if change=='modifier':u['qualifiers']=[dict(kind='WRITTEN_MODIFIER',quote='した')]
        if change=='extra_root':units.append(dict(quote='費用',node_kind='SCENE',parent_quote=None,scope_role=None,qualifiers=[]))
        if change=='unread_root':units.clear()
    _,_,a,c=build(change=edit)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_negative_operators_and_object_children_remain_bound_to_the_original_field():
    def edit(data):
        u=data['fields'][1]['units'][0]
        u['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='僕'),dict(kind='NEGATION',quote='しなかった')]
        data['fields'][1]['units'].append(dict(quote='費用',node_kind=None,parent_quote=u['quote'],scope_role='CONTENT_TARGET',qualifiers=[]))
    snap,value,a,c=build(sample(True),change=edit)
    assert a.graph.nodes[0].polarity=='negative'
    p=prepared(snap)
    frozen=freeze_analysis_sources(p.request)
    with patch.object(compiler,'compile_observed_graph',wraps=compiler.compile_observed_graph) as checked:
        again,_=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert checked.call_count==1 and checked.call_args.args[0]==frozen
    assert again.graph==a.graph


@pytest.mark.parametrize('change',['raw','hash','request','owner','record','category','multi_record'])
def test_model_response_and_owner_snapshot_binding_are_not_reassigned(change):
    snap,value,_,_=build()
    if change=='raw':value=replace(value,response=replace(value.response,raw=value.response.raw+' '))
    if change=='hash':value=replace(value,response=replace(value.response,raw_sha256='0'*64))
    if change=='request':value=replace(value,request_ref=value.request_ref+'changed')
    if change=='record':snap['members'][0]['original']['memo_action']='僕は予定を記録した。'
    if change=='category':snap['members'][0]['original']['category']=['生活']
    if change=='multi_record':
        # A larger, freshly bound snapshot is now qualified. The old one-record
        # response must still never be reassigned after another record appears.
        snap['members'].append(source_snapshot(2)['members'][1])
    with pytest.raises(ERRORS):
        service.build_cumulative_map('00000000-0000-0000-0000-000000000002' if change=='owner' else OWNER,snap,model_input=value)


def test_comparison_is_not_silently_used_as_an_action_only_request():
    snap=sample();p=prepared(snap)
    req=replace(p.request,comparison_previous_request=p.request)
    with pytest.raises(ERRORS):
        other=prepare_analysis_model_quoted_parent_units(req,source_guard=p.source_guard,prompt_version=p.prompt_version)
        generate_analysis_model_observed_actions(req,call(other,packet(other)))


@pytest.mark.parametrize('memo',['雨宿りのメモ。','連絡先の控え。','まだ決めていない。'])
def test_nonempty_unread_other_field_is_counted_even_without_a_shared_nucleus(memo):
    snap=sample();snap['members'][0]['original']['memo']=memo
    _,_,a,c=build(snap)
    assert a is not None and c['mapped_count']==c['unparsed_count']==1
    assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)
    assert memo.rstrip('。') not in a.safe_text_projection(authenticated_owner_scope=OWNER)['text']


def test_edited_original_never_reuses_old_answers_and_keeps_the_stale_count():
    snap=sample();old=copy.deepcopy(snap['members'][0]['original']);old['memo']='僕は仕事を続けた。'
    snap['members'][0]['thread']=dict(user_id=OWNER,original_emotion_id=old['id'],source_snapshot=old)
    snap['members'][0]['events']=[dict(kind='ANSWER')]
    _,_,a,c=build(snap)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    assert c['stale_supplement_count']==1


@pytest.mark.parametrize('omitted',[False,True])
def test_ordinary_saved_wire_restores_both_views_without_model_or_compiler(tmp_path,omitted):
    snap=sample()
    if omitted:snap['members'][0]['original']['memo_action']='費用を記録した。'
    snap,value,a,c=build(snap)
    projection=a.safe_projection(authenticated_owner_scope=OWNER)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=text,content_json=dict(report_mode='standard',watashiMap=projection,map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    path=tmp_path/'ordinary-map.json';path.write_text(canonical(expected))
    rpc=AsyncMock(return_value=json.loads(path.read_text()))
    forbidden=AssertionError('saved read must not regenerate')
    with patch.object(service,'_rpc',rpc),patch.object(MeaningExperienceEngine,'generate',side_effect=forbidden),\
         patch.object(compiler,'compile_observed_graph',side_effect=forbidden),\
         patch.object(compiler,'compile_model_observed_actions',side_effect=forbidden),\
         patch.object(author,'realize_observed_graph',side_effect=forbidden),\
         patch.object(author,'generate_observed_map',side_effect=forbidden):
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected
    assert rpc.call_args.args[1]['p_user_id']==OWNER
    private=service.private_storage_evidence(a)
    assert private['schema_version']=='analysis.private-evidence.v1'
    assert 'かもしれない' not in canonical(private) and value.response.raw not in canonical(private)
    if omitted:
        assert a.graph.nodes[0].proposition.actor=='UNSPECIFIED'
        assert '誰の行動かは未確定' in text
        assert c['mapped_count']==c['unparsed_count']==1
        assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)


@pytest.mark.parametrize('field',['memo','memo_action'])
@pytest.mark.parametrize('literal,lemma',[
    ('振り返りメモを書いた','書く'),('資料を調べた','調べる'),
    ('方法を試した','試す'),('新しいメモ帳を見た','見る'),
    ('資料を作った','作る'),('仕事メモを残した','残す'),
    ('費用を記録した','記録する'),('予定をメモした','メモする'),
    ('仕事を続けた','続ける'),('私の考えを書いた','書く'),
    ('費用を記録しなかった','記録する'),('資料を調べなかった','調べる')])
def test_model_keeps_existing_complete_omitted_action_without_assigning_an_actor(literal,lemma,field):
    snap=sample();snap['members'][0]['original'].update(memo='',memo_action='')
    snap['members'][0]['original'][field]=literal+'。'
    _,value,a,c=build(snap)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    assert c['mapped_count']==1 and c['unparsed_count']==0
    node,=a.graph.nodes
    assert (node.proposition.actor,node.proposition.predicate_lemma,node.modality,node.temporal_scope)==(
        'UNSPECIFIED',lemma,'fact','past')
    assert node.polarity==('negative' if 'なかった' in literal else 'positive')
    assert node.visible_label==literal and not a.graph.edges
    assert node.selected_categories==('仕事',)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '誰の行動かは未確定' in text and text==normal.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    source,=freeze_analysis_sources(value.request).sources
    evidence,=node.evidence_refs
    assert source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode()==literal
    assert hashlib.sha256(literal.encode()).hexdigest()==evidence.literal_sha256


@pytest.mark.parametrize('field',['memo','memo_action'])
def test_polite_omitted_negative_keeps_existing_source_field_support(field):
    snap=sample();snap['members'][0]['original'].update(memo='',memo_action='')
    snap['members'][0]['original'][field]='資料を調べなかったです。'
    _,_,a,c=build(snap)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert c==normal_counts
    if field=='memo':
        assert a is not None and a.graph==normal.graph
        assert a.graph.nodes[0].proposition.actor=='UNSPECIFIED'
        assert a.graph.nodes[0].polarity=='negative'
    else:
        # The existing shared source proof does not establish this action
        # field form. The model label must not manufacture that proof.
        assert a is None and normal is None and c['mapped_count']==0


@pytest.mark.parametrize('actor_quote',['私','考え'])
def test_possessive_or_object_qualifier_cannot_supply_omitted_actor(actor_quote):
    snap=sample();snap['members'][0]['original'].update(memo='私の考えを書いた。',memo_action='')
    def edit(data):data['fields'][0]['units'][0]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote=actor_quote)]
    _,_,a,c=build(snap,change=edit)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_omitted_negative_action_keeps_bound_negation_and_target_child():
    snap=sample();snap['members'][0]['original'].update(memo='費用を記録しなかった。',memo_action='')
    def edit(data):
        root=data['fields'][0]['units'][0]
        root['qualifiers']=[dict(kind='NEGATION',quote='しなかった')]
        data['fields'][0]['units'].append(dict(quote='費用',node_kind=None,
            parent_quote=root['quote'],scope_role='CONTENT_TARGET',qualifiers=[]))
    _,_,a,c=build(snap,change=edit)
    assert a is not None and c['unparsed_count']==0
    node,=a.graph.nodes
    assert node.proposition.actor=='UNSPECIFIED' and node.polarity=='negative'


def test_omitted_actor_occurrences_never_become_same_person_recurrence():
    snap=source_snapshot(2)
    for member in snap['members']:member['original'].update(memo='資料を調べた。',memo_action='')
    _,_,a,c=build(snap)
    assert a is not None and c['mapped_count']==2 and c['unparsed_count']==0
    assert len(a.graph.nodes)==2 and not a.graph.edges
    assert all(n.proposition.actor=='UNSPECIFIED' and len(n.record_refs)==1 for n in a.graph.nodes)
    assert a.graph.nodes[0].evidence_refs!=a.graph.nodes[1].evidence_refs


@pytest.mark.parametrize('literal',['私は、\n資料を調べた。','資料を調べたという話だった。',
    '資料を調べたと思った。','資料を調べたい。','資料を調べている。',
    '資料を調べた。まだ分からない。'])
def test_omitted_action_keeps_whole_source_and_incomplete_topic_boundary(literal):
    snap=sample();snap['members'][0]['original'].update(memo=literal,memo_action='')
    _,_,a,c=build(snap)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def sequence_build(text,quotes,*,change=None,snapshot_change=None):
    snap=source_snapshot(1)
    snap['members'][0]['original'].update(memo=text,memo_action='')
    if snapshot_change:snapshot_change(snap)
    p=prepared(snap)
    units=[dict(quote=quote,node_kind='ACTION_OR_NONACTION',parent_quote=None,
        scope_role=None,qualifiers=[]) for quote in quotes]
    data=dict(fields=[dict(field=1,units=units)])
    if change:change(data)
    value=call(p,data)
    artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=value)
    return snap,value,artifact,coverage


@pytest.mark.parametrize('text,quotes,ordered',[
    ('僕は資料を調べた。僕は費用を記録した。',
        ['僕は資料を調べた','僕は費用を記録した'],False),
    ('私は資料を見た。その後、私は分担を決めた。',
        ['私は資料を見た','私は分担を決めた'],True),
    ('私は資料を作らなかった。それから、私は予定をメモした。',
        ['私は資料を作らなかった','私は予定をメモした'],True),
    ('私は資料を調べた。私は分担を決めなかった。私は仕事を続けた。',
        ['私は資料を調べた','私は分担を決めなかった','私は仕事を続けた'],False)])
def test_complete_multiple_model_actions_keep_original_graph_and_written_order(text,quotes,ordered):
    snap,_,a,c=sequence_build(text,quotes)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    assert c['mapped_count']==1 and c['unparsed_count']==0
    assert len(a.graph.nodes)==len(quotes) and len(a.graph.edges)==int(ordered)
    assert all(n.proposition.actor=='SELF' and n.selected_categories==('仕事',) for n in a.graph.nodes)
    assert all(e.edge_kind=='OBSERVED_ORDER' for e in a.graph.edges)
    if not ordered:
        assert any(g.missing_scope=='ROUTE_CONNECTION' for g in a.graph.unknown_gaps)
    assert a.safe_text_projection(authenticated_owner_scope=OWNER)['text']==normal.safe_text_projection(authenticated_owner_scope=OWNER)['text']


def test_model_unit_order_and_omitted_sequence_prefix_do_not_rewrite_source_order():
    text='私は資料を見た。その後、私は分担を決めた。'
    quotes=['私は資料を見た','私は分担を決めた']
    def edit(data):
        for u in data['fields'][0]['units']:
            u['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='私は')]
        data['fields'][0]['units'].reverse()
    snap,_,a,_=sequence_build(text,quotes,change=edit)
    normal,_=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph
    assert a.graph.edges[0].endpoint_refs==('n1','n2')


@pytest.mark.parametrize('mutation',['missing','kind','combined','extra','cross_child','false_actor','false_negative'])
def test_multiple_action_packet_must_prove_every_clause_once(mutation):
    text='僕は資料を調べた。僕は費用を記録した。'
    quotes=['僕は資料を調べた','僕は費用を記録した']
    def edit(data):
        units=data['fields'][0]['units']
        if mutation=='missing':units.pop()
        if mutation=='kind':units[1]['node_kind']='ROLE'
        if mutation=='combined':units[:]=[dict(units[0],quote=text.rstrip('。'))]
        if mutation=='extra':units.append(dict(units[0],quote='資料',node_kind='SCENE'))
        if mutation=='cross_child':units.append(dict(quote='費用',node_kind=None,
            parent_quote=quotes[0],scope_role='CONTENT_TARGET',qualifiers=[]))
        if mutation=='false_actor':units[1]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='費用')]
        if mutation=='false_negative':units[1]['qualifiers']=[dict(kind='NEGATION',quote='した')]
    try:
        _,_,a,c=sequence_build(text,quotes,change=edit)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('text,quotes',[
    ('僕は資料を調べた。不明な出来事があった。僕は費用を記録した。',
        ['僕は資料を調べた','僕は費用を記録した']),
    ('僕は資料を調べた。僕は費用を記録した。まだ分からない。',
        ['僕は資料を調べた','僕は費用を記録した']),
    ('僕は資料を調べた。姉は費用を記録した。',
        ['僕は資料を調べた','姉は費用を記録した']),
    ('僕は資料を調べた。費用を記録した。',
        ['僕は資料を調べた','費用を記録した']),
    ('その後、私は資料を見た。それから、私は分担を決めた。',
        ['私は資料を見た','私は分担を決めた'])])
def test_multiple_action_scope_does_not_hide_unread_text_or_assign_actors(text,quotes):
    _,_,a,c=sequence_build(text,quotes)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_multiple_action_saved_wire_preserves_both_views_without_compilation():
    text='僕は資料を調べた。僕は費用を記録した。'
    _,_,a,c=sequence_build(text,['僕は資料を調べた','僕は費用を記録した'])
    projection=a.safe_projection(authenticated_owner_scope=OWNER)
    content=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=content,content_json=dict(report_mode='standard',watashiMap=projection,map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    with patch.object(service,'_rpc',AsyncMock(return_value=json.loads(canonical(expected)))),\
         patch.object(compiler,'compile_observed_graph',side_effect=AssertionError('saved compiler')),\
         patch.object(author,'realize_observed_graph',side_effect=AssertionError('saved author')):
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected


PLAIN_ACTION_WISH = '私は考えをノートに書いた。私は仕事を続けたい。'


def wish_build(text=PLAIN_ACTION_WISH, *, kinds=('ACTION_OR_NONACTION', 'ATTENTION_OR_THOUGHT'),
        prompt='selected_material.v4', count=1, change=None, snapshot_change=None):
    snap=source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo=text,memo_action='')
    if snapshot_change:snapshot_change(snap)
    p=prepared(snap,prompt)
    fields=json.loads(p.messages()[1]['content'])['fields']
    data=dict(fields=[dict(field=f['field'],units=[dict(quote=quote,node_kind=kind,
        parent_quote=None,scope_role=None,qualifiers=[])
        for quote,kind in zip(f['text'].rstrip('。').split('。'),kinds)]) for f in fields])
    if change:change(data)
    value=call(p,data)
    artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=value)
    return snap,value,artifact,coverage


@pytest.mark.parametrize('prompt',['selected_material.v4','selected_material.v7'])
def test_complete_action_and_wish_keep_the_existing_source_graph_and_meaning(prompt):
    snap,_,a,c=wish_build(prompt=prompt)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    action,wish=a.graph.nodes
    assert (action.node_kind,action.modality,action.temporal_scope)==('ACTION_OR_NONACTION','fact','past')
    assert (wish.node_kind,wish.modality,wish.temporal_scope)==('ATTENTION_OR_THOUGHT','wish','current_input')
    assert all(n.proposition.actor=='SELF' for n in a.graph.nodes)
    assert c['mapped_count']==1 and c['unparsed_count']==0 and not a.graph.edges
    assert any(g.missing_scope=='ROUTE_CONNECTION' for g in a.graph.unknown_gaps)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert text==normal.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    labels=[n['visible_label'] for n in a.safe_projection(authenticated_owner_scope=OWNER)['nodes']]
    assert sum('実行済み' in label for label in labels)==1
    assert '仕事を続けることへの希望' in labels[1] and '実行済み' not in labels[1]


def test_twenty_complete_original_records_keep_each_action_and_wish_witness():
    snap,_,a,c=wish_build(count=20)
    assert a is not None and c['source_count']==c['processed_count']==c['mapped_count']==20
    assert c['unparsed_count']==0 and len(a.graph.nodes)==2 and not a.graph.edges
    refs={m['original']['id'] for m in snap['members']}
    for node in a.graph.nodes:
        assert set(node.record_refs)==refs and len(node.evidence_refs)==20
        assert node.selected_categories==('仕事',)
    assert a.graph.nodes[1].modality=='wish'


@pytest.mark.parametrize('literal,time',[('私は仕事を続けたい','current_input'),
    ('私は仕事を続けたかった','past')])
@pytest.mark.parametrize('prompt',['selected_material.v4','selected_material.v7'])
def test_single_plain_positive_wish_keeps_hope_and_its_written_time(literal,time,prompt):
    snap,_,a,c=wish_build(literal+'。',kinds=('ATTENTION_OR_THOUGHT',),prompt=prompt)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    node,=a.graph.nodes
    assert (node.modality,node.temporal_scope)==('wish',time)
    text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '希望' in text and ('（当時）' in text)==(time=='past')
    assert '実行済み' not in text and not a.graph.edges and c['unparsed_count']==0


@pytest.mark.parametrize('ending,time',[('たくない','current_input'),('たくなかった','past')])
@pytest.mark.parametrize('with_action',[False,True])
@pytest.mark.parametrize('with_negation_qualifier',[False,True])
@pytest.mark.parametrize('prompt',['selected_material.v4','selected_material.v7'])
def test_complete_negative_wish_uses_source_polarity_without_repairing_raw(
        ending,time,with_action,with_negation_qualifier,prompt):
    literal='私は仕事を続け'+ending
    text=('私は考えをノートに書いた。' if with_action else '')+literal+'。'
    kinds=(('ACTION_OR_NONACTION',) if with_action else ())+('ATTENTION_OR_THOUGHT',)
    sent=[]
    def edit(data):
        wish=data['fields'][0]['units'][-1]
        if with_negation_qualifier:
            wish['qualifiers']=[dict(kind='NEGATION',quote='続け'+ending)]
        sent.append(canonical(data))
    snap,value,a,c=wish_build(text,kinds=kinds,prompt=prompt,change=edit)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and normal is not None and a.graph==normal.graph and c==normal_counts
    assert value.response.raw==sent[0]
    assert value.response.raw_sha256==hashlib.sha256(sent[0].encode()).hexdigest()
    raw_wish=json.loads(value.response.raw)['fields'][0]['units'][-1]
    assert raw_wish['quote']==literal
    assert raw_wish['qualifiers']==([dict(kind='NEGATION',quote='続け'+ending)]
        if with_negation_qualifier else [])
    wish=a.graph.nodes[-1]
    assert (wish.node_kind,wish.proposition.actor,wish.polarity,wish.modality,wish.temporal_scope)==(
        'ATTENTION_OR_THOUGHT','SELF','negative','wish',time)
    assert wish.visible_label==literal and not a.graph.edges
    labels=[n['visible_label'] for n in a.safe_projection(authenticated_owner_scope=OWNER)['nodes']]
    assert labels[-1]=='選択カテゴリ：仕事\n仕事を続けることを望まない'+('（当時）' if time=='past' else '')
    assert sum('実行済み' in label for label in labels)==int(with_action)
    assert a.safe_text_projection(authenticated_owner_scope=OWNER)['text']==normal.safe_text_projection(
        authenticated_owner_scope=OWNER)['text']
    assert c['mapped_count']==1 and c['unparsed_count']==0


@pytest.mark.parametrize('ending',['たくない','たくなかった'])
@pytest.mark.parametrize('mutation',['operator_removed','kind','false_actor','false_negative'])
def test_negative_wish_cannot_lose_negation_or_change_type_or_actor(ending,mutation):
    def edit(data):
        wish=data['fields'][0]['units'][0]
        if mutation=='operator_removed':wish['quote']='私は仕事を続けたく'
        if mutation=='kind':wish['node_kind']='ACTION_OR_NONACTION'
        if mutation=='false_actor':wish['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='仕事')]
        if mutation=='false_negative':wish['qualifiers']=[dict(kind='NEGATION',quote='仕事')]
    try:
        _,_,a,c=wish_build('私は仕事を続け'+ending+'。',
            kinds=('ATTENTION_OR_THOUGHT',),change=edit)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('mutation',['kind','missing','operator_removed','false_actor',
    'false_negative','modifier','cross_child','extra_root'])
def test_wish_units_cannot_erase_the_operator_or_change_source_semantics(mutation):
    def edit(data):
        units=data['fields'][0]['units'];wish=units[1]
        if mutation=='kind':wish['node_kind']='ACTION_OR_NONACTION'
        if mutation=='missing':units.pop()
        if mutation=='operator_removed':wish['quote']='私は仕事を続け'
        if mutation=='false_actor':wish['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='仕事')]
        if mutation=='false_negative':wish['qualifiers']=[dict(kind='NEGATION',quote='たい')]
        if mutation=='modifier':wish['qualifiers']=[dict(kind='WRITTEN_MODIFIER',quote='たい')]
        if mutation=='cross_child':units.append(dict(quote='仕事',node_kind=None,
            parent_quote=units[0]['quote'],scope_role='CONTENT_TARGET',qualifiers=[]))
        if mutation=='extra_root':units.append(dict(wish,quote='仕事',node_kind='ROLE'))
    try:
        _,_,a,c=wish_build(change=edit)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('text',[
    '私は考えをノートに書いた。その後、私は仕事を続けたい。',
    '私は仕事を続けたい。その後、私は考えをノートに書いた。',
    '私は考えをノートに書かなかった。私は仕事を続けたい。',
    '私は考えをノートに書かなかった。私は仕事を続けたくない。',
    '私は考えをノートに書かなかった。私は仕事を続けたくなかった。',
    '私は考えをノートに書いた。その後、私は仕事を続けたくない。',
    '私は仕事を続けたくなかった。その後、私は考えをノートに書いた。',
    '私は考えをノートに書いた。仕事を続けたい。',
    '私は考えをノートに書いた。仕事を続けたくない。',
    '私は考えをノートに書いた。仕事を続けたくなかった。',
    '私は考えをノートに書いた。姉は仕事を続けたい。',
    '私は考えをノートに書いた。姉は仕事を続けたくない。',
    '私は考えをノートに書いた。姉は仕事を続けたくなかった。',
    '私は考えをノートに書いた。私は仕事を続けたいかもしれない。',
    '私は考えをノートに書いた。私は仕事を続けたくないかもしれない。',
    '私は考えをノートに書いた。まだ言葉にできない。私は仕事を続けたい。',
    '私は考えをノートに書いた。私は仕事を続けたい。まだ分からない。',
])
def test_new_wish_scope_does_not_add_order_negative_actions_actor_or_unread_scope(text):
    try:
        _,_,a,c=wish_build(text)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('text',[
    '私は記録を残した。私は資料を調べたかもしれないと思っている。',
    '私は記録を残した。私は仕事を続けたくないと思っている。',
])
def test_cognition_is_not_silently_admitted_as_a_plain_wish(text):
    _,_,a,c=wish_build(text)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('wish',['私は仕事を続けたい。',
    '私は仕事を続けたくない。','私は仕事を続けたくなかった。'])
def test_complete_wish_and_action_fields_use_their_own_original_proof(wish):
    def split(snap):
        snap['members'][0]['original'].update(memo=wish,memo_action='私は資料を見た。')
    def wish_kind(data):
        data['fields'][0]['units'][0]['node_kind']='ATTENTION_OR_THOUGHT'
    _,_,a,c=wish_build(snapshot_change=split,change=wish_kind)
    assert a is not None and len(a.graph.nodes)==2 and not a.graph.edges
    assert c['mapped_count']==1 and c['unparsed_count']==0
    assert {e.field_path for n in a.graph.nodes for e in n.evidence_refs}=={'memo','memo_action'}


@pytest.mark.parametrize('wish',['私は仕事を続けたい。',
    '私は仕事を続けたくない。','私は仕事を続けたくなかった。'])
def test_original_wish_proof_does_not_admit_supplement_wishes(wish):
    from test_analysis_saved_period import with_answer
    def answer(snap):
        original=snap['members'][0]['original']
        original['emotion_details']=[dict(type='平穏',strength='medium')]
        snap['members'][0]=with_answer(snap['members'][0],wish)
    def answer_kind(data):
        data['fields'][1]['units'][0]['node_kind']='ATTENTION_OR_THOUGHT'
    try:
        _,_,a,c=wish_build('私は資料を見た。',kinds=('ACTION_OR_NONACTION',),
            snapshot_change=answer,change=answer_kind)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def split_wish_build(memo, memo_action, *, prompt='selected_material.v7', change=None):
    snap=source_snapshot(1)
    snap['members'][0]['original'].update(memo=memo,memo_action=memo_action)
    p=prepared(snap,prompt)
    fields=json.loads(p.messages()[1]['content'])['fields']
    data=dict(fields=[dict(field=f['field'],units=[dict(quote=q,
        node_kind='ATTENTION_OR_THOUGHT' if any(x in q for x in ('たい','たかった','たくない','たくなかった'))
            else 'ACTION_OR_NONACTION',parent_quote=None,scope_role=None,qualifiers=[])
        for q in f['text'].rstrip('。').split('。')]) for f in fields])
    if change:change(data)
    value=call(p,data)
    artifact,coverage=service.build_cumulative_map(OWNER,snap,model_input=value)
    return snap,value,artifact,coverage


@pytest.mark.parametrize('ending,time,polarity',[('たい','current_input','positive'),
    ('たかった','past','positive'),('たくない','current_input','negative'),
    ('たくなかった','past','negative')])
@pytest.mark.parametrize('swap',[False,True])
@pytest.mark.parametrize('prompt',['selected_material.v4','selected_material.v7'])
def test_split_wish_keeps_whole_graph_field_evidence_and_written_meaning(ending,time,polarity,swap,prompt):
    texts=['私は資料を見た。','私は仕事を続け'+ending+'。']
    if swap:texts.reverse()
    snap,value,a,c=split_wish_build(*texts,prompt=prompt)
    normal,normal_counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==normal_counts
    assert len(a.graph.nodes)==2 and not a.graph.edges and c['unparsed_count']==0
    assert any(g.missing_scope=='ROUTE_CONNECTION' for g in a.graph.unknown_gaps)
    assert not any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)
    wish,=tuple(n for n in a.graph.nodes if n.node_kind=='ATTENTION_OR_THOUGHT')
    assert (wish.proposition.actor,wish.modality,wish.temporal_scope,wish.polarity)==('SELF','wish',time,polarity)
    source,=freeze_analysis_sources(value.request).sources
    for node in a.graph.nodes:
        e,=node.evidence_refs
        text=source_field_text(source,e.field_path)
        assert text[e.scalar_start:e.scalar_end]==node.visible_label
        assert source.envelope.raw_utf8[e.utf8_start:e.utf8_end].decode()==node.visible_label
        assert e.field_sha256==hashlib.sha256(text.encode()).hexdigest()
    actual_text=a.safe_text_projection(authenticated_owner_scope=OWNER)
    expected_text=normal.safe_text_projection(authenticated_owner_scope=OWNER)
    assert {k:v for k,v in actual_text.items() if k!='projection_of'}=={
        k:v for k,v in expected_text.items() if k!='projection_of'}
    assert value.response.raw_sha256==hashlib.sha256(value.response.raw.encode()).hexdigest()


@pytest.mark.parametrize('wish',['私は仕事を続けたい。','私は仕事を続けたかった。',
    '私は仕事を続けたくない。','私は仕事を続けたくなかった。'])
def test_single_memo_action_wish_uses_its_own_source_field(wish):
    snap,_,a,c=split_wish_build('',wish)
    normal,counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==counts and c['unparsed_count']==0
    assert a.graph.nodes[0].evidence_refs[0].field_path=='memo_action'


def test_split_fields_cover_each_clause_in_its_own_scalar_coordinate_space():
    snap,_,a,c=split_wish_build('私は資料を見た。私は仕事を続けたい。',
        '私は考えをノートに書きたくなかった。')
    normal,counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==counts
    assert len(a.graph.nodes)==3 and not a.graph.edges and c['unparsed_count']==0


@pytest.mark.parametrize('memo,memo_action',[
    ('私は資料を見なかった。','私は仕事を続けたい。'),
    ('友人は言った。','私は仕事を続けたい。'),
    ('私は仕事を続けたい。','友人は「準備できた」と言った。'),
    ('私は資料を見た。','私は仕事を続けたい。まだ分からない。'),
    ('私は仕事を続けたい。','私は資料を調べたい。'),
    ('私は資料を見た。私は仕事を続けたい。','私は資料を見た。'),
])
def test_split_fields_do_not_supply_an_actor_close_reports_or_discard_unread_material(memo,memo_action):
    try:
        _,_,a,c=split_wish_build(memo,memo_action)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('wish',['仕事を続けたい。','姉は仕事を続けたい。',
    '私は仕事を続けたいかもしれない。'])
def test_unproved_other_field_keeps_the_existing_partial_action_and_unread_gap(wish):
    snap,_,a,c=split_wish_build('私は資料を見た。',wish)
    normal,counts=service.build_cumulative_map(OWNER,snap)
    assert a is not None and a.graph==normal.graph and c==counts
    node,=a.graph.nodes
    assert node.node_kind=='ACTION_OR_NONACTION' and node.visible_label=='私は資料を見た'
    assert c['mapped_count']==1 and c['unparsed_count']==1 and not a.graph.edges
    assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)


@pytest.mark.parametrize('mutation',['wrong_kind','missing_clause','cross_child','wrong_actor'])
def test_split_wish_model_units_still_need_their_own_complete_source_proof(mutation):
    def edit(data):
        wish=data['fields'][1]['units'][0]
        if mutation=='wrong_kind':wish['node_kind']='ACTION_OR_NONACTION'
        if mutation=='missing_clause':data['fields'][1]['units']=[]
        if mutation=='wrong_actor':wish['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='仕事')]
        if mutation=='cross_child':data['fields'][0]['units'].append(dict(quote='資料',
            parent_quote=wish['quote'],node_kind=None,scope_role='CONTENT_TARGET',qualifiers=[]))
    try:
        _,_,a,c=split_wish_build('私は資料を見た。','私は仕事を続けたい。',change=edit)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_split_wish_saved_map_replays_without_source_compilation_or_authoring():
    _,_,a,c=split_wish_build('私は資料を見た。','私は仕事を続けたくなかった。')
    assert a is not None
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    with patch.object(service,'_rpc',AsyncMock(return_value=json.loads(canonical(expected)))),\
         patch.object(compiler,'compile_observed_graph',side_effect=AssertionError('saved compiler')),\
         patch.object(compiler,'compile_model_observed_actions',side_effect=AssertionError('saved model compiler')),\
         patch.object(compiler,'_model_complete_observed_plain_wishes',side_effect=AssertionError('saved wish proof')),\
         patch.object(author,'realize_observed_graph',side_effect=AssertionError('saved author')),\
         patch.object(author,'generate_observed_map',side_effect=AssertionError('saved map author')):
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected


@pytest.mark.parametrize('wish',['私は仕事を続けたい。',
    '私は仕事を続けたくない。','私は仕事を続けたくなかった。'])
def test_action_wish_saved_wire_replays_without_compiler_or_author(wish):
    _,_,a,c=wish_build('私は考えをノートに書いた。'+wish)
    assert a is not None
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    with patch.object(service,'_rpc',AsyncMock(return_value=json.loads(canonical(expected)))),\
         patch.object(compiler,'compile_observed_graph',side_effect=AssertionError('saved compiler')),\
         patch.object(compiler,'compile_model_observed_actions',side_effect=AssertionError('saved model compiler')),\
         patch.object(compiler,'_model_complete_observed_plain_wishes',side_effect=AssertionError('saved wish proof')),\
         patch.object(author,'realize_observed_graph',side_effect=AssertionError('saved author')),\
         patch.object(author,'generate_observed_map',side_effect=AssertionError('saved map author')):
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected
