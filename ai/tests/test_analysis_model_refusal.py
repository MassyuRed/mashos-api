"""Finite original refusal proof: no invented actor, attendance or action day."""
import asyncio
import copy
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
from test_analysis_model_supplement_wish import assert_source_evidence
from test_analysis_saved_period import with_answer


ERRORS = (AnalysisSourceError, admission.AnalysisSemanticError)


def fixture(text='昨日の会議への招待は断った。', *, noun='昨日の会議への招待',
        finite='断った', count=1, field='memo', extra='', change=None):
    snap = source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo='', memo_action='')
        member['original'][field] = text
        if extra:
            member['original']['memo_action'] = extra
    p = prepared(snap, 'selected_material.v13')
    fields = __import__('json').loads(p.messages()[1]['content'])['fields']
    data = dict(fields=[dict(field=f['field'], units=[
        unit(finite), unit(noun, None, parent=finite, scope='CONTENT_TARGET')]
        if f['text'] == text else []) for f in fields])
    if change:
        change(data)
    return snap, p, call(p, data)


def assert_unread(snap, value):
    try:
        artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    except ERRORS:
        return
    assert artifact is None and counts['mapped_count'] == 0


@pytest.mark.parametrize('noun', ['会議への招待', '集まりへの誘い', '仕事の依頼', '計画の提案'])
@pytest.mark.parametrize('case', ['は', 'を'])
@pytest.mark.parametrize('finite,polarity', [('断った', 'positive'), ('断らなかった', 'negative')])
def test_complete_refusal_preserves_written_object_case_polarity_and_unknown_actor(noun, case, finite, polarity):
    snap, p, value = fixture(noun + case + finite + '。', noun=noun, finite=finite)
    original = copy.deepcopy(snap)
    raw = value.response.raw
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    normal, normal_counts = service.build_cumulative_map(OWNER, snap)
    assert artifact is not None and artifact.graph == normal.graph and counts == normal_counts
    node, = artifact.graph.nodes
    q = node.proposition
    assert (node.node_kind, q.actor, q.predicate_lemma, q.arguments,
        q.polarity, q.modality, q.temporal_scope, q.relative_day) == (
            'ACTION_OR_NONACTION', 'UNSPECIFIED', '断る', ((case, noun),),
            polarity, 'fact', 'past', '')
    assert counts['mapped_count'] == 1 and counts['unparsed_count'] == 0
    assert not artifact.graph.edges and not artifact.graph.annotations
    assert not artifact.graph.conflicts and not node.update_refs
    assert node.selected_categories == ('仕事',)
    assert {g.missing_scope for g in artifact.graph.unknown_gaps} == {
        'SCENE', 'ROLE', 'ATTENTION_OR_THOUGHT', 'IMMEDIATE_RESULT_OR_AFTERMATH'}
    label = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label']
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert noun + case + '断る' in label and '誰の行動かは未確定' in label and label in text
    assert ('実行済み' in label) == (polarity == 'positive')
    assert ('行わなかった' in label) == (polarity == 'negative')
    assert '参加' not in text and not q.sequence_marker and not q.written_modifiers
    assert_source_evidence(artifact, freeze_analysis_sources(p.request))
    candidate, coverage = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = service.serialize_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value, artifact=candidate, coverage=coverage)
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('saved compiler')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('saved author')):
        restored, restored_counts = service.reload_cumulative_quoted_parent_candidates(OWNER, snap, saved)
    assert restored.graph == candidate.graph and restored_counts == coverage
    assert snap == original and value.response.raw == raw


def test_nominal_day_does_not_date_the_refusal_or_identify_two_actors():
    snap, p, value = fixture(count=2)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['mapped_count'] == 2
    assert len(artifact.graph.nodes) == 2 and not artifact.graph.edges
    assert all(n.proposition.relative_day == '' and n.proposition.actor == 'UNSPECIFIED'
        and len(n.record_refs) == len(n.evidence_refs) == 1 for n in artifact.graph.nodes)
    assert_source_evidence(artifact, freeze_analysis_sources(p.request))


@pytest.mark.parametrize('text', [
    '友人は断った。', '私は招待は断った。', '友人が招待は断った。',
    '今日は招待は断った。', '昨日招待は断った。', '昨日分招待は断った。',
    '何の招待は断った。', '誰の招待は断った。', '少し招待は断った。',
    '忙しいので招待は断った。', '招待は断ったから安心した。',
    '招待は断ったと思った。', '招待は断ったかもしれない。',
    '「招待は断った」と友人は言った。', '夢を見た。招待は断った。',
    '聞いた話だ。招待は断った。', '招待は断った。まだ分からない。',
    '招待は断った？', '招待は断ったなら。', '招待は断った。。',
    '招待は断りました。', '招待は断る。', '招待は断りたい。',
    '招待は断ったこと。', '招待は断ったのではない。',
])
def test_short_model_root_cannot_erase_actor_time_report_reason_or_unread_tail(text):
    try:
        snap, _, value = fixture(text, noun='招待')
    except ERRORS:
        return
    assert_unread(snap, value)


@pytest.mark.parametrize('field,extra', [('memo_action', ''), ('memo', '私は資料を見た。'),
    ('memo', 'まだ分からない。')])
def test_original_proof_never_discards_another_field(field, extra):
    snap, _, value = fixture(field=field, extra=extra)
    assert_unread(snap, value)


def test_ordinary_answer_cannot_borrow_the_original_only_refusal_proof():
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo='まだ分からない。', memo_action='',
        emotion_details=[dict(type='平穏', strength='medium')])
    snap['members'][0] = with_answer(snap['members'][0], '会議への招待は断った。')
    try:
        p = prepared(snap, 'selected_material.v13')
        value = call(p, dict(fields=[dict(field=1, units=[]), dict(field=2, units=[
            unit('断った'), unit('会議への招待', None, parent='断った', scope='CONTENT_TARGET')])]))
    except ERRORS:
        return
    assert_unread(snap, value)


@pytest.mark.parametrize('mutation', ['missing_object', 'short_object', 'false_actor', 'false_negative',
    'wrong_kind', 'extra_root', 'object_as_root', 'wrong_parent'])
def test_short_predicate_requires_the_exact_complete_object_and_matching_units(mutation):
    def change(data):
        roots = data['fields'][0]['units']
        root, child = roots
        if mutation == 'missing_object': roots.pop()
        if mutation == 'short_object': child['quote'] = '会議'
        if mutation == 'false_actor': root['qualifiers'].append(dict(kind='EXPLICIT_ACTOR', quote='会議'))
        if mutation == 'false_negative': root['qualifiers'].append(dict(kind='NEGATION', quote='断った'))
        if mutation == 'wrong_kind': root['node_kind'] = 'ATTENTION_OR_THOUGHT'
        if mutation == 'extra_root': roots.append(unit('会議', 'ROLE'))
        if mutation == 'object_as_root': root['quote'] = '昨日の会議への招待'
        if mutation == 'wrong_parent': child['parent_quote'] = '会議'
    try:
        snap, _, value = fixture(change=change)
    except ERRORS:
        return
    assert_unread(snap, value)


def test_saved_refusal_label_is_read_without_compilation_or_generation():
    snap, _, value = fixture()
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    row = dict(id=str(UUID(artifact.artifact_id[9:])), source_profile=service.PROFILE,
        report_mode='standard', content_text=text,
        content_json=dict(report_mode='standard', watashiMap=projection, map_context=counts))
    expected = dict(items=[row], subscription_tier='free', matched=True, history_limit=2)
    forbidden = AssertionError('saved refusal must not regenerate')
    with patch.object(service, '_rpc', AsyncMock(return_value=expected)), \
         patch.object(MeaningExperienceEngine, 'generate', side_effect=forbidden), \
         patch.object(compiler, 'compile_observed_graph', side_effect=forbidden), \
         patch.object(compiler, 'compile_model_observed_actions', side_effect=forbidden), \
         patch.object(author, 'realize_observed_graph', side_effect=forbidden):
        assert asyncio.run(service.read_maps(OWNER, report_id=row['id'])) == expected
