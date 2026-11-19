"""A short source clause selects its entire provenance-bound original for later phases."""
from copy import deepcopy
import json

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts, probe
from test_analysis_occurrence_v11_plan_choices import packet
from test_analysis_saved_period import with_answer
from test_analysis_semantic_history_core import correction_snapshot

PROFILE = core.SEMANTIC_MAP_OCCURRENCE_V13_PROFILE


def prepare(*notes):
    snapshot = source_snapshot(len(notes))
    for row, note in zip(snapshot['members'], notes, strict=True):
        row['original'].update(memo=note, memo_action='')
    return app.prepare_semantic_map(OWNER, snapshot, prompt_version=PROFILE)


def view(p):
    material = json.loads(p.messages()[1]['content'])
    original, table, allowed = choices.restore_view(material)
    return material, original, table, allowed


def test_each_clause_restores_full_outer_sentence_and_retains_raw_choice():
    quote = '手袋を外したが、見回りの人が「蒸気は止まった」と書いただけで、中の温度は調べていない。'
    p = prepare('廊下を歩いた。' + quote)
    material, original, table, _ = view(p)
    assert original['fields'][0]['text'].endswith(quote)
    cues = [cue for (field, cue), full in table.items() if full == quote]
    assert 2 <= len(cues) <= 3 and cues[0] == '手袋を外したが' and cues[-1] == '中の温度は調べていない'
    for cue in cues:
        raw = packet(material, (1, cue))
        assert accepts(raw, p.messages())
        assert core.admit_semantic_node_local_v4_plan_response(p, raw)['nodes'][0]['units'][0]['evidence'] == [
            dict(field=1, quote=quote)]
        assert raw['nodes'][0]['units'][0]['evidence'][0]['quote'] == cue
    repeated = packet(material, (1, cues[0]), (1, cues[-1]))
    assert not accepts(repeated, p.messages())
    with pytest.raises(ValueError, match='repeated'):
        core.admit_semantic_node_local_v4_plan_response(p, repeated)
    repeated['nodes'][0]['units'][0]['evidence'] += repeated['nodes'].pop()['units'][0]['evidence']
    assert not accepts(repeated, p.messages())
    with pytest.raises(ValueError, match='plan_invalid'):
        core.admit_semantic_node_local_v4_plan_response(p, repeated)


def test_position_has_no_semantic_identity_and_legacy_ordinals_are_unavailable():
    a = '端の計器を読んだが、中央の温度はまだ測っていない。'
    b = '翌朝は塗装室で別の加熱器を止めた。'
    p, rotated = prepare('机を拭いた。' + a + b), prepare(b + a + '机を拭いた。')
    m, _, table, _ = view(p)
    rotated_m, _, reordered, _ = view(rotated)
    assert table == reordered and m['source_choices_sha256'] != rotated_m['source_choices_sha256']
    assert table[1, '中央の温度はまだ測っていない'] == a
    assert table[1, b[:-1]] == b
    for bad in (packet(m, (1, '@1')), packet(m, (1, '中央の温度')), packet(rotated_m, (1, b[:-1]))):
        assert not accepts(bad, p.messages())
        with pytest.raises(ValueError, match='choice_invalid'):
            core.admit_semantic_node_local_v4_plan_response(p, bad)
    leaf = core.prepare_semantic_leaf(p, (p.frozen.members[0].saved_record_ref,))
    with pytest.raises(ValueError, match='choice_invalid'):
        core.admit_semantic_node_local_v4_plan_response(leaf, packet(m, (1, b[:-1])))


def test_sparse_merge_preserves_compounds_ambiguous_clauses_long_literals_and_offsets():
    first = '風を調べたが、旗は動かなかった。'
    second = '周囲を見たが、旗は動かなかった。'
    long = 'この欄には読点や区切りを使わない長い言葉があり途中の数文字に切り分けてはいけない。'
    text = first + second + long
    rows = [dict(field=7, scalar_range=[8+text.index(q), 8+text.index(q)+len(q)], quote=q)
            for q in (first, second, first + second, long)]
    data = dict(author_profile=PROFILE, history_stage={'kind':'MERGE'},
        fields=[dict(field=7, source_role='ORIGINAL_INPUT', text=text, fragment_scalar_range=[8, 8+len(text)])],
        leaf_source_index=rows)
    wire, table, allowed = choices.prepare(data)
    assert choices.restore_view(wire)[0] == data and wire['fields'][0]['text'] == text
    assert (7, '旗は動かなかった') not in table
    assert table[7, long] == long
    for shown, row in zip(wire['leaf_source_index'], rows, strict=True):
        assert row['quote'] in allowed[7] and all(table[7, cue] == row['quote'] for cue in shown['choice'])
    raw = deepcopy(wire)
    raw['leaf_source_index'][0]['scalar_range'][0] -= 1
    with pytest.raises(ValueError, match='unbound'):
        choices.restore_view(raw)


def test_supplement_and_entire_correction_remain_bound_to_their_own_field_and_clock():
    snap = correction_snapshot()
    snap['members'][0]['original']['emotion_details'] = [dict(type='平穏', strength='medium')]
    snap['members'][0] = with_answer(snap['members'][0], '私は日程を決めなかった。')
    p = app.prepare_semantic_map(OWNER, snap, prompt_version=PROFILE)
    material, original, table, _ = view(p)
    source = {f['field']: f for f in json.loads(p.material_json)['fields']}
    for f in original['fields']:
        before = source[f['field']]
        assert all(f[key] == val for key, val in before.items())
    supplement, = [f for f in source.values() if f['source_role'] == 'SUPPLEMENTAL_ANSWER']
    correction, = [f for f in source.values() if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION']
    assert correction['record'] is None and correction['record_refs'] == [1, 2]
    row = next(f for f in material['fields'] if f['field'] == correction['field'])
    assert row['source_recorded_at'] == correction['source_recorded_at']
    assert table[supplement['field'], '私は日程を決めなかった'] == supplement['text']
    c = [k for (f, k), text in table.items() if f == correction['field'] and text == correction['text']]
    assert len(c) == 2
    first_by_record = {}
    for (field, cue), quote in table.items():
        if source[field]['source_role'] == 'ORIGINAL_INPUT':
            first_by_record.setdefault(source[field]['record'], (field, cue))
    raw = packet(material, *first_by_record.values(), (supplement['field'], '私は日程を決めなかった'),
                 (correction['field'], c[0]))
    assert accepts(raw, p.messages())
    closed = core.admit_semantic_node_local_v4_plan_response(p, raw)
    assert closed['nodes'][-1]['units'][0]['evidence'] == [dict(quote=correction['text'], field=correction['field'])]
    # Same words cannot be carried as somebody else's original or a shortened correction.
    for field in [supplement['field'], next(iter(first_by_record.values()))[0]]:
        bad = deepcopy(raw)
        bad['nodes'][-1]['units'][0]['evidence'][0]['field'] = field
        assert not accepts(bad, p.messages())
        with pytest.raises(ValueError):
            core.admit_semantic_node_local_v4_plan_response(p, bad)
    swapped = deepcopy(material)
    next(f for f in swapped['fields'] if f['field'] == supplement['field'])['source_role'] = 'ORIGINAL_INPUT'
    with pytest.raises(ValueError, match='choice_scope_invalid'):
        probe.semantic_output_schema([p.messages()[0], dict(role='user', content=json.dumps(swapped))])


def test_worked_example_keeps_unconfirmed_and_unperformed_events_without_emptying_each_field():
    p = prepare('鉢を運んだ。')
    prompt = p.messages()[0]['content']
    shown = json.loads(prompt.split('例入力=')[-1].splitlines()[0])
    plan = json.loads(prompt.split('例出力=')[-1].splitlines()[0])
    original, table, _ = choices.restore_view(shown)
    selected = {table[r['field'], r['quote']] for n in plan['nodes'] for u in n['units'] for r in u['evidence']}
    assert {'予備のポンプは動かしていない。', '羽根が欠けているかは中を開けるまで分からない。'} <= selected
    assert '作業台を拭いた。' in original['fields'][0]['text'] and '作業台を拭いた。' not in selected
    assert len(plan['nodes']) == 2 and '枠を埋める必要はありません' in prompt
