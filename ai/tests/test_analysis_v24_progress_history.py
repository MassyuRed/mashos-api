"""Long v24 histories advance on validated phases; all prior entry points stay finite."""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import analysis_cumulative_service as cumulative
import analysis_model_source as sources
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core


def source():
    return sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://local.invalid/chat/completions',
        model=sources.SEMANTIC_OCCURRENCE_V24_MODEL, api_key='synthetic-only',
        semantic_prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)


@pytest.mark.parametrize(('version', 'members', 'fits', 'expected'), [
    (24, 12, False, True), (24, 2, False, True), (24, 1, False, False),
    (24, 12, True, False), (23, 12, False, False),
])
def test_only_split_v24_histories(monkeypatch, version, members, fits, expected):
    profile = getattr(core, f'SEMANTIC_MAP_OCCURRENCE_V{version}_PROFILE')
    parent = SimpleNamespace(prompt_version=profile, frozen=SimpleNamespace(members=range(members)))
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits', lambda _: fits)
    assert asyncio.run(cumulative._v24_history_uses_per_phase(source(), parent)) is expected
    assert not asyncio.run(cumulative._v24_history_uses_per_phase(object(), parent))


def test_progress_can_span_an_hour_without_reusing_any_response(monkeypatch):
    parent = SimpleNamespace(prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
        frozen=SimpleNamespace(members=range(12)))
    leaves = tuple(SimpleNamespace(kind='LEAF', index=i) for i in range(12))
    merge = SimpleNamespace(kind='MERGE', prompt_version=parent.prompt_version)
    seen, elapsed = [], [0.0]
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits', lambda p: p is not parent)
    monkeypatch.setattr(cumulative, 'prepare_semantic_history_batches', lambda _: leaves)
    monkeypatch.setattr(core, 'prepare_semantic_merge', lambda *a: merge)
    monkeypatch.setattr(maps, 'build_semantic_history_stage', lambda *a: SimpleNamespace(artifact='map', coverage='complete'))
    monkeypatch.setattr(cumulative, '_require_model_write_active', lambda: None)

    async def acquire(provider, stage, *, per_phase=False, merge_deadline=None):
        assert per_phase and merge_deadline is None
        # Three accepted phases at 105 seconds each, with no real waiting or model.
        elapsed[0] += 315.0
        seen.append(stage)
        await asyncio.sleep(0)
        return 'accepted'

    async def scenario():
        loop = asyncio.get_running_loop()
        real_time = loop.time
        with monkeypatch.context() as clock:
            clock.setattr(loop, 'time', lambda: real_time() + elapsed[0])
            return await cumulative._semantic_history_map(source(), parent)

    monkeypatch.setattr(cumulative, '_model_response', acquire)
    assert asyncio.run(scenario()) == ('map', 'complete')
    assert seen == [*leaves, merge] and elapsed[0] == 4095


def test_phase_policy_stalled_preparation_never_enters_model(monkeypatch):
    parent = SimpleNamespace(prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
        frozen=SimpleNamespace(members=range(2)))
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits', lambda p: False)
    monkeypatch.setattr(sources, 'SEMANTIC_REQUEST_TIMEOUT_SECONDS', 0.005)
    calls = []
    async def blocked(function, *args):
        await asyncio.Event().wait()
    async def acquire(*a, **kw):
        calls.append(1)
    monkeypatch.setattr(asyncio, 'to_thread', blocked)
    monkeypatch.setattr(cumulative, '_model_response', acquire)
    with pytest.raises(HTTPException) as error:
        asyncio.run(cumulative._semantic_history_map(source(), parent))
    assert error.value.status_code == 504 and not calls


@pytest.mark.parametrize('disposition', ['claim_changed', 'claim_unknown', 'cancelled'])
def test_unconfirmed_worker_ownership_cannot_enter_sql_commit(monkeypatch, disposition):
    from analysis_job_progress import MapJobClaimChanged, MapJobClaimUnavailable, map_job_progress
    from test_analysis_cumulative import OWNER, source_snapshot

    snapshot = source_snapshot(2)
    parent = SimpleNamespace(prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE,
        frozen=SimpleNamespace(members=range(2)))
    recorded = []
    artifact = SimpleNamespace(artifact_id='artifact:' + '1' * 32,
        safe_projection=lambda **owner: {}, safe_text_projection=lambda **owner: {'text': 'synthetic'},
        private_evidence=lambda: {})
    async def read(*args, **kwargs):
        return {'items': []}
    async def rpc(name, payload):
        recorded.append(name)
        assert name == 'analysis_cumulative_source_snapshot'
        return snapshot
    async def finished(model, prepared, *, per_phase):
        assert per_phase
        return artifact, {}
    async def check_latest_claim():
        recorded.append('check_owner')
        if disposition == 'cancelled':
            asyncio.current_task().cancel()
        else:
            raise MapJobClaimChanged() if disposition == 'claim_changed' else MapJobClaimUnavailable()

    monkeypatch.setattr(cumulative, 'observed_mode', lambda: 'development')
    monkeypatch.setattr(cumulative, 'read_maps', read)
    monkeypatch.setattr(cumulative, '_rpc', rpc)
    monkeypatch.setattr(cumulative, '_semantic_history_map', finished)
    monkeypatch.setattr(cumulative, '_checked_projection', lambda *args: None)
    monkeypatch.setattr(sources, 'semantic_analysis_input_fits', lambda p: False)
    monkeypatch.setattr(maps, 'prepare_semantic_map', lambda *a, **kw: parent)
    expected = {'claim_changed': MapJobClaimChanged, 'claim_unknown': MapJobClaimUnavailable,
                'cancelled': asyncio.CancelledError}[disposition]
    with map_job_progress(None, check_latest_claim), pytest.raises(expected):
        asyncio.run(cumulative.ensure_map(OWNER, model_source=source()))
    assert recorded == ['analysis_cumulative_source_snapshot', 'check_owner']
