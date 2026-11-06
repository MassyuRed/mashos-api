"""Opt-in actor/field instructions preserve source-bound unresolved candidates."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
from unittest.mock import patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSupplement, commitment
from test_analysis_cumulative import source_snapshot, OWNER
from test_analysis_model_quoted_parent_units import call
from test_analysis_model_role_decision import sample


def prepared(text):
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=text, memo_action='')
    return snap, service.prepare_cumulative_category_units(OWNER, snap,
        prompt_version='selected_material.v7')


def unit(text, kind='ACTION_OR_NONACTION', *, actor=None, parent=None, scope=None, qualifiers=()):
    q = ([] if actor is None else [dict(kind='EXPLICIT_ACTOR', quote=actor)]) + list(qualifiers)
    return dict(quote=text, node_kind=kind, parent_quote=parent, scope_role=scope, qualifiers=q)


def test_v7_corrects_only_the_actor_explanation_and_keeps_v4_v6_messages():
    snap = sample()
    v4, v6, v7 = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v4', 'selected_material.v6', 'selected_material.v7')]
    assert admission.digest(v4.messages()) == 'fc06c5a05d4994fc4dfb3b464cf78f0e978f2ed47a538a322cd72e29ab26169e'
    assert v6.messages()[0]['content'] == v4.messages()[0]['content'] + admission._responsibility_decision_units_instruction()
    assert v4.messages()[1] == v6.messages()[1] == v7.messages()[1]
    assert len({p.request_ref for p in (v4, v6, v7)}) == 3
    assert v4.request == v6.request == v7.request
    old = admission._actor_field_boundaries_units_instruction()
    new = admission._actor_field_boundaries_units_instruction(distinguish_actor=True)
    assert v7.messages()[0]['content'] == v6.messages()[0]['content'].replace(old, new)
    assert '所有格「僕の」と主題格「僕は」はどちらも' in old
    assert '所有格「僕の」と主題格「僕は」はどちらも' not in new
    assert 'そのunitの述語の主体' in new and '一意な原文範囲' in new


def test_actual_four_prompt_examples_bind_to_their_own_source_fields():
    instruction = admission._possessive_actor_units_instruction()
    material, packet = instruction.split('例の入力:', 1)[1].split('\n例の出力:', 1)
    material = json.loads(material)
    packet = json.loads(packet.split('\n今回の各unit', 1)[0])
    snap = source_snapshot(4)
    for member, field in zip(snap['members'], material['fields']):
        member['original'].update(memo=field['text'], memo_action='')
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v7')
    value = call(p, packet)
    a, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    assert counts['mapped_count'] == 0 and counts['unparsed_count'] == 4
    assert [len(f.units) for f in a.graph.fields] == [2, 2, 2, 2]
    assert [u.parent for f in a.graph.fields for u in f.units] == [None, 1] * 4


@pytest.mark.parametrize('text,actor', [
    ('私の予定をメモした', None),
    ('私は友人の予定をメモした', '私'),
    ('友人は私の予定をメモした', '友人'),
    ('私は私の予定をメモした', '私は'),
    ('予定をメモしなかった', None),
])
def test_v7_keeps_exact_actor_ownership_and_negation_without_owner_promotion(text, actor):
    snap, p = prepared(text+'。')
    qualifiers = [dict(kind='NEGATION', quote='なかった')] if text.endswith('なかった') else []
    value = call(p, dict(fields=[dict(field=1, units=[unit(text, actor=actor, qualifiers=qualifiers)])]))
    a, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    u = a.graph.fields[0].units[0]
    assert u.quote == text and u.actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
    assert u.polarity == u.modality == u.temporal_scope == 'AS_WRITTEN_UNRESOLVED'
    assert [q.quote for q in u.qualifiers] == ([] if actor is None else [actor]) + [q['quote'] for q in qualifiers]
    assert a.graph.route_edges == () and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=a, coverage=counts)
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('saved generation')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, raw) == (a, counts)


def test_v7_still_rejects_invented_actor_and_ambiguous_repeated_pronoun():
    for text, actor in [('予定をメモしなかった', '私'), ('私は私の予定をメモした', '私')]:
        snap, p = prepared(text+'。')
        with pytest.raises(admission.AnalysisSemanticError):
            service.build_cumulative_quoted_parent_candidates(OWNER, snap,
                model_input=call(p, dict(fields=[dict(field=1, units=[unit(text, actor=actor)])])))


def test_reason_and_unperformed_wish_remain_candidates_with_no_route():
    reason = '間違いがあると困るので'
    action = '提出前に読み直した'
    wish = '速さより正確に伝えたかった'
    snap, p = prepared(reason+'、'+action+'。'+wish+'。')
    packet = dict(fields=[dict(field=1, units=[unit(action),
        unit(reason, None, parent=action, scope='WRITTEN_REASON',
            qualifiers=[dict(kind='REASON_MARKER', quote='ので')]),
        unit(wish, 'ATTENTION_OR_THOUGHT')])])
    value = call(p, packet)
    a, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    assert [u.node_kind for u in a.graph.fields[0].units] == ['ACTION_OR_NONACTION', None, 'ATTENTION_OR_THOUGHT']
    assert a.graph.route_edges == () and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1
    assert all(u.modality == 'AS_WRITTEN_UNRESOLVED' for u in a.graph.fields[0].units)
    assert 'SELF' not in [u.actor for u in a.graph.fields[0].units]
    r = a.graph.fields[0].units[1]
    assert r.parent == 1 and r.scope_role == 'WRITTEN_REASON'
    assert [(q.kind, q.quote) for q in r.qualifiers] == [('REASON_MARKER', 'ので')]
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=a, coverage=counts)
    assert json.loads(raw)['state']['response']['raw'] == value.response.raw
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('saved generation')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, raw) == (a, counts)


@pytest.mark.parametrize('profile,messages_sha256,request_ref,state_sha256', [
    ('selected_material.v4',
        'fc06c5a05d4994fc4dfb3b464cf78f0e978f2ed47a538a322cd72e29ab26169e',
        'analysis-quoted-parent-units-request:0291e8c92f60ffbf83782766cf0e75e9bc638edb48bfc20bba5537b0720366ab',
        'd6e218fe0904288d2b80453970e61db19ed0781485fc1ad5983c5f7ebb5c70ac'),
    ('selected_material.v6',
        '0679025a93ba53bb788dcca62f918ce6e359e1e094539e693f2d5a3327651d06',
        'analysis-quoted-parent-units-request:3a307e11e738118bc9c74987f190c0aa05a9410c163a40afb55a70e30560dd33',
        '7b18691da1cc0fffb3562b0978f3bc1238bdbed6068875b696043346e23d1a85'),
    ('selected_material.v7',
        '876db20d3e2c6d1d719bfca456d434dbdb9cf9acb22d8329bcef409ae1336af7',
        'analysis-quoted-parent-units-request:08974feb50de114488e96f4d625faaf26d6e92c3cf85fa9fbd0bc1b1aa32c6c5',
        '6344a9529308bc261b659675114d9d70903c1f83659becb8d40b9f657b0f388a'),
])
def test_legacy_v4_v6_v7_messages_ref_and_state_match_pre_v8_known_bytes(
        profile, messages_sha256, request_ref, state_sha256):
    # Captured on pre-v8 API09b650 in Jupyter with this existing sample and
    # empty-unit synthetic packet; no real model response is copied here.
    p = service.prepare_cumulative_category_units(OWNER, sample(), prompt_version=profile)
    assert admission.digest(p.messages()) == messages_sha256 and p.request_ref == request_ref
    value = call(p, dict(fields=[dict(field=1, units=[])]))
    artifact = admission.generate_analysis_model_quoted_parent_units(value.request, value)
    raw = admission.serialize_analysis_model_quoted_parent_units(value, artifact)
    assert hashlib.sha256(raw.encode('utf-8')).hexdigest() == state_sha256
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('legacy state compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('legacy state author')):
        restored = admission.reload_analysis_model_quoted_parent_units(p, raw)
        assert admission.serialize_analysis_model_quoted_parent_units(value, restored) == raw


def test_v8_adds_only_the_actual_field_inventory_after_the_complete_v7_system():
    snap = source_snapshot(2)
    original = copy.deepcopy(snap)
    v7, v8 = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v7', 'selected_material.v8')]
    tail = ('\n今回の入力field番号一覧：[1,2]。総数：2。'
        '出力fieldsには全番号を入力順に各1回ずつ返してください。')
    assert v8.messages()[0]['content'] == v7.messages()[0]['content'] + tail
    assert v8.messages()[1] == v7.messages()[1]
    assert len(v8.messages()) == 2 and v8.request == v7.request and v8.source_guard == v7.source_guard
    assert v8.request_ref != v7.request_ref and admission.digest(v8.messages()) != admission.digest(v7.messages())
    assert 'そのunitの述語の主体' in v8.messages()[0]['content']
    assert v8.messages()[0]['content'].endswith(tail) and '私は考えをノートに書いた' not in tail
    assert snap == original


def test_v8_inventory_counts_both_original_fields_and_all_qualified_answers(monkeypatch):
    snap = source_snapshot(2)
    snap['members'][0]['original'].update(memo='私は本を見た。', memo_action='私は費用を記録した。')
    snap['members'][1]['original']['memo'] = '私は資料を見た。'
    base = service._cumulative_model_request(OWNER, snap)
    first = base.members[0]
    texts = ('僕はノートを見た。', '僕は資料を見た。', '僕は日程を決めた。')
    answers = tuple(AnalysisSupplement(str(UUID(int=1200+i)), OWNER, first.saved_record_ref,
        first.saved_record_version, text, commitment(text)) for i, text in enumerate(texts))
    request = replace(base, members=(replace(first, supplements=answers), base.members[1]))
    monkeypatch.setattr(service, '_cumulative_model_request', lambda *_:request)
    v7, v8 = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v7', 'selected_material.v8')]
    material = json.loads(v8.messages()[1]['content'])
    assert v8.messages()[1] == v7.messages()[1]
    assert v8.messages()[0]['content'] == v7.messages()[0]['content'] + (
        '\n今回の入力field番号一覧：[1,2,3,4,5,6]。総数：6。'
        '出力fieldsには全番号を入力順に各1回ずつ返してください。')
    assert len(material['records']) == 2 and [f['field'] for f in material['fields']] == [1,2,3,4,5,6]
    assert [f['text'] for f in material['fields']] == [
        '私は本を見た。', '私は費用を記録した。', *texts, '私は資料を見た。']
    assert [f['source_role'] for f in material['fields']] == [
        'ORIGINAL_INPUT','ORIGINAL_INPUT',*(['SUPPLEMENTAL_ANSWER']*3),'ORIGINAL_INPUT']
    assert material['records'][0]['fields'] == [1,2,3,4,5] and material['records'][1]['fields'] == [6]
    packet = dict(fields=[dict(field=f['field'], units=[unit(f['text'])]) for f in material['fields']])
    value = call(v8, packet)
    artifact = admission.generate_analysis_model_quoted_parent_units(value.request, value)
    assert [f.complete_source_text for f in artifact.graph.fields] == [f['text'] for f in material['fields']]
    raw = admission.serialize_analysis_model_quoted_parent_units(value, artifact)
    saved = json.loads(raw)
    assert saved['schema_version'] == admission.QUOTED_PARENT_MATERIAL_V8_STATE
    assert saved['prompt_version'] == 'selected_material.v8' and saved['response'] == asdict(value.response)
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('state compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('state author')):
        assert admission.reload_analysis_model_quoted_parent_units(v8, raw) == artifact


@pytest.mark.parametrize('source_profile,target_profile', [
    ('selected_material.v7','selected_material.v8'), ('selected_material.v8','selected_material.v7')])
def test_v7_v8_response_and_state_cannot_cross_reuse(source_profile, target_profile):
    snap = source_snapshot(1)
    source, target = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in (source_profile, target_profile)]
    value = call(source, dict(fields=[dict(field=1, units=[])]))
    artifact = admission.generate_analysis_model_quoted_parent_units(value.request, value)
    raw = admission.serialize_analysis_model_quoted_parent_units(value, artifact)
    assert admission.reload_analysis_model_quoted_parent_units(source, raw) == artifact
    with pytest.raises(admission.AnalysisSemanticError, match='analysis_quoted_parent_units_response_invalid'):
        admission._admit_quoted_parent_units(target.request, replace(target, response=value.response))
    # Changing only the advertised ref cannot conceal changed system bytes.
    forged = replace(value.response, request_ref=target.request_ref)
    with pytest.raises(admission.AnalysisSemanticError, match='analysis_quoted_parent_units_response_invalid'):
        admission._admit_quoted_parent_units(target.request, replace(target, response=forged))
    with pytest.raises(admission.AnalysisSemanticError, match='analysis_quoted_parent_units_state_invalid'):
        admission.reload_analysis_model_quoted_parent_units(target, raw)
    assert value.response.raw == json.loads(raw)['response']['raw']


@pytest.mark.parametrize('count', [6,7])
def test_v8_still_rejects_field_one_only_for_repeated_multi_record_source(count):
    snap = source_snapshot(count)
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v8')
    fields = json.loads(p.messages()[1]['content'])['fields']
    assert len(fields) == count and len({f['text'] for f in fields}) == 1
    collapsed = call(p, dict(fields=[dict(field=1, units=[])]))
    with pytest.raises(admission.AnalysisSemanticError, match='analysis_quoted_parent_units_packet_invalid'):
        admission.generate_analysis_model_quoted_parent_units(p.request, collapsed)
    # Complete wire coverage may honestly contain no extracted units. It is
    # retained as unparsed source, without inventing a meaning or a saved map.
    complete = call(p, dict(fields=[dict(field=f['field'], units=[]) for f in fields]))
    artifact = admission.generate_analysis_model_quoted_parent_units(p.request, complete)
    assert len(artifact.graph.fields) == len(artifact.graph.unparsed_record_refs) == count
    assert all(not f.units and f.complete_source_text == fields[i]['text']
        for i, f in enumerate(artifact.graph.fields))
    assert artifact.graph.route_edges == ()


def test_private_v8_does_not_expand_transport_planner_or_batch_envelope_selection():
    from analysis_model_source import SelfHostedAnalysisModelSource
    with pytest.raises(ValueError):
        SelfHostedAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/v1/chat/completions',
            model='synthetic-analysis', api_key='synthetic-private-key', prompt_version='selected_material.v8')
    snap = source_snapshot(1)
    with pytest.raises(ValueError, match='analysis_model_batch_profile_invalid'):
        service.prepare_cumulative_model_batches(OWNER, snap, prompt_version='selected_material.v8',
            measure_budget=lambda _:service.AnalysisModelInputBudget(1,1))
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v8')
    value = call(p, dict(fields=[dict(field=1, units=[])]))
    with pytest.raises(admission.AnalysisSemanticError, match='analysis_model_batch_parent_invalid'):
        admission.generate_analysis_model_observed_batches(admission.AnalysisModelObservedBatchInput(p,(value,)))


def test_v9_keeps_v7_source_and_default_but_uses_separate_response_identity():
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo='私は費用を記録したかった。', memo_action='')
    original = copy.deepcopy(snap)
    v7, v9 = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v7', 'selected_material.v9')]
    assert service.prepare_cumulative_category_units(OWNER, snap).prompt_version == 'selected_categories.v1'
    assert v9.messages()[1] == v7.messages()[1] and v9.request == v7.request
    assert v9.messages()[0]['content'] == v7.messages()[0]['content'] + admission._wish_boundaries_units_instruction()
    assert v9.request_ref != v7.request_ref and admission.digest(v9.messages()) != admission.digest(v7.messages())
    assert snap == original


@pytest.mark.parametrize('source_profile,target_profile', [
    ('selected_material.v7','selected_material.v9'), ('selected_material.v9','selected_material.v7'),
    ('selected_material.v8','selected_material.v9'), ('selected_material.v9','selected_material.v8')])
def test_v9_response_and_state_cannot_cross_reuse(source_profile, target_profile):
    test_v7_v8_response_and_state_cannot_cross_reuse(source_profile, target_profile)


@pytest.mark.parametrize('profile', ['selected_material.v9', 'selected_material.v12'])
@pytest.mark.parametrize('suffix,negative', [
    ('記録したい', False), ('記録したかった', False),
    ('記録したくない', True), ('記録したくなかった', True)])
def test_v9_preserves_exact_wish_source_and_reloads_without_generation(suffix, negative, profile):
    snap = source_snapshot(1)
    text = '私は費用を' + suffix
    snap['members'][0]['original'].update(memo=text+'。', memo_action='')
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=profile)
    qualifiers = [dict(kind='NEGATION', quote=suffix)] if negative else []
    packet = dict(fields=[dict(field=1, units=[
        unit(text, 'ATTENTION_OR_THOUGHT', actor='私', qualifiers=qualifiers),
        unit('費用', None, parent=text, scope='CONTENT_TARGET')])])
    value = call(p, packet)
    candidate = admission.generate_analysis_model_quoted_parent_units(p.request, value)
    raw = admission.serialize_analysis_model_quoted_parent_units(value, candidate)
    assert json.loads(raw)['schema_version'] == (admission.QUOTED_PARENT_MATERIAL_V9_STATE if profile.endswith('v9') else admission.QUOTED_PARENT_MATERIAL_V12_STATE)
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')):
        assert admission.reload_analysis_model_quoted_parent_units(p, raw) == candidate
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['unparsed_count'] == 0
    assert len(artifact.graph.nodes) == 1 and not artifact.graph.edges
    node=artifact.graph.nodes[0]
    assert (node.modality,node.polarity,node.temporal_scope) == ('wish','negative' if negative else 'positive','past' if suffix.endswith(('たかった','なかった')) else 'current_input')
    assert value.response.raw == json.loads(raw)['response']['raw']


def test_private_v9_does_not_expand_transport_or_batch_selection():
    from analysis_model_source import SelfHostedAnalysisModelSource
    with pytest.raises(ValueError):
        SelfHostedAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/v1/chat/completions',
            model='synthetic-analysis', api_key='synthetic-private-key', prompt_version='selected_material.v9')
    with pytest.raises(ValueError, match='analysis_model_batch_profile_invalid'):
        service.prepare_cumulative_model_batches(OWNER, source_snapshot(1), prompt_version='selected_material.v9',
            measure_budget=lambda _:service.AnalysisModelInputBudget(1,1))


def test_v10_adds_only_independent_examples_and_preserves_v9_material():
    snap = sample()
    original = copy.deepcopy(snap)
    v9, v10 = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v9', 'selected_material.v10')]
    assert v10.request == v9.request and v10.messages()[1] == v9.messages()[1]
    assert v10.messages()[0]['content'] == v9.messages()[0]['content'] + admission._negative_wish_examples_units_instruction()
    assert v10.request_ref != v9.request_ref and admission.digest(v10.messages()) != admission.digest(v9.messages())
    assert snap == original


@pytest.mark.parametrize('source_profile,target_profile', [
    ('selected_material.v7','selected_material.v10'), ('selected_material.v10','selected_material.v7'),
    ('selected_material.v9','selected_material.v10'), ('selected_material.v10','selected_material.v9')])
def test_v10_response_and_state_cannot_cross_reuse(source_profile, target_profile):
    test_v7_v8_response_and_state_cannot_cross_reuse(source_profile, target_profile)


@pytest.mark.parametrize('example_index,expected', [
    (0, [('negative','wish','current_input')]),
    (1, [('positive','fact','past'), ('negative','wish','past')])])
def test_actual_v10_examples_keep_complete_negation_and_each_explicit_actor_on_reload(example_index, expected):
    lines = admission._negative_wish_examples_units_instruction().splitlines()
    materials = [json.loads(line[len('例の入力:'):]) for line in lines if line.startswith('例の入力:')]
    packets = [json.loads(line[len('例の出力:'):]) for line in lines if line.startswith('例の出力:')]
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=materials[example_index]['fields'][0]['text'], memo_action='')
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v10')
    value = call(p, packets[example_index])
    candidate, coverage = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    state = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=candidate, coverage=coverage)
    assert json.loads(state)['state']['schema_version'] == admission.QUOTED_PARENT_MATERIAL_V10_STATE
    with patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, state) == (candidate, coverage)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is not None and counts['mapped_count'] == 1 and counts['unparsed_count'] == 0
    assert [(n.polarity,n.modality,n.temporal_scope) for n in artifact.graph.nodes] == expected
    assert all(n.proposition.actor == 'SELF' for n in artifact.graph.nodes) and not artifact.graph.edges
    qualifiers = [u.qualifiers for u in candidate.graph.fields[0].units]
    assert all(any(q.kind == 'EXPLICIT_ACTOR' for q in qs) for qs in qualifiers)
    negative = '作りたくない' if example_index == 0 else '試したくなかった'
    assert [q.quote for qs in qualifiers for q in qs if q.kind == 'NEGATION'] == [negative]
    assert value.response.raw == json.loads(state)['state']['response']['raw']


def test_private_v10_keeps_short_negative_wish_unsupported_and_normal_selection_closed():
    from analysis_model_source import SelfHostedAnalysisModelSource
    snap = source_snapshot(1)
    text = '私は模型を作りたくない'
    snap['members'][0]['original'].update(memo=text+'。', memo_action='')
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v10')
    value = call(p, dict(fields=[dict(field=1, units=[unit(text, 'ATTENTION_OR_THOUGHT', actor='私',
        qualifiers=[dict(kind='NEGATION', quote='たくない')])])]))
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact is None and counts['unparsed_count'] == 1
    assert service.prepare_cumulative_category_units(OWNER, snap).prompt_version == 'selected_categories.v1'
    with pytest.raises(ValueError):
        SelfHostedAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/v1/chat/completions',
            model='synthetic-analysis', api_key='synthetic-private-key', prompt_version='selected_material.v10')
    with pytest.raises(ValueError, match='analysis_model_batch_profile_invalid'):
        service.prepare_cumulative_model_batches(OWNER, snap, prompt_version='selected_material.v10',
            measure_budget=lambda _:service.AnalysisModelInputBudget(1,1))


@pytest.mark.parametrize('source_profile,target_profile', [
    ('selected_material.v10','selected_material.v11'),
    ('selected_material.v11','selected_material.v10'),
    ('selected_material.v11','selected_material.v12'),
    ('selected_material.v12','selected_material.v11')])
def test_v11_response_and_state_cannot_cross_reuse(source_profile, target_profile):
    test_v7_v8_response_and_state_cannot_cross_reuse(source_profile, target_profile)


def test_v11_preserves_v10_source_and_meaning_instructions():
    snap = sample()
    before = copy.deepcopy(snap)
    old, new = [service.prepare_cumulative_category_units(OWNER, snap, prompt_version=p)
        for p in ('selected_material.v10','selected_material.v11')]
    fields = json.loads(new.messages()[1]['content'])['fields']
    assert old.request == new.request and old.messages()[1] == new.messages()[1]
    assert new.messages()[0]['content'] == old.messages()[0]['content'] + (
        admission._field_ordinal_units_instruction([f['field'] for f in fields]) +
        admission._field_object_boundaries_units_instruction())
    assert new.request_ref != old.request_ref and snap == before


@pytest.mark.parametrize('profile', ['selected_material.v11', 'selected_material.v12'])
def test_v11_keeps_parent_local_source_binding_and_saved_non_generation_reload(profile):
    from test_analysis_model_parent_local_content import prepare
    snap, p, value = prepare(profile=profile)
    candidate, coverage = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=candidate, coverage=coverage)
    assert json.loads(saved)['state']['schema_version'] == (admission.QUOTED_PARENT_MATERIAL_V11_STATE if profile.endswith('v11') else admission.QUOTED_PARENT_MATERIAL_V12_STATE)
    with patch.object(compiler,'compile_analysis_unit_candidates',side_effect=AssertionError('compile')), \
         patch.object(author,'realize_analysis_unit_candidates',side_effect=AssertionError('author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER,snap,saved) == (candidate,coverage)
    artifact, counts = service.build_cumulative_map(OWNER,snap,model_input=value)
    assert artifact is not None and counts['mapped_count'] == 1 and counts['unparsed_count'] == 0
    assert [(n.node_kind,n.modality,n.polarity) for n in artifact.graph.nodes] == [
        ('ACTION_OR_NONACTION','fact','positive'),('ATTENTION_OR_THOUGHT','wish','negative')]
    assert value.response.raw == json.loads(saved)['state']['response']['raw']


@pytest.mark.parametrize('raw', [
    '{"fields":[{"field":1,"units":[],"field":2,"units":[]}]}',
    '{"fields":[]}',
    '{"fields":[{"field":2,"units":[]}]}'])
@pytest.mark.parametrize('profile', ['selected_material.v11', 'selected_material.v12'])
def test_v11_never_repairs_duplicate_keys_missing_fields_or_wrong_ordinals(raw, profile):
    p = service.prepare_cumulative_category_units(OWNER,source_snapshot(1),prompt_version=profile)
    response = admission.AnalysisModelQuotedParentUnitsResponse(p.request_ref,admission.digest(p.messages()),
        hashlib.sha256(raw.encode()).hexdigest(),'stop',raw)
    with pytest.raises(admission.AnalysisSemanticError):
        admission._admit_quoted_parent_units(p.request,replace(p,response=response))


@pytest.mark.parametrize('profile', ['selected_material.v11', 'selected_material.v12'])
def test_v11_does_not_enable_normal_model_selection(profile):
    from analysis_model_source import SelfHostedAnalysisModelSource
    with pytest.raises(ValueError):
        SelfHostedAnalysisModelSource(endpoint='https://synthetic-analysis.invalid/v1/chat/completions',
            model='synthetic-analysis',api_key='synthetic-private-key',prompt_version=profile)
    with pytest.raises(ValueError,match='analysis_model_batch_profile_invalid'):
        service.prepare_cumulative_model_batches(OWNER,source_snapshot(1),prompt_version=profile,
            measure_budget=lambda _:service.AnalysisModelInputBudget(1,1))



def test_v12_inherits_v11_without_mutating_material_or_normal_defaults():
    snap = sample()
    original = copy.deepcopy(snap)
    old, new = [service.prepare_cumulative_category_units(OWNER,snap,prompt_version=p)
        for p in ('selected_material.v11','selected_material.v12')]
    assert old.request == new.request and old.messages()[1] == new.messages()[1]
    assert new.messages()[0]['content'] == old.messages()[0]['content'] + admission._inflection_qualifier_boundaries_units_instruction()
    assert old.request_ref != new.request_ref and admission.digest(old.messages()) != admission.digest(new.messages())
    assert snap == original and service.prepare_cumulative_category_units(OWNER,snap).prompt_version == 'selected_categories.v1'


@pytest.mark.parametrize('extra', [
    [dict(kind='WRITTEN_MODIFIER',quote='たかった')],
    [dict(kind='EXPLICIT_ACTOR',quote='僕')]])
def test_v12_does_not_repair_or_adopt_a_misannotated_past_wish(extra):
    snap=source_snapshot(1)
    text='私は費用を記録したかった'
    snap['members'][0]['original'].update(memo=text+'。',memo_action='')
    p=service.prepare_cumulative_category_units(OWNER,snap,prompt_version='selected_material.v12')
    value=call(p,dict(fields=[dict(field=1,units=[unit(text,'ATTENTION_OR_THOUGHT',actor='私',qualifiers=extra)])]))
    if extra[0]['kind']=='EXPLICIT_ACTOR':
        with pytest.raises(admission.AnalysisSemanticError):
            service.build_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value)
    else:
        artifact,counts=service.build_cumulative_map(OWNER,snap,model_input=value)
        assert artifact is None and counts['unparsed_count']==1
        assert value.response.raw == admission.canonical(dict(fields=[dict(field=1,units=[unit(text,'ATTENTION_OR_THOUGHT',actor='私',qualifiers=extra)])]))
