"""Saved Analysis lifecycle; verified API callers only, never a request-body owner.

DB snapshots are transient. Only closed evidence and owner-safe projections are
persisted. Reads return stored text/graph and never run the meaning engine.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import os
import re
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException
from supabase_client import sb_post_rpc


def _require(condition):
    if not condition:
        raise ValueError("analysis_saved_artifact_invalid")


def observed_mode():
    value = os.getenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'off').strip().lower()
    return value if value in {'off', 'read_only', 'development'} else 'read_only'


def observed_enabled():
    return observed_mode() != 'off'


async def _rpc(name, payload):
    try:
        response = await sb_post_rpc(name, payload, timeout=8.0)
        if response.status_code >= 300:
            code = response.json().get('code', '')
            status = {'42501': 403, 'P0002': 404, '40001': 409,
                      '23505': 409, '23503': 409, '22023': 400, '54000': 422}.get(code, 503)
            raise HTTPException(status, 'analysis_storage_unavailable' if status == 503
                                else 'analysis_source_or_access_unavailable')
        return response.json()
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        # A lost commit ACK is unknown, never claimed saved and never retried.
        raise HTTPException(503, 'analysis_storage_unavailable') from None


def _evidence(ref):
    return {key: getattr(ref, key) for key in (
        'evidence_id', 'source_span_id', 'source_envelope_id', 'field_path',
        'element_index', 'field_utf8_start', 'field_utf8_end', 'scalar_start',
        'scalar_end', 'utf8_start', 'utf8_end', 'field_sha256', 'literal_sha256')}


def private_storage_evidence(artifact):
    """Explicit allowlist: no raw node label, proposition noun or source body."""
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import commitment
    graph = {
        'nodes': [{key: getattr(n, key) for key in ('node_ref', 'node_kind',
            'record_refs', 'polarity', 'modality', 'temporal_scope', 'update_refs')}
            | {'evidence_refs': [_evidence(e) for e in n.evidence_refs]}
            for n in artifact.graph.nodes],
        'edges': [{'edge_ref': e.edge_ref, 'edge_kind': e.edge_kind,
            'endpoint_refs': e.endpoint_refs, 'evidence_refs': [_evidence(r) for r in e.evidence_refs]}
            for e in artifact.graph.edges],
        'unknown_gaps': [{key: getattr(g, key) for key in (
            'gap_ref', 'between_node_refs', 'missing_scope', 'reason_code')} for g in artifact.graph.unknown_gaps],
        'source_updates': [{'update_ref': u.update_ref, 'operation': u.operation,
            'record_ref': u.record_ref, 'target_evidence': _evidence(u.target_evidence),
            'answer_evidence_refs': [_evidence(e) for e in u.answer_evidence_refs],
            'replacement_evidence_refs': [_evidence(e) for e in u.replacement_evidence_refs]}
            for u in artifact.graph.source_updates],
        'conflicts': [{'conflict_ref': c.conflict_ref, 'target_refs': c.target_refs,
            'reason_code': c.reason_code, 'evidence_refs': [_evidence(e) for e in c.evidence_refs]}
            for c in artifact.graph.conflicts],
        'annotations': [{key: getattr(a, key) for key in ('annotation_ref', 'target_ref',
            'kind', 'annotation_state', 'uncertainty', 'alternative_explanations',
            'forbidden_promotions', 'update_refs')}
            | {'evidence_refs': [_evidence(e) for e in a.evidence_refs]}
            for a in artifact.graph.annotations],
    }
    return {'schema_version': 'analysis.private-evidence.v1', 'projection_of': artifact.reference,
        'source_set_ref': artifact.source_set_ref, 'graph_commitment': commitment(graph), 'graph': graph,
        'source_members': [{key: getattr(m, key) for key in (
            'saved_record_ref', 'saved_record_version', 'member_role', 'source_commitment',
            'inclusion_status', 'inclusion_or_exclusion_reason', 'child_source_envelope_refs')}
            for m in artifact.source_members]}


def _checked_projection(projection, report_id):
    """Closed saved-wire validator. Never repair corrupt data with legacy text."""
    from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import NODE_KINDS
    keys = {'schema_version', 'wire_kind', 'projection_of', 'artifact_version', 'period_label',
            'period_comparison', 'nodes', 'edges', 'annotation_badges', 'unknown_gaps',
            'conflict_badges', 'accessibility_linear_order'}
    try:
        _require(type(projection) is dict and set(projection) == keys)
        _require(projection['schema_version'] == 'cocolon.cmee.analysis_watashi_map_safe_projection.v1alpha1')
        _require(projection['wire_kind'] == 'watashi.map.v2' and projection['artifact_version'] == 1)
        _require(projection['projection_of'] == 'artifact:' + UUID(report_id).hex + '@1')
        _require(type(projection['period_label']) is str)
        _require(projection['period_comparison'] == {'state': 'NO_PREVIOUS', 'reason_codes': [], 'safe_change_kinds': []})
        nodes = projection['nodes']
        _require(type(nodes) is list and nodes)
        refs = []
        for n in nodes:
            _require(set(n) == {'node_ref', 'node_kind', 'visible_label', 'evidence_badge_count'})
            _require(re.fullmatch(r'n[1-9][0-9]*', n['node_ref']) and n['node_kind'] in NODE_KINDS)
            _require(type(n['visible_label']) is str and n['visible_label'])
            _require(type(n['evidence_badge_count']) is int and n['evidence_badge_count'] > 0)
            refs.append(n['node_ref'])
        _require(len(set(refs)) == len(refs) and projection['accessibility_linear_order'] == refs)
        for index, e in enumerate(projection['edges'], 1):
            _require(e['edge_ref'] == 'e' + str(index) and type(e['visible_label']) is str)
            if e['edge_kind'] == 'OBSERVED_ORDER':
                _require(set(e) == {'edge_ref', 'edge_kind', 'visible_label', 'from_ref', 'to_ref'})
                endpoints = [e['from_ref'], e['to_ref']]
            else:
                _require(e['edge_kind'] == 'REPEATED_COOCCURRENCE')
                _require(set(e) == {'edge_ref', 'edge_kind', 'visible_label', 'endpoint_refs'})
                endpoints = e['endpoint_refs']
            _require(len(endpoints) == len(set(endpoints)) == 2 and set(endpoints) <= set(refs))
        for g in projection['unknown_gaps']:
            _require(set(g) == {'gap_ref', 'between_node_refs', 'visible_label'})
            _require(type(g['visible_label']) is str and re.fullmatch(r'g[1-9][0-9]*', g['gap_ref']))
            _require(1 <= len(g['between_node_refs']) <= 2 and set(g['between_node_refs']) <= set(refs))
        from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import CONFLICT_LABEL, BURDEN_LABELS
        annotations = projection['annotation_badges']
        _require(type(annotations) is list)
        seen_annotations = set()
        thought_refs = {n['node_ref'] for n in nodes if n['node_kind'] == 'ATTENTION_OR_THOUGHT'}
        for index, a in enumerate(annotations, 1):
            _require(type(a) is dict and set(a) == {'annotation_ref', 'target_ref', 'kind', 'visible_label'})
            _require(a['annotation_ref'] == 'a' + str(index) and a['kind'] == 'BURDEN')
            _require(type(a['target_ref']) is str and a['target_ref'] in thought_refs
                     and a['visible_label'] in BURDEN_LABELS.values())
            key = (a['target_ref'], a['visible_label'])
            _require(key not in seen_annotations)
            seen_annotations.add(key)
        conflicts = projection['conflict_badges']
        _require(type(conflicts) is list)
        seen_targets = set()
        for index, c in enumerate(conflicts, 1):
            _require(type(c) is dict and set(c) == {'conflict_ref', 'target_refs', 'visible_label'})
            _require(c['conflict_ref'] == 'c' + str(index) and c['visible_label'] == CONFLICT_LABEL)
            targets = c['target_refs']
            _require(type(targets) is list and len(targets) == 2
                     and all(type(ref) is str and ref in refs for ref in targets)
                     and len(set(targets)) == 2)
            pair = frozenset(targets)
            _require(pair not in seen_targets)
            seen_targets.add(pair)
    except (AssertionError, KeyError, TypeError, ValueError, AttributeError):
        raise HTTPException(503, 'analysis_saved_artifact_invalid') from None
    return projection


async def read_saved(user_id, *, report_type='latest', report_mode=None, report_id=None,
                     start=None, end=None, limit=60, offset=0, history=False, days=None):
    try:
        owner = str(UUID(user_id))
        rid = str(UUID(report_id)) if report_id is not None else None
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(404, 'analysis_report_unavailable') from None
    result = await _rpc('analysis_observed_read', {'p_user_id': owner,
        'p_report_type': report_type, 'p_mode': report_mode, 'p_id': rid,
        'p_start': start, 'p_end': end, 'p_limit': limit, 'p_offset': offset, 'p_history': history, 'p_days': days})
    try:
        _require(type(result) is dict and set(result) == {'items', 'subscription_tier', 'matched'})
        _require(type(result['matched']) is bool)
        _require(result['subscription_tier'] in {'free', 'plus', 'premium'} and type(result['items']) is list)
        safe_items = []
        keys = {'id', 'report_type', 'report_mode', 'title', 'period_start', 'period_end',
                'generated_at', 'updated_at', 'content_text', 'content_json'}
        for row in result['items']:
            _require(set(row) == keys and type(row['content_text']) is str)
            _require(set(row['content_json']) == {'report_mode', 'watashiMap'})
            _require(row['report_mode'] == row['content_json']['report_mode'])
            _require(row['report_mode'] in {'light', 'standard', 'deep'})
            tier = result['subscription_tier']
            _require(tier == 'premium' or (tier == 'plus' and row['report_mode'] != 'deep') or (
                tier == 'free' and not history and row['report_type'] == 'latest' and row['report_mode'] == 'light'))
            projection = _checked_projection(row['content_json']['watashiMap'], row['id'])
            from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import ObservedSelfStructureMap
            _require(row['content_text'] == ObservedSelfStructureMap._text_from_visual(projection)['text'])
            safe_items.append(row)
        return {'items': safe_items, 'subscription_tier': result['subscription_tier'], 'matched': result['matched']}
    except (AssertionError, KeyError, TypeError, ValueError):
        raise HTTPException(503, 'analysis_saved_artifact_invalid') from None


async def generate_saved(user_id, *, start, end, report_mode, report_type):
    from astor_material_snapshots import _analysis_saved_member, AnalysisSavedSourceError
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisObservedMapRequest, _time
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    owner = str(UUID(user_id))
    args = {'p_user_id': owner, 'p_start': start, 'p_end': end,
            'p_mode': report_mode, 'p_report_type': report_type}
    snapshot = await _rpc('analysis_observed_source_snapshot', args)
    try:
        _require(re.fullmatch(r'analysis-db-v1:[0-9a-f]{64}', snapshot['guard']))
        _require(type(snapshot['members']) is list and len(snapshot['members']) <= 100)
        records = tuple(_analysis_saved_member(dict(s, tier=snapshot['tier'], now=snapshot['now']),
            owner=owner, input_id=s['original']['id'], tier=snapshot['tier'], start=_time(start), end=_time(end))[0]
            for s in snapshot['members'])
        request = AnalysisObservedMapRequest('analysis-saved-' + uuid4().hex, owner, start, end, records)
        outcome = await asyncio.to_thread(MeaningExperienceEngine().generate, request)
        if outcome.artifact is None or outcome.status.value != 'GENERATED':
            raise HTTPException(422, 'analysis_observed_map_unavailable')
        artifact = outcome.artifact
        projection = artifact.safe_projection(authenticated_owner_scope=owner)
        text = artifact.safe_text_projection(authenticated_owner_scope=owner)['text']
        private = private_storage_evidence(artifact)
        _checked_projection(projection, str(UUID(artifact.artifact_id[9:])))
    except HTTPException:
        raise
    except (AnalysisSavedSourceError, AssertionError, ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(422, 'analysis_saved_source_unavailable') from None
    report_id = await _rpc('analysis_observed_commit', dict(args, p_guard=snapshot['guard'],
        p_artifact_id=artifact.artifact_id, p_private_evidence=private, p_projection=projection, p_text=text))
    # Re-read through the same access owner: a concurrent deletion after commit
    # cannot be mistaken for a currently available report.
    result = await read_saved(owner, report_id=report_id, report_mode=report_mode, limit=1)
    if not result['items']:
        raise HTTPException(409, 'analysis_source_changed')
    from response_microcache import invalidate_prefix
    await invalidate_prefix('report_reads:analysis_unread:' + owner)
    await invalidate_prefix('startup_snapshot:' + owner)
    return result['items'][0]


def _period_days(period):
    if not re.fullmatch(r'[1-9][0-9]{0,3}d', str(period)):
        raise HTTPException(400, 'analysis_period_invalid')
    return int(period[:-1])


def _ensure_response(row, *, report_mode, period, refreshed, monthly=False, start=None, end=None):
    return {'status': 'ok', 'refreshed': refreshed,
        'reason': 'saved' if refreshed else ('up_to_date' if row else 'no_visible_content'),
        'report_mode': report_mode, 'period': period,
        'period_start': row['period_start'] if row else start,
        'period_end': row['period_end'] if row else end,
        'generated_at': row['generated_at'] if row else None,
        'latest_generated_at': row['generated_at'] if row else None,
        'title': row['title'] if row else None, 'content_text': row['content_text'] if row else None,
        'meta': row['content_json']['watashiMap'] if row else None,
        'has_visible_content': bool(row), 'skip_reason': None if row else 'analysis_saved_map_unavailable',
        'history_saved': bool(row) if monthly else False}


async def ensure_saved(user_id, *, period, report_mode, ensure=True, force=False, monthly=False):
    days = _period_days(period)
    now = datetime.now(timezone.utc)
    if monthly:
        jst = now.astimezone(timezone(timedelta(hours=9)))
        end_dt = jst.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    else:
        end_dt = now
    start, end = (end_dt - timedelta(days=days)).isoformat(), end_dt.isoformat()
    report_type = 'monthly' if monthly else 'latest'
    result = await read_saved(user_id, report_type=report_type, report_mode=report_mode, limit=1,
        start=start if monthly else None, end=end if monthly else None, days=days)
    row = result['items'][0] if result['items'] else None
    if row and not monthly:
        from cocolon_meaning_experience_engine.cores.analysis.source_adapter import _time
        if _time(row['period_end']) - _time(row['period_start']) != timedelta(days=days):
            row = None
        elif ensure and observed_mode() == 'development' and now - _time(row['period_end']) >= timedelta(days=1):
            row = None
    refreshed = False
    if ensure and (force or row is None) and observed_mode() == 'development':
        row = await generate_saved(user_id, start=start, end=end, report_mode=report_mode, report_type=report_type)
        refreshed = True
    return _ensure_response(row, report_mode=report_mode, period=period, refreshed=refreshed,
                            monthly=monthly, start=start, end=end)


async def saved_status(user_id, *, period='28d'):
    days = _period_days(period)
    result = await read_saved(user_id, limit=1, days=days)
    default_mode = {'free': 'light', 'plus': 'standard', 'premium': 'deep'}[result['subscription_tier']]
    if result['items'] and result['items'][0]['report_mode'] != default_mode:
        result = await read_saved(user_id, report_mode=default_mode, limit=1, days=days)
    row = result['items'][0] if result['items'] else None
    return {'version_key': row['content_json']['watashiMap']['projection_of'] if row else None,
        'generated_at': row['generated_at'] if row else None,
        'saved_report_mode': row['report_mode'] if row else None,
        'has_visible_content': bool(row), 'skip_reason': None if row else 'analysis_saved_map_unavailable'}
