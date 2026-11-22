"""Preserve an original current state paired with an explicitly scheduled time."""
from copy import deepcopy

import pytest

import analysis_plan_source_choices as source


V20 = 'semantic_map.node_local.v4.occurrence.v20'
V21 = 'semantic_map.node_local.v4.occurrence.v21'


def material(sentences, profile=V21):
    def field(number, path, value):
        return dict(field=number, field_path=path, text=value, source_role='ORIGINAL_INPUT', record=1)
    return dict(author_profile=profile, records=[dict(record=1, recorded_at='2026-05-11T16:00:00Z')],
        fields=[field(1, 'memo', ''.join(sentences)), field(2, 'memo_action', '書類を確認した。')])


@pytest.mark.parametrize('sentence', [
    '引き渡しは来月なので、まだ鍵を渡していない。', '返却を明後日に決めたが、今は自宅にある。',
    '受取日は三日後と決まったので、現在は窓口にある。',
])
def test_citation_preserves_both_written_times(sentence):
    other = ('別紙に番号を控えた。', '荷物の封を閉じた。', '出発の時刻を確かめた。')
    for sentences in ((sentence, *other), (*other, sentence)):
        orig = material(sentences)
        expected = [i for i, q in enumerate(sentences) if q != sentence]
        before = source.plan_reading_regions(dict(orig, author_profile=V20), {})[1]
        after = source.plan_reading_regions(orig, {})[1]
        chosen = [[(1, sentences[i]) for i in expected]]
        assert not before.missing(chosen) and after.missing(chosen)
        assert not after.missing([*chosen, [(1, sentence)]])
        assert not after.missing([*chosen, [(1, ''.join(sentences[:2] if sentences[0] == sentence else sentences[-2:]))]])
        shown, _, _ = source.prepare(orig)
        assert source.restore_view(shown)[0] == orig
        corrupt = deepcopy(shown)
        corrupt['records'][0]['memo_reading_regions']['scalar_ranges'][0][0] += 1
        with pytest.raises(ValueError):
            source.restore_view(corrupt)


@pytest.mark.parametrize('text', [
    '来月は旅行に行きたいが、今は家にいる。', '来週晴れたら、まだ開いていない窓を開けよう。',
    '「開始は明日なので、まだ始めていない」と聞いた。', '来週は受付がある。まだ提出していない。',
    '開催は来月かもしれないので、まだ予約していない。', '来年だが、現在はどうなのか？',
    '明日持っていく予定で、別の棚の位置も測った。',
])
def test_no_time_claim_inferred_from_hopes_or_unlinked_sentences(text):
    assert not source._scheduled_current_state(text)


def test_repeat_defers_to_an_outstanding_source_but_separate_facts_can_share_it_afterward():
    question = '担当が戻ったかは聞いていない。'
    plain = ('荷物を届けた。', '印を受け取った。', '荷物の写真を保存した。')
    orig = material((*plain, question))
    region = source.plan_reading_regions(orig, {})[1]
    first, second = [[(1, plain[0]), (1, plain[1])]], [(1, plain[2])]
    assert not region.can_reuse(first, second, 1, plain[0])
    assert region.can_reuse(first, second, 1, question)
    assert region.can_reuse(first, [*second, (1, question)], 1, plain[0])
    assert region.can_reuse(first, [*second, (1, plain[2] + question)], 1, plain[0])
    for non_report in ('いつか行きたい。', '担当の帰宅を確認した。', '「戻ったかは聞いていない」と知人が書いた。'):
        ordinary = source.plan_reading_regions(material((*plain, non_report)), {})[1]
        assert ordinary.can_reuse(first, second, 1, plain[0])


def test_prior_profiles_never_add_a_report_prerequisite():
    plain = ('紙を広げた。', '先方が着いたかは確認していない。', '封筒を開けた。', '署名をした。')
    old = source.plan_reading_regions(material(plain, profile=V20), {})[1]
    assert old.can_reuse([[(1, plain[0])]], [], 1, plain[0])


def test_crowded_unconfirmed_reports_do_not_consume_the_remaining_unit():
    open_reports = ('店に届いたかは聞いていない。', '相手が戻ったかは尋ねていない。', '箱を見たかも確認していない。')
    plain = ('封筒を重ねた。', '表紙に印をつけた。', '家に帰った。')
    region = source.plan_reading_regions(material((*open_reports, *plain)), {})[1]
    assert not region.open_reports
    assert region.can_reuse([[(1, plain[0])]], [], 1, plain[0])


def test_native_and_cmee_compare_original_report_before_reuse():
    from test_analysis_occurrence_v13_plan_choices import view
    from test_analysis_occurrence_v17_record_owners import packet, verify
    from test_analysis_occurrence_v18_compact_originals import prepared

    sentences = ('封筒を用意した。', '担当者が着いたかは確認していない。', '用紙を広げた。', '机の位置を調べた。')
    for profile in (V20, V21):
        p = prepared([('荷物を受け取った。', ''.join(sentences))], profile)
        _, original, _, _ = view(p)
        field = next(f['field'] for f in original['fields'] if f['field_path'] == 'memo')
        first, second = [(field, sentences[0])], [(field, sentences[2])]
        verify(p, packet(p, [[first, [*second, *first]]]), profile == V20)
        verify(p, packet(p, [[first, [*second, (field, sentences[1]), *first]]]), True)
