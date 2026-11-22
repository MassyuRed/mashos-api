"""The repaired spelling reaches existing updates and immutable saved delivery."""
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan, _prepare_emlis_meaning_from_plan)
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_relief_cognition import BASE, LEFT, RIGHT, UPDATES, facets
from test_cmee_emlis_relief_unknown import UNKNOWN
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_cmee_emlis_contrast_degree import NoGeneration
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run

KANA = BASE.replace('寂しい', 'さびしい')


@pytest.mark.parametrize('name,old,new,time', UPDATES, ids=[r[0] for r in UPDATES])
def test_revising_or_withdrawing_the_repaired_pair_expires_joint_reception(name, old, new, time):
    old = old.replace('寂しい', 'さびしい')
    new = new.replace('寂しい', 'さびしい') if new else None
    req = begin(KANA + '褒められたのに、嬉しくなかった。')
    first = MeaningExperienceEngine().generate(req)
    assert first.artifact and first.question
    assert '私も少し安心しましたが' in first.artifact.reception
    assert 'さびしいという気持ちにも、今、耳を傾けていたいです' in first.artifact.reception
    reply = f'「{old}」ではなく「{new}」です。' if new else f'「{old}」は誤りです。'
    req = advance(req, reply)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    update, = prepared.checkpoint.answer_update.updates
    assert update.operation == ('REVISE' if new else 'WITHDRAW')
    assert not prepared.checkpoint.unresolved_parts
    assert not facets(project_thread_meaning(prepared, plan).selected_reception)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact
    assert '私も少し安心しました' not in out.artifact.text
    assert '耳を傾けていたい' not in out.artifact.text
    assert old not in out.artifact.text
    remaining = RIGHT.replace('寂しい', 'さびしい') if old == LEFT else LEFT
    assert remaining in out.artifact.text
    assert '褒められた' in out.artifact.text and '嬉しくなかった' in out.artifact.text
    if new:
        assert new in out.artifact.reception
        assert any(n.semantic_frame.time_scope == time and n.source_fields == ('answer_text_private',)
                   for n in plan.nuclei)
    context = actual(request=req)
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no author replay')):
        assert read_body(context, out.artifact.text).passed


def old_prepare(req):
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread,
        original_meaning_plan(thread, _legacy_cognitive_feeling_orthography=True)).checkpoint


def export_dto(name, dto):
    if folder := os.environ.get('CMEE_LONELINESS_DTO_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, name + '.json').write_text(json.dumps(dto, ensure_ascii=False))


def reopen(user, parent, saved):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved
    assert run(reader.start(user, parent)) == saved


@pytest.mark.parametrize('case,memo', [('pair', KANA), ('unknown', KANA + UNKNOWN)])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'old_unavailable'])
def test_saved_body_or_old_failure_reopens_without_generation(qcase, qdb, monkeypatch, case, memo, historical):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, memo])
    if historical:
        monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(service.start(user, parent))
    if historical:
        assert saved['state'] == 'RESPONSE_FAILED' and saved['failure_code'] == 'body_not_validated'
        assert saved['current_observation'] is None and not saved['can_retry']
    else:
        assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
        body = saved['current_observation']['text']
        assert 'そのさびしさにも、今、耳を傾けていたいです' in body
        assert 'かもしれないと思うとさびしい' in body
        if case == 'unknown':
            assert 'わからない' in body
    assert saved['pending_question'] is None and not saved['can_continue']
    reopen(user, parent, saved)
    export_dto(f'{case}-{historical}', saved)


@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_old_meaning'])
def test_confirmed_interruption_reuses_complete_saved_meaning(qcase, qdb, monkeypatch, after_checkpoint):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, KANA])
    prepare, generate = service.engine.prepare_emlis_update, service.engine.generate

    def interrupted(*_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare if after_checkpoint else interrupted)
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with pytest.raises(asyncio.CancelledError):
        run(service.start(user, parent))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        (lambda *_: pytest.fail('saved meaning must be reused')) if after_checkpoint else prepare)
    saved = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u344-confirmed-retry',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    current = [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(current) == 1 and saved['operation_id'] == pending['operation_id']
    if after_checkpoint:
        assert current == meanings
        assert saved['current_observation'] is None and saved['failure_code'] == 'body_not_validated'
    else:
        assert saved['state'] == 'COMPLETED' and saved['current_observation']
        observation, = (e for e in after['events'] if e['kind'] == 'OBSERVATION')
        assert observation['payload']['meaning_checkpoint_ref'] == current[0]['payload']['checkpoint_id']
    reopen(user, parent, saved)
    export_dto(f'retry-{after_checkpoint}', saved)


def test_old_completed_kanji_body_remains_immutable(qcase, qdb, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, BASE])
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(service.start(user, parent))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
    assert 'その寂しさにも、今、耳を傾けていたいです' in saved['current_observation']['text']
    reopen(user, parent, saved)
    export_dto('old-complete', saved)
