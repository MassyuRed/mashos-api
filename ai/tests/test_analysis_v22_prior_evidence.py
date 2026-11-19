"""Use the author's own intact limits on what an earlier event establishes now."""
import pytest

import analysis_plan_source_choices as source
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v17_record_owners import packet, verify
from test_analysis_occurrence_v18_compact_originals import prepared
from test_analysis_v21_recorded_schedule import V21, material


V22 = 'semantic_map.node_local.v4.occurrence.v22'
SHARED = ('図面を開いた。', '壁の位置を測った。')


@pytest.mark.parametrize('text', [
    '以前の表示は紙に残しているが、それを今も工事中という意味にはしていない。',
    '前回の写真に花が写っていたものの、現在も咲いているとは限らない。',
    '昨日の検査では数値が低かったが、現時点の性能を示すものではない。',
    '先月、担当者が記した温度は控えてあるが、それを現在の室温の根拠にはしていない。',
])
def test_keeps_the_prior_observation_and_the_limit_on_present_interpretation(text):
    assert source._limits_current_inference(text)


@pytest.mark.parametrize('text', [
    '以前の写真には橋が写っていたが、今も通れると考えている。',
    '以前の数字は手元にあるが、当時の計画の根拠にはしていない。',
    '以前は申請の記録を保存した。現在進行中とは限らない。',
    '以前と間取りは違うが、今の作業には使っていない。',
    '昨日の復旧を確認できたら、現在も動いているとは限らない。',
    '以前の記録を見たが、現在も使えるとは限らないとは言っていない。',
    '「先日の写真はあるが、今も設置中とは限らない」と同僚が話した。',
    '仮に昨日の通知を残していたとしても、今の根拠にはならない。',
])
def test_does_not_infer_a_limit_from_merely_adjacent_facts_dialogue_or_hypotheticals(text):
    assert not source._limits_current_inference(text)


def test_free_choice_with_competing_qualifications_and_ineligible_source():
    first = '先月の見取り図はあるが、現在も同じ間取りとは言えない。'
    second = '昨日の写真は手元にあるが、今も同じ位置にあるとは限らない。'
    current = material((*SHARED, first, second), V22)
    assert not source.prior_evidence_limits(current)
    region = source.plan_reading_regions(current, {})[1]
    for quote in (first, second):
        assert region.missing([[(1, SHARED[0]), (1, quote)]]) == 0
    current = material((*SHARED, first, '机には荷物があった。'), V22)
    assert source.prior_evidence_limits(current) == {1: {first}}
    current['fields'][0]['fragment_is_complete_field'] = False
    assert not source.prior_evidence_limits(current)


def test_native_and_admission_retain_the_complete_earlier_source_and_denied_current_inference():
    qualified = '三日前に担当者が記した温度は控えてあるが、それを現在の室温の根拠にはしていない。'
    distractor = '帰りに荷物を置いた。'
    for profile in (V21, V22):
        p = prepared([('図面を確認した。', ''.join((*SHARED, qualified, distractor)))], profile)
        _, original, _, _ = view(p)
        field = next(f['field'] for f in original['fields'] if f['field_path'] == 'memo')
        first = (field, SHARED[0])
        verify(p, packet(p, [[[first, (field, distractor)]]]), profile == V21)
        accepted = verify(p, packet(p, [[[first, (field, qualified)]]]), True)
        assert accepted['nodes'][0]['units'][0]['evidence'][1] == dict(field=field, quote=qualified)
