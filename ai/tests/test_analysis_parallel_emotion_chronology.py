"""Parallel selections have no time order; quantities retain every selection.

Synthetic entries exercise the actual shared weekly feature owner and worker
transition owner. No model, DB, generation job or device claim is involved.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'services'))
    import astor_worker
    from analysis_engine.emotion_structure_engine import weekly, daily
    from analysis_engine.models import EmotionEntry, BaselineProfile
    return astor_worker, weekly, daily, EmotionEntry, BaselineProfile


def entry(modules, record, hour, label, strength=2, index=0):
    instant = datetime(2026, 11, 7, tzinfo=timezone.utc) + timedelta(hours=hour)
    return modules[3](id=f'{record}:{index}', timestamp=instant.isoformat(),
        date='2026-11-07', label=label, intensity=strength, memo='私は公園で休んだ。')


def parallel(modules, record='parallel', hour=1):
    return [entry(modules, record, hour, 'anxiety', 1),
            entry(modules, record, hour, 'peace', 3, index=1)]


def test_single_to_single_keeps_chronological_transition_and_weighted_totals(modules):
    worker, weekly, _, _, _ = modules
    observations = [entry(modules, 'a', 0, 'anxiety', 1), entry(modules, 'b', 1, 'peace', 3)]
    transitions = worker._build_transition_records(observations)
    assert [(t['from_label'], t['to_label'], t['minutes']) for t in transitions] == [('anxiety', 'calm', 60.0)]
    snapshot = weekly.build_weekly_features(observations, 'synthetic')
    assert snapshot.alternation_rate == 1.0
    assert snapshot.wcounts['anxiety'] == 1 and snapshot.wcounts['peace'] == 3


def test_one_parallel_record_has_no_transition_and_is_invariant_to_selection_order(modules):
    worker, weekly, daily, _, _ = modules
    observations = parallel(modules)
    before = deepcopy(observations)
    for selected in (observations, list(reversed(observations))):
        assert worker._build_transition_records(selected) == []
        model = worker._build_deep_control_model_payload(selected, scope_kind='daily', period_label='synthetic')
        assert model['summary']['transitionCount'] == 0 and model['recovery_time'] == []
        snapshot = weekly.build_weekly_features(selected, 'synthetic')
        assert snapshot.alternation_rate is None and snapshot.motifs == []
        assert snapshot.counts == dict(joy=0, sadness=0, anxiety=1, anger=0, peace=1)
        assert snapshot.wcounts == dict(joy=0, sadness=0, anxiety=1, anger=0, peace=3)
        assert sum(b['inputCount'] for b in snapshot.time_buckets) == 1
        assert sum(b['weightedTotal'] for b in snapshot.time_buckets) == 4
        text = daily.narrate_daily(selected, 'synthetic').structural_comment
        assert '不安' in text and '平穏' in text
        assert all(word not in text for word in ('切り替わ', '→', '戻る', '回復'))
    assert observations == before


@pytest.mark.parametrize('before,after', [(True, False), (False, True), (True, True)])
def test_parallel_observation_breaks_adjacency_without_connecting_across_it(modules, before, after):
    worker, weekly, _, _, _ = modules
    observations = ([entry(modules, 'before', 0, 'sadness')] if before else [])
    observations += parallel(modules)
    observations += ([entry(modules, 'after', 2, 'joy')] if after else [])
    assert worker._build_transition_records(observations) == []
    snapshot = weekly.build_weekly_features(observations, 'synthetic')
    assert snapshot.alternation_rate is None
    assert snapshot.motifs == [] and snapshot.motif_counts == {}
    assert sum(snapshot.counts.values()) == len(observations)


def test_valid_runs_on_either_side_of_parallel_record_are_preserved_without_a_bridge(modules):
    worker, weekly, _, _, _ = modules
    observations = [entry(modules, 'a', 0, 'sadness'), entry(modules, 'b', 1, 'peace')]
    observations += parallel(modules, hour=2)
    observations += [entry(modules, 'c', 3, 'joy'), entry(modules, 'd', 4, 'anxiety')]
    transitions = worker._build_transition_records(list(reversed(observations)))
    assert [(t['from_label'], t['to_label']) for t in transitions] == [('sadness', 'calm'), ('joy', 'anxiety')]
    snapshot = weekly.build_weekly_features(observations, 'synthetic')
    assert snapshot.alternation_rate == 1.0 and snapshot.motifs == []


def test_established_three_single_record_motif_is_preserved(modules):
    _, weekly, _, _, _ = modules
    observations = [entry(modules, 'a', 0, 'sadness'), entry(modules, 'b', 1, 'peace'), entry(modules, 'c', 2, 'joy')]
    assert weekly.build_weekly_features(observations, 'synthetic').motif_counts == {'sadness-peace-joy': 1}


def test_distinct_record_ids_at_same_instant_do_not_supply_an_invented_order(modules):
    worker, weekly, _, _, _ = modules
    observations = [entry(modules, 'first', 0, 'anxiety'), entry(modules, 'second', 0, 'peace')]
    observations[1].timestamp = '2026-11-07T09:00:00+09:00'
    assert worker._build_transition_records(observations) == []
    snapshot = weekly.build_weekly_features(observations, 'synthetic')
    assert snapshot.alternation_rate is None
    assert sum(b['inputCount'] for b in snapshot.time_buckets) == 2


def test_weekly_narrator_marks_unknown_chronology_unavailable_even_with_a_baseline(modules):
    _, weekly, _, _, BaselineProfile = modules
    snapshot = weekly.build_weekly_features(parallel(modules), 'synthetic')
    baseline = BaselineProfile('synthetic-owner', 4, 1,
        {'alternation': {'mu': 0.5, 'sigma': 0.1}}, {})
    narrative = weekly.narrate_weekly(snapshot, baseline)
    item = next(i for i in narrative.evidence['items'] if i['key'] == 'alternation')
    assert item['status'] == 'insufficient'
    motif = next(i for i in narrative.evidence['items'] if i['key'] == 'motif')
    assert motif['status'] == 'insufficient'
    assert narrative.evidence['internal']['alternation']['current'] is None


@pytest.mark.parametrize('score', [1, 2, 3])
def test_every_parallel_emotion_and_strength_remains_in_quantities(modules, score):
    worker, weekly, _, _, _ = modules
    labels = ['joy', 'sadness', 'anger', 'anxiety', 'peace']
    observations = [entry(modules, 'same-record', 0, label, score, index=i) for i, label in enumerate(labels)]
    snapshot = weekly.build_weekly_features(observations, 'synthetic')
    assert snapshot.counts == dict.fromkeys(labels, 1)
    assert snapshot.wcounts == dict.fromkeys(labels, score)
    assert snapshot.n_events == 5 and worker._build_transition_records(observations) == []
    assert sum(b['inputCount'] for b in snapshot.time_buckets) == 1
