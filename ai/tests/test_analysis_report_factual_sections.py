"""Independent quantitative fixtures for the existing weather report renderer.

Card/section/graph shapes are retained while unsupported psychological claims
are replaced by observations. These tests do not certify model understanding.
"""
from copy import deepcopy
import json

import pytest

import api_analysis_reports as reports


KEYS = ('joy', 'sadness', 'anxiety', 'anger', 'calm')
SUMMARY_KEYS = {'overviewComment', 'movementItems', 'timeComment', 'readerComment',
    'structuralComment', 'gentleComment', 'nextPoints', 'evidence', 'compositionMode', 'source'}
STANDARD_KEYS = {'version', 'displayMode', 'reportType', 'contentText', 'metrics',
    'features', 'timeline', 'summary', 'analysisPayload', 'timeBuckets'}
UNSUPPORTED = ('安心を確かめたい', '同じテーマ', '気持ちの芯', '戻ろう', '整え直そう',
    'ためと考える', '人への配慮', '自分を支えるため', '自分を責め', '反応の軸')


def fixture(kind):
    totals = dict(joy=3, sadness=2, anxiety=1, anger=0, calm=9)
    shares = dict(joy=20, sadness=13, anxiety=7, anger=0, calm=60)
    buckets = [{'dateKey': '2026-11-02', 'label': '11/2', **totals},
        {'dateKey': '2026-11-03', 'label': '11/3', **dict.fromkeys(KEYS, 0)}]
    time_buckets = [{'bucket': '18-24', 'inputCount': 4, 'weightedTotal': 15,
        'weightedCounts': totals, 'counts': dict(joy=1, sadness=1, anxiety=1, anger=0, calm=3),
        'sharePct': shares, 'dominantKey': 'calm'}]
    weekly = dict(n_events=6, counts=dict(joy=1, sadness=1, anxiety=1, anger=0, peace=3),
        wcounts=dict(joy=3, sadness=2, anxiety=1, anger=0, peace=9),
        share=dict(joy=.2, sadness=2/15, anxiety=1/15, anger=0, peace=.6),
        daily_share=[{'date': '2026-11-02', 'share': dict(peace=.9, anxiety=.1)}],
        alternation_rate=0, entropy=.5, gini_simpson=.5, run_stats={'max': 2},
        intensity={'mean': 2.5}, motifs=[{'motif': 'joy-peace-joy'}], motif_counts={'joy-peace-joy': 1},
        center2d={'x': 0, 'y': 1}, keywords=['synthetic-word'], time_buckets=time_buckets)
    payload = {'entry_count': 6, 'weekly_snapshot': weekly,
        'monthly_report': {'share_trend': [dict(peace=.9, anxiety=.1)],
            'alternation_trend': [0], 'intensity_std_trend': [.5],
            'center_shift': {'distance': .1}, 'motif_trend': [{'synthetic': 1}],
            'time_buckets': time_buckets},
        'snapshot_ref': {'snapshot_id': 'synthetic-source'},
        'period': {'start_iso': '2026-11-01T15:00:00Z', 'end_iso': '2026-11-08T14:59:59.999Z'}}
    views = dict(metrics={'totals': totals, 'sharePct': shares, 'totalAll': 15},
        day=buckets[0], days=buckets, weeks=[dict(index=i, label=f'第{i+1}週', total=15 if i == 0 else 0,
            **(totals if i == 0 else dict.fromkeys(KEYS, 0))) for i in range(4)],
        movement={'key': 'down', 'totalToday': 15, 'totalYesterday': 20,
            'diffTotal': -5, 'dominantToday': 'calm', 'dominantYesterday': 'anxiety'},
        timeBuckets=time_buckets)
    return dict(report_type=kind, title='synthetic report', period_start_iso='2026-11-01T15:00:00Z',
        period_end_iso='2026-11-08T14:59:59.999Z', analysis_payload=payload,
        snapshot_summary={'emotions_public': 4, 'emotions_total': 5}, snapshot_views=views)


@pytest.mark.parametrize('kind', ['daily', 'weekly', 'monthly'])
def test_standard_preserves_all_previous_keys_sections_cards_and_quantitative_graphs(kind):
    data = fixture(kind)
    before = deepcopy(data)
    result = reports._build_standard_report_payload(**data)
    assert set(result) == STANDARD_KEYS
    assert set(result['summary']) == SUMMARY_KEYS
    assert result['contentText'].count('【') == 5
    assert len(result['summary']['movementItems']) == 4
    assert len(result['summary']['evidence']['items']) == 4
    assert len(result['summary']['readerComment'].split('。')) >= 5
    assert result['metrics']['weightedCounts'] == before['snapshot_views']['metrics']['totals']
    assert result['metrics']['share'] == before['snapshot_views']['metrics']['sharePct']
    assert result['metrics']['totalAll'] == 15
    assert len(result['timeBuckets']) == 4
    evening = next(row for row in result['timeBuckets'] if row['bucket'] == '18-24')
    assert evening['inputCount'] == 4
    assert evening['weightedTotal'] == 15
    assert result['features']['snapshotRef'] == before['analysis_payload']['snapshot_ref']
    assert result['features']['period'] == before['analysis_payload']['period']
    if kind == 'daily':
        assert result['metrics']['entryCount'] == 4
        assert result['features']['day'] == before['snapshot_views']['day']
        assert result['features']['movement'] == before['snapshot_views']['movement']
    elif kind == 'weekly':
        assert result['metrics']['eventCount'] == 4
        assert result['features']['days'] == before['snapshot_views']['days']
        for key in ('runStats', 'intensity', 'motifs', 'motifCounts', 'center2d', 'keywords'):
            assert result['features'][key]
    else:
        assert result['features']['weeks'] == before['snapshot_views']['weeks']
        assert len(result['features']['weeklyBreakdown']) == 4
        assert result['metrics']['alternationTrend'] == [0]
        assert result['metrics']['intensityStdTrend'] == [.5]
        assert result['metrics']['centerShift'] == {'distance': .1}
        assert result['features']['motifTrend'] == [{'synthetic': 1}]
    displayed = result['contentText'] + json.dumps(result['summary'], ensure_ascii=False)
    assert not any(phrase in displayed for phrase in UNSUPPORTED)
    assert data == before


def test_weekly_peace_fraction_alias_and_counts_are_not_mistaken_for_raw_input_count():
    data = fixture('weekly')
    data['snapshot_summary']['emotions_public'] = 1
    result = reports._build_standard_report_payload(**data)
    assert result['metrics']['eventCount'] == 1
    assert result['metrics']['weightedCounts']['calm'] == 9
    assert result['metrics']['share']['calm'] == 60
    assert result['metrics']['counts']['calm'] == 3
    assert result['timeline'][0]['share'] == dict(joy=0, sadness=0, anxiety=10, anger=0, calm=90)
    assert '最大の加重値は「平穏」の9' in result['contentText']
    assert '分析対象の入力が1件' in result['contentText']
    assert '公開' not in result['contentText']
    assert '入力件数1件' in result['contentText']


@pytest.mark.parametrize('kind', ['daily', 'weekly', 'monthly'])
def test_generated_analysis_comments_cannot_replace_snapshot_quantitative_observations(kind):
    data = fixture(kind)
    data['analysis_payload']['narrative'] = {'structural_comment': 'あなたの本質は不安です。',
        'gentle_comment': '安心を確かめたいからです。'}
    data['analysis_payload']['weekly_snapshot']['wcounts'] = {'anxiety': 999, 'peace': 0}
    data['analysis_payload']['weekly_snapshot']['share'] = {'anxiety': 1.0, 'peace': 0}
    result = reports._build_standard_report_payload(**data)
    assert result['metrics']['weightedCounts']['calm'] == 9
    assert result['metrics']['share']['calm'] == 60
    assert '最大の加重値は「平穏」の9' in result['contentText']
    assert 'あなたの本質' not in result['contentText']
    assert '安心を確かめたい' not in result['contentText']


def test_monthly_fraction_trend_has_the_same_percentage_unit_and_calm_label_as_its_charts():
    result = reports._build_standard_report_payload(**fixture('monthly'))
    expected = dict(joy=0, sadness=0, anxiety=10, anger=0, calm=90)
    assert result['metrics']['shareTrend'] == [expected]
    assert result['timeline'] == [expected]


def test_absent_time_buckets_do_not_imply_reactions_spread_across_a_day():
    data = fixture('weekly')
    data['snapshot_views'].pop('timeBuckets')
    data['analysis_payload']['weekly_snapshot'].pop('time_buckets')
    data['analysis_payload']['monthly_report'].pop('time_buckets')
    result = reports._build_standard_report_payload(**data)
    assert '時間帯別の内訳がありません' in result['summary']['timeComment']
    assert '朝から夜' not in result['summary']['timeComment']
    assert result['contentText'].count('【') == 5


def test_snapshot_zero_and_ties_are_preserved_without_derived_positive_values_overriding_them():
    data = fixture('weekly')
    data['snapshot_views']['metrics'] = {'totals': dict.fromkeys(KEYS, 0),
        'sharePct': dict.fromkeys(KEYS, 0), 'totalAll': 0}
    result = reports._build_standard_report_payload(**data)
    assert result['metrics']['weightedCounts'] == dict.fromkeys(KEYS, 0)
    assert '強度を加えた合計は0' in result['contentText']
    data['snapshot_views']['metrics'] = {'totals': dict(joy=3, sadness=0, anxiety=0, anger=0, calm=3),
        'sharePct': dict(joy=50, sadness=0, anxiety=0, anger=0, calm=50), 'totalAll': 6}
    result = reports._build_standard_report_payload(**data)
    assert '最大の加重値は「喜び・平穏」の3' in result['contentText']


def deep_fixture(kind, version='emotion_structure.deep.v2'):
    edges = [dict(from_label='anxiety', to_label='calm', count=3, share=.75,
        mean_minutes=30, median_minutes=25, p75_minutes=45,
        mean_intensity_from=3, mean_intensity_to=2, dominant_time_buckets=['18-24'], evidence={'count': 3}),
        dict(from_label='calm', to_label='joy', count=1, share=.25,
        mean_minutes=10, median_minutes=10, p75_minutes=10,
        mean_intensity_from=2, mean_intensity_to=1, dominant_time_buckets=['6-12'], evidence={'count': 1})]
    poison = 'あなたの本質は、安心を確かめたい気持ちです。自分を支えるためです。'
    themes = [dict(theme_id=f'theme_{i+1}', theme_hint=hint,
        phrase_samples=[f'記録を確認した{i+1}', f'資料を開いた{i+1}'],
        keywords=[f'確認{i+1}'], linked_transition_keys=[route],
        dominant_time_buckets=['18-24'], count=count, meaning_comment=poison)
        for i, (hint, route, count) in enumerate([
            ('self_pressure', 'anxiety->calm', 3), ('interpersonal_caution', 'calm->joy', 1)])]
    patterns = [dict(pattern_id=f'pattern_{i+1}', label=poison, description=poison,
        size=edge['count'], score=edge['share'], transition_keys=[f"{edge['from_label']}->{edge['to_label']}"],
        representative_edges=[edge], dominant_time_buckets=edge['dominant_time_buckets'])
        for i, edge in enumerate(edges)]
    episodes = [dict(pattern_id=f'pattern_{i+1}', linked_theme_ids=[f'theme_{i+1}'],
        route_keys=[f"{edge['from_label']}->{edge['to_label']}"],
        recovery_route_key=f"{edge['from_label']}->{edge['to_label']}", count=edge['count'],
        pattern_label=poison, pattern_comment=poison)
        for i, edge in enumerate(edges)]
    phases = [dict(phase_id=key, phase_label=label, entry_count=entry_count, transition_count=edge['count'],
        theme_hints=[themes[i]['theme_hint']], theme_labels=[poison],
        phrase_samples=themes[i]['phrase_samples'], route_keys=episodes[i]['route_keys'],
        recovery_route_key=episodes[i]['recovery_route_key'], dominant_time_buckets=edge['dominant_time_buckets'],
        count=entry_count, phase_comment=poison)
        for i, (key, label, entry_count, edge) in enumerate([
            ('first_half', '前半', 6, edges[0]), ('second_half', '後半', 4, edges[1])])]
    shifts = [dict(shift_id='first_to_second', from_phase_id='first_half', to_phase_id='second_half',
        emerging_theme_hints=['interpersonal_caution'], settling_theme_hints=['self_pressure'],
        emerging_theme_labels=[poison], settling_theme_labels=[poison],
        emerging_route_keys=['calm->joy'], settling_route_keys=['anxiety->calm'],
        from_recovery_route_key='anxiety->calm', to_recovery_route_key='calm->joy',
        direction_hint='recovery_shift', shift_label=poison, shift_comment=poison)]
    model = dict(transition_matrix={'anxiety': {'calm': 3}, 'calm': {'joy': 1}},
        transition_edges=edges, recovery_time=[dict(edge, min_minutes=5, max_minutes=45) for edge in edges],
        memo_triggers=[dict(keyword='確認', count=3, related_emotions=['anxiety', 'calm'],
            related_transitions=['anxiety->calm'], phrase_samples=['記録を確認した'], theme_hint='self_pressure')],
        memo_themes=themes, control_patterns=patterns, pattern_episodes=episodes,
        monthly_phases=phases if kind == 'monthly' else [], monthly_shifts=shifts if kind == 'monthly' else [],
        summary={'transitionCount': 4, 'edgeCount': 2, 'patternCount': 2,
            'memoKeywordCount': 1, 'memoThemeCount': 2, 'patternEpisodeCount': 2,
            'quoteSampleCount': 4, 'themeLinkedTransitionCount': 2,
            'phaseCount': 2 if kind == 'monthly' else 0, 'shiftCount': 1 if kind == 'monthly' else 0},
        meta={'analysisVersion': version, 'clustering': 'synthetic'})
    return dict(report_type=kind, title='synthetic deep report', period_start_iso='2026-11-01T15:00:00Z',
        period_end_iso='2026-11-08T14:59:59.999Z', deep_analysis_payload={
            'analysis_version': version, 'snapshot_ref': {'snapshot_id': 'synthetic-source'},
            'period': {'start_iso': '2026-11-01T15:00:00Z', 'end_iso': '2026-11-08T14:59:59.999Z'},
            'deep_control_model': model})


@pytest.mark.parametrize('kind,sections', [('daily', 5), ('weekly', 6), ('monthly', 7)])
def test_deep_keeps_full_cards_graphs_statistics_and_sections_without_psychological_comments(kind, sections):
    data = deep_fixture(kind)
    before = deepcopy(data)
    result = reports._build_structural_report_payload(**data)
    assert result is not None
    assert result['contentText'].count('【') == sections
    assert len(result['summary']['themeItems']) == 2
    assert len(result['summary']['movementItems']) == 3
    assert len(result['memoThemes']) == 2
    assert len(result['memoTriggers']) == 1
    assert len(result['controlPatterns']) == 2
    assert len(result['patternEpisodes']) == 2
    assert len(result['transitionEdges']) == 2
    assert len(result['recoveryTime']) == 2
    assert result['transitionMatrix']['anxiety']['calm'] == 3
    assert result['transitionEdges'][0]['count'] == 3
    assert result['transitionEdges'][0]['share'] == .75
    assert result['recoveryTime'][0]['meanMinutes'] == 30
    assert result['recoveryTime'][0]['medianMinutes'] == 25
    assert result['metrics']['transitionCount'] == 4
    assert result['metrics']['patternCount'] == 2
    assert result['metrics']['quoteSampleCount'] == 4
    if kind in ('weekly', 'monthly'):
        assert len(result['summary']['patternItems']) == 2
    if kind == 'monthly':
        assert len(result['summary']['phaseItems']) == 2
        assert len(result['summary']['shiftItems']) == 1
        assert len(result['monthlyPhases']) == 2
        assert len(result['monthlyShifts']) == 1
        assert all(row['phaseComment'] for row in result['monthlyPhases'])
        assert all(row['shiftComment'] for row in result['monthlyShifts'])
        assert '感情ラベルの集計対象は6件' in result['contentText']
        assert '前半と後半の集計項目の比較' in result['contentText']
    displayed = result['contentText'] + json.dumps(result['summary'], ensure_ascii=False)
    displayed += json.dumps({key: result[key] for key in ('memoThemes', 'controlPatterns', 'patternEpisodes', 'monthlyPhases', 'monthlyShifts')}, ensure_ascii=False)
    assert not any(value in displayed for value in UNSUPPORTED)
    assert 'あなたの本質' not in displayed
    assert '記録間隔' in result['contentText']
    assert data == before


def test_deep_v1_fallback_keeps_its_cards_and_observation_sections():
    data = deep_fixture('daily', version='emotion_structure.deep.v1')
    result = reports._build_structural_report_payload(**data)
    assert result['contentText'].count('【') == 6
    assert set(result['summary']) == {'structuralComment', 'gentleComment', 'nextPoints', 'evidence', 'source'}
    assert len(result['summary']['evidence']['items']) == 4
    assert len(result['summary']['nextPoints']) == 4
    assert '遷移が4件' in result['contentText']
    assert '平均30分' in result['contentText']
    assert '中央値は25分' in result['contentText']
    assert not any(value in result['contentText'] for value in UNSUPPORTED)


@pytest.mark.parametrize('kind', ['daily', 'weekly', 'monthly'])
def test_legacy_light_renderers_keep_the_full_period_observation_and_do_not_invent_input_counts(kind):
    data = fixture(kind)
    common = {key: data[key] for key in ('title', 'period_start_iso', 'period_end_iso')}
    views = data['snapshot_views']
    if kind == 'daily':
        text = reports._render_daily_standard_v3_text(**common, metrics=views['metrics'],
            summary={'emotions_public': 4}, movement=views['movement'])
        assert '分析対象の入力が4件' in text
        assert '前日の加重合計20' in text
        assert '差は-5' in text
    elif kind == 'weekly':
        text = reports._render_weekly_standard_v3_text(**common, metrics=views['metrics'], days=views['days'])
        assert '分析対象の入力が' not in text and '入力件数' not in text
        assert '11/2の加重合計が最大値15' in text
    else:
        text = reports._render_monthly_standard_v3_text(**common, metrics=views['metrics'], weeks=views['weeks'])
        assert '分析対象の入力が' not in text and '入力件数' not in text
        assert '最初の2週の加重合計は15、後の2週は0' in text
    assert text.count('【') == 5
    assert '公開' not in text
    assert '内訳は喜び3、悲しみ2、不安1、怒り0、平穏9' in text
    assert '弱を1、中を2、強を3' in text
    assert len(text) >= 450
    assert not any(value in text for value in UNSUPPORTED)


def test_daily_motion_reports_recorded_weighted_difference_instead_of_a_motive_or_calmness():
    text = reports._render_daily_motion_line({'key': 'down', 'totalToday': 4, 'totalYesterday': 10})
    assert text == '前日の加重合計は10、この日は4で、差は-6でした。'
    assert '比較の加重集計' in reports._render_daily_motion_line({'key': 'stable'})


def test_zero_fraction_graphs_keep_all_labels_and_deep_peace_alias_keeps_its_counts():
    assert reports._engine_share_percent({'peace': 0, 'joy': 0}) == dict.fromkeys(KEYS, 0)
    matrix = reports._normalize_transition_matrix({'anxiety': {'peace': 3}, 'peace': {'joy': 1}})
    assert matrix['anxiety']['calm'] == 3
    assert matrix['calm']['joy'] == 1
    assert 'peace' not in matrix and 'peace' not in matrix['anxiety']
    edge = reports._normalize_transition_edges([{'from_label': 'anxiety', 'to_label': 'peace', 'count': 3}])[0]
    interval = reports._normalize_recovery_time_rows([{'from_label': 'peace', 'to_label': 'joy', 'count': 1, 'mean_minutes': 10}])[0]
    assert edge['toLabel'] == 'calm' and edge['routeLabel'] == '不安 → 平穏' and edge['count'] == 3
    assert interval['fromLabel'] == 'calm' and interval['count'] == 1 and interval['meanMinutes'] == 10


def test_time_bucket_label_cannot_override_the_quantitative_weights():
    data = fixture('weekly')
    data['snapshot_views']['timeBuckets'][0]['dominantKey'] = 'anxiety'
    result = reports._build_standard_report_payload(**data)
    evening = next(row for row in result['timeBuckets'] if row['bucket'] == '18-24')
    assert evening['dominantKey'] == 'calm'
    assert '「平穏」の加重値が最大' in result['summary']['timeComment']
    assert '「不安」の加重値が最大' not in result['summary']['timeComment']
