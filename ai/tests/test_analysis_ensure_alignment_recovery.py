"""Exercise the ordinary ensure route and existing queue/worker with fake storage.

Only coherent legacy derived rows lacking the alignment key can request repair.
The real numeric producers, queue enqueue implementation, HTTP route, and report
admission run; no external database, model, deployment, or saved history is used.
"""
import asyncio
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api_analysis_reports as reports
import astor_job_queue as queue
import astor_material_snapshots as materials
from subscription import SubscriptionTier
from test_analysis_snapshot_factual_binding import OWNER, fixture


class _Drained(BaseException):
    pass


def _setup(monkeypatch, kind="weekly", *, enabled=True, deep_state="missing"):
    scope, rows, snapshot, standard, deep = fixture(monkeypatch, kind)
    import astor_worker as worker
    standard["payload"].pop("source_alignment")
    if deep_state == "missing":
        deep["payload"].pop("source_alignment")
    elif deep_state == "absent":
        deep = None
    derived = dict(standard=standard, deep=deep)
    jobs, events, writes, produced, snapshot_attempts = {}, [], [], [], []
    history = {"old-period": {"id": "history-report", "content_text": "保存当時の本文",
        "content_json": {"standardReport": {"contentText": "保存当時の本文"}}}}
    old_history = deepcopy(history)
    saved = {}
    info = materials._parse_emotion_period_scope(scope)
    now = info["period_end_utc"] + timedelta(milliseconds=1)
    target = reports._build_target_period(kind, now)
    assert target.period_start_iso == info["period_start_iso"]

    async def user(*args, **kwargs): return OWNER
    async def tier(*args, **kwargs): return SubscriptionTier.PREMIUM
    async def get_snapshot(*args, **kwargs): return deepcopy(snapshot)
    async def get_derived(*args, **kwargs):
        row = derived[kwargs["analysis_stage"]]
        return deepcopy(row) if row is not None and row["snapshot_id"] == kwargs["snapshot_id"] else None
    async def exists(*args, **kwargs): return saved.get("id")
    async def save_report(payload):
        # This storage seam rejects any attempted write outside the exact
        # current owner/period, rather than treating a detached history dict
        # as evidence about an actual database history reader.
        assert payload["user_id"] == OWNER
        assert payload["report_type"] == kind
        assert payload["period_start"] == target.period_start_iso
        assert payload["period_end"] == target.period_end_iso
        writes.append(deepcopy(payload))
        saved.update(deepcopy(payload), id="current-report")
        return "current-report"
    async def no_op(*args, **kwargs): return None
    monkeypatch.setattr(reports, "_resolve_user_id_from_token", user)
    monkeypatch.setattr(reports, "get_subscription_tier_for_user", tier)
    monkeypatch.setattr(reports, "_fetch_latest_snapshot_row", get_snapshot)
    monkeypatch.setattr(reports, "_fetch_analysis_result", get_derived)
    monkeypatch.setattr(reports, "_report_exists", exists)
    monkeypatch.setattr(reports, "_upsert_report", save_report)
    monkeypatch.setattr(reports, "try_acquire_lock", None)
    monkeypatch.setattr(reports, "MYWEB_LOCK_WAIT_SECONDS", 0)
    monkeypatch.setattr(reports, "invalidate_prefix", no_op)
    monkeypatch.setattr(reports, "attach_emlis_context_anchors", lambda body, anchors: body)

    # Keep enqueue_job itself real, including its done -> queued semantics.
    async def patch_job(path, *, json, params, **kwargs):
        assert path == "/rest/v1/" + queue.JOBS_TABLE
        key = params["job_key"][3:]
        job = jobs.get(key)
        wanted = params["status"]
        match = job is not None and ((wanted == "eq.running" and job["status"] == "running")
            or (wanted == "neq.running" and job["status"] != "running"))
        if match:
            job.update(deepcopy(json))
            events.append(deepcopy(job))
        return httpx.Response(200, json=[job] if match else [])
    async def post_job(path, *, json, params, **kwargs):
        assert params == {"on_conflict": "job_key"}
        jobs[json["job_key"]] = dict(deepcopy(json), status="queued", attempts=0)
        events.append(deepcopy(jobs[json["job_key"]]))
        return httpx.Response(201, json=[])
    monkeypatch.setattr(queue, "ensure_supabase_config", lambda: None)
    monkeypatch.setattr(queue, "sb_patch", patch_job)
    monkeypatch.setattr(queue, "sb_post", post_job)
    monkeypatch.setattr(worker, "enqueue_job", queue.enqueue_job)
    monkeypatch.setattr(materials, "enqueue_job", queue.enqueue_job)

    async def fetch_rows(owner, *, start_iso, **kwargs):
        assert owner == OWNER
        return deepcopy(rows if start_iso == info["period_start_iso"] else [])
    async def snapshot_meta(*args, **kwargs): return deepcopy(snapshot)
    async def insert_snapshot(**kwargs):
        snapshot_attempts.append(deepcopy(kwargs))
        if kwargs["snapshot_type"] == "public":
            assert kwargs["source_hash"] == snapshot["source_hash"]
        # Existing identical snapshot is immutable; its old row is retained.
        return False
    async def generate_snapshots(*, user_id, scope, trigger):
        return await materials._generate_and_store_emotion_period_snapshots(
            user_id=user_id, scope=scope, trigger=trigger)
    async def save_derived(*, row):
        stage = row["analysis_stage"]
        produced.append(deepcopy(row))
        identifier = (derived[stage] or {}).get("id", "synthetic-derived-" + stage)
        derived[stage] = dict(deepcopy(row), id=identifier)
        return True
    monkeypatch.setattr(materials, "fetch_emotions_in_range", fetch_rows)
    monkeypatch.setattr(materials, "_fetch_latest_snapshot_meta", snapshot_meta)
    monkeypatch.setattr(materials, "_insert_snapshot_row", insert_snapshot)
    monkeypatch.setattr(worker, "generate_and_store_material_snapshots", generate_snapshots)
    monkeypatch.setattr(worker, "_fetch_latest_public_snapshot_row", get_snapshot)
    monkeypatch.setattr(worker, "fetch_emotions_in_range", fetch_rows)
    monkeypatch.setattr(worker, "_upsert_analysis_result", save_derived)
    monkeypatch.setattr(worker, "EMOTION_REPORT_V2_ENABLED", enabled)
    async def acquire(**kwargs): return SimpleNamespace(acquired=True)
    monkeypatch.setattr(worker, "try_acquire_lock", acquire)
    monkeypatch.setattr(worker, "release_lock", no_op)
    monkeypatch.setattr(worker, "_run_worker_maintenance", no_op)
    allowed = {"snapshot_generate_v1", "analyze_emotion_structure_standard_v1", "analyze_emotion_structure_deep_v1"}
    async def next_job(**kwargs):
        for job in jobs.values():
            if job["status"] == "queued" and job["job_type"] in allowed:
                return SimpleNamespace(**deepcopy(job))
        raise _Drained()
    async def claim(*, job_key, **kwargs):
        jobs[job_key]["status"] = "running"
        return SimpleNamespace(**deepcopy(jobs[job_key]))
    async def done(*, job_key, **kwargs):
        jobs[job_key]["status"] = "done"
        return True
    async def unexpected_retry(**kwargs): raise AssertionError("Synthetic worker unexpectedly retried: " + repr(kwargs))
    monkeypatch.setattr(worker, "fetch_next_queued_job", next_job)
    monkeypatch.setattr(worker, "claim_job", claim)
    monkeypatch.setattr(worker, "mark_done_if_unchanged", done)
    monkeypatch.setattr(worker, "requeue", unexpected_retry)
    monkeypatch.setattr(worker, "mark_failed", unexpected_retry)
    app = FastAPI()
    reports.register_analysis_report_routes(app)
    return SimpleNamespace(scope=scope, kind=kind, snapshot=snapshot, rows=rows, derived=derived, jobs=jobs,
        events=events, writes=writes, produced=produced, snapshot_attempts=snapshot_attempts,
        history=history, old_history=old_history, saved=saved, worker=worker, client=TestClient(app),
        body=dict(types=[kind], now_iso=now.isoformat(), include_astor=True), target=target)


def _ensure(state, *, force=False):
    response = state.client.post("/analysis/reports/ensure", headers={"Authorization": "Bearer synthetic"},
        json=dict(state.body, force=force))
    assert response.status_code == 200
    return response.json()["results"][0]


def _drain_real_producers(state, *, stages=frozenset({"standard", "deep"})):
    with pytest.raises(_Drained):
        asyncio.run(state.worker._worker_loop())
    assert {row["analysis_stage"] for row in state.produced} == stages
    assert all(row["payload"]["source_alignment"]["source_hash"] == state.snapshot["source_hash"]
        and row["snapshot_id"] == state.snapshot["id"] for row in state.produced)


@pytest.mark.parametrize("kind", ["daily", "weekly", "monthly"])
@pytest.mark.parametrize("enabled", [False, True])
def test_normal_ensure_recovers_only_missing_alignment_through_existing_queue_and_real_producers(monkeypatch, kind, enabled):
    state = _setup(monkeypatch, kind, enabled=enabled)
    key = f"snapshot_generate_v1:{OWNER}:{state.scope}"
    # An already completed job with the same key must be made runnable again.
    state.jobs[key] = dict(job_key=key, job_type="snapshot_generate_v1", user_id=OWNER,
        payload={}, priority=12, attempts=0, status="done")
    before_snapshot = deepcopy(state.snapshot)
    result = _ensure(state)
    assert result["status"] == "skipped" and result["skip_reason"] == "analysis_snapshot_alignment_pending"
    assert result["report_id"] is None and state.writes == []
    job = state.jobs[key]
    assert job["status"] == "queued" and job["priority"] == 12
    assert job["payload"]["scope"] == state.scope
    proof = dict(snapshot_id=state.snapshot["id"], source_hash=state.snapshot["source_hash"])
    assert job["payload"]["recover_deep_alignment"] == proof
    delay = reports._parse_iso_utc(job["run_after"]) - reports._parse_iso_utc(job["updated_at"])
    assert delay == timedelta(seconds=10)
    assert state.history == state.old_history and state.snapshot == before_snapshot
    _drain_real_producers(state)
    assert len(state.snapshot_attempts) == 2 and state.snapshot == before_snapshot
    expected_standard_key = f"analysis_emotion_structure_standard:{OWNER}:{state.scope}:{state.snapshot['source_hash']}"
    expected_deep_key = f"analysis_emotion_structure_deep:{OWNER}:{state.scope}:{state.snapshot['source_hash']}"
    assert state.jobs[expected_standard_key]["status"] == "done"
    assert state.jobs[expected_deep_key]["status"] == "done"
    assert state.jobs[expected_standard_key]["payload"]["recover_deep_alignment"] == proof
    automatic = [job for job in state.jobs.values() if job["job_type"] == "generate_emotion_report_v2"]
    assert bool(automatic) is enabled
    assert state.writes == []
    refreshed = _ensure(state)
    assert refreshed["status"] == "generated" and refreshed["report_id"] == "current-report", refreshed
    assert len(state.writes) == 1 and state.writes[0]["user_id"] == OWNER
    assert state.writes[0]["period_start"] == state.target.period_start_iso
    assert state.writes[0]["content_json"]["reportValidity"]["save_allowed"] is True
    assert state.history == state.old_history and state.snapshot == before_snapshot


@pytest.mark.parametrize("deep_state", ["absent", "aligned"])
def test_flag_false_standard_only_repair_never_enables_new_deep_or_automatic_reports(monkeypatch, deep_state):
    state = _setup(monkeypatch, enabled=False, deep_state=deep_state)
    before_deep = deepcopy(state.derived["deep"])
    pending = _ensure(state)
    assert pending["skip_reason"] == "analysis_snapshot_alignment_pending"
    snapshot_job = state.jobs[f"snapshot_generate_v1:{OWNER}:{state.scope}"]
    assert snapshot_job["payload"].get("recover_deep_alignment") is None
    _drain_real_producers(state, stages={"standard"})
    assert state.derived["deep"] == before_deep
    assert not any(job["job_type"] in {"analyze_emotion_structure_deep_v1", "generate_emotion_report_v2"}
        for job in state.jobs.values())
    assert state.writes == [] and state.history == state.old_history
    complete = _ensure(state)
    assert complete["status"] == "generated" and len(state.writes) == 1
    assert bool(state.writes[0]["content_json"].get("deepReport")) is (deep_state == "aligned")
    assert state.history == state.old_history


@pytest.mark.parametrize("bad", ["none", "absent", "extra_key", "wrong_id", "wrong_hash"])
def test_flag_false_repair_requires_exact_existing_deep_proof(monkeypatch, bad):
    state = _setup(monkeypatch, enabled=False)
    assert _ensure(state)["skip_reason"] == "analysis_snapshot_alignment_pending"
    payload = state.jobs[f"snapshot_generate_v1:{OWNER}:{state.scope}"]["payload"]
    proof = payload["recover_deep_alignment"]
    if bad == "none": payload["recover_deep_alignment"] = None
    elif bad == "absent": payload.pop("recover_deep_alignment")
    elif bad == "extra_key": proof["unproved_stage"] = "deep"
    elif bad == "wrong_id": proof["snapshot_id"] = "other-snapshot"
    else: proof["source_hash"] = "f" * 64
    _drain_real_producers(state, stages={"standard"})
    assert not any(job["job_type"] in {"analyze_emotion_structure_deep_v1", "generate_emotion_report_v2"}
        for job in state.jobs.values())
    assert "source_alignment" not in state.derived["deep"]["payload"]
    assert state.writes == [] and state.history == state.old_history


@pytest.mark.parametrize("changed", ["snapshot_id", "source_hash"])
def test_flag_false_repair_proof_does_not_follow_a_changed_snapshot_source(monkeypatch, changed):
    state = _setup(monkeypatch, enabled=False)
    assert _ensure(state)["skip_reason"] == "analysis_snapshot_alignment_pending"
    old_proof = deepcopy(state.jobs[f"snapshot_generate_v1:{OWNER}:{state.scope}"]["payload"]["recover_deep_alignment"])
    if changed == "snapshot_id":
        state.snapshot["id"] = "00000000-0000-0000-0000-000000000999"
    else:
        state.rows[0]["memo_action"] = "私は資料を追加していません。"
        updated = materials.compute_source_hash_from_emotion_meta(user_id=OWNER, scope=state.scope,
            snapshot_type="public", meta_rows=state.rows)
        assert updated != old_proof["source_hash"]
        state.snapshot["source_hash"] = updated
        state.snapshot["payload"]["source_hash"] = updated
    _drain_real_producers(state, stages={"standard"})
    assert not any(job["job_type"] in {"analyze_emotion_structure_deep_v1", "generate_emotion_report_v2"}
        for job in state.jobs.values())
    assert state.writes == [] and state.history == state.old_history


@pytest.mark.parametrize("bad", ["owner", "hash", "period", "alignment_none", "alignment_wrong"])
def test_other_mismatches_do_not_enqueue_or_overwrite_history(monkeypatch, bad):
    state = _setup(monkeypatch)
    # Standard is missing alignment; a different deep-stage error takes priority.
    deep = state.derived["deep"]
    if bad == "owner": deep["target_user_id"] = "other-owner"
    elif bad == "hash": deep["source_hash"] = "f" * 64
    elif bad == "period": deep["payload"]["period"]["start_iso"] = "2000-01-01T00:00:00Z"
    elif bad == "alignment_none": deep["payload"]["source_alignment"] = None
    else: deep["payload"]["source_alignment"] = {}
    result = _ensure(state)
    assert result["status"] == "error" and result["error"] == "analysis_snapshot_source_mismatch"
    assert state.jobs == {} and state.writes == [] and state.history == state.old_history


def test_existing_report_and_explicit_force_keep_their_original_scope(monkeypatch):
    state = _setup(monkeypatch)
    state.saved.update(id="existing-current", content_text="既存の保存本文")
    original = deepcopy(state.saved)
    result = _ensure(state)
    assert result["status"] == "exists" and result["report_id"] == "existing-current"
    assert state.jobs == {} and state.saved == original
    pending = _ensure(state, force=True)
    assert pending["skip_reason"] == "analysis_snapshot_alignment_pending"
    assert state.saved == original and state.writes == []
    _drain_real_producers(state)
    generated = _ensure(state, force=True)
    assert generated["status"] == "generated" and len(state.writes) == 1
    assert state.history == state.old_history


def test_failed_enqueue_is_an_error_and_never_claims_pending_work(monkeypatch):
    state = _setup(monkeypatch)
    async def broken(*args, **kwargs): raise RuntimeError("synthetic queue unavailable")
    monkeypatch.setattr(queue, "sb_patch", broken)
    result = _ensure(state)
    assert result["status"] == "error" and result["error"] == "analysis_snapshot_alignment_enqueue_failed"
    assert state.jobs == {} and state.writes == [] and state.history == state.old_history
