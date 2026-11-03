"""All-owned-input map lifecycle and immutable monthly references.

The authenticated API resolves the owner. No external model, lookback window,
new language realizer, or reconstruction of unsaved past months is used here.
"""
from __future__ import annotations

import asyncio
from collections import Counter
from datetime import date
import json
import re
from uuid import UUID, uuid4

from fastapi import HTTPException

import analysis_observed_service as observed
from analysis_observed_service import _checked_projection, private_storage_evidence, observed_mode

PROFILE = 'cumulative.v1'


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
        from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import ObservedSelfStructureMap
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
            if row['content_text'] != ObservedSelfStructureMap._text_from_visual(projection)['text']:
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


def prepare_cumulative_model_fields(owner, snapshot):
    """Explicit offline probe; never selected by ensure_map or an HTTP flag."""
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        AnalysisObservedMapRequest, commitment, _time)
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_fields
    owner = _owner(owner)
    start, end = snapshot['period_start'], snapshot['period_end']
    records = tuple(_analysis_saved_member(dict(raw, tier=snapshot['tier'], now=snapshot['now']),
        owner=owner, input_id=raw['original']['id'], tier=snapshot['tier'],
        start=_time(start), end=_time(end), cumulative=True)[0] for raw in snapshot['members'])
    request_id = 'analysis-model-' + commitment([owner, snapshot['guard'], start, end])[7:]
    request = AnalysisObservedMapRequest(request_id, owner, start, end, records)
    return prepare_analysis_model_fields(request, source_guard=snapshot['guard'])


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


def prepare_cumulative_quoted_parent_units(owner, snapshot):
    """Separate explicit private wire; the normal builder never selects it."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_quoted_parent_units
    prepared = prepare_cumulative_model_fields(owner, snapshot)
    return prepare_analysis_model_quoted_parent_units(prepared.request, source_guard=prepared.source_guard)


def prepare_cumulative_category_units(owner, snapshot, *, prompt_version='selected_categories.v1'):
    """Current category-aware 4B preparation; legacy saved probes stay v1."""
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        prepare_analysis_model_quoted_parent_units, QUOTED_PARENT_CATEGORY_PROFILE)
    prepared = prepare_cumulative_model_fields(owner, snapshot)
    request = replace(prepared.request, selected_category_context=True)
    return prepare_analysis_model_quoted_parent_units(request, source_guard=prepared.source_guard,
        prompt_version=prompt_version)


def build_cumulative_quoted_parent_candidates(owner, snapshot, *, model_input):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsInput, require)
    require(type(model_input) is AnalysisModelQuotedParentUnitsInput,
            'analysis_quoted_parent_units_binding_invalid')
    expected = (prepare_cumulative_category_units(owner, snapshot, prompt_version=model_input.prompt_version)
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot))
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
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot))
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
    prepared = (prepare_cumulative_category_units(owner, snapshot, prompt_version=saved['state']['prompt_version'])
        if type(saved) is dict and type(saved.get('state')) is dict
        and saved['state'].get('prompt_version') in {'selected_categories.v1', 'selected_material.v2'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot))
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
        if model_input.prompt_version in {'selected_categories.v1', 'selected_material.v2'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot))
    require(model_input.request == expected.request and model_input.request_ref == expected.request_ref
        and model_input.source_guard == expected.source_guard
        and model_input.prompt_version == expected.prompt_version,
        'analysis_written_role_input_invalid')
    return expected


def build_cumulative_written_role_map(owner, snapshot, *, model_input):
    """Explicit offline vertical to the existing map; normal ensure is unchanged."""
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        generate_analysis_model_written_role)
    _written_role_input(owner, snapshot, model_input)
    artifact = generate_analysis_model_written_role(model_input.request, model_input)
    # The admission scope consumes one complete original field/record. Missing
    # stages stay gaps; no choice criterion, task outcome or route is invented.
    coverage = _checked_coverage(dict(profile=PROFILE, source_count=1, processed_count=1,
        mapped_count=1, unparsed_count=0, excluded_count=0,
        exclusion_reasons={}, stale_supplement_count=0))
    return artifact, coverage


def serialize_cumulative_written_role_map(owner, snapshot, *, model_input, artifact, coverage):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        serialize_analysis_model_written_role, canonical, require)
    _written_role_input(owner, snapshot, model_input)
    require(canonical(coverage) == canonical(_checked_coverage(dict(profile=PROFILE, source_count=1,
        processed_count=1, mapped_count=1, unparsed_count=0, excluded_count=0,
        exclusion_reasons={}, stale_supplement_count=0))), 'analysis_written_role_coverage_invalid')
    state = json.loads(serialize_analysis_model_written_role(model_input, artifact))
    return canonical(dict(schema_version='cocolon.cmee.cumulative_written_role_file.v1',
        coverage=coverage, state=state))


def reload_cumulative_written_role_map(owner, snapshot, raw):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        _load, canonical, require, reload_analysis_model_written_role)
    saved = _load(raw)
    require(type(saved) is dict and set(saved) == {'schema_version', 'coverage', 'state'}
        and saved['schema_version'] == 'cocolon.cmee.cumulative_written_role_file.v1'
        and type(saved['state']) is dict, 'analysis_written_role_file_invalid')
    prompt = saved['state'].get('prompt_version')
    prepared = (prepare_cumulative_category_units(owner, snapshot, prompt_version=prompt)
        if prompt in {'selected_categories.v1', 'selected_material.v2'}
        else prepare_cumulative_quoted_parent_units(owner, snapshot))
    artifact = reload_analysis_model_written_role(prepared, canonical(saved['state']))
    coverage = _checked_coverage(dict(profile=PROFILE, source_count=1, processed_count=1,
        mapped_count=1, unparsed_count=0, excluded_count=0,
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
            AnalysisModelFieldKindsInput, require)
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


async def ensure_map(user_id, *, ensure=True, force=False, monthly=False):
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
        category_current = bool(current_row and all(
            n['visible_label'].startswith(CATEGORY_LABEL_PREFIX) and '\n' in n['visible_label']
            for n in current_row['content_json']['watashiMap']['nodes']))
        refresh_category_policy = bool(current_row and not category_current)
        if current_row and not force and not refresh_category_policy:
            rid = await _rpc('analysis_cumulative_commit', dict(p_user_id=owner, p_guard=snapshot['guard'],
                p_existing_id=current_row['id']))
        else:
            try:
                artifact, coverage = await asyncio.to_thread(build_cumulative_map, owner, snapshot)
            except (ValueError, KeyError, TypeError, AttributeError):
                raise HTTPException(422, 'analysis_saved_source_unavailable') from None
            if artifact is None:
                return _response(None, coverage=coverage)
            projection = artifact.safe_projection(authenticated_owner_scope=owner)
            text = artifact.safe_text_projection(authenticated_owner_scope=owner)['text']
            private = private_storage_evidence(artifact)
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
    return _response(row, refreshed=refreshed, monthly=monthly, coverage=coverage)


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
    return dict(version_key=row['content_json']['watashiMap']['projection_of'] if row else None,
        generated_at=row['generated_at'] if row else None, saved_report_mode='standard' if row else None,
        has_visible_content=bool(row), skip_reason=None if row else 'analysis_saved_map_unavailable')


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
    items = []
    for row in raw['items']:
        original = row['original']
        if commitment(original) != row['analyzed_version']:
            items.append(dict(id=original['id'], created_at=original['created_at'],
                memo=original['memo'], memo_action=original['memo_action'], answers=[],
                version_state='EDITED_SINCE_ANALYSIS'))
            continue
        member, _ = _analysis_saved_member(dict(row, tier=raw['tier'], now=raw['now']),
            owner=owner, input_id=original['id'], tier=raw['tier'],
            start=_time(original['created_at'], saved_utc=True), end=_time(raw['now']), cumulative=True)
        sources = freeze_analysis_sources(AnalysisObservedMapRequest('analysis-evidence-'+uuid4().hex,
            owner, _time(original['created_at'], saved_utc=True).isoformat(), raw['now'], (member,))).sources
        envelopes = {s.envelope.envelope_id for s in sources}
        unchanged = commitment(original) == row['analyzed_version'] and set(row['expected_envelopes']) <= envelopes
        answers = [source_field_text(s, 'memo') for s in sources
            if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER' and s.envelope.envelope_id in row['expected_envelopes']]
        items.append(dict(id=original['id'], created_at=original['created_at'],
            memo=original['memo'], memo_action=original['memo_action'],
            answers=answers, version_state='CURRENT' if unchanged else 'EDITED_SINCE_ANALYSIS'))
    return items


