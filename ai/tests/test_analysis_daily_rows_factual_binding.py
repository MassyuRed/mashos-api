"""Direct daily cron reports must be proved by frozen local rows, not candidates.

All rows, users, requests, and writes are synthetic. This is a numerical source /
transport / admission regression; it is not a natural-language quality benchmark.
"""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json

import httpx
import pytest
from fastapi import HTTPException

import api_analysis_reports as reports
from cocolon_text_generation_core.adapters.analysis_composer import evaluate_analysis_composer


OWNER = "synthetic-daily-owner"
EMOTIONS = ["喜び", "悲しみ", "怒り", "不安", "平穏"]
CATEGORIES = ["生活", "仕事", "趣味", "人間関係", "恋愛", "健康", "学習", "価値観", "人生"]


def _target():
    return reports._build_target_period("daily", datetime(2026, 11, 8, 3, tzinfo=timezone.utc))


def _row(identifier, stamp, strength="medium", *, emotions=None):
    selected = EMOTIONS if emotions is None else emotions
    return dict(id=identifier, user_id=OWNER, created_at=stamp, emotions=selected,
        emotion_details=[dict(type=kind, strength=strength) for kind in selected],
        memo="今日は友人の誘いを断りたいとは思わなかった。",
        memo_action="昨日は友人の誘いを断った。", category=CATEGORIES[:],
        is_secret=False, emotion_strength_avg=reports.STRENGTH_SCORE[strength])


def _source(*, previous=True):
    target = _target()
    current = [_row("first", target.period_start_iso, "weak"),
        _row("middle", "2026-11-07T01:00:00.000Z", "medium"),
        _row("last", target.period_end_iso, "strong")]
    before = [_row("before", "2026-11-06T01:00:00.000Z", "strong")] if previous else []
    return reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
        current_rows=current, previous_rows=before)


def _candidate_and_binding(source):
    rendered = reports._render_daily_rows_source(source)
    candidate = {key: deepcopy(value) for key, value in rendered.items() if key != "content_text"}
    candidate["publish"] = dict(status="READY", scope=reports.SNAPSHOT_SCOPE_DEFAULT,
        snapshotType="public", publicSourceHash="a" * 64, generatedForTier="free", secretExcluded=True)
    binding = reports._daily_rows_composer_binding(source, public_source_hash="a" * 64,
        generated_for_tier="free")
    return rendered, candidate, binding


def _evaluate(candidate, binding, *, text=None, legacy=None, materials=None):
    return evaluate_analysis_composer(domain="emotion_structure",
        materials=binding["materials"] if materials is None else materials,
        report_text=binding["expected_text"] if text is None else text,
        content_json=candidate, output_payload=candidate,
        material_fields=["counts", "timestamp", "emotion_details", "strength"],
        snapshot_binding=binding,
        snapshot_legacy_text=binding["expected_legacy_text"] if legacy is None else legacy)


def test_frozen_rows_keep_original_fields_owner_period_and_all_strengths_without_candidate_prose():
    source = _source()
    raw, target, facts = reports._daily_rows_factual_parts(source)
    assert raw["profile"] == "analysis.daily.rows.facts.v1" and raw["owner"] == OWNER
    assert "snapshot" not in raw and "snapshot_id" not in raw
    assert raw["current_rows"][0]["memo"] != raw["current_rows"][0]["memo_action"]
    assert raw["current_rows"][0]["category"] == CATEGORIES
    assert raw["period"]["periodStartIso"] == target.period_start_iso
    assert facts["current"]["input_count"] == 3
    assert facts["previous"]["input_count"] == 1
    assert facts["current"]["metrics"]["totals"] == dict.fromkeys(reports.EMOTION_KEYS, 6)
    assert facts["current"]["selected_strength_counts"] == {
        key: dict(weak=1, medium=1, strong=1) for key in reports.EMOTION_KEYS}
    assert facts["comparison"] == dict(state="OBSERVED", current_weighted_total=30,
        previous_weighted_total=15, difference=15)
    rendered, candidate, binding = _candidate_and_binding(source)
    assert all(heading in rendered["content_text"] for heading in (
        "【昨日、見えていたこと】", "【気持ちの変化】", "【このレポートについて】"))
    assert "分析対象の感情記録は3件" in rendered["content_text"]
    assert "前日分の分析対象の感情記録は1件" in rendered["content_text"]
    assert "公開" not in rendered["content_text"]
    assert "前日15、対象期間30" in rendered["content_text"]
    assert "喜び・悲しみ・不安・怒り・平穏" in rendered["content_text"]
    material_text = json.dumps(binding["materials"], ensure_ascii=False)
    assert raw["current_rows"][0]["memo"] not in material_text
    assert raw["current_rows"][0]["memo_action"] not in material_text
    assert rendered["content_text"] not in material_text
    assert binding["source_bytes"] == source
    assert binding["source_digest"] == hashlib.sha256(source.encode()).hexdigest()
    result = _evaluate(candidate, binding)
    assert result.passed, result.rejection_reasons
    assert not any("candidate-sentence" in identifier for identifier in result.candidate.used_phrase_unit_ids)
    public_meta = result.as_meta()
    assert public_meta["meta"]["runtime_meta"]["snapshot_source"] == dict(
        profile=reports.DAILY_ROWS_FACT_PROFILE, source_digest=binding["source_digest"], matched=True)
    def check_private(value):
        if isinstance(value, dict):
            assert "source_bytes" not in value
            for item in value.values(): check_private(item)
        elif isinstance(value, (list, tuple)):
            for item in value: check_private(item)
        elif isinstance(value, str):
            assert source not in value
            assert raw["current_rows"][0]["memo"] not in value
            assert raw["current_rows"][0]["memo_action"] not in value
    check_private(public_meta)


def test_no_previous_rows_is_unknown_and_never_claims_stable_or_previous_day_similarity():
    source = _source(previous=False)
    _, _, facts = reports._daily_rows_factual_parts(source)
    assert facts["comparison"]["state"] == "UNKNOWN"
    assert facts["comparison"]["difference"] is None
    rendered, candidate, binding = _candidate_and_binding(source)
    assert "比較できません" in rendered["content_text"]
    assert "前日と近い" not in rendered["content_text"] and "stable" not in rendered["content_text"]
    assert _evaluate(candidate, binding).passed


def test_freeze_is_order_independent_and_keeps_bytes_after_caller_mutation():
    target = _target()
    rows = [_row("last", target.period_end_iso), _row("first", target.period_start_iso)]
    frozen = reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
        current_rows=rows, previous_rows=[])
    assert frozen == reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
        current_rows=list(reversed(rows)), previous_rows=[])
    rows[0]["memo_action"] = "変更した行動欄です。"
    assert "変更した行動欄" not in frozen
    updated = reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
        current_rows=rows, previous_rows=[])
    assert hashlib.sha256(updated.encode()).hexdigest() != hashlib.sha256(frozen.encode()).hexdigest()


@pytest.mark.parametrize("change", ["owner", "missing_field", "duplicate_id", "cross_period_id", "before", "after", "secret", "self_only", "target"])
def test_source_rejects_wrong_owner_shape_period_secret_or_nonordinary_input(change):
    target = _target()
    row = _row("row", target.period_start_iso)
    rows = [row]
    previous = []
    if change == "owner": row["user_id"] = "other-owner"
    elif change == "missing_field": row.pop("memo_action")
    elif change == "duplicate_id": rows.append(deepcopy(row))
    elif change == "cross_period_id": previous.append(_row("row", "2026-11-06T01:00:00.000Z"))
    elif change == "before": row["created_at"] = "2026-11-06T14:59:59.999Z"
    elif change == "after": row["created_at"] = "2026-11-07T15:00:00.000Z"
    elif change == "secret": row["is_secret"] = True
    elif change == "self_only": row.update(emotions=["自己理解"], emotion_details=[])
    elif change == "target": target = replace(target, title="誤った対象期間")
    with pytest.raises(HTTPException) as error:
        reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
            current_rows=rows, previous_rows=previous)
    assert error.value.status_code == 409


@pytest.mark.parametrize("change", ["owner", "period"])
def test_previous_rows_have_their_own_owner_and_period_boundary(change):
    target = _target()
    previous = _row("before", "2026-11-06T01:00:00.000Z")
    if change == "owner": previous["user_id"] = "other-owner"
    else: previous["created_at"] = target.period_start_iso
    with pytest.raises(HTTPException) as error:
        reports._freeze_daily_rows_report_source(user_id=OWNER, target=target,
            current_rows=[_row("now", target.period_start_iso)], previous_rows=[previous])
    assert error.value.status_code == 409


@pytest.mark.parametrize("change", ["text", "legacy", "metrics", "standard", "weather", "extra_deep", "publish", "material", "digest"])
def test_composer_rejects_candidate_and_audit_mutation_against_independent_source(change):
    _, candidate, binding = _candidate_and_binding(_source())
    kwargs = {}
    if change == "text": kwargs["text"] = binding["expected_text"] + "\nあなたは不安の多い人です。"
    elif change == "legacy": kwargs["legacy"] = binding["expected_legacy_text"] + "\n根拠のない別本文です。"
    elif change == "metrics": candidate["metrics"]["totalAll"] += 1
    elif change == "standard": candidate["standardReport"]["contentText"] += "\n架空の分析です。"
    elif change == "weather": candidate["kokoroWeather"]["summary"]["weather_label"] = "架空の天気"
    elif change == "extra_deep": candidate["deepReport"] = dict(contentText="本人はこういう人です。")
    elif change == "publish": candidate["publish"]["publicSourceHash"] = "b" * 64
    elif change == "material": kwargs["materials"] = binding["materials"][:-1]
    elif change == "digest": binding["source_digest"] = "f" * 64
    evaluation = _evaluate(candidate, binding, **kwargs)
    assert not evaluation.passed
    assert "analysis_snapshot_source_mismatch" in evaluation.rejection_reasons


@pytest.mark.asyncio
async def test_http_fetch_reads_all_capped_pages_with_owner_period_and_both_original_fields(monkeypatch):
    target = _target()
    rows = [_row(f"row-{index:04d}", target.period_start_iso) for index in range(1003)]
    captured = []
    def handler(request):
        captured.append(request)
        assert request.url.params.get_list("created_at") == [
            "gte." + target.period_start_iso, "lte." + target.period_end_iso]
        assert request.url.params["user_id"] == "eq." + OWNER
        assert request.url.params["is_secret"] == "eq.false"
        assert request.url.params["order"] == "created_at.asc,id.asc"
        assert set(request.url.params["select"].split(",")) == {
            "id", "user_id", "created_at", "emotions", "emotion_details", "memo", "memo_action",
            "category", "is_secret", "emotion_strength_avg"}
        offset = int(request.url.params["offset"])
        return httpx.Response(206, json=rows[offset:offset + 137])
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://synthetic.invalid") as client:
        async def get(path, *, params, **kwargs):
            return await client.get(path, params=params)
        monkeypatch.setattr(reports, "_sb_get", get)
        actual = await reports._fetch_emotion_rows(OWNER, target.period_start_iso, target.period_end_iso)
    assert actual == rows and len(captured) == 9
    assert [int(req.url.params["offset"]) for req in captured] == [0,137,274,411,548,685,822,959,1003]


@pytest.mark.parametrize("bad", ["foreign", "duplicate"])
@pytest.mark.asyncio
async def test_http_fetch_rejects_mixed_owner_or_ignored_offset(monkeypatch, bad):
    row = _row("row", _target().period_start_iso)
    if bad == "foreign": row["user_id"] = "other-owner"
    async def get(*args, **kwargs): return httpx.Response(200, json=[row])
    monkeypatch.setattr(reports, "_sb_get", get)
    with pytest.raises(HTTPException) as error:
        await reports._fetch_emotion_rows(OWNER, _target().period_start_iso, _target().period_end_iso)
    assert error.value.status_code == 502


@pytest.mark.parametrize("bad", ["json", "non_list", "non_dict", "missing_id", "http"])
@pytest.mark.asyncio
async def test_http_fetch_never_returns_partial_rows_after_an_invalid_later_page(monkeypatch, bad):
    first = _row("first", _target().period_start_iso)
    async def get(path, *, params, **kwargs):
        if dict(params)["offset"] == "0": return httpx.Response(200, json=[first])
        if bad == "json": return httpx.Response(200, content=b"{")
        if bad == "http": return httpx.Response(503, json={"message": "synthetic unavailable"})
        payload = {} if bad == "non_list" else [None] if bad == "non_dict" else [dict(user_id=OWNER)]
        return httpx.Response(200, json=payload)
    monkeypatch.setattr(reports, "_sb_get", get)
    with pytest.raises(HTTPException) as error:
        await reports._fetch_emotion_rows(OWNER, _target().period_start_iso, _target().period_end_iso)
    assert error.value.status_code == 502


@pytest.mark.parametrize("gate_case", ["valid", "mutated", "validity_unavailable", "composer_unavailable"])
@pytest.mark.asyncio
async def test_actual_daily_generation_uses_current_and_previous_rows_and_passes_real_gate(monkeypatch, gate_case):
    from subscription import SubscriptionTier
    import astor_job_queue
    source = json.loads(_source())
    target, calls, saved = _target(), [], []
    async def fetch(owner, start, end):
        calls.append((owner, start, end))
        return deepcopy(source["current_rows"] if start == target.period_start_iso else source["previous_rows"])
    async def tier(*args, **kwargs): return SubscriptionTier.FREE
    async def public_hash(*args, **kwargs): return "a" * 64
    async def upsert(payload): saved.append(deepcopy(payload)); return "daily-report"
    async def enqueue(**kwargs): return None
    monkeypatch.setattr(reports, "_fetch_emotion_rows", fetch)
    monkeypatch.setattr(reports, "get_subscription_tier_for_user", tier)
    monkeypatch.setattr(reports, "_fetch_latest_snapshot_hash", public_hash)
    monkeypatch.setattr(reports, "_upsert_report", upsert)
    monkeypatch.setattr(astor_job_queue, "enqueue_job", enqueue)
    if gate_case == "mutated":
        real_attach = reports._attach_analysis_report_validity_meta_if_available
        def mutate_then_attach(content, **kwargs):
            content["metrics"]["totalAll"] = 999
            return real_attach(content, **kwargs)
        monkeypatch.setattr(reports, "_attach_analysis_report_validity_meta_if_available", mutate_then_attach)
    elif gate_case == "validity_unavailable":
        monkeypatch.setattr(reports, "evaluate_analysis_report_validity", None)
    elif gate_case == "composer_unavailable":
        monkeypatch.setattr(reports, "evaluate_analysis_composer", None)
    # Anchors are an independent later projection, not this report's admission.
    monkeypatch.setattr(reports, "attach_emlis_context_anchors", lambda content, anchors: content)
    monkeypatch.setattr(reports, "build_emotion_report_emlis_context_anchors", lambda **kwargs: {})
    text, content, _, meta = await reports._generate_and_save(OWNER, target, include_astor=False)
    if gate_case != "valid":
        assert meta["status"] == "skipped" and meta["skip_reason"] == "analysis_report_text_generation_rejected"
        assert saved == [] and text == ""
        return
    assert meta == dict(status="generated", report_id="daily-report"), content.get("reportValidity")
    assert len(saved) == 1 and saved[0]["user_id"] == OWNER
    assert saved[0]["content_text"] == text == content["standardReport"]["contentText"]
    assert content["reportValidity"]["analysis_composer_passed"] is True
    assert content["publish"]["publicSourceHash"] == "a" * 64
    assert calls == [(OWNER, target.period_start_iso, target.period_end_iso),
        (OWNER, source["period"]["previousPeriodStartIso"], source["period"]["previousPeriodEndIso"])]
    assert content["metrics"]["totalAll"] == 30
    assert "前日15、対象期間30" in text
    assert "snapshot_id" not in json.dumps(saved[0], ensure_ascii=False)
