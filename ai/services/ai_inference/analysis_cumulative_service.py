"""All-owned-input map lifecycle and immutable monthly references.

The authenticated API resolves the owner. Only an explicit caller can supply
an asynchronous model source; HTTP and scheduled callers keep the default.
No lookback window, new realizer, or unsaved past months are introduced.
"""
from __future__ import annotations

import asyncio
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date
import inspect
import json
import os
import re
from typing import TYPE_CHECKING, Callable
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException

import analysis_observed_service as observed
from analysis_observed_service import _checked_projection as _checked_v2_projection, private_storage_evidence, observed_mode

PROFILE = 'cumulative.v1'
MODEL_SOURCE_TIMEOUT_SECONDS = 60.0

if TYPE_CHECKING:
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelQuotedParentUnitsInput


@dataclass(frozen=True, slots=True)
class AnalysisModelInputBudget:
    """Explicit CPU measurements, not an output or execution-time guarantee."""
    prompt_tokens: int
    request_body_bytes: int


@dataclass(frozen=True, slots=True)
class CumulativeModelBatchPlan:
    """Private preparation only; never a response, artifact or saved map."""
    parent: AnalysisModelQuotedParentUnitsInput
    batches: tuple[AnalysisModelQuotedParentUnitsInput, ...]
    budgets: tuple[AnalysisModelInputBudget, ...]
    record_refs: tuple[tuple[str, ...], ...]
    context_tokens: int
    reserved_new_tokens: int
    max_request_bytes: int


@dataclass
class _ModelMapFlight:
    source: object
    task: asyncio.Task
    waiters: int = 0


# Only concurrent, identical explicit calls share a task. There is no completed
# response cache; abandoned tasks are cancelled. Tasks never cross loops/owners.
_model_map_flights = {}


def _checked_projection(projection, report_id):
    if type(projection) is dict and projection.get('wire_kind') == 'watashi.map.v3':
        from analysis_semantic_map import validate_semantic_projection
        try:
            return validate_semantic_projection(projection, report_id)
        except (ValueError, KeyError, TypeError, AttributeError, AssertionError):
            raise HTTPException(503, 'analysis_saved_artifact_invalid') from None
    return _checked_v2_projection(projection, report_id)


def _projection_text(projection):
    if projection.get('wire_kind') == 'watashi.map.v3':
        from analysis_semantic_map import semantic_projection_text
        return semantic_projection_text(projection)
    from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import ObservedSelfStructureMap
    return ObservedSelfStructureMap._text_from_visual(projection)['text']


def _legacy_semantic_projection(projection):
    """Keep installed v2 clients readable while a diagram-capable build ships.

    Meaning relations are not mislabeled as repeated occurrence or causation.
    The new client receives the actual v3 graph; old clients receive the same
    interpretations as clearly identified text, with the same evidence IDs.
    """
    def label(node):
        return '\n'.join(['読み取り：' + node['title'], node['summary'], node['explanation'],
            *node['context'], *['この記録では決められないこと：' + x for x in node['unknowns']]])
    return dict(schema_version='cocolon.cmee.analysis_watashi_map_safe_projection.v1alpha1',
        wire_kind='watashi.map.v2', projection_of=projection['projection_of'],
        artifact_version=1, period_label=projection['period_label'],
        period_comparison=dict(state='NO_PREVIOUS', reason_codes=[], safe_change_kinds=[]),
        nodes=[dict(node_ref=n['node_ref'], node_kind='ATTENTION_OR_THOUGHT',
            visible_label=label(n),
            evidence_badge_count=n['evidence_badge_count']) for n in projection['nodes']],
        edges=[], annotation_badges=[], unknown_gaps=[], conflict_badges=[],
        accessibility_linear_order=projection['accessibility_linear_order'])


def map_response_for_renderer(payload, renderer):
    """Compatibility only; no generation, storage rewrite, or evidence change."""
    if renderer == 'semantic.v1':
        return payload
    meta = payload.get('meta')
    if type(meta) is dict and meta.get('wire_kind') == 'watashi.map.v3':
        payload = deepcopy(payload)
        payload['meta'] = _legacy_semantic_projection(meta)
        payload['content_text'] = _projection_text(payload['meta'])
    item = payload.get('item')
    if type(item) is dict and item.get('content_json', {}).get('watashiMap', {}).get('wire_kind') == 'watashi.map.v3':
        payload = deepcopy(payload)
        row = payload['item']
        row['content_json']['watashiMap'] = _legacy_semantic_projection(row['content_json']['watashiMap'])
        row['content_text'] = _projection_text(row['content_json']['watashiMap'])
    return payload


async def _rpc(name, payload):
    return await observed._rpc(name, payload)


def _owner(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(404, 'analysis_report_unavailable') from None


def _month(value):
    if value is None:
        return None
    try:
        month = date.fromisoformat(str(value) + '-01' if len(str(value)) == 7 else str(value))
        if month.day != 1:
            raise ValueError
        return month.isoformat()
    except (ValueError, TypeError):
        raise HTTPException(400, 'analysis_month_invalid') from None


async def read_maps(user_id, *, report_id=None, history=False, limit=60, offset=0, month=None, metadata_only=False):
    result = await _rpc('analysis_cumulative_read', dict(p_user_id=_owner(user_id),
        p_id=_owner(report_id) if report_id is not None else None,
        p_history=history, p_limit=limit, p_offset=offset, p_month=_month(month), p_metadata_only=metadata_only))
    try:
        if (set(result) != {'items', 'subscription_tier', 'matched', 'history_limit'}
                or result['subscription_tier'] not in {'free', 'plus', 'premium'}
                or type(result['items']) is not list or type(result['matched']) is not bool
                or result['history_limit'] != {'free': 2, 'plus': 12, 'premium': None}[result['subscription_tier']]):
            raise ValueError
        for row in result['items']:
            if metadata_only:
                if (row['source_profile'] != PROFILE or row['report_mode'] != 'standard'
                        or 'content_json' in row or 'content_text' in row):
                    raise ValueError
                _owner(row['id'])
                continue
            if (row['source_profile'] != PROFILE or row['report_mode'] != 'standard'
                    or set(row['content_json']) != {'report_mode', 'watashiMap', 'map_context'}
                    or row['content_json']['report_mode'] != 'standard'):
                raise ValueError
            projection = _checked_projection(row['content_json']['watashiMap'], row['id'])
            if row['content_text'] != _projection_text(projection):
                raise ValueError
            _checked_coverage(row['content_json']['map_context'])
        return result
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(503, 'analysis_saved_artifact_invalid') from None


def _checked_coverage(coverage):
    keys = {'profile', 'source_count', 'processed_count', 'mapped_count',
            'unparsed_count', 'excluded_count', 'exclusion_reasons', 'stale_supplement_count'}
    if type(coverage) is not dict or set(coverage) != keys or coverage['profile'] != PROFILE:
        raise ValueError('analysis_coverage_invalid')
    if any(type(coverage[k]) is not int or coverage[k] < 0 for k in keys - {'profile', 'exclusion_reasons'}):
        raise ValueError('analysis_coverage_invalid')
    if (coverage['source_count'] != coverage['processed_count'] + coverage['excluded_count']
            or coverage['mapped_count'] > coverage['processed_count']
            or coverage['unparsed_count'] > coverage['processed_count']
            or type(coverage['exclusion_reasons']) is not dict
            or any(type(k) is not str or not re.fullmatch(r'analysis_[a-z_]+', k)
                   or type(v) is not int or v < 1 for k, v in coverage['exclusion_reasons'].items())
            or sum(coverage['exclusion_reasons'].values()) != coverage['excluded_count']):
        raise ValueError('analysis_coverage_invalid')
    return coverage


def _cumulative_model_request(owner, snapshot):
    """Resolve the existing saved-source owner before any model profile."""
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        AnalysisObservedMapRequest, commitment, _time)
    owner = _owner(owner)
    start, end = snapshot['period_start'], snapshot['period_end']
    records = tuple(_analysis_saved_member(dict(raw, tier=snapshot['tier'], now=snapshot['now']),
        owner=owner, input_id=raw['original']['id'], tier=snapshot['tier'],
        start=_time(start), end=_time(end), cumulative=True)[0] for raw in snapshot['members'])
    request_id = 'analysis-model-' + commitment([owner, snapshot['guard'], start, end])[7:]
    request = AnalysisObservedMapRequest(request_id, owner, start, end, records)
    return request


def prepare_cumulative_model_fields(owner, snapshot):
    """Explicit offline probe; never selected by ensure_map or an HTTP flag."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_fields
    return prepare_analysis_model_fields(_cumulative_model_request(owner, snapshot), source_guard=snapshot['guard'])


def prepare_cumulative_model_field_kinds(owner, snapshot):
    """Explicit offline classifications; source admission is shared with v1."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_field_kinds
    prepared = prepare_cumulative_model_fields(owner, snapshot)
    return prepare_analysis_model_field_kinds(prepared.request, source_guard=prepared.source_guard)


def prepare_cumulative_model_units(owner, snapshot, *, instruction_version='baseline.v1'):
    """Explicit private candidate profile; no normal map/HTTP switch."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_units
    prepared = prepare_cumulative_model_fields(owner, snapshot)
    return prepare_analysis_model_units(prepared.request, source_guard=prepared.source_guard,
        instruction_version=instruction_version)


def build_cumulative_unit_candidates(owner, snapshot, *, model_input):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelUnitsInput, require)
    require(type(model_input) is AnalysisModelUnitsInput, 'analysis_model_units_binding_invalid')
    expected = prepare_cumulative_model_units(owner, snapshot, instruction_version=model_input.instruction_version)
    require(type(model_input) is AnalysisModelUnitsInput
        and model_input.request == expected.request and model_input.request_ref == expected.request_ref
        and model_input.source_guard == expected.source_guard, 'analysis_model_units_binding_invalid')
    artifact = MeaningExperienceEngine().generate(expected.request, semantic_input=model_input)
    return artifact, _unit_candidate_coverage(expected, snapshot)


def _unit_candidate_coverage(expected, snapshot):
    count = len(expected.request.members)
    stale = sum(sum(e.get('kind') == 'ANSWER' for e in raw['events'])
        for raw in snapshot['members'] if raw.get('thread')
        and raw['thread'].get('source_snapshot') != raw['original'])
    return _checked_coverage(dict(profile=PROFILE, source_count=count, processed_count=count,
        mapped_count=0, unparsed_count=count, excluded_count=0, exclusion_reasons={},
        stale_supplement_count=stale))


def serialize_cumulative_unit_candidates(owner, snapshot, *, model_input, artifact, coverage):
    """One private caller-managed file containing exact cumulative coverage."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        canonical, require, serialize_analysis_model_units)
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelUnitsInput
    require(type(model_input) is AnalysisModelUnitsInput, 'analysis_model_units_binding_invalid')
    expected = prepare_cumulative_model_units(owner, snapshot, instruction_version=model_input.instruction_version)
    require(type(model_input) is type(expected) and model_input.request == expected.request
        and model_input.request_ref == expected.request_ref and model_input.source_guard == expected.source_guard
        and canonical(coverage) == canonical(_unit_candidate_coverage(expected, snapshot)),
        'analysis_model_units_coverage_invalid')
    return canonical(dict(schema_version='cocolon.cmee.cumulative_unit_candidates_file.v1',
        coverage=coverage, state=json.loads(serialize_analysis_model_units(model_input, artifact))))


def reload_cumulative_unit_candidates(owner, snapshot, raw, *, instruction_version='baseline.v1'):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        _load, canonical, require, reload_analysis_model_units)
    prepared = prepare_cumulative_model_units(owner, snapshot, instruction_version=instruction_version)
    saved = _load(raw)
    require(type(saved) is dict and set(saved) == {'schema_version','coverage','state'}
        and saved['schema_version'] == 'cocolon.cmee.cumulative_unit_candidates_file.v1'
        and canonical(saved['coverage']) == canonical(_unit_candidate_coverage(prepared, snapshot)),
        'analysis_model_units_coverage_invalid')
    return reload_analysis_model_units(prepared, canonical(saved['state'])), saved['coverage']


def prepare_cumulative_quoted_parent_units(owner, snapshot, *, prompt_version='baseline.v1'):
    """Separate explicit private wire; the normal builder never selects it."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_quoted_parent_units
    prepared = prepare_cumulative_model_fields(owner, snapshot)
    return prepare_analysis_model_quoted_parent_units(prepared.request, source_guard=prepared.source_guard,
        prompt_version=prompt_version)


def prepare_cumulative_category_units(owner, snapshot, *, prompt_version='selected_categories.v1'):
    """Current category-aware 4B preparation; legacy saved probes stay v1."""
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        prepare_analysis_model_quoted_parent_units, QUOTED_PARENT_CATEGORY_PROFILE)
    request = replace(_cumulative_model_request(owner, snapshot), selected_category_context=True)
    return prepare_analysis_model_quoted_parent_units(request, source_guard=snapshot['guard'],
        prompt_version=prompt_version)


def prepare_cumulative_model_batches(owner, snapshot, *,
        measure_budget: Callable[[AnalysisModelQuotedParentUnitsInput], AnalysisModelInputBudget],
        prompt_version='selected_material.v4', context_tokens=8192,
        reserved_new_tokens=2048, max_request_bytes=65536):
    """Plan all eligible records without acquiring or combining model responses.

    The caller supplies synchronous measurements from its pinned tokenizer and
    actual HTTP JSON encoder. No tokenizer dependency or default estimate is
    introduced in the API. Each independently bound child retains the whole
    record, its original fields and all qualified answers, the full period and
    the original database guard. Fieldless records stay with a neighbouring
    complete record; they never become a new empty-source model request. No
    snapshot with a fabricated subset guard is constructed. An indivisible
    record group that exceeds a budget rejects the entire preparation. This
    deterministic greedy grouping is conservative, not an optimal-partition
    proof: a fieldless group budget failure does not prove no other grouping
    could fit.

    This input-budget plan is not selected by ensure_map or its factory. It
    neither promises that a response fits 2048 tokens nor changes the existing
    60-second logical acquisition deadline. Raw response composition and batch
    execution require their own explicit private contract.
    """
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        _model_fields_source, prepare_analysis_model_quoted_parent_units,
        require_analysis_model_observed_scope)
    if (type(prompt_version) is not str
            or prompt_version not in {'selected_material.v4', 'selected_material.v7'}):
        raise ValueError('analysis_model_batch_profile_invalid')
    if (type(context_tokens) is not int or not 0 < context_tokens <= 8192
            or type(reserved_new_tokens) is not int or not 2048 <= reserved_new_tokens < context_tokens
            or type(max_request_bytes) is not int or not 0 < max_request_bytes <= 65536
            or not callable(measure_budget) or inspect.iscoroutinefunction(measure_budget)):
        raise ValueError('analysis_model_batch_budget_invalid')
    parent = prepare_cumulative_category_units(owner, snapshot, prompt_version=prompt_version)
    frozen, fields = _model_fields_source(parent.request, allow_supplements=True)
    # Check the same complete-source safety/answer/update boundary before any
    # budget callback; splitting must not hide an ineligible record or answer.
    require_analysis_model_observed_scope(parent.request, frozen=frozen)
    members = {member.saved_record_ref: member for member in parent.request.members}
    if len(members) != len(parent.request.members):
        raise ValueError('analysis_model_batch_duplicate_record')
    ordered = tuple(members[member.saved_record_ref] for member in frozen.members)
    nonempty = {field['source'].record_ref for field in fields}
    groups, pending = [], []
    for member in ordered:
        pending.append(member)
        if member.saved_record_ref in nonempty:
            groups.append(tuple(pending))
            pending = []
    if pending:
        groups[-1] += tuple(pending)

    def measure(prepared):
        budget = measure_budget(prepared)
        if (type(budget) is not AnalysisModelInputBudget
                or type(budget.prompt_tokens) is not int or budget.prompt_tokens <= 0
                or type(budget.request_body_bytes) is not int or budget.request_body_bytes <= 0):
            if inspect.iscoroutine(budget):
                budget.close()
            raise ValueError('analysis_model_batch_budget_invalid')
        return budget

    def fits(budget):
        return (budget.prompt_tokens + reserved_new_tokens <= context_tokens
            and budget.request_body_bytes <= max_request_bytes)

    def oversized(group):
        return ValueError('analysis_model_batch_record_budget_exceeded' if len(group) == 1
            else 'analysis_model_batch_group_budget_exceeded')

    def child(records):
        request = replace(parent.request, members=tuple(records))
        return prepare_analysis_model_quoted_parent_units(request,
            source_guard=parent.source_guard, prompt_version=parent.prompt_version)

    parent_budget = measure(parent)
    if fits(parent_budget):
        return CumulativeModelBatchPlan(parent, (parent,), (parent_budget,),
            (tuple(member.saved_record_ref for member in ordered),),
            context_tokens, reserved_new_tokens, max_request_bytes)
    if len(groups) == 1:
        raise oversized(groups[0])
    batches, budgets, record_refs = [], [], []
    current, prepared, budget = (), None, None
    for group in groups:
        candidate = current + group
        candidate_input = child(candidate)
        candidate_budget = measure(candidate_input)
        if fits(candidate_budget):
            current, prepared, budget = candidate, candidate_input, candidate_budget
            continue
        if not current:
            raise oversized(group)
        batches.append(prepared)
        budgets.append(budget)
        record_refs.append(tuple(record.saved_record_ref for record in current))
        current = group
        prepared = child(current)
        budget = measure(prepared)
        if not fits(budget):
            raise oversized(group)
    batches.append(prepared)
    budgets.append(budget)
    record_refs.append(tuple(record.saved_record_ref for record in current))
    if tuple(ref for group in record_refs for ref in group) != tuple(m.saved_record_ref for m in ordered):
        raise ValueError('analysis_model_batch_partition_invalid')
    return CumulativeModelBatchPlan(parent, tuple(batches), tuple(budgets), tuple(record_refs),
        context_tokens, reserved_new_tokens, max_request_bytes)


def _cumulative_batch_parent(owner, snapshot, model_input):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelObservedBatchInput, require)
    require(type(model_input) is AnalysisModelObservedBatchInput,
        'analysis_model_batch_input_invalid')
    return _written_role_input(owner, snapshot, model_input.parent)


def build_cumulative_model_batch_map(owner, snapshot, *, model_input):
    """Explicit offline composition only; ensure/factory/store never select it."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        generate_analysis_model_observed_batches)
    parent = _cumulative_batch_parent(owner, snapshot, model_input)
    artifact, mapped, unread = generate_analysis_model_observed_batches(model_input, with_record_counts=True)
    coverage = _unit_candidate_coverage(parent, snapshot)
    coverage.update(mapped_count=mapped, unparsed_count=unread)
    return artifact, _checked_coverage(coverage)


def serialize_cumulative_model_batch_input(owner, snapshot, *, model_input):
    """Caller-managed private input bytes, without a saved-map claim."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        serialize_analysis_model_observed_batch_input)
    _cumulative_batch_parent(owner, snapshot, model_input)
    return serialize_analysis_model_observed_batch_input(model_input)


def reload_cumulative_model_batch_input(owner, snapshot, raw, *, prompt_version='selected_material.v4'):
    """Rebind INPUTS only; later composition requires an explicit build call."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        reload_analysis_model_observed_batch_input)
    prepared = prepare_cumulative_category_units(owner, snapshot, prompt_version=prompt_version)
    return reload_analysis_model_observed_batch_input(prepared, raw)


def build_cumulative_quoted_parent_candidates(owner, snapshot, *, model_input):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsInput, require)
    require(type(model_input) is AnalysisModelQuotedParentUnitsInput,
            'analysis_quoted_parent_units_binding_invalid')
    expected = (prepare_cumulative_category_units(owner, snapshot, prompt_version=model_input.prompt_version)
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2', 'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7', 'selected_material.v9', 'selected_material.v10', 'selected_material.v11', 'selected_material.v12', 'selected_material.v13'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot, prompt_version=model_input.prompt_version))
    require(model_input.request == expected.request and model_input.request_ref == expected.request_ref
        and model_input.source_guard == expected.source_guard, 'analysis_quoted_parent_units_binding_invalid')
    artifact = MeaningExperienceEngine().generate(expected.request, semantic_input=model_input)
    return artifact, _unit_candidate_coverage(expected, snapshot)


def serialize_cumulative_quoted_parent_candidates(owner, snapshot, *, model_input, artifact, coverage):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsInput, canonical, require, serialize_analysis_model_quoted_parent_units)
    require(type(model_input) is AnalysisModelQuotedParentUnitsInput,
            'analysis_quoted_parent_units_binding_invalid')
    expected = (prepare_cumulative_category_units(owner, snapshot, prompt_version=model_input.prompt_version)
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2', 'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7', 'selected_material.v9', 'selected_material.v10', 'selected_material.v11', 'selected_material.v12', 'selected_material.v13'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot, prompt_version=model_input.prompt_version))
    require(model_input.request == expected.request and model_input.request_ref == expected.request_ref
        and model_input.source_guard == expected.source_guard
        and canonical(coverage) == canonical(_unit_candidate_coverage(expected, snapshot)),
        'analysis_quoted_parent_units_coverage_invalid')
    return canonical(dict(schema_version='cocolon.cmee.cumulative_quoted_parent_unit_candidates_file.v1',
        coverage=coverage, state=json.loads(serialize_analysis_model_quoted_parent_units(model_input, artifact))))


def reload_cumulative_quoted_parent_candidates(owner, snapshot, raw):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        _load, canonical, require, reload_analysis_model_quoted_parent_units)
    saved = _load(raw)
    prompt = (saved['state'].get('prompt_version', 'baseline.v1')
        if type(saved) is dict and type(saved.get('state')) is dict else 'baseline.v1')
    prepared = (prepare_cumulative_category_units(owner, snapshot, prompt_version=saved['state']['prompt_version'])
        if type(saved) is dict and type(saved.get('state')) is dict
        and saved['state'].get('prompt_version') in {'selected_categories.v1', 'selected_material.v2', 'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7', 'selected_material.v9', 'selected_material.v10', 'selected_material.v11', 'selected_material.v12', 'selected_material.v13'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot, prompt_version=prompt))
    require(type(saved) is dict and set(saved) == {'schema_version','coverage','state'}
        and saved['schema_version'] == 'cocolon.cmee.cumulative_quoted_parent_unit_candidates_file.v1'
        and canonical(saved['coverage']) == canonical(_unit_candidate_coverage(prepared, snapshot)),
        'analysis_quoted_parent_units_coverage_invalid')
    return reload_analysis_model_quoted_parent_units(prepared, canonical(saved['state'])), saved['coverage']


def _written_role_input(owner, snapshot, model_input):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsInput, require)
    require(type(model_input) is AnalysisModelQuotedParentUnitsInput,
            'analysis_written_role_input_invalid')
    expected = (prepare_cumulative_category_units(owner, snapshot, prompt_version=model_input.prompt_version)
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2', 'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7', 'selected_material.v9', 'selected_material.v10', 'selected_material.v11', 'selected_material.v12', 'selected_material.v13'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot, prompt_version=model_input.prompt_version))
    require(model_input.request == expected.request and model_input.request_ref == expected.request_ref
        and model_input.source_guard == expected.source_guard
        and model_input.prompt_version == expected.prompt_version,
        'analysis_written_role_input_invalid')
    return expected


def build_cumulative_written_role_map(owner, snapshot, *, model_input, with_action=False, clause=False):
    """Explicit offline vertical to the existing map; normal ensure is unchanged."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        generate_analysis_model_written_role)
    _written_role_input(owner, snapshot, model_input)
    artifact = generate_analysis_model_written_role(model_input.request, model_input, with_action=with_action, clause=clause)
    # The old scope consumes complete fields; explicit clause mode consumes
    # only the leading role and preserves the rest as unparsed SOURCE_SCOPE.
    # No choice criterion, task outcome or route is invented.
    coverage = _checked_coverage(dict(profile=PROFILE, source_count=1, processed_count=1,
        mapped_count=1, unparsed_count=1 if clause else 0, excluded_count=0,
        exclusion_reasons={}, stale_supplement_count=0))
    return artifact, coverage


def serialize_cumulative_written_role_map(owner, snapshot, *, model_input, artifact, coverage, with_action=False, clause=False):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        serialize_analysis_model_written_role, canonical, require)
    _written_role_input(owner, snapshot, model_input)
    require(canonical(coverage) == canonical(_checked_coverage(dict(profile=PROFILE, source_count=1,
        processed_count=1, mapped_count=1, unparsed_count=1 if clause else 0, excluded_count=0,
        exclusion_reasons={}, stale_supplement_count=0))), 'analysis_written_role_coverage_invalid')
    state = json.loads(serialize_analysis_model_written_role(model_input, artifact, with_action=with_action, clause=clause))
    return canonical(dict(schema_version=('cocolon.cmee.cumulative_written_role_clause_file.v1' if clause else
        'cocolon.cmee.cumulative_written_role_action_file.v1' if with_action
        else 'cocolon.cmee.cumulative_written_role_file.v1'),
        coverage=coverage, state=state))


def reload_cumulative_written_role_map(owner, snapshot, raw, *, with_action=False, clause=False):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        _load, canonical, require, reload_analysis_model_written_role)
    saved = _load(raw)
    require(type(saved) is dict and set(saved) == {'schema_version', 'coverage', 'state'}
        and saved['schema_version'] == ('cocolon.cmee.cumulative_written_role_clause_file.v1' if clause else
            'cocolon.cmee.cumulative_written_role_action_file.v1' if with_action
            else 'cocolon.cmee.cumulative_written_role_file.v1')
        and type(saved['state']) is dict, 'analysis_written_role_file_invalid')
    prompt = saved['state'].get('prompt_version')
    prepared = (prepare_cumulative_category_units(owner, snapshot, prompt_version=prompt)
        if prompt in {'selected_categories.v1', 'selected_material.v2', 'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7', 'selected_material.v9', 'selected_material.v10', 'selected_material.v11', 'selected_material.v12', 'selected_material.v13'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot, prompt_version=prompt))
    artifact = reload_analysis_model_written_role(prepared, canonical(saved['state']), with_action=with_action, clause=clause)
    coverage = _checked_coverage(dict(profile=PROFILE, source_count=1, processed_count=1,
        mapped_count=1, unparsed_count=1 if clause else 0, excluded_count=0,
        exclusion_reasons={}, stale_supplement_count=0))
    require(type(saved['coverage']) is dict and canonical(saved['coverage']) == canonical(coverage),
            'analysis_written_role_coverage_invalid')
    return artifact, coverage


def build_cumulative_map(owner, snapshot, *, model_input=None):
    """Use the existing compiler/author once for the complete eligible set.

    A source whose safety/update semantics cannot be admitted is explicitly
    counted, rather than blocking every future map or being called analyzed.
    """
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        AnalysisObservedMapRequest, AnalysisSourceError, freeze_analysis_sources, _time)
    from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import compile_observed_graph
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.contracts import EngineStatus
    if model_input is not None:
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
            AnalysisModelFieldKindsInput, AnalysisModelQuotedParentUnitsInput,
            generate_analysis_model_observed_actions, require)
        if type(model_input) is AnalysisModelQuotedParentUnitsInput:
            expected = _written_role_input(owner, snapshot, model_input)
            artifact, mapped, unread = generate_analysis_model_observed_actions(
                expected.request, model_input, with_record_counts=True)
            coverage = _unit_candidate_coverage(expected, snapshot)
            coverage.update(mapped_count=mapped, unparsed_count=unread)
            return artifact, _checked_coverage(coverage)
        expected = (prepare_cumulative_model_field_kinds(owner, snapshot)
            if type(model_input) is AnalysisModelFieldKindsInput else prepare_cumulative_model_fields(owner, snapshot))
        require(type(model_input) is type(expected) and model_input.request == expected.request
            and model_input.request_ref == expected.request_ref
            and model_input.source_guard == expected.source_guard, 'analysis_model_input_binding_invalid')
        outcome = MeaningExperienceEngine().generate(expected.request, semantic_input=model_input)
        artifact = outcome.artifact
        mapped = {r for n in artifact.graph.nodes for r in n.record_refs} if artifact else set()
        # Visible classification candidates are still semantically unparsed.
        count = len(expected.request.members)
        stale = sum(sum(e.get('kind') == 'ANSWER' for e in raw['events'])
            for raw in snapshot['members'] if raw.get('thread')
            and raw['thread'].get('source_snapshot') != raw['original'])
        coverage = _checked_coverage(dict(profile=PROFILE, source_count=count,
            processed_count=count, mapped_count=len(mapped), unparsed_count=count,
            excluded_count=0, exclusion_reasons={}, stale_supplement_count=stale))
        return artifact, coverage
    start, end = snapshot['period_start'], snapshot['period_end']
    records, reasons, unparsed, mapped, stale = [], Counter(), 0, 0, 0
    request_id = 'analysis-cumulative-' + uuid4().hex
    for raw in snapshot['members']:
        member, _ = _analysis_saved_member(dict(raw, tier=snapshot['tier'], now=snapshot['now']),
            owner=owner, input_id=raw['original']['id'], tier=snapshot['tier'],
            start=_time(start), end=_time(end), cumulative=True)
        if raw.get('thread') and raw['thread'].get('source_snapshot') != raw['original']:
            stale += sum(e.get('kind') == 'ANSWER' for e in raw['events'])
        single = AnalysisObservedMapRequest(request_id, owner, start, end, (member,),
            selected_category_context=True)
        try:
            graph = compile_observed_graph(freeze_analysis_sources(single))
        except AnalysisSourceError as exc:
            code = str(exc)
            if code not in {'analysis_separate_safety_required', 'analysis_supplement_interpretation_pending',
                    'analysis_interpretation_correction_pending',
                    'analysis_correction_target_unresolved', 'analysis_correction_replacement_unsupported'}:
                raise
            reasons[code] += 1
            continue
        records.append(member)
        mapped += int(bool(graph.nodes))
        unparsed += int(not graph.nodes or any(g.missing_scope == 'SOURCE_SCOPE' for g in graph.unknown_gaps))
    coverage = _checked_coverage(dict(profile=PROFILE, source_count=len(snapshot['members']),
        processed_count=len(records), mapped_count=mapped, unparsed_count=unparsed,
        excluded_count=sum(reasons.values()), exclusion_reasons=dict(reasons), stale_supplement_count=stale))
    if not records:
        return None, coverage
    request = AnalysisObservedMapRequest(request_id, owner, start, end, tuple(records),
        selected_category_context=True)
    outcome = MeaningExperienceEngine().generate(request)
    if (outcome.artifact is None and outcome.status is EngineStatus.UNAVAILABLE
            and outcome.reason_codes == ('analysis_observed_route_not_established',)):
        return None, coverage
    if outcome.artifact is None or outcome.status is not EngineStatus.GENERATED:
        raise HTTPException(422, 'analysis_observed_map_unavailable')
    return outcome.artifact, coverage


async def ensure_map(user_id, *, ensure=True, force=False, monthly=False, model_source=None):
    """Coalesce identical overlapping explicit model updates in this process."""
    owner = _owner(user_id)
    if model_source is None and ensure and observed_mode() == 'development':
        from analysis_model_source import application_analysis_model_source
        model_source = application_analysis_model_source()
    if model_source is None or not ensure or observed_mode() != 'development':
        return await _ensure_map(owner, ensure=ensure, force=force,
            monthly=monthly, model_source=model_source)
    key = (asyncio.get_running_loop(), owner, id(model_source), force, monthly)
    flight = _model_map_flights.get(key)
    if flight is None:
        flight = _ModelMapFlight(model_source, asyncio.create_task(_ensure_map(owner,
            ensure=ensure, force=force, monthly=monthly, model_source=model_source)))
        _model_map_flights[key] = flight
    flight.waiters += 1
    try:
        return deepcopy(await asyncio.shield(flight.task))
    finally:
        flight.waiters -= 1
        if not flight.waiters:
            if _model_map_flights.get(key) is flight:
                del _model_map_flights[key]
            if not flight.task.done():
                flight.task.cancel()
            # Retrieve a late failure even when every caller was cancelled.
            flight.task.add_done_callback(_consume_model_map_completion)


def _consume_model_map_completion(task):
    if not task.cancelled():
        task.exception()


async def _model_response(model_source, prepared):
    _require_model_write_active()
    try:
        from analysis_model_source import is_semantic_analysis_model_source
        timeout = 215.0 if is_semantic_analysis_model_source(model_source) else MODEL_SOURCE_TIMEOUT_SECONDS
        async with asyncio.timeout(timeout) as deadline:
            response = await model_source(prepared)
        # A cooperative provider may catch cancellation to finish its cleanup.
        # A response returned after that deadline must still never be committed.
        if deadline.expired():
            raise TimeoutError
        _require_model_write_active()
        return response
    except TimeoutError:
        raise HTTPException(504, 'analysis_model_source_timeout') from None
    except (httpx.HTTPError, OSError, RuntimeError):
        raise HTTPException(503, 'analysis_model_source_unavailable') from None


def _require_model_write_active():
    if asyncio.current_task().cancelling():
        raise asyncio.CancelledError
    if observed_mode() != 'development':
        raise HTTPException(503, 'analysis_model_source_unavailable')


async def _ensure_map(user_id, *, ensure=True, force=False, monthly=False, model_source=None):
    """Save/read the normal map; explicit transport may opt into the v7 input.

    The asynchronous source returns AnalysisModelQuotedParentUnitsResponse.
    It is called once only when rebuilding within the existing consumer scope.
    Saved reads do not acquire responses; failed responses never use a fallback.
    """
    owner = _owner(user_id)
    result = await read_maps(owner, history=monthly, limit=1)
    row = result['items'][0] if result['items'] else None
    # For a monthly request, only this month's actual capture is up to date.
    from datetime import datetime, timezone, timedelta
    this_month = datetime.now(timezone(timedelta(hours=9))).date().replace(day=1).isoformat()
    if monthly and row and row['snapshot_month'] != this_month:
        row = None
    if monthly and row:
        return _response(row, monthly=True)
    refreshed, coverage = False, None
    if ensure and observed_mode() == 'development':
        current = await read_maps(owner, limit=1) if monthly else result
        current_row = current['items'][0] if current['items'] else None
        snapshot = await _rpc('analysis_cumulative_source_snapshot', {'p_user_id': owner})
        if not re.fullmatch(r'analysis-db-cumulative-v1:[0-9a-f]{64}', snapshot['guard']):
            raise HTTPException(503, 'analysis_saved_source_unavailable')
        # The commit is also the idempotent monthly capture for a reused map.
        # Refresh an old current once under the category policy. Historical
        # month references are immutable and returned above without rebuilding.
        from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import CATEGORY_LABEL_PREFIX
        from analysis_model_source import is_semantic_analysis_model_source
        semantic_source = is_semantic_analysis_model_source(model_source)
        semantic_current = bool(current_row and current_row['content_json']['watashiMap']['wire_kind'] == 'watashi.map.v3')
        category_current = bool(semantic_current or (current_row and all(
            n['visible_label'].startswith(CATEGORY_LABEL_PREFIX) and '\n' in n['visible_label']
            for n in current_row['content_json']['watashiMap']['nodes'])))
        refresh_category_policy = bool(current_row and (
            (semantic_source and not semantic_current) or not category_current))
        if current_row and not force and not refresh_category_policy:
            rid = await _rpc('analysis_cumulative_commit', dict(p_user_id=owner, p_guard=snapshot['guard'],
                p_existing_id=current_row['id']))
        else:
            try:
                if semantic_source:
                    from analysis_semantic_map import prepare_semantic_map, build_semantic_map, SemanticMapNoMaterial
                    try:
                        from analysis_model_source import analysis_model_prompt_version
                        prepared = await asyncio.to_thread(prepare_semantic_map, owner, snapshot,
                            prompt_version=analysis_model_prompt_version(model_source))
                    except SemanticMapNoMaterial as excluded:
                        artifact, coverage = None, _checked_coverage(excluded.coverage)
                    else:
                        response = await _model_response(model_source, prepared)
                        artifact, coverage = await asyncio.to_thread(build_semantic_map, prepared, response)
                elif model_source is None:
                    artifact, coverage = await asyncio.to_thread(build_cumulative_map, owner, snapshot)
                else:
                    from dataclasses import replace
                    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
                        AnalysisModelQuotedParentUnitsResponse, require,
                        require_analysis_model_observed_scope)
                    from analysis_model_source import analysis_model_prompt_version
                    prepared = prepare_cumulative_category_units(owner, snapshot,
                        prompt_version=analysis_model_prompt_version(model_source))
                    require_analysis_model_observed_scope(prepared.request)
                    response = await _model_response(model_source, prepared)
                    require(type(response) is AnalysisModelQuotedParentUnitsResponse,
                        'analysis_quoted_parent_units_response_invalid')
                    artifact, coverage = await asyncio.to_thread(build_cumulative_map, owner, snapshot,
                        model_input=replace(prepared, response=response))
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                import logging
                locations = []
                trace = exc.__traceback__
                while trace is not None:
                    locations.append(f'{trace.tb_frame.f_code.co_name}:{trace.tb_lineno}')
                    trace = trace.tb_next
                logging.getLogger(__name__).warning('analysis_saved_source_rejected type=%s stage=%s',
                    type(exc).__name__, '>'.join(locations))
                raise HTTPException(422, 'analysis_saved_source_unavailable') from None
            if artifact is None:
                return _response(None, coverage=coverage)
            if model_source is not None:
                _require_model_write_active()
                from analysis_model_source import require_current_analysis_model_source
                try:
                    require_current_analysis_model_source(model_source)
                except RuntimeError:
                    raise HTTPException(503, 'analysis_model_source_unavailable') from None
            projection = artifact.safe_projection(authenticated_owner_scope=owner)
            text = artifact.safe_text_projection(authenticated_owner_scope=owner)['text']
            private = artifact.private_evidence() if semantic_source else private_storage_evidence(artifact)
            private['coverage'] = coverage
            private['source_record_refs'] = [s['original']['id'] for s in snapshot['members']]
            _checked_projection(projection, str(UUID(artifact.artifact_id[9:])))
            rid = await _rpc('analysis_cumulative_commit', dict(p_user_id=owner, p_guard=snapshot['guard'],
                p_artifact_id=artifact.artifact_id, p_private_evidence=private, p_projection=projection,
                p_text=text, p_start=snapshot['period_start'], p_end=snapshot['period_end'],
                p_force=force or refresh_category_policy))
            refreshed = True
        checked = await read_maps(owner, report_id=rid if not monthly else None,
            history=monthly, month=this_month if monthly else None, limit=1)
        row = checked['items'][0] if checked['items'] else None
        if not row:
            raise HTTPException(409, 'analysis_source_changed')
        if refreshed and row['id'] == str(UUID(artifact.artifact_id[9:])):
            await _queue_map_update_notification(owner, row)
    return _response(row, refreshed=refreshed, monthly=monthly, coverage=coverage)


async def _queue_map_update_notification(owner, row):
    """Best-effort reservation after the new map passed its saved-source guard."""
    try:
        from fcm_push_queue import enqueue_single_user_push_notification
        await enqueue_single_user_push_notification(
            user_id=owner, title='Emlis', body='わたしマップが更新されました',
            event_type='watashi_map_updated',
            job_key_prefix='watashi_map_updated:' + row['id'],
            data=dict(type='watashi_map_updated', target='watashi_map', screen='Analysis', user_id=owner,
                report_id=row['id'], version_key=row['content_json']['watashiMap']['projection_of']),
            priority=60, only_if_absent=True)
    except Exception:
        # A notification outage must not turn the already saved map into a
        # failed analysis. This reservation is best effort, not an outbox.
        import logging
        logging.getLogger(__name__).warning('Watashi map completion push reservation failed')


def _response(row, *, refreshed=False, monthly=False, coverage=None):
    insufficient = row is None and coverage is not None and coverage['source_count'] > 0
    return dict(status='ok', refreshed=refreshed, reason='saved' if refreshed else ('up_to_date' if row else ('insufficient_input' if insufficient else 'no_visible_content')),
        report_mode='standard', period='all', period_start=row['period_start'] if row else None,
        period_end=row['period_end'] if row else None, generated_at=row['generated_at'] if row else None,
        latest_generated_at=row['generated_at'] if row else None, title=row['title'] if row else None,
        content_text=row['content_text'] if row else None, meta=row['content_json']['watashiMap'] if row else None,
        map_context=row['content_json']['map_context'] if row else coverage,
        report_id=row['id'] if row else None, snapshot_month=row['snapshot_month'] if row else None,
        captured_at=row['captured_at'] if row else None, source_profile=PROFILE,
        has_visible_content=bool(row), skip_reason=None if row else ('analysis_insufficient_input' if insufficient else 'analysis_saved_map_unavailable'),
        history_saved=bool(row) if monthly else False)


async def map_status(user_id):
    result = await read_maps(user_id, limit=1)
    row = result['items'][0] if result['items'] else None
    try:
        refresh_status = await map_refresh_status(user_id)
    except Exception:
        # A queue outage must not hide a valid, separately authorized map.
        import logging
        logging.getLogger(__name__).warning('Analysis refresh status read failed')
        refresh_status = 'failed'
    return dict(version_key=row['content_json']['watashiMap']['projection_of'] if row else None,
        generated_at=row['generated_at'] if row else None, saved_report_mode='standard' if row else None,
        has_visible_content=bool(row), skip_reason=None if row else 'analysis_saved_map_unavailable',
        refresh_status=refresh_status)


def _map_refresh_queue_enabled():
    return (observed_mode() == 'development' and
        os.getenv('ASTOR_WORKER_QUEUE_ENABLED', 'false').strip().lower() in {'1', 'true', 'yes', 'y', 'on'})


async def map_refresh_status(user_id):
    """Read only the authenticated owner's existing refresh-job state."""
    owner = _owner(user_id)
    if not _map_refresh_queue_enabled():
        return None
    from astor_job_queue import JOBS_TABLE
    from supabase_client import sb_get
    response = await sb_get(f'/rest/v1/{JOBS_TABLE}', params={
        'select': 'status,job_type', 'user_id': 'eq.' + owner,
        'job_key': 'eq.myprofile_latest_refresh:' + owner, 'limit': '1'}, timeout=3.0)
    if response.status_code != 200:
        raise HTTPException(503, 'analysis_refresh_status_unavailable')
    try:
        rows = response.json()
        if type(rows) is not list or len(rows) > 1 or (rows and type(rows[0]) is not dict):
            raise ValueError
        row = rows[0] if rows else None
        if row and row.get('job_type') == 'myprofile_latest_refresh_v1':
            status = row.get('status')
            if status in {'queued', 'running', 'failed'}:
                return status
        return None
    except (ValueError, TypeError, KeyError):
        raise HTTPException(503, 'analysis_refresh_status_unavailable') from None


async def request_map_refresh(user_id, *, force=False, trigger='map_view', requested_at=None,
                              debounce_seconds=20):
    """Queue an existing ASTOR refresh without acquiring a model response here.

    Saved-current and pending-job reads prevent ordinary screen polling from
    resetting the job's debounce or replacing an explicit forced update.
    """
    owner = _owner(user_id)
    if not _map_refresh_queue_enabled():
        return None
    if trigger not in {'map_view', 'manual', 'emotion_submit'}:
        raise ValueError('analysis_refresh_trigger_invalid')
    if not force and (await read_maps(owner, limit=1, metadata_only=True))['items']:
        return await map_refresh_status(owner)
    status = await map_refresh_status(owner)
    if not force and trigger != 'emotion_submit' and status in {'queued', 'running'}:
        return status
    from datetime import datetime, timezone
    from astor_job_queue import enqueue_job
    await enqueue_job(job_key='myprofile_latest_refresh:' + owner,
        job_type='myprofile_latest_refresh_v1', user_id=owner,
        payload=dict(trigger=trigger, force=bool(force), requested_at=requested_at or
            datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
        debounce_seconds=debounce_seconds, priority=50)
    return status if status == 'running' else 'queued'


async def map_history(user_id, *, limit=60, offset=0):
    result = await read_maps(user_id, history=True, limit=min(limit + 1, 200), offset=offset, metadata_only=True)
    rows = result['items']
    has_more = len(rows) > limit
    if limit == 200 and len(rows) == limit:
        has_more = bool((await read_maps(user_id, history=True, limit=1, offset=offset + limit, metadata_only=True))['items'])
    return dict(status='ok', items=[{k: v for k, v in r.items() if k not in {'content_text', 'content_json'}}
        for r in rows[:limit]], limit=limit, offset=offset, has_more=has_more,
        next_offset=offset + limit if has_more else None, subscription_tier=result['subscription_tier'])


async def map_evidence(user_id, report_id, node, *, month=None):
    if not re.fullmatch(r'n[1-9][0-9]*', node):
        raise HTTPException(400, 'analysis_node_invalid')
    raw = await _rpc('analysis_cumulative_evidence', dict(p_user_id=_owner(user_id),
        p_id=_owner(report_id), p_node=node, p_month=_month(month)))
    try:
        return {'items': await asyncio.to_thread(_project_evidence, _owner(user_id), raw)}
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(409, 'analysis_evidence_source_changed') from None


def _project_evidence(owner, raw):
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        commitment, _time, AnalysisObservedMapRequest, freeze_analysis_sources, source_field_text)
    correction_evidence = []
    if raw.get('map_corrections'):
        from cocolon_meaning_experience_engine.cores.analysis.map_interpretation_correction import qualify_map_correction
        for pair in raw['map_corrections']:
            saved = pair['saved']
            source = qualify_map_correction(owner, saved['source'], allow_stale=True)
            current = qualify_map_correction(owner, pair['current'], allow_stale=True)
            if (current != source or saved['source_envelope_id'] != source.envelope.envelope_id
                    or saved['evidence'] != asdict(source.evidence)
                    or saved['cohort_refs'] != list(source.cohort_refs)):
                raise ValueError('analysis_map_correction_evidence_changed')
            target = source.target_context
            correction_evidence.append((source.cohort_refs, dict(
                correction_id=source.correction_id, text=source.explanation,
                recorded_at=source.recorded_at, target_artifact_ref=target['artifact_ref'],
                target_kind=target['kind'], target_ref=target['ref'],
                version_state='CURRENT' if pair['current']['source_state'] == 'ACTIVE'
                    else 'EDITED_SINCE_ANALYSIS')))
    items = []
    for row in raw['items']:
        original = row['original']
        corrections = [value for refs, value in correction_evidence if original['id'] in refs]
        extra = ({'map_corrections': corrections,
            **({'evidence_scope': 'MAP_CORRECTION_CONTEXT'} if not row['expected_envelopes'] else {})}
            if corrections else {})
        if commitment(original) != row['analyzed_version']:
            items.append(dict(id=original['id'], created_at=original['created_at'],
                memo=original['memo'], memo_action=original['memo_action'], answers=[],
                version_state='EDITED_SINCE_ANALYSIS', **extra))
            continue
        member, _ = _analysis_saved_member(dict(row, tier=raw['tier'], now=raw['now']),
            owner=owner, input_id=original['id'], tier=raw['tier'],
            start=_time(original['created_at'], saved_utc=True), end=_time(raw['now']), cumulative=True)
        sources = freeze_analysis_sources(AnalysisObservedMapRequest('analysis-evidence-'+uuid4().hex,
            owner, _time(original['created_at'], saved_utc=True).isoformat(), raw['now'], (member,))).sources
        envelopes = {s.envelope.envelope_id for s in sources}
        unchanged = commitment(original) == row['analyzed_version'] and set(row['expected_envelopes']) <= envelopes
        answers = [source_field_text(s, 'memo') for s in sources
            if s.envelope.source_role in {'SUPPLEMENTAL_ANSWER', 'USER_INTERPRETATION_CORRECTION'}
            and s.envelope.envelope_id in row['expected_envelopes']]
        items.append(dict(id=original['id'], created_at=original['created_at'],
            memo=original['memo'], memo_action=original['memo_action'],
            answers=answers, version_state='CURRENT' if unchanged else 'EDITED_SINCE_ANALYSIS', **extra))
    return items



