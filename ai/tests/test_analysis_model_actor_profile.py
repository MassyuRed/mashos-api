"""Opt-in actor explanation preserves source identity and unresolved candidates."""
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
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
