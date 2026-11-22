"""Shared source meaning reaches the sole writer and the same saved OBS.

Provider text is synthetic. These checks establish source/realization and
receipt continuity, not a claim that the real model's prose is now correct.
"""
import copy
from dataclasses import replace
import hashlib
import json

import httpx
import pytest

import emlis_thread_store
from emlis_thread_service import EmlisThreadService, Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import (
    ACTIVE_MEANING_PROFILE, NaturalReplyInput, build_natural_reply_messages,
    prepare_natural_reply, system_message_for,
)
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb
from test_emlis_natural_reply_application import natural_case, BODY
from test_emlis_interpretation_correction import correct


def _source(qdb, parent, *, unknown=False):
    memo = '私は仕事を続けたい。私は費用を記録した。'
    if unknown:
        memo += 'くるくるした余韻だけが残った。'
    qdb.query("update public.emotions set memo=$2,memo_action=$3 where id=$1",
              [parent, memo, '私は資料を調べた。'])
    return memo


def _observations(snapshot):
    return [event for event in snapshot['events'] if event['kind'] == 'OBSERVATION']


def test_active_meaning_and_unread_text_reach_writer_without_replacing_original(natural_case, qdb, monkeypatch):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent, unknown=True)
    dto = run(service.start(user, parent))
    assert len(calls) == 1 and dto['current_observation']['text'] == BODY
    request = calls[0]
    original_material = json.loads(request.material_json)
    assert original_material['current']['memo'] == original
    writer = json.loads(build_natural_reply_messages(request)[1]['content'])
    current, = writer['records']
    assert current['scope'] == 'CURRENT_INPUT'
    assert current['metadata']['category'] == ['仕事']
    assert current['metadata']['emotion_details'] == [{'type': '平穏', 'strength': 'medium'}]
    # The unsupported clause is still source text, not erased to fit the
    # finite graph. Full source identity remains in the separate original.
    assert 'くるくるした余韻だけが残った。' in ''.join(f['text'] for f in current['active_fields'])
    assert current['source_duties']['unassessed_source_ranges']
    assert current['source_duties']['claims']
    saved = run(service.store.read(user, input_id=parent))
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == saved['thread']['data']['analysis_state'] == 'GENERATED'
    assert artifact['analysis_material'] == json.loads(request.analysis_material_json)
    assert artifact['analysis_material'] == saved['thread']['data']['analysis_material']
    assert artifact['analysis_material']['coverage']['full_source_semantic_coverage'] is False
    assert artifact['meaning_profile'] == ACTIVE_MEANING_PROFILE
    assert 'analysis_material' not in json.dumps(dto)

    def no_derivation(*args, **kwargs):
        raise AssertionError('saved GET must not derive meaning or regenerate')
    import cocolon_meaning_experience_engine.cores.analysis.semantic_admission as shared
    monkeypatch.setattr(shared, 'prepare_emlis_analysis_material', no_derivation)
    assert run(service.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(calls) == 1


@pytest.mark.parametrize('explanation, new_text', [
    ('「私は仕事を続けたい」は取り消します。', None),
    ('「私は仕事を続けたい」ではなく「私は家族を守りたい」です。', '私は家族を守りたい'),
])
def test_person_update_changes_active_author_meaning_not_unrelated_fields(natural_case, qdb, explanation, new_text):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent)
    first = run(service.start(user, parent))
    before = run(service.store.read(user, input_id=parent))
    old_observation = copy.deepcopy(_observations(before)[-1])
    updated = run(correct(service, user, first, explanation=explanation))
    assert updated['current_observation'] is not None and len(calls) == 2
    request = calls[-1]
    current, = json.loads(build_natural_reply_messages(request)[1]['content'])['records']
    texts = [f['text'] for f in current['active_fields']]
    assert all('私は仕事を続けたい' not in text for text in texts)
    assert any('私は費用を記録した' in text for text in texts)
    assert any('私は資料を調べた' in text for text in texts)
    assert bool(new_text and any(new_text in text for text in texts)) == (new_text is not None)
    assert current['source_updates']
    assert json.loads(request.material_json)['current']['memo'] == original
    saved = run(service.store.read(user, input_id=parent))
    assert _observations(saved)[0] == old_observation
    assert saved['thread']['current_meaning_event_id'] is None
    assert _observations(saved)[-1]['payload']['artifact']['analysis_material']['state'] == 'GENERATED'
    assert run(service.get(user, parent))['current_observation'] == updated['current_observation']
    assert len(calls) == 2


def test_unsupported_replacement_remains_full_unresolved_source_not_old_active_facts(natural_case, qdb):
    user, parent, service, calls = natural_case
    original = _source(qdb, parent)
    first = run(service.start(user, parent))
    explanation = '「私は仕事を続けたい」ではなく「私は友人を助けたい」です。'
    updated = run(correct(service, user, first, explanation=explanation))
    current, = json.loads(build_natural_reply_messages(calls[-1])[1]['content'])['records']
    assert current['meaning_state'] == 'NOT_GENERATED'
    assert current['active_state'] == 'PENDING'
    assert current['active_fields'] == [] and current['source_duties'] is None
    all_sources = json.dumps(current['unresolved_sources'], ensure_ascii=False)
    assert original in all_sources and explanation in all_sources
    assert '私は資料を調べた。' in all_sources
    target, = current['correction_targets']
    assert target['source_role'] == 'AI_INTERPRETATION_TARGET'
    assert target['text'] == '少し安心できた'
    assert current['unresolved_sources'][target['explanation_source'] - 1]['fields']['memo'] == explanation
    saved = run(service.store.read(user, input_id=parent))
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == 'NOT_GENERATED'
    assert artifact['analysis_material']['coverage']['pending_source_ranges']
    assert updated['current_observation']['text'] == BODY and len(calls) == 2


def test_unknown_only_text_is_kept_without_generated_meaning(natural_case, qdb):
    user, parent, service, calls = natural_case
    text = 'くるくるした余韻だけが残った。'
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, text])
    run(service.start(user, parent))
    current, = json.loads(build_natural_reply_messages(calls[0])[1]['content'])['records']
    assert current['meaning_state'] == 'NOT_GENERATED'
    assert current['active_state'] == 'RESOLVED'
    assert [field['text'] for field in current['active_fields']] == [text]
    assert current['source_duties']['claims'] == []
    assert current['source_duties']['unassessed_source_ranges']
    saved = run(service.store.read(user, input_id=parent))
    assert _observations(saved)[-1]['payload']['artifact']['analysis_state'] == 'NOT_GENERATED'


def test_legacy_received_reply_keeps_legacy_messages_after_new_service_restart(natural_case, monkeypatch, qdb):
    user, parent, service, calls = natural_case
    _source(qdb, parent)
    service.natural_meaning_profile = None
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    pending = run(service.start(user, parent))
    assert pending['can_retry'] and len(calls) == 1
    assert calls[0].meaning_profile is None and calls[0].writer_material_json is None
    before = run(service.store.read(user, input_id=parent))
    received = copy.deepcopy(next(e for e in before['events']
        if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'))
    import cocolon_meaning_experience_engine.cores.analysis.semantic_admission as shared

    def no_new_material(*args, **kwargs):
        raise AssertionError('a legacy receipt is not rebound to new meaning')

    monkeypatch.setattr(shared, 'prepare_emlis_analysis_material', no_new_material)
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE,
        natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-old-receipt',
        operation_id=pending['operation_id']))
    assert result['current_observation']['text'] == BODY and len(calls) == 1
    saved = run(service.store.read(user, input_id=parent))
    assert next(e for e in saved['events'] if e['id'] == received['id']) == received
    artifact = _observations(saved)[-1]['payload']['artifact']
    assert artifact['analysis_state'] == 'NOT_GENERATED' and 'analysis_material' not in artifact
    assert 'natural_meaning_profile' not in saved['thread']['data']


@pytest.mark.parametrize('receipt_kind', ['current', 'previous', 'changed_hash'])
def test_new_received_reply_reuses_only_the_same_fixed_meaning_and_messages(natural_case, monkeypatch, qdb, receipt_kind):
    user, parent, service, calls = natural_case
    _source(qdb, parent)
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    pending = run(service.start(user, parent))
    before = run(service.store.read(user, input_id=parent))
    as_of = before['thread']['data']['natural_meaning_as_of']
    material_ref = json.loads(calls[0].analysis_material_json)['material_ref']
    receipt = next(e for e in before['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED')
    assert receipt['payload']['meaning_profile'] == ACTIVE_MEANING_PROFILE
    if receipt_kind == 'previous':
        # Before context-aware writing the same two-field record was sent
        # with no context protocol tag. Preserve its exact receipt on retry.
        old_writer = json.loads(calls[0].writer_material_json)
        assert old_writer.pop('source_context_version')
        old_input = replace(calls[0], writer_material_json=json.dumps(old_writer, ensure_ascii=False, separators=(',', ':')))
        old_messages = build_natural_reply_messages(old_input)
        old_hash = hashlib.sha256(json.dumps(old_messages, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        assert old_hash != receipt['payload']['writer_messages_sha256']
        for event in before['events']:
            if event['payload'].get('stage') in {'NATURAL_REPLY_CALL_STARTED', 'NATURAL_REPLY_RECEIVED'}:
                qdb.query("update public.emlis_thread_events set payload=jsonb_set(payload-'writer_context_version',"
                          "'{writer_messages_sha256}',to_jsonb($2::text)) where id=$1", [event['id'], old_hash])
        receipt['payload']['writer_messages_sha256'] = old_hash
    if receipt_kind == 'changed_hash':
        qdb.query("update public.emlis_thread_events set payload=jsonb_set(payload,'{writer_messages_sha256}',to_jsonb($2::text)) where id=$1",
                  [receipt['id'], 'different-writer-message-hash'])
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE,
        natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-meaning-receipt',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    assert len(calls) == 1 and after['thread']['data']['natural_meaning_as_of'] == as_of
    if receipt_kind == 'changed_hash':
        assert result['current_observation'] is None and not result['can_retry']
        assert result['failure_code'] == 'natural_reply_writer_identity_changed'
        assert not _observations(after)
    else:
        assert result['current_observation']['text'] == BODY
        artifact = _observations(after)[-1]['payload']['artifact']
        assert artifact['analysis_material']['material_ref'] == material_ref
        assert artifact['writer_messages_sha256'] == receipt['payload']['writer_messages_sha256']
        assert artifact['analysis_state'] == 'GENERATED'



@pytest.mark.parametrize('old_receipt', [False, True])
def test_corrected_circumstance_writer_retries_exact_prior_projection(natural_case, qdb, monkeypatch, old_receipt):
    from cocolon_meaning_experience_engine import natural_reply
    from test_emlis_q2_application import answer

    user, parent, service, calls = natural_case
    feeling = 'つらかったんです'
    circumstance = '会議がうまくできませんでした'
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, feeling])
    initial = run(service.start(user, parent))
    assert initial['pending_question']['text'] == 'なにがつらかったんですか？'
    refined = run(answer(service, user, initial, circumstance))
    assert refined['body_state'] == 'REFINED' and refined['meaning_updated']

    failed = False

    async def fail_first_observation_save(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    def legacy_writer_context(*args, **kwargs):
        kwargs['include_corrected_circumstance'] = False
        return prepare_natural_reply(*args, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', fail_first_observation_save)
    with monkeypatch.context() as prior:
        if old_receipt:
            prior.setattr(natural_reply, 'prepare_natural_reply', legacy_writer_context)
        pending = run(correct(service, user, refined, explanation='「つらかったんです」ではなく「私は不安だった」です。'))
    assert failed and pending['can_retry'] and len(calls) == 3
    material = json.loads(calls[-1].analysis_material_json)
    writer = json.loads(calls[-1].writer_material_json)
    row, = writer['records']
    if old_receipt:
        assert row['active_state'] == 'PENDING' and not row['active_fields']
        assert 'corrected_circumstance' not in material
        version = natural_reply.SOURCE_CONTEXT_VERSION
    else:
        assert row['active_state'] == 'RESOLVED'
        assert [(field['source_role'], field['text']) for field in row['active_fields']] == [
            ('SUPPLEMENTAL_ANSWER', circumstance), ('USER_INTERPRETATION_CORRECTION', '私は不安だった'),
        ]
        assert all('ai_question_context' not in field for field in row['active_fields'])
        assert material['corrected_circumstance'] is True
        version = natural_reply.CORRECTED_SOURCE_CONTEXT_VERSION
    assert writer['source_context_version'] == version

    before = run(service.store.read(user, input_id=parent))
    receipt = [e for e in before['events'] if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'][-1]
    assert receipt['payload']['writer_context_version'] == version
    restarted = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=service.natural_reply_source)
    result = run(restarted.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='resume-corrected-reply',
        operation_id=pending['operation_id']))
    assert result['current_observation']['text'] == BODY and len(calls) == 3
    after = run(service.store.read(user, input_id=parent))
    assert next(e for e in after['events'] if e['id'] == receipt['id']) == receipt
    saved = _observations(after)[-1]['payload']['artifact']
    assert saved['analysis_material'] == material
    assert saved['writer_messages_sha256'] == receipt['payload']['writer_messages_sha256']
    assert run(restarted.get(user, parent))['current_observation'] == result['current_observation']

def test_writer_uses_compact_meaning_without_private_evidence_or_losing_source():
    from test_analysis_active_update_material import saved_update, REVISE
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request
    saved = saved_update(REVISE)
    request = _request(saved, include_context=False, analysis_source_only=True)
    material, _ = prepare_natural_reply(request, meaning_profile=ACTIVE_MEANING_PROFILE,
        owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    private = json.loads(material.analysis_material_json)
    messages = build_natural_reply_messages(material)
    writer = json.loads(messages[1]['content'])
    record, = writer['records']
    assert [f['text'] for f in record['active_fields']] == [f['text'] for f in private['active_fields']]
    assert [c['reading']['polarity'] for c in record['source_duties']['claims']] == [
        c['proposition']['polarity'] for c in private['source_duties']['claims']]
    assert [c['reading']['time'] for c in record['source_duties']['claims']] == [
        c['proposition']['temporal_scope'] for c in private['source_duties']['claims']]
    assert [c['reading']['actor'] for c in record['source_duties']['claims']] == [
        c['proposition']['actor'] for c in private['source_duties']['claims']]
    assert record['source_updates'][0]['operation'] == 'REVISE'
    assert record['source_updates'][0]['target_text'] == '私は仕事を続けたい'
    assert 'graph' not in record and 'sources' not in record
    assert 'active_claims' not in messages[0]['content']
    assert 'answer_meaning' not in messages[0]['content']

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    forbidden = {'source_envelope_id', 'source_id', 'field_ref', 'material_ref', 'record_ref',
        'record_version', 'source_set_ref', 'evidence', 'evidence_refs', 'evidence_id',
        'field_sha256', 'literal_sha256', 'utf8_start', 'utf8_end', 'source_parts'}
    assert not forbidden.intersection(keys(writer))
    # Private evidence remains available for save/replay; author input does
    # not repeat its graph, locators, hashes and full quotation per claim.
    assert private['active_fields'][0]['evidence']['literal_sha256']
    assert len(messages[1]['content'].encode()) < len(material.analysis_material_json.encode()) // 2


def test_compact_wire_keeps_long_unparsed_fields_once_and_legacy_bytes_unchanged():
    from test_emlis_analysis_material import uncorrected
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request
    memo, action = 'くるくるした余韻。' * 120, '🦉QKZ。' * 120
    saved = uncorrected(memo, action)
    request = _request(saved, include_context=False, analysis_source_only=True)
    legacy, _ = prepare_natural_reply(request)
    old_messages = [dict(role='system', content=system_message_for(legacy)),
                    dict(role='user', content=legacy.material_json)]
    old_bytes = json.dumps(old_messages, ensure_ascii=False).encode()
    material, _ = prepare_natural_reply(request, meaning_profile=ACTIVE_MEANING_PROFILE,
        owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    wire = build_natural_reply_messages(material)[1]['content']
    assert wire.count(memo) == wire.count(action) == 1
    assert [f['text'] for f in json.loads(wire)['records'][0]['active_fields']] == [memo, action]
    assert json.loads(material.analysis_material_json)['original_record'] == saved['original']
    # No implicit migration of a historical request to the new author view.
    restored = NaturalReplyInput(legacy.source_prefix_ref, legacy.material_json)
    assert json.dumps(build_natural_reply_messages(restored), ensure_ascii=False).encode() == old_bytes


@pytest.mark.parametrize('answers', [('その時は重かった。',), ('はい。', 'はい。')])
def test_answer_writing_keeps_each_issued_question_with_its_answer_not_as_user_evidence(answers):
    from test_emlis_analysis_material import uncorrected, answer_request
    from test_analysis_saved_period import OWNER, NOW

    saved = uncorrected('褒められたのに、嬉しくなかった。', '会議で発表した。')
    request = answer_request(saved, answers)
    control = request.emlis_thread.question_control_context
    prompts = ('「褒められた」は、あなたにはどんな意味として届きましたか。', 'その日の発表はどうでしたか。')
    questions = tuple(replace(q, prompt_private=prompts[i]) for i, q in enumerate(control.issued_questions))
    thread = replace(request.emlis_thread, question_control_context=replace(control, pending_question=questions[-1],
                      issued_questions=questions))
    request = replace(request, emlis_thread=thread)
    options = dict(response_stage='REFINED', meaning_profile=ACTIVE_MEANING_PROFILE,
                   owner_scope=OWNER, original_record=saved['original'], as_of=NOW)
    previous, _ = prepare_natural_reply(request, **options, bind_writer_context=False)
    current, _ = prepare_natural_reply(request, **options)
    assert current.material_json == previous.material_json and current.analysis_material_json == previous.analysis_material_json
    system, wire = build_natural_reply_messages(current)
    assert '欄は出来事の順番を示しません' in system['content']
    assert 'current_answers' not in system['content']
    record, = json.loads(wire['content'])['records']
    rows = record['unresolved_sources'] if record['active_state'] == 'PENDING' else record['active_fields']
    bound = [row for row in rows if row['source_role'] == 'SUPPLEMENTAL_ANSWER']
    assert [row['ai_question_context'] for row in bound] == list(prompts[:len(answers)])
    assert all('ai_question_context' not in row for row in rows if row['source_role'] != 'SUPPLEMENTAL_ANSWER')
    assert all(prompt not in previous.writer_material_json for prompt in prompts)


def test_final_single_field_uses_the_recipient_instruction_without_an_answer():
    from test_emlis_analysis_material import uncorrected
    from test_analysis_saved_period import OWNER, NOW
    from emlis_thread_service import _request

    saved = uncorrected('誘われたのに、悲しかった。', '')
    request = _request(saved, include_context=False, analysis_source_only=True)
    options = dict(meaning_profile=ACTIVE_MEANING_PROFILE, owner_scope=OWNER,
                   original_record=saved['original'], as_of=NOW)
    current, _ = prepare_natural_reply(request, **options)
    previous, _ = prepare_natural_reply(request, **options, bind_writer_context=False)
    system, source = build_natural_reply_messages(current)
    assert '書き出しからEmlisが本人に話しかける返事' in system['content']
    assert 'この記録で大事な点を一つ' in system['content']
    assert '短い受け取りや一度の言い換えも構いません' not in system['content']
    assert '今回は回答後です' not in system['content']
    assert json.loads(source['content'])['records'] == json.loads(previous.writer_material_json)['records']
