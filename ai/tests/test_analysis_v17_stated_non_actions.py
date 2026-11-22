"""A source can explicitly report a non-action and independently leave an outcome open."""
from copy import deepcopy
import json

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts


def material(text, *, source_role='ORIGINAL_INPUT', path='memo_action', **attrs):
    return {'fields': [dict(field=7, field_path=path, source_role=source_role, text=text, **attrs)]}


@pytest.mark.parametrize('source,part,closed', [
    ('会議では質問せず、同僚にも予定をまだ話していない。', '同僚にも予定をまだ話していない', True),
    ('今日は相談せず、担当者へ状況を説明していません。', '担当者へ状況を説明していません', True),
    ('私は先生に結果を答えていなかった。', '私は先生に結果を答えていなかった', True),
    ('私は予定を聞いていない。', '私は予定を聞いていない', False),
    ('連絡が来たかは聞いていない。', '連絡が来たかは聞いていない', False),
    ('私はまだ知らされていない。', '私はまだ知らされていない', False),
    ('担当者が予定を伝えていないかもしれない。', '担当者が予定を伝えていない', False),
    ('「友人に変更を伝えていない」と先生が話した。', '友人に変更を伝えていない', False),
    ('先生は言った。友人に変更を伝えていない。', '友人に変更を伝えていない', False),
    ('友人に変更を伝えていない。と先生は言った。', '友人に変更を伝えていない', False),
    ('もし中止なら、友人に変更を伝えていない。', '友人に変更を伝えていない', False),
    ('連絡を誰に伝えたかは分からない。', '連絡を誰に伝えたかは分からない', False),
    ('今回は相談せず、友人に結果を伝えていないが、相手が結果を知っていたかは分からない。',
     '相手が結果を知っていたかは分からない', False),
])
def test_only_outer_finite_nonaction_is_closed(source, part, closed):
    assert ((7, part) in choices.recorded_non_actions(material(source))) is closed


def test_source_role_and_complete_fragments_are_preserved():
    quote = '同僚に変更を話していない'
    for kwargs in [dict(source_role='SUPPLEMENTAL_ANSWER'), dict(source_role='USER_ANALYSIS_MAP_CORRECTION'),
                   dict(fragment_is_complete_field=False)]:
        assert not choices.recorded_non_actions(material(quote + '。', **kwargs))


def test_negative_action_from_established_reader_requires_explicit_scope():
    src = '私は資料を調べなかった。'
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo='', memo_action=src)
    p = maps.prepare_semantic_map(OWNER, snap, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE)
    m = json.loads(p.material_json)
    assert m['source_duties']['claims'][0]['reading']['predicate'] == '調べる'
    assert choices.recorded_non_actions(m) == {(1, src[:-1])}
    for key, val in [('actor','UNKNOWN'),('polarity','positive'),('time','future'),('dependent','QUOTE'),('modality','wish')]:
        other=deepcopy(m);other['source_duties']['claims'][0]['reading'][key]=val
        assert not choices.recorded_non_actions(other)


@pytest.mark.parametrize('uncertainty_source', [
    '担当者から連絡が来たかは聞いていない。',
    '私は予定を伝えていないが、担当者から連絡が来たかは聞いていない。',
])
def test_original_action_and_scoped_uncertainty_in_both_validators(uncertainty_source):
    known = '同僚にも予定をまだ話していない。'
    unknown = '担当者から連絡が来たかは聞いていない。'
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo='',memo_action=uncertainty_source + '今日は相談せず、' + known)
    p = maps.prepare_semantic_map(OWNER, snap, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE)
    f = json.loads(p.material_json)['fields'][0]['field']
    evidence = [dict(field=f,quote=text) for text in ['今日は相談せず、' + known, uncertainty_source]]
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[dict(node_id='n1',units=[dict(evidence=evidence)])])
    facts = {core._semantic_fact_part_key(evidence,i): e['quote'] for i,e in enumerate(evidence)}
    u = dict(evidence_ref='n1.u1',source_mode='RECORDED',fact_parts=facts,
        unknowns=[dict(source_field=f,source_quote=text) for text in (known, unknown)])
    bodies = dict(schema_version=core._semantic_v4_schema('NODES'),plan_sha256=core.semantic_map_hash(plan),
        nodes={'n1':dict(units={'u1':u},node_kind='STATE_CONTEXT',perspective='SELF',title=uncertainty_source,meaning='')})
    joined = core._semantic_v4_join(plan,bodies)
    a,b=core._semantic_qualification_candidates(joined,predicate_cues=True)
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'),nodes_sha256=core.semantic_map_hash(joined),
        qualification_review={a:dict(status='OPEN',source_quote=known),b:dict(status='OPEN',source_quote=unknown)},
        edges=[],overview=dict(node_refs=['n1'],title='伝達と連絡の確認'))
    messages = core.semantic_node_local_v4_messages(p,'RELATIONS',plan=plan,nodes=bodies)
    assert not accepts(rel,messages)
    with pytest.raises(core.AnalysisSemanticMapError, match='qualification_review_invalid'):
        core.semantic_node_local_v4_relations(p,plan,bodies,rel)
    rel['qualification_review'][a] = dict(status='STATED')
    assert accepts(rel,messages)
    result=core.semantic_node_local_v4_relations(p,plan,bodies,rel)
    assert result['nodes'][0]['units'][0]['unknowns'] == [dict(source_field=f,source_quote=unknown)]


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_finite_nominal_talking_is_written_in_either_original_field(field):
    quote = '担当者にはまだ買い替えの話をしていない'
    assert (7, quote) in choices.recorded_non_actions(material(quote + '。', path=field))


@pytest.mark.parametrize('source', [
    '友人は悩んでいた。先生に結果をまだ伝えていない。',
    '上司から届いたメッセージ：先生に結果をまだ伝えていない。',
    '友人がくれた文面を転記する。先生に結果をまだ伝えていない。本人が連絡を済ませたかは確かめていない。',
    '私の記憶は曖昧だ。先生に結果をまだ伝えていない。そうだったか、すでに連絡したのかは覚えていない。',
    '何を相手に伝えたかは確かめていない。',
    'もし教室が変われば、先生にはまだ変更の話をしていない。',
    'その人に「変更の話をしていない」と言われた。',
])
def test_unresolved_third_party_or_subsequent_revision_keeps_qualification_open(source):
    for field in ('memo', 'memo_action'):
        assert not choices.recorded_non_actions(material(source, path=field))


def test_corroboration_stays_within_record_and_addressee():
    quote = '先生にはまだ変更の話をしていない'
    memo = material('場所が変わった。' + quote + '。', path='memo', record=3)['fields'][0]
    action = dict(memo, field=8, field_path='memo_action', text='私は先生にも変更を伝えていない。')
    for companion, accepted in [(action, True), (dict(action,record=4), False),
                                (dict(action,text='私は部員にも変更を伝えていない。'), False),
                                (dict(action,source_role='USER_ANALYSIS_MAP_CORRECTION'), False)]:
        assert ((7, quote) in choices.recorded_non_actions({'fields':[memo, companion]})) is accepted
