"""Whole-record semantic history planning over real source admission.

All inputs, questions, answers and person corrections below are synthetic.
Record/field-count callbacks deliberately control test partitions; they are
not tokenizer measurements or evidence of a real model's capacity or quality.
No provider, account, hosted database or native renderer is used.
"""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from uuid import UUID

import pytest

import analysis_cumulative_service as service
import analysis_model_source as sources
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.map_interpretation_correction import (
    checked_map_correction,
)
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSupplement, commitment,
)
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_map_correction_application import row as correction_row


PROFILE = admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE
CAPACITY = 'analysis_semantic_history_capacity_exceeded'


def history(count):
    snapshot = source_snapshot(count)
    for member in snapshot['members']:
        member['original'].update(memo='私は資料を調べたい。',
            memo_action='私は費用を記録した。',
            emotion_details=[dict(type='平穏', strength='medium')])
    return snapshot


def prepare(snapshot, *, request=None):
    if request is None:
        return semantic.prepare_semantic_map(OWNER, snapshot, prompt_version=PROFILE)
    return admission.prepare_analysis_semantic_map(request, snapshot, prompt_version=PROFILE)


def records(prepared):
    return tuple(member.saved_record_ref for member in prepared.frozen.members)


def material(stage):
    return json.loads(stage.material_json)


def no_acquisition_or_sql(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('input planning reached acquisition or persistence')
    monkeypatch.setattr(service, '_rpc', forbidden)
    monkeypatch.setattr(service, '_model_response', forbidden)
    monkeypatch.setattr(sources.SelfHostedSemanticAnalysisModelSource, '__call__', forbidden)


def synthetic_record_budget(monkeypatch, maximum):
    calls = []

    def fits(prepared):
        refs = getattr(prepared, 'record_refs', None)
        selected = records(prepared) if refs is None else refs
        calls.append(selected)
        return len(selected) <= maximum

    # The planner imports the current source owner's function at call time.
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits', fits)
    monkeypatch.setattr(sources, 'semantic_history_leaf_target_fits', fits)
    return calls


def assert_complete_partition(parent, stages):
    expected = records(parent)
    flattened = tuple(ref for stage in stages for ref in stage.record_refs)
    assert len(flattened) == len(set(flattened)) == len(expected)
    assert set(flattened) == set(expected)
    assert [expected.index(stage.record_refs[0]) for stage in stages] == sorted(
        expected.index(stage.record_refs[0]) for stage in stages)
    parent_fields = material(parent)['fields']
    seen_fields = []
    for stage in stages:
        assert stage.kind == 'LEAF' and stage.parent is parent and stage.response is None
        assert stage.source_guard == parent.source_guard and stage.prompt_version == parent.prompt_version
        assert stage.record_refs == tuple(ref for ref in expected if ref in stage.record_refs)
        ordinals = {expected.index(ref) + 1 for ref in stage.record_refs}
        body = material(stage)
        assert [record['record'] for record in body['records']] == sorted(ordinals)
        expected_fields = [field for field in parent_fields if field['record'] in ordinals
            or field['record'] is None and set(field['record_refs']) <= ordinals]
        assert body['fields'] == expected_fields
        seen_fields.extend(field['field'] for field in body['fields'])
    assert sorted(seen_fields) == [field['field'] for field in parent_fields]


def add_correction(snapshot, number, indexes):
    """Use the existing qualified person-source row shape, not a forged input."""
    value = correction_row()
    value.update(correction_id=str(UUID(int=9000 + number)), recorded_at=snapshot['now'])
    value['target_context']['cohort'] = [dict(
        record_ref=snapshot['members'][index]['original']['id'],
        source_guard='analysis-map-member-v1:' + f'{index + 1:064x}') for index in indexes]
    # SQL owns whether a real row is current. This is a fully synthetic,
    # owner-resolved ACTIVE snapshot; the production source checker still runs.
    snapshot.setdefault('map_corrections', []).append(checked_map_correction(OWNER, value))


def test_message_byte_capacity_is_exact_utf8_not_character_or_token_count():
    limit = sources.SEMANTIC_MAX_PROMPT_BYTES
    assert limit == 49152
    def prepared(text):
        return SimpleNamespace(messages=lambda: [dict(role='user', content=text)])
    overhead = len(json.dumps(prepared('').messages(), ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8'))
    assert sources.semantic_analysis_input_fits(prepared('x' * (limit - overhead)))
    assert not sources.semantic_analysis_input_fits(prepared('x' * (limit - overhead + 1)))
    assert not sources.semantic_analysis_input_fits(prepared('あ' * (limit // 3)))


def test_fitting_whole_parent_keeps_existing_messages_and_never_creates_a_leaf(monkeypatch):
    snapshot = history(2)
    parent = prepare(snapshot)
    before, original, messages = deepcopy(parent), deepcopy(snapshot), deepcopy(parent.messages())
    no_acquisition_or_sql(monkeypatch)
    calls = synthetic_record_budget(monkeypatch, 2)
    monkeypatch.setattr(admission, 'prepare_semantic_leaf',
        lambda *_: pytest.fail('a fitting whole parent must not be repartitioned'))
    assert service.prepare_semantic_history_batches(parent) == ()
    assert calls == [records(parent)]
    assert parent == before and parent.messages() == messages and snapshot == original


@pytest.mark.parametrize('count, maximum, sizes', [(5, 2, [2, 2, 1]), (101, 40, [40, 40, 21])])
def test_all_history_including_oldest_and_beyond_one_hundred_is_an_exact_partition(
        count, maximum, sizes, monkeypatch):
    snapshot = history(count)
    original = deepcopy(snapshot)
    parent = prepare(snapshot)
    before, messages = deepcopy(parent), deepcopy(parent.messages())
    no_acquisition_or_sql(monkeypatch)
    synthetic_record_budget(monkeypatch, maximum)
    stages = service.prepare_semantic_history_batches(parent)
    assert len(stages) == 3 <= sources.SEMANTIC_HISTORY_MAX_LEAVES
    assert sources.SEMANTIC_HISTORY_MAX_LEAVES == admission.SEMANTIC_HISTORY_MAX_LEAVES
    assert [len(stage.record_refs) for stage in stages] == sizes
    assert_complete_partition(parent, stages)
    assert stages[0].record_refs[0] == snapshot['members'][0]['original']['id']
    assert stages[-1].record_refs[-1] == snapshot['members'][-1]['original']['id']
    assert parent == before and parent.messages() == messages and snapshot == original


def test_both_original_fields_and_three_qualified_answers_are_one_atomic_record(monkeypatch):
    snapshot = history(2)
    original = deepcopy(snapshot)
    request = service._cumulative_model_request(OWNER, snapshot)
    first = request.members[0]
    texts = ('私は本を見た。', '私は日程を決めなかった。', '私は記録を残した。')
    answers = tuple(AnalysisSupplement(str(UUID(int=8000 + index)), OWNER,
        first.saved_record_ref, first.saved_record_version, text, commitment(text))
        for index, text in enumerate(texts))
    request = replace(request, members=(replace(first, supplements=answers), request.members[1]))
    parent = prepare(snapshot, request=request)
    before = deepcopy(parent)
    no_acquisition_or_sql(monkeypatch)
    synthetic_record_budget(monkeypatch, 1)
    stages = service.prepare_semantic_history_batches(parent)
    assert len(stages) == 2
    assert_complete_partition(parent, stages)
    fields = material(stages[0])['fields']
    assert [field['text'] for field in fields] == [
        snapshot['members'][0]['original']['memo'], snapshot['members'][0]['original']['memo_action'], *texts]
    assert [field['source_role'] for field in fields] == ['ORIGINAL_INPUT'] * 2 + ['SUPPLEMENTAL_ANSWER'] * 3
    assert [field['supplement'] for field in fields[2:]] == [1, 2, 3]
    assert stages[0].parent.request.members[0].supplements == answers
    assert parent == before and snapshot == original

    # A single occasion exceeding a test field budget is refused whole. It
    # must not be rescued by silently dropping one answer or one input field.
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits',
        lambda stage: len(material(stage)['fields']) <= 4)
    with pytest.raises(ValueError, match=CAPACITY):
        service.prepare_semantic_history_batches(parent)
    assert parent == before and snapshot == original


def test_overlapping_noncontiguous_correction_cohorts_stay_united_in_parent_order(monkeypatch):
    snapshot = history(6)
    add_correction(snapshot, 1, (0, 2))
    add_correction(snapshot, 2, (2, 4))
    original = deepcopy(snapshot)
    parent = prepare(snapshot)
    before = deepcopy(parent)
    refs = records(parent)
    no_acquisition_or_sql(monkeypatch)
    synthetic_record_budget(monkeypatch, 3)
    stages = service.prepare_semantic_history_batches(parent)
    assert [stage.record_refs for stage in stages] == [(refs[0], refs[2], refs[4]), (refs[1], refs[3], refs[5])]
    assert_complete_partition(parent, stages)
    first, second = map(material, stages)
    assert [field['record_refs'] for field in first['fields'] if field['record'] is None] == [[1, 3], [3, 5]]
    assert [row['correction_id'] for row in first['map_corrections']] == [
        row['correction_id'] for row in snapshot['map_corrections']]
    assert second['map_corrections'] == []
    assert not any(field['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION' for field in second['fields'])
    assert parent == before and snapshot == original


@pytest.mark.parametrize('case', ['seven_leaves', 'indivisible_record', 'indivisible_correction_cohort'])
def test_unrepresentable_history_is_rejected_before_provider_or_sql(case, monkeypatch):
    snapshot = history(7 if case == 'seven_leaves' else 4)
    if case == 'indivisible_correction_cohort':
        add_correction(snapshot, 3, (0, 2, 3))
    parent = prepare(snapshot)
    before, original = deepcopy(parent), deepcopy(snapshot)
    no_acquisition_or_sql(monkeypatch)
    synthetic_record_budget(monkeypatch, 0 if case == 'indivisible_record' else
        2 if case == 'indivisible_correction_cohort' else 1)
    with pytest.raises(ValueError, match=CAPACITY):
        service.prepare_semantic_history_batches(parent)
    assert parent == before and snapshot == original

