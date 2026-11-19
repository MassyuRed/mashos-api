"""Ordinary PLAN author selects separated original context within the existing evidence budget."""
from copy import deepcopy
import pytest

import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import advance
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v17_record_owners import compact, packet, parser, verify
from test_analysis_occurrence_v18_compact_originals import prepared

V19, V20 = core.SEMANTIC_MAP_OCCURRENCE_V19_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V20_PROFILE
SENTENCES = ('展示台に箱があった。', '私は受付で札を受け取った。', '配置を記録した。', '待ち時間を測った。', '窓を開けた。', '次に来る日は決めた。')
ACTION = '会場を訪ねた。'


def sample(version=V20, text=None):
    p = prepared([(ACTION, text or ''.join(SENTENCES))], version)
    shown, original, _, _ = view(p)
    field = next(f['field'] for f in original['fields'] if f['field_path'] == 'memo')
    return p, field, shown, original


@pytest.mark.parametrize('version,valid', [(V19, True), (V20, False)])
def test_scattered_source_is_verifiable_without_prescribing_any_particular_sentence(version, valid):
    p, f, shown, orig = sample(version)
    assert ('memo_reading_regions' in shown['records'][0]) == (version == V20)
    verify(p, packet(p, [[[(f, SENTENCES[4]), (f, SENTENCES[0])]]]), valid)
    for indices in [(4, 2, 0), (1, 3, 5)]:
        verify(p, packet(p, [[[(f, SENTENCES[i]) for i in indices]]]), True)
    for left, right in ((1, 2), (3, 4)):
        third = SENTENCES[0] if left == 3 else SENTENCES[-1]
        verify(p, packet(p, [[[(f, SENTENCES[left] + SENTENCES[right])], [(f, third)]]]), True)


def test_source_overlap_is_local_to_one_fact_and_preserves_new_context():
    p, f, _, _ = sample()
    repeated = [(f, s) for s in (SENTENCES[0], SENTENCES[1], SENTENCES[0] + SENTENCES[1])]
    rest = [(f, SENTENCES[3]), (f, SENTENCES[5])]
    verify(p, packet(p, [[repeated, rest]]), False)
    verify(p, packet(p, [[repeated[:2], [repeated[2], *rest]]]), True)
    extended = [(f, SENTENCES[0]), (f, SENTENCES[0] + SENTENCES[1]), *rest]
    verify(p, packet(p, [[extended]]), True)


def test_last_unit_reserves_slots_and_exposes_a_completion_after_the_last_free_choice():
    p, f, _, _ = sample()
    last = [(f, SENTENCES[i]) for i in (0, 1, 3, 5)]
    raw = packet(p, [[[(f, SENTENCES[0])], last]])
    first, second, _, _ = [compact(root) for root in raw['nodes'][0]['units'][1]['evidence']]
    wire = compact(raw)
    cut = wire.index(second, wire.rindex('{"evidence":[')) + len(second)
    state = advance(parser(p, raw), wire[:cut])
    assert ']' not in state.get_allowed_characters()
    with pytest.raises(ValueError):
        advance(state, ',' + first)
    assert advance(state, wire[cut:]).can_end()


def test_real_paragraphs_bind_positions_and_recovery_refuses_tampered_reading_ranges():
    paragraphs = [''.join(f'第{i}段の記録{j}をメモした。' for j in range(count))
                  for i, count in enumerate((3, 10, 5, 3, 5, 4))]
    text = '\n\n'.join(paragraphs)
    p, field, shown, original = sample(text=text)
    bounds = shown['records'][0]['memo_reading_regions']
    assert bounds['field'] == field
    assert [text[a:b] for a, b in bounds['scalar_ranges']] == [
        '\n\n'.join(paragraphs[i:i + 2]) for i in (0, 2, 4)]
    corrupt = deepcopy(shown)
    corrupt['records'][0]['memo_reading_regions']['scalar_ranges'][1][0] += 1
    with pytest.raises(ValueError, match='unbound'):
        choices.restore_view(corrupt)
    action_field, action, _ = choices.compact_action_pairs(original)[1]
    selected = [(field, paragraphs[i].split('。')[1] + '。') for i in (1, 2, 5)]
    verify(p, packet(p, [[[(action_field, action)], selected]]), True)


def test_history_updates_fragments_small_or_over_budget_materials_keep_free_reading():
    _, _, _, original = sample()
    short = deepcopy(original)
    for field in short['fields']:
        if field['field_path'] == 'memo':
            field['text'] = ''.join(SENTENCES[:3])
    assert not choices.plan_reading_regions(short, {})
    for stage in ('LEAF', 'MERGE'):
        assert not choices.plan_reading_regions(dict(original, history_stage=dict(kind=stage)), {})
    for key in ('conflicts', 'source_updates', 'unresolved_sources'):
        updated = dict(original, emlis_source_materials=[{'record': 1, key: ['更新']}])
        assert not choices.plan_reading_regions(updated, {})
    for role in ('SUPPLEMENTAL_ANSWER', 'USER_ANALYSIS_MAP_CORRECTION'):
        extra = dict(record=1, field=7, field_path='answer', source_role=role, text='本人からの追記。')
        assert not choices.plan_reading_regions(dict(original, fields=[*original['fields'], extra]), {})
    cut = deepcopy(original)
    cut['fields'][0]['fragment_is_complete_field'] = False
    assert not choices.plan_reading_regions(cut, {})
    costly = ''.join(chr(0x21001 + i) * 85 + '。' for i in range(6))
    _, _, shown, original = sample(text=costly)
    assert not choices.plan_reading_regions(original, choices.compact_action_pairs(original))
    assert 'memo_reading_regions' not in shown['records'][0]


def test_one_last_citation_can_cover_both_remaining_regions_at_their_boundary():
    p, field, _, original = sample()
    action = next(f['field'] for f in original['fields'] if f['field_path'] == 'memo_action')
    # The first three choices in the last unit still cover only the first region.
    last = [(field, SENTENCES[0]), (action, ACTION), (field, SENTENCES[1]), (field, SENTENCES[3] + SENTENCES[4])]
    verify(p, packet(p, [[[(action, ACTION)], last]]), True)
