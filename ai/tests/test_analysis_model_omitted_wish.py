"""An original's one complete plain wish never acquires an unwritten actor.

These synthetic packets test the finite consumer and evidence contract. They
are not new model responses or a historical before/after generation trial.
"""
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
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, freeze_analysis_sources)
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_actor_profile import unit
from test_analysis_model_observed_actions import prepared
from test_analysis_model_quoted_parent_units import call
from test_analysis_model_supplement_wish import assert_source_evidence, supplement_fixture
from test_analysis_saved_period import with_answer


PROFILE = 'selected_material.v13'
ERRORS = (admission.AnalysisSemanticError, AnalysisSourceError)
FORMS = [
    ('たい', 'current_input', 'positive'), ('たかった', 'past', 'positive'),
    ('たくない', 'current_input', 'negative'), ('たくなかった', 'past', 'negative'),
]
LEXEMES = [
    ('記録を書き', '書く'), ('資料を調べ', '調べる'), ('方法を試し', '試す'),
    ('資料を見', '見る'), ('模型を作り', '作る'), ('記録を残し', '残す'),
    ('費用を記録し', '記録する'), ('予定をメモし', 'メモする'), ('仕事を続け', '続ける'),
]


def fixture(text='写真を見たかった。', *, profile=PROFILE, count=1,
        field='memo', quote=None, qualifiers=(), change=None):
    snap = source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo='', memo_action='')
        member['original'][field] = text
    p = prepared(snap, profile)
    fields = json.loads(p.messages()[1]['content'])['fields']
    data = dict(fields=[dict(field=f['field'], units=[unit(
        f['text'].strip().rstrip('。') if quote is None else quote,
        'ATTENTION_OR_THOUGHT', qualifiers=qualifiers)]) for f in fields])
    if change:
        change(data)
    return snap, p, call(p, data)


def assert_unread(snap, value):
    try:
        artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    except ERRORS:
        return
    assert artifact is None
    assert counts['mapped_count'] == 0 and counts['unparsed_count'] == len(snap['members'])


@pytest.mark.parametrize('ending,time,polarity', FORMS)
@pytest.mark.parametrize('object_and_stem,lemma', LEXEMES)
def test_nine_plain_wish_verbs_keep_omitted_actor_and_their_own_complete_source(
        object_and_stem, lemma, ending, time, polarity):
    finite = object_and_stem.split('を', 1)[1] + ending
    qualifiers = [dict(kind='NEGATION', quote=finite)] if polarity == 'negative' else []
    snap, p, value = fixture(object_and_stem + ending + '。', qualifiers=qualifiers)
    before = copy.deepcopy(snap)
    raw, raw_hash = value.response.raw, value.response.raw_sha256
    candidate, coverage = service.build_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value)
    saved = service.serialize_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value, artifact=candidate, coverage=coverage)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    normal, normal_counts = service.build_cumulative_map(OWNER, snap)
    assert artifact is not None and normal is not None
    assert artifact.graph == normal.graph and counts == normal_counts
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == counts['excluded_count'] == 0
    node, = artifact.graph.nodes
    assert (node.node_kind, node.proposition.actor, node.proposition.predicate_lemma,
        node.modality, node.temporal_scope, node.polarity) == (
            'ATTENTION_OR_THOUGHT', 'UNSPECIFIED', lemma, 'wish', time, polarity)
    assert node.visible_label == object_and_stem + ending
    assert node.record_refs == (snap['members'][0]['original']['id'],)
    assert node.selected_categories == ('仕事',) and not node.update_refs
    assert len(node.evidence_refs) == 1 and node.evidence_refs[0].field_path == 'memo'
    assert not artifact.graph.edges and not artifact.graph.annotations and not artifact.graph.conflicts
    assert {g.missing_scope for g in artifact.graph.unknown_gaps} == {
        'SCENE', 'ROLE', 'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'}
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    label = projection['nodes'][0]['visible_label']
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '誰の希望かは未確定' in label and '誰の希望かは未確定' in text
    assert ('当時' in label) == (time == 'past')
    assert ('ことを望まない' in label) == (polarity == 'negative')
    assert '実行済み' not in text and '（1件の記録）' in text
    assert projection['nodes'][0]['evidence_badge_count'] == 1
    frozen = freeze_analysis_sources(p.request)
    assert artifact.source_members == frozen.members and artifact.source_set_ref == frozen.source_set_ref
    assert_source_evidence(artifact, frozen)
    assert candidate.graph.fields[0].units[0].actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
    # The candidate/raw before and after the typed proof are the same packet.
    again, again_coverage = service.build_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value)
    assert service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=again, coverage=again_coverage) == saved
    assert json.loads(saved)['state']['response']['raw'] == raw
    assert value.response.raw == raw and value.response.raw_sha256 == raw_hash
    assert raw_hash == hashlib.sha256(raw.encode()).hexdigest() and snap == before


@pytest.mark.parametrize('profile', ['selected_material.v4', 'selected_material.v7', PROFILE])
def test_omitted_actor_proof_does_not_depend_on_a_new_prompt(profile):
    snap, _, value = fixture(profile=profile)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['mapped_count'] == 1 and counts['unparsed_count'] == 0
    assert artifact.graph.nodes[0].proposition.actor == 'UNSPECIFIED'


@pytest.mark.parametrize('ending,time,polarity', FORMS[2:])
def test_complete_negative_wish_needs_no_synthetic_negation_qualifier(ending, time, polarity):
    snap, _, value = fixture('写真を見' + ending + '。')
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['unparsed_count'] == 0
    node, = artifact.graph.nodes
    assert (node.polarity, node.modality, node.temporal_scope) == (polarity, 'wish', time)
    assert json.loads(value.response.raw)['fields'][0]['units'][0]['qualifiers'] == []


@pytest.mark.parametrize('prefix,expected_nodes', [('', 2), ('私は', 1)])
def test_two_records_never_identify_omitted_actors_but_keep_existing_self_aggregation(prefix, expected_nodes):
    qualifiers = [dict(kind='EXPLICIT_ACTOR', quote='私')] if prefix else []
    snap, _, value = fixture(prefix + '写真を見たかった。', count=2, qualifiers=qualifiers)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and len(artifact.graph.nodes) == expected_nodes
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 2
    assert counts['unparsed_count'] == 0 and not artifact.graph.edges
    nodes = artifact.graph.nodes
    if prefix:
        assert len(nodes[0].record_refs) == len(nodes[0].evidence_refs) == 2
        assert nodes[0].proposition.actor == 'SELF'
    else:
        assert all(n.proposition.actor == 'UNSPECIFIED' for n in nodes)
        assert all(len(n.record_refs) == len(n.evidence_refs) == 1 for n in nodes)
        assert {n.record_refs[0] for n in nodes} == {m['original']['id'] for m in snap['members']}
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert [n['evidence_badge_count'] for n in projection['nodes']] == ([2] if prefix else [1, 1])
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert ('（2件の記録）' in text) == bool(prefix)
    assert text.count('（1件の記録）') == (0 if prefix else 2)
    assert_source_evidence(artifact, freeze_analysis_sources(value.request))


def test_object_ownership_is_not_an_actor_witness():
    snap, _, value = fixture('私の写真を見たかった。')
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['unparsed_count'] == 0
    node, = artifact.graph.nodes
    assert node.proposition.actor == 'UNSPECIFIED'
    assert node.proposition.arguments == (('を', '私の写真'),)
    snap, _, forged = fixture('私の写真を見たかった。',
        qualifiers=[dict(kind='EXPLICIT_ACTOR', quote='私')])
    assert_unread(snap, forged)


@pytest.mark.parametrize('text,quote', [
    ('友人は写真を見たかった。', '写真を見たかった'),
    ('写真を見たかったと思った。', '写真を見たかった'),
    ('写真を見たかったかもしれない。', '写真を見たかった'),
    ('「写真を見たかった」と友人は言った。', '写真を見たかった'),
    ('写真を見たかったのか。', '写真を見たかった'),
    ('写真を見たかった？', '写真を見たかった'),
    ('写真を見たかった。写真を見たい。', '写真を見たかった'),
    ('写真を見たかった。まだ分からない。', '写真を見たかった'),
    ('資料を見た。写真を見たかった。', '写真を見たかった'),
    ('その後、写真を見たかった。', '写真を見たかった'),
    ('昨日、写真を見たかった。', '写真を見たかった'),
    ('少し写真を見たかった。', '写真を見たかった'),
    ('写真を見たいです。', '写真を見たいです'),
    ('見たかった。', '見たかった'),
    ('写真が見たかった。', '写真が見たかった'),
    ('写真を見たかった。。', '写真を見たかった'),
])
def test_incomplete_or_different_source_scope_cannot_be_promoted_by_a_short_wish_quote(text, quote):
    snap, _, value = fixture(text, quote=quote)
    assert_unread(snap, value)


@pytest.mark.parametrize('layout', ['memo_action_only', 'second_unknown_field', 'same_wish_in_both_fields'])
def test_original_proof_requires_one_nonempty_memo_field(layout):
    snap, _, _ = fixture()
    if layout == 'memo_action_only':
        snap['members'][0]['original'].update(memo='', memo_action='写真を見たかった。')
    else:
        snap['members'][0]['original']['memo_action'] = (
            'まだ言葉にできません。' if layout == 'second_unknown_field' else '写真を見たかった。')
    p = prepared(snap, PROFILE)
    fields = json.loads(p.messages()[1]['content'])['fields']
    data = dict(fields=[dict(field=f['field'], units=([] if '分か' in f['text'] or 'できません' in f['text']
        else [unit(f['text'].rstrip('。'), 'ATTENTION_OR_THOUGHT')])) for f in fields])
    assert_unread(snap, call(p, data))


@pytest.mark.parametrize('answer', ['写真を見たい。', '写真を見たかった。',
    '写真を見たくない。', '写真を見たくなかった。'])
def test_saved_answer_omitted_wish_does_not_gain_the_new_original_only_scope(answer):
    snap, _, value = supplement_fixture(answer, prompt=PROFILE)
    assert_unread(snap, value)


def test_original_omitted_wish_and_existing_self_answer_stay_one_record_occasion():
    snap, _, _ = fixture()
    snap['members'][0] = with_answer(snap['members'][0], '私は資料を見た。')
    p = prepared(snap, PROFILE)
    data = dict(fields=[dict(field=1, units=[unit('写真を見たかった', 'ATTENTION_OR_THOUGHT')]),
        dict(field=2, units=[unit('私は資料を見た', actor='私')])])
    value = call(p, data)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and len(artifact.graph.nodes) == 2 and not artifact.graph.edges
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == 0
    assert [(n.modality, n.proposition.actor) for n in artifact.graph.nodes] == [
        ('wish', 'UNSPECIFIED'), ('fact', 'SELF')]
    assert all(n.record_refs == (snap['members'][0]['original']['id'],) for n in artifact.graph.nodes)
    assert len({e.source_envelope_id for n in artifact.graph.nodes for e in n.evidence_refs}) == 2
    assert_source_evidence(artifact, freeze_analysis_sources(p.request))


@pytest.mark.parametrize('mutation', ['kind', 'missing', 'partial', 'invented_actor',
    'owned_noun_actor', 'false_negative', 'short_negative', 'modifier', 'extra_root', 'wrong_child'])
def test_omitted_wish_packet_cannot_replace_its_source_proof(mutation):
    def change(data):
        units = data['fields'][0]['units']
        root = units[0]
        if mutation == 'kind': root['node_kind'] = 'ACTION_OR_NONACTION'
        if mutation == 'missing': units.clear()
        if mutation == 'partial': root['quote'] = '仕事を続け'
        if mutation == 'invented_actor': root['qualifiers'].append(dict(kind='EXPLICIT_ACTOR', quote='私'))
        if mutation == 'owned_noun_actor': root['qualifiers'].append(dict(kind='EXPLICIT_ACTOR', quote='仕事'))
        if mutation == 'false_negative': root['qualifiers'][-1]['quote'] = '仕事'
        if mutation == 'short_negative': root['qualifiers'][-1]['quote'] = 'たくなかった'
        if mutation == 'modifier': root['qualifiers'].append(dict(kind='WRITTEN_MODIFIER', quote='たくなかった'))
        if mutation == 'extra_root': units.append(unit('仕事', 'ROLE'))
        if mutation == 'wrong_child': units.append(unit('続け', None, parent=root['quote'], scope='CONTENT_TARGET'))
    snap, _, value = fixture('仕事を続けたくなかった。',
        qualifiers=[dict(kind='NEGATION', quote='続けたくなかった')], change=change)
    raw = value.response.raw
    assert_unread(snap, value)
    assert value.response.raw == raw


@pytest.mark.parametrize('mutation', ['raw', 'hash', 'messages', 'request', 'guard', 'owner', 'source'])
def test_response_cannot_be_reassigned_after_omitted_wish_binding(mutation):
    snap, _, value = fixture()
    if mutation == 'raw': value = replace(value, response=replace(value.response, raw=value.response.raw + ' '))
    if mutation == 'hash': value = replace(value, response=replace(value.response, raw_sha256='0' * 64))
    if mutation == 'messages': value = replace(value, response=replace(value.response, messages_sha256='0' * 64))
    if mutation == 'request': value = replace(value, request_ref=value.request_ref + 'changed')
    if mutation == 'guard': snap['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    if mutation == 'source': snap['members'][0]['original']['memo'] = '写真を見たくなかった。'
    owner = str(UUID(int=2)) if mutation == 'owner' else OWNER
    with pytest.raises(ERRORS):
        service.build_cumulative_map(owner, snap, model_input=value)


@pytest.mark.parametrize('mutation', ['record', 'version', 'path', 'text', 'envelope',
    'field_hash', 'scalar_start', 'utf8_start', 'literal_hash'])
def test_saved_candidate_cannot_reassign_or_modify_the_omitted_wish_field(mutation):
    snap, p, value = fixture()
    candidate, coverage = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = json.loads(service.serialize_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value, artifact=candidate, coverage=coverage))
    field = saved['state']['graph']['fields'][0]
    if mutation == 'record': field['record_ref'] = str(UUID(int=999))
    if mutation == 'version': field['record_version'] = 'changed'
    if mutation == 'path': field['field_path'] = 'memo_action'
    if mutation == 'text': field['complete_source_text'] += 'まだ分からない。'
    if mutation == 'envelope': field['evidence']['source_envelope_id'] += 'changed'
    if mutation == 'field_hash': field['evidence']['field_sha256'] = '0' * 64
    if mutation == 'scalar_start': field['evidence']['scalar_start'] = 1
    if mutation == 'utf8_start': field['evidence']['utf8_start'] += 1
    if mutation == 'literal_hash': field['units'][0]['evidence']['literal_sha256'] = '0' * 64
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('reload compiler')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('reload author')):
        with pytest.raises(admission.AnalysisSemanticError):
            service.reload_cumulative_quoted_parent_candidates(OWNER, snap, admission.canonical(saved))


def test_saved_map_replays_the_unresolved_actor_label_without_generating_again():
    snap, _, value = fixture()
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '誰の希望かは未確定' in text
    row = dict(id=str(UUID(artifact.artifact_id[9:])), source_profile=service.PROFILE,
        report_mode='standard', content_text=text,
        content_json=dict(report_mode='standard', watashiMap=projection, map_context=counts))
    expected = dict(items=[row], subscription_tier='free', matched=True, history_limit=2)
    forbidden = AssertionError('saved omitted wish must not regenerate')
    with patch.object(service, '_rpc', AsyncMock(return_value=json.loads(admission.canonical(expected)))), \
         patch.object(MeaningExperienceEngine, 'generate', side_effect=forbidden), \
         patch.object(compiler, 'compile_observed_graph', side_effect=forbidden), \
         patch.object(compiler, 'compile_model_observed_actions', side_effect=forbidden), \
         patch.object(author, 'realize_observed_graph', side_effect=forbidden):
        assert asyncio.run(service.read_maps(OWNER, report_id=row['id'])) == expected
