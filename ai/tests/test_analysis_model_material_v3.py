"""Original/answer provenance through the explicit offline model boundary."""
import copy
from dataclasses import replace
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from astor_material_snapshots import AnalysisSavedSourceError
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisSemanticError, AnalysisSemanticUnsupported, prepare_analysis_model_quoted_parent_units,
    generate_analysis_model_quoted_parent_units, serialize_analysis_model_quoted_parent_units,
    reload_analysis_model_quoted_parent_units, canonical)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, AnalysisSupplement, commitment)
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_saved_period import with_answer
from test_analysis_model_quoted_parent_units import call

PROMPT = 'selected_material.v3'


def snapshot(answer='私は資料を調べた。'):
    snap = source_snapshot(1, tier='plus')
    original = snap['members'][0]['original']
    original.update(memo='私は資料を見た。', memo_action='私は記録を残した。',
        emotion_details=[dict(type='平穏', strength='medium')])
    snap['members'][0] = with_answer(snap['members'][0], answer)
    return snap


def prepared(snap):
    return service.prepare_cumulative_category_units(OWNER, snap, prompt_version=PROMPT)


def packet(p):
    fields = json.loads(p.messages()[1]['content'])['fields']
    return dict(fields=[dict(field=f['field'], units=[dict(quote=f['text'],
        node_kind='ACTION_OR_NONACTION', parent_quote=None, scope_role=None, qualifiers=[])])
        for f in fields])


def test_saved_answer_owner_to_model_to_exact_saved_candidate_without_generated_text():
    snap = snapshot()
    p = prepared(snap)
    messages = p.messages()
    material = json.loads(messages[1]['content'])
    fields = material['fields']
    assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT'] * 2 + ['SUPPLEMENTAL_ANSWER']
    assert [f['supplement'] for f in fields] == [None, None, 1]
    assert [f['record'] for f in fields] == [1, 1, 1]
    assert [f['field_path'] for f in fields] == ['memo', 'memo_action', 'memo']
    assert [f['text'] for f in fields] == ['私は資料を見た。', '私は記録を残した。', '私は資料を調べた。']
    assert all(f['selected_categories'] == ['仕事'] for f in fields)
    assert material['records'][0]['fields'] == [1, 2, 3]
    assert 'GENERATED_BODY_IS_NOT_SOURCE' not in canonical(messages)
    assert 'QUESTION_IS_NOT_ANALYSIS_SOURCE' not in canonical(messages)
    assert snap['members'][0]['original']['id'] not in canonical(material)
    assert '意味上の境界' in messages[0]['content'] and '理由' in messages[0]['content']
    value = call(p, packet(p))
    artifact, coverage = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    assert len(artifact.graph.fields) == 3
    assert len({f.evidence.source_envelope_id for f in artifact.graph.fields}) == 2
    assert coverage['source_count'] == coverage['unparsed_count'] == 1
    assert coverage['mapped_count'] == 0 and artifact.graph.route_edges == ()
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=coverage)
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('engine')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compiler')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, raw) == (artifact, coverage)


@pytest.mark.parametrize('change', ['owner', 'question', 'round', 'parent_ref'])
def test_invalid_saved_answer_binding_is_rejected_before_a_model_call(change):
    snap = snapshot()
    member = snap['members'][0]
    if change == 'owner': member['thread']['user_id'] = '00000000-0000-0000-0000-000000000002'
    answer = next(e for e in member['events'] if e['kind'] == 'ANSWER')
    if change == 'question': answer['question_id'] = 'not-issued'
    if change == 'round': answer['payload']['source']['round_index'] = 2
    if change == 'parent_ref': answer['payload']['source']['original_source_ref'] = 'foreign'
    with pytest.raises(AnalysisSavedSourceError):
        prepared(snap)


@pytest.mark.parametrize('text', ['「私は資料を見た」を撤回します。',
    '「私は資料を見た」ではなく「私は資料を調べた」です。', '私は資料を見なかった。'])
def test_corrections_withdrawals_and_unresolved_opposition_keep_existing_rejection(text):
    with pytest.raises((AnalysisSourceError, AnalysisSemanticError)):
        prepared(snapshot(text))


@pytest.mark.parametrize('old_prompt', ['baseline.v1', 'selected_categories.v1', 'selected_material.v2',
                                      'semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_old_profiles_keep_their_answer_scope_and_cannot_read_v3_files(old_prompt):
    snap = snapshot()
    with pytest.raises(AnalysisSemanticUnsupported):
        (service.prepare_cumulative_category_units if old_prompt.startswith('selected_')
         else service.prepare_cumulative_quoted_parent_units)(OWNER, snap, prompt_version=old_prompt)
    clean = source_snapshot(1)
    p = prepared(clean)
    value = call(p, packet(p))
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, clean, model_input=value)
    raw = json.loads(service.serialize_cumulative_quoted_parent_candidates(OWNER, clean,
        model_input=value, artifact=artifact, coverage=counts))
    raw['state']['prompt_version'] = old_prompt
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, clean, canonical(raw))


@pytest.mark.parametrize('change', ['answer', 'original', 'guard', 'category'])
def test_fresh_source_or_call_change_cannot_reuse_an_old_model_response(change):
    snap = snapshot()
    p = prepared(snap)
    value = call(p, packet(p))
    changed = copy.deepcopy(snap)
    if change == 'answer':
        next(e for e in changed['members'][0]['events'] if e['kind'] == 'ANSWER')['payload']['source']['answer_text_private'] = '私は記録を残した。'
    if change == 'original': changed['members'][0]['original']['memo'] = '私は仕事を続けた。'
    if change == 'guard': changed['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    if change == 'category': changed['members'][0]['original']['category'] = ['趣味']
    with pytest.raises((AnalysisSavedSourceError, AnalysisSemanticError, AnalysisSourceError)):
        service.build_cumulative_quoted_parent_candidates(OWNER, changed, model_input=value)


def test_three_bound_supplements_are_independent_fields_and_not_three_occasions():
    clean = source_snapshot(1)
    clean['members'][0]['original'].update(memo='私は資料を見た。', memo_action='')
    p = prepared(clean)
    member = p.request.members[0]
    texts = ('私は資料を調べた。', '私は記録を残した。', '私は仕事を続けたい。')
    member = replace(member, supplements=tuple(AnalysisSupplement('answer-' + str(i), OWNER,
        member.saved_record_ref, member.saved_record_version, text, commitment(text))
        for i, text in enumerate(texts, 1)))
    request = replace(p.request, members=(member,))
    p = prepare_analysis_model_quoted_parent_units(request, source_guard=p.source_guard, prompt_version=PROMPT)
    material = json.loads(p.messages()[1]['content'])
    assert len(material['records']) == 1 and len(material['fields']) == 4
    assert [f['supplement'] for f in material['fields']] == [None, 1, 2, 3]
    value = call(p, packet(p))
    artifact = generate_analysis_model_quoted_parent_units(request, value)
    saved = serialize_analysis_model_quoted_parent_units(value, artifact)
    assert reload_analysis_model_quoted_parent_units(p, saved) == artifact
    assert len({f.evidence.source_envelope_id for f in artifact.graph.fields}) == 4
    assert artifact.graph.route_edges == ()


def test_metadata_or_sibling_answer_cannot_be_quoted_as_current_field():
    snap = snapshot(); p = prepared(snap)
    for quote in ('仕事', '私は資料を調べた。'):
        data = packet(p)
        data['fields'][0]['units'][0]['quote'] = quote
        with pytest.raises(AnalysisSemanticError):
            service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=call(p, data))


def test_model_supplement_cannot_enter_the_original_only_typed_role_vertical():
    snap = snapshot('私は資料を調べた。')
    raw = snap['members'][0]['original']
    raw.update(memo='私の役割は連絡係だった。', memo_action='')
    snap['members'][0] = with_answer(dict(original=raw), '私は資料を調べた。')
    p = prepared(snap)
    data = packet(p)
    data['fields'][0]['units'][0]['node_kind'] = 'ROLE'
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import generate_analysis_model_written_role
    with pytest.raises(AnalysisSemanticUnsupported):
        generate_analysis_model_written_role(p.request, call(p, data))
