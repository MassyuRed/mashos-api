"""The raw model selects only from the source view of this exact PLAN request."""
from copy import deepcopy
import json

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts, probe
from test_analysis_occurrence_v9_plan import node


def prepared_with(*notes):
    snapshot = source_snapshot(len(notes))
    for row, text in zip(snapshot['members'], notes, strict=True):
        row['original'].update(memo=text, memo_action='')
    return app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V11_PROFILE)


def packet(material, *pairs):
    return dict(schema_version=core._semantic_v4_schema('PLAN'),
                source_choices_sha256=material['source_choices_sha256'],
                nodes=[node(i, [dict(quote=q, field=f)]) for i, (f, q) in enumerate(pairs, 1)])


def test_short_selections_and_literal_passages_roundtrip_without_changing_receipt_or_source():
    p = prepared_with('初日は薄い紙を五枚折った。窓を開けた。', '翌日は厚い紙を二枚折った。窓を閉めた。')
    material = json.loads(p.messages()[1]['content'])
    original, table, _ = choices.restore_view(material)
    assert [f['text'] for f in original['fields']] == [f['text'] for f in json.loads(p.material_json)['fields']]
    raw = packet(material, (1, '@1'), (2, original['fields'][1]['text']))
    assert accepts(raw, p.messages())
    before = deepcopy(raw)
    plan = core.admit_semantic_node_local_v4_plan_response(p, raw)
    assert plan['nodes'][0]['units'][0]['evidence'] == [dict(quote=table[1, '@1'], field=1)]
    assert plan['nodes'][1] == raw['nodes'][1]
    assert raw == before
    assert 'source_choices_sha256' not in plan


def test_scope_field_unknown_alias_and_ineligible_substring_all_fail_before_nodes():
    p = prepared_with('小皿を二枚並べた。', '広い皿を一枚洗った。')
    messages = p.messages()
    material = json.loads(messages[1]['content'])
    good = packet(material, (1, '@1'), (2, '@2'))
    for f, q in [(2, '@1'), (1, '@999'), (1, '二枚')]:
        bad = packet(material, (f, q), (2, '@2'))
        with pytest.raises(ValueError, match='plan_choice_invalid'):
            core.admit_semantic_node_local_v4_plan_response(p, bad)
        assert not accepts(bad, messages)
    other = dict(good, source_choices_sha256='0'*64)
    assert not accepts(other, messages)
    corrupt_messages = [messages[0], dict(messages[1], content=json.dumps(dict(material, source_choices_sha256='0'*64)))]
    with pytest.raises(ValueError, match='choice_scope_invalid'):
        probe.semantic_output_schema(corrupt_messages)
    changed = deepcopy(material)
    changed['fields'][0]['passages'][0][1] = '異なる記録です。'
    with pytest.raises(ValueError, match='choice_scope_invalid'):
        probe.semantic_output_schema([messages[0], dict(messages[1], content=json.dumps(changed))])
    with pytest.raises(ValueError, match='semantic_plan_sources_invalid'):
        choices.restore_view(dict(material, fields=[None]))
    with pytest.raises(ValueError, match='plan_choice_invalid'):
        core.admit_semantic_node_local_v4_plan_response(p, other)
    for fields in ([material['fields'][0]] * 2, [dict(material['fields'][0], field=True)]):
        altered = [messages[0], dict(messages[1], content=json.dumps(dict(material, fields=fields)))]
        with pytest.raises(ValueError, match='semantic_field_invalid'):
            probe.semantic_output_schema(altered)
    leaf = core.prepare_semantic_leaf(p, (p.frozen.members[0].saved_record_ref,))
    with pytest.raises(ValueError, match='plan_choice_invalid'):
        core.admit_semantic_node_local_v4_plan_response(leaf, good)


def test_literal_selector_collision_and_repeated_or_escaped_prose_are_lossless():
    p = prepared_with('窓を拭いた。', '@1')
    material = json.loads(p.messages()[1]['content'])
    assert material['fields'][1]['text'] == '@1'
    raw = packet(material, (1, '@1'), (2, '@1'))
    assert accepts(raw, p.messages())
    plan = core.admit_semantic_node_local_v4_plan_response(p, raw)
    assert [n['units'][0]['evidence'][0]['quote'] for n in plan['nodes']] == ['窓を拭いた。', '@1']
    text = '同じ。別。 同じ。\n「文。中」。「未完'
    data = {'fields':[dict(field=1, source_role='ORIGINAL_INPUT', text=text)]}
    view, _, allowed = choices.prepare(data)
    assert choices.restore_view(view)[0] == data and '同じ。' not in allowed[1]
    escaped = dict(data['fields'][0], text='彼は"x"と書いた。\n次に記録した。')
    view, _, allowed = choices.prepare(dict(fields=[escaped]))
    assert choices.restore_view(view)[0]['fields'] == [escaped]
    assert '彼は"x"と書いた。' not in allowed[1]


def test_sparse_merge_only_numbers_verified_leaf_choices_inside_shown_fragment():
    text = '机に置いた。箱を閉めた。'
    data = dict(history_stage={'kind':'MERGE'},
        fields=[dict(field=8, text=text, fragment_scalar_range=[7, 7+len(text)], source_role='ORIGINAL_INPUT')],
        leaf_source_index=[dict(field=8, quote='箱を閉めた。', scalar_range=[13,19])])
    view, table, _ = choices.prepare(data)
    assert table == {(8, '@1'): '箱を閉めた。'}
    assert view['fields'] == data['fields']
    assert choices.restore_view(view)[0] == data
    bad = deepcopy(view)
    bad['leaf_source_index'][0]['scalar_range'][0] -= 1
    with pytest.raises(ValueError, match='unbound'):
        choices.restore_view(bad)


def test_v11_example_selects_source_labels_and_uses_its_own_scope():
    p = prepared_with('月曜は内袋を開いた。')
    messages = p.messages()
    example_input = json.loads(messages[0]['content'].split('例入力=')[-1].splitlines()[0])
    example_plan = json.loads(messages[0]['content'].split('例出力=')[-1].splitlines()[0])
    assert example_plan['source_choices_sha256'] == example_input['source_choices_sha256']
    assert example_plan['source_choices_sha256'] != json.loads(messages[1]['content'])['source_choices_sha256']
    assert example_plan['nodes'][0]['units'][0]['evidence'][0]['quote'] == '@1'


def test_leaf_and_merge_replay_the_raw_plan_with_their_own_request_identity():
    import hashlib
    from test_analysis_node_local_v4_phases import artifact, response
    from test_analysis_occurrence_v9_plan import compact
    from test_analysis_occurrence_v11_display import map_stages

    parent, _, _ = map_stages('机に置いた部品を数えた。', '引き出しに袋を戻した。')

    def receipt(stage):
        fields = json.loads(stage.material_json)['fields']
        _, plan, nodes = map_stages(*(f['text'] for f in fields))
        for i, field in enumerate(fields, 1):
            plan['nodes'][i-1]['units'][0]['evidence'][0]['field'] = field['field']
            nodes['nodes'][f'n{i}']['units']['u1']['unknowns'] = []
        nodes['plan_sha256'] = core.semantic_map_hash(plan)
        relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'),
            nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, nodes)),
            qualification_review={}, edges=[], overview=dict(node_refs=['n1'], title=fields[0]['text']))
        result = artifact(stage, (plan, nodes, relations))
        result['schema_version'] = core.semantic_node_local_v4_artifact_schema(stage)
        material = json.loads(stage.messages()[1]['content'])
        raw = compact(packet(material, *((f['field'], '@' + str(i)) for i, f in enumerate(fields, 1))))
        result['phases'][0].update(raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest())
        return response(stage, result)

    leaves = []
    for member in parent.frozen.members:
        leaf = core.prepare_semantic_leaf(parent, (member.saved_record_ref,))
        first = receipt(leaf)
        assert core.build_semantic_stage(leaf, first).request_ref == leaf.request_ref
        leaves.append((leaf, first))
    merge = core.prepare_semantic_merge(parent, tuple(leaves))
    scopes = {json.loads(item.messages()[1]['content'])['source_choices_sha256']
              for item in (parent, leaves[0][0], leaves[1][0], merge)}
    assert len(scopes) == 4
    second = receipt(merge)
    final = core.build_semantic_stage(merge, second)
    review = final.artifact.private_evidence()['graph']['meaning_review']
    assert review['node_local_plan']['phase_artifact'] == json.loads(second.raw)
    assert [entry['raw'] for entry in review['history_synthesis']['leaf_candidates']] == [
        original.raw for _, original in leaves]
