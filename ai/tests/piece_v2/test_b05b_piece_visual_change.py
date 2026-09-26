"""Visual-only changes to a prepared Piece; not preview storage or HTTP.

Unit cases use synthetic control lineage and the real CMEE/B9 authors.
SQL cases use the existing isolated Q2 database and saved Emlis state.
No live account, database, public route or native renderer is exercised.
"""
import asyncio
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
import api_account_visibility
import emlis_thread_store
from emlis_thread_service import EmlisThreadService
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
from piece_v2_source_adapter import PieceSavedOriginal, PieceSavedHandoff, PieceSavedSourceAdapter
import piece_v2_preview_service as preview

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
SOURCE_FIELDS = ('source_input_id', 'source_input_version', 'source_input_bundle_commitment')
OBSERVATION_FIELDS = ('emlis_observation_stage', 'emlis_observation_result_identity',
                      'question_need_decision_identity', 'supplemental_answer_identity')
UNCHANGED = ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
             'format_type', 'eligible_formats', 'visibility_scope',
             'api_contract_version', 'piece_contract_version')
run = asyncio.run


def choice(theme=None, ratio=None, branding=None):
    return dict(theme_id=theme, aspect_ratio=ratio, branding_mode=branding)


def request(handoff, requested_format=None):
    lineage = handoff.lineage_payload()
    source = {k: lineage['source_input'][k] for k in SOURCE_FIELDS}
    source.update({k: lineage['observation'][k] for k in OBSERVATION_FIELDS})
    return dict(source_ref=source, requested_format=requested_format, visual_selection=choice())


class Adapter:
    """Synthetic control seam only; not a persisted or authenticated record."""
    def __init__(self, tier='premium'):
        row = dict(id=INPUT, created_at='2026-09-26T00:00:00+00:00',
                   memo='私が大切にしたいのは、家族と落ち着いてゆっくり話す時間です。',
                   memo_action='', category=['生活'], emotions=['自己理解'],
                   emotion_details=[dict(type='自己理解', strength='medium')])
        bundle = normalize_emlis_current_input(row)
        original = PieceSavedOriginal(OWNER, INPUT, 'emlis.current_input_bundle.v1',
            'sha256:' + artifact_sha256(bundle), 'sha256:' + canonical_sha256_hex(row),
            row['created_at'], tier, canonical_json_bytes(row), canonical_json_bytes(bundle))
        lineage = dict(source_input=dict(source_input_id=INPUT,
            source_input_version=original.source_input_version,
            source_input_bundle_commitment=original.input_bundle_commitment),
            observation=dict(emlis_observation_stage='normal_observation',
                emlis_observation_result_identity='synthetic-initial-result',
                question_need_decision_identity=None, supplemental_answer_identity=None))
        self.handoff = PieceSavedHandoff(original, '60000000-0000-4000-8000-000000000001',
                                         1, canonical_json_bytes(lineage))
        self.checks = 0
        self.on_check = None

    async def resolve_original_handoff(self, authorization, saved_input_id):
        assert saved_input_id == INPUT
        return self.handoff

    async def revalidate_original_handoff(self, authorization, previous):
        self.checks += 1
        if self.on_check:
            self.on_check(self.checks)
        return self.handoff


def prepared(tier='premium', fmt=None):
    adapter = Adapter(tier)
    service = preview.PiecePreviewService(source_adapter=adapter)
    result = run(service.prepare_original(None, request(adapter.handoff, fmt)))
    adapter.checks = 0
    return service, adapter, result


def disallow_author(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('visual change must not generate or rewrite the body')
    monkeypatch.setattr(preview, 'generate_piece_candidate', forbidden)


def same_content(before, after):
    a, b = before.artifact_payload(), after.artifact_payload()
    assert {k: a[k] for k in UNCHANGED} == {k: b[k] for k in UNCHANGED}
    assert a['piece_text'].encode('utf-8') == b['piece_text'].encode('utf-8')
    assert before.handoff == after.handoff
    assert set(a) == set(b) == set(UNCHANGED) | {'visual_recipe', 'visual_recipe_hash'}
    assert b['visual_recipe_hash'] == canonical_sha256_hex(b['visual_recipe'])


@pytest.mark.parametrize('fmt', ['short_essay', 'quote', 'declaration'])
@pytest.mark.parametrize('selection', [choice(), choice('quiet_night'),
    choice(ratio='9:16'), choice(branding='off'), choice('quiet_night', '9:16', 'off')])
def test_permitted_visual_change_keeps_every_content_byte_without_author(monkeypatch, fmt, selection):
    service, adapter, before = prepared(fmt=fmt)
    original_bytes = before._artifact_json
    disallow_author(monkeypatch)
    after = run(service.prepare_visual_change(None, before, selection))
    same_content(before, after)
    assert adapter.checks == 2 and before._artifact_json == original_bytes
    out = after.artifact_payload()
    assert out['visual_recipe']['theme']['theme_id'] == (selection['theme_id'] or 'soft_paper')
    assert out['visual_recipe']['aspect_ratio'] == (selection['aspect_ratio'] or '4:5')
    assert out['visual_recipe']['branding']['branding_mode'] == (selection['branding_mode'] or 'required_subtle')
    assert not any(k in out for k in ('preview_id', 'expires_at', 'safety_state', 'source_ref'))
    print('VISUAL_CHANGE_ARTIFACT', json.dumps(dict(before=before.artifact_payload(),
                                                   after=out), ensure_ascii=False))


@pytest.mark.parametrize('tier,selection', [('free', choice()), ('plus', choice('quiet_night'))])
def test_free_and_plus_keep_existing_allowed_visuals(monkeypatch, tier, selection):
    service, adapter, before = prepared(tier)
    disallow_author(monkeypatch)
    after = run(service.prepare_visual_change(None, before, selection))
    same_content(before, after)
    assert after.artifact_payload()['visual_recipe']['branding']['branding_mode'] == (
        'required_small' if tier == 'free' else 'required_subtle')


@pytest.mark.parametrize('tier,selection', [
    ('free', choice('quiet_night')), ('free', choice(ratio='9:16')), ('free', choice(branding='off')),
    ('plus', choice(ratio='9:16')), ('plus', choice(branding='off')),
    ('premium', choice('unknown')), ('premium', choice(ratio='1:1')),
    ('premium', choice(branding='required_small'))])
def test_unavailable_selection_does_not_change_previous(monkeypatch, tier, selection):
    service, adapter, before = prepared(tier)
    raw = before._artifact_json
    disallow_author(monkeypatch)
    with pytest.raises(PieceContractError) as exc:
        run(service.prepare_visual_change(None, before, selection))
    assert exc.value.code == 'PIECE_VISUAL_SELECTION_NOT_ALLOWED' and exc.value.detail is None
    assert before._artifact_json == raw and adapter.checks == 1


@pytest.mark.parametrize('selection', [None, [], {}, {'theme_id': None},
    dict(choice(), requested_format='quote'), choice(theme=1), choice(ratio='')])
def test_invalid_selection_is_rejected_before_source_read(monkeypatch, selection):
    service, adapter, before = prepared()
    disallow_author(monkeypatch)
    with pytest.raises(PieceContractError) as exc:
        run(service.prepare_visual_change(None, before, selection))
    assert exc.value.code in ('PIECE_REQUEST_INVALID', 'PIECE_VISUAL_SELECTION_NOT_ALLOWED')
    assert exc.value.detail is None and adapter.checks == 0


@pytest.mark.parametrize('check', [1, 2])
@pytest.mark.parametrize('code', ['PIECE_AUTH_REQUIRED', 'PIECE_SOURCE_NOT_FOUND',
                                 'PIECE_SOURCE_NOT_ELIGIBLE', 'PIECE_CONFLICT'])
def test_source_access_or_state_failure_never_returns_a_candidate(monkeypatch, check, code):
    service, adapter, before = prepared()
    raw = before._artifact_json
    def fail(n):
        if n == check:
            raise PieceContractError(code, 'internal diagnostic')
    adapter.on_check = fail
    disallow_author(monkeypatch)
    with pytest.raises(PieceContractError) as exc:
        run(service.prepare_visual_change(None, before, choice('quiet_night')))
    assert exc.value.code == code and exc.value.detail is None
    assert adapter.checks == check and before._artifact_json == raw


@pytest.mark.parametrize('check', [1, 2])
def test_changed_tier_is_not_silently_applied_to_old_preparation(monkeypatch, check):
    service, adapter, before = prepared()
    def change(n):
        if n == check:
            adapter.handoff = replace(adapter.handoff,
                original=replace(adapter.handoff.original, subscription_tier='free'))
    adapter.on_check = change
    disallow_author(monkeypatch)
    with pytest.raises(PieceContractError, match='^PIECE_CONFLICT$'):
        run(service.prepare_visual_change(None, before, choice('quiet_night', '9:16', 'off')))
    assert adapter.checks == check


def test_choice_is_copied_before_await_and_results_do_not_mutate_previous(monkeypatch):
    service, adapter, before = prepared()
    selection = choice('quiet_night', '9:16', 'off')
    adapter.on_check = lambda n: selection.update(theme_id='soft_paper')
    disallow_author(monkeypatch)
    after = run(service.prepare_visual_change(None, before, selection))
    assert after.artifact_payload()['visual_recipe']['theme']['theme_id'] == 'quiet_night'
    payload = after.artifact_payload(); payload['piece_text'] = 'changed copy'
    payload['visual_recipe']['aspect_ratio'] = '1:1'
    same_content(before, after)
    assert after.artifact_payload()['visual_recipe']['aspect_ratio'] == '9:16'


@pytest.mark.parametrize('key', ['piece_text_hash', 'content_payload_hash', 'visual_recipe_hash',
                                'format_type', 'api_contract_version', 'visibility_scope'])
def test_corrupt_internal_preparation_is_not_repaired_into_success(monkeypatch, key):
    service, adapter, before = prepared()
    payload = before.artifact_payload(); payload[key] = 'invalid'
    corrupted = replace(before, _artifact_json=canonical_json_bytes(payload))
    disallow_author(monkeypatch)
    with pytest.raises(PieceContractError, match='^PIECE_HASH_MISMATCH$'):
        run(service.prepare_visual_change(None, corrupted, choice()))
    assert adapter.checks == 1


@pytest.mark.parametrize('error', [RuntimeError('internal failure'), asyncio.CancelledError()])
def test_unexpected_failure_is_body_free_but_cancellation_propagates(monkeypatch, error):
    service, adapter, before = prepared()
    def fail(n): raise error
    adapter.on_check = fail
    disallow_author(monkeypatch)
    expected = asyncio.CancelledError if isinstance(error, asyncio.CancelledError) else PieceContractError
    with pytest.raises(expected) as exc:
        run(service.prepare_visual_change(None, before, choice()))
    if expected is PieceContractError:
        assert str(exc.value) == 'PIECE_TEMPORARILY_UNAVAILABLE'


def test_repeating_same_choice_keeps_the_same_assembly_not_a_saved_id(monkeypatch):
    service, adapter, before = prepared()
    disallow_author(monkeypatch)
    first = run(service.prepare_visual_change(None, before, choice('quiet_night')))
    second = run(service.prepare_visual_change(None, first, choice('quiet_night')))
    assert first._artifact_json == second._artifact_json
    assert adapter.checks == 4


@pytest.fixture(scope='module')
def database():
    assert os.environ.get('Q2_PGLITE_MODULE'), 'isolated retained SQL runtime required'
    path = Path(__file__).parents[1] / 'test_emlis_q2_application.py'
    spec = importlib.util.spec_from_file_location('piece_visual_change_sql_fixture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    db = module.Database()
    yield db
    db.proc.stdin.close(); db.proc.wait(timeout=10)


@pytest.mark.parametrize('change_during_visual', [False, True])
def test_sql_saved_state_keeps_body_and_rechecks_after_visual(database, monkeypatch, change_during_visual):
    db = database; user, parent = str(uuid4()), str(uuid4())
    for sql, params in [
        ('insert into auth.users values ($1)', [user]),
        ("insert into public.profiles values ($1,'plus')", [user]),
        ("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['生活'],array['不安'],$4)",
         [parent, user, '私は強い不安を感じています。私は読書を大切にしたい。',
          json.dumps([dict(type='不安', strength='strong')])])]:
        assert 'code' not in db.query(sql, params)
    async def verify(_token): return user
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    emlis = EmlisThreadService()
    initial = run(emlis.start(user, parent))
    assert initial['state'] == 'COMPLETED' and initial['current_observation'] is not None
    adapter = PieceSavedSourceAdapter()
    authorization = 'Bearer synthetic-visual-session'
    handoff = run(adapter.resolve_original_handoff(authorization, parent))
    service = preview.PiecePreviewService(source_adapter=adapter)
    before = run(service.prepare_original(authorization, request(handoff)))
    stored_before = run(emlis.store.read(user, input_id=parent))
    disallow_author(monkeypatch)
    builder = preview.build_visual_recipe
    def build(*args, **kwargs):
        value = builder(*args, **kwargs)
        if change_during_visual:
            assert 'code' not in db.query('update public.emotions set memo_action=$1 where id=$2',
                                          ['私は今は休みたい。', parent])
        return value
    monkeypatch.setattr(preview, 'build_visual_recipe', build)
    if change_during_visual:
        with pytest.raises(PieceContractError) as exc:
            run(service.prepare_visual_change(authorization, before, choice('quiet_night')))
        assert exc.value.code in ('PIECE_SOURCE_NOT_ELIGIBLE', 'PIECE_CONFLICT')
    else:
        after = run(service.prepare_visual_change(authorization, before, choice('quiet_night')))
        same_content(before, after)
        assert after.artifact_payload()['visual_recipe']['theme']['theme_id'] == 'quiet_night'
        print('VISUAL_CHANGE_SQL_ARTIFACT', json.dumps(dict(before=before.artifact_payload(),
                                                          after=after.artifact_payload()), ensure_ascii=False))
    stored_after = run(emlis.store.read(user, input_id=parent))
    assert stored_before['thread'] == stored_after['thread']
    assert stored_before['events'] == stored_after['events']
