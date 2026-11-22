"""Prepare fictional current-owner messages; optionally run one bounded batch.

Preparation and admission are CPU-only. ``execute`` is a separate, explicit
operation for an already approved existing endpoint, model and existing auth.
It never starts a service, loads weights, trains, retries or reads broad env.
Raw responses return to the production CPU owners; no source or raw is fixed.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import UUID

SCHEMA = 'cocolon.current-4b-packet.v1'
OWNER = str(UUID(int=9100))
NOW = '2026-11-14T09:00:00+00:00'
AS_OF = '2026-11-14T09:01:00+00:00'
PAST = '2026-11-03T09:00:00+00:00'
MAX_GENERATIONS = 6
MAX_SECONDS = 300
MAX_RESPONSE_BYTES = 262144


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False)


def sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def original(number, memo, memo_action='', *, emotions=('平穏',),
             strengths=('medium',), created_at=NOW, categories=('仕事',)):
    """Exactly the existing seven-key current input; all people are fictional."""
    return dict(id=str(UUID(int=number)), created_at=created_at,
        category=list(categories), emotions=list(emotions),
        emotion_details=[dict(type=name, strength=strength)
            for name, strength in zip(emotions, strengths, strict=True)],
        memo=memo, memo_action=memo_action)


def _thread(raw, number):
    from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
    from cocolon_meaning_experience_engine.contracts import GenerationRequest
    from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
    from cocolon_meaning_experience_engine.emlis_thread_contracts import (
        EmlisThreadInputV1, EmlisQuestionControlV1)
    req = GenerationRequest('fictional-current-4b-' + str(number),
        build_emlis_current_input_bundle(raw), raw['id'],
        execution_mode='DEVELOPMENT_APPLICATION')
    control = EmlisThreadInputV1(str(UUID(int=number + 10000)),
        freeze_text_source(req).envelope.envelope_id,
        capability_snapshot='Q3_PREMIUM',
        question_control_context=EmlisQuestionControlV1(question_limit=3))
    return replace(req, emlis_thread=control)


def _emlis_cases():
    from cocolon_meaning_experience_engine.emlis_thread_contracts import (
        InterpretationCorrectionSource, SupplementalAnswerSource,
        EmlisQuestionControlV1)
    from cocolon_meaning_experience_engine.emlis_thread_history import (
        OwnedHistorySourceV1, FrameFeedbackSourceV1, derive_interpretive_frames)
    from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
    from cocolon_meaning_experience_engine.emlis_question import (
        original_meaning_plan, question_candidate)
    from cocolon_meaning_experience_engine.natural_reply import (
        ACTIVE_MEANING_PROFILE, prepare_natural_reply, build_natural_reply_messages)

    raw = original(9101, '私は仕事を続けたい。私は費用を記録した。', '私は資料を調べた。')
    req = _thread(raw, 9101)
    correction = InterpretationCorrectionSource(str(UUID(int=19101)),
        req.emlis_thread.thread_id, req.emlis_thread.original_source_ref,
        str(UUID(int=29101)), '仕事を続けたいのですね。',
        '「私は仕事を続けたい」ではなく「私は家族を守りたい」です。', NOW)
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        interpretation_corrections=(correction,)))

    past_raw = original(9102, '褒められたのに、嬉しくなかった。', created_at=PAST,
        emotions=('悲しみ',), strengths=('medium',), categories=('人間関係',))
    past_req = _thread(past_raw, 9102)
    admitted = admit_emlis_thread(past_req)
    _, question = question_candidate(admitted, original_meaning_plan(admitted),
        parent_request_id=past_req.request_id)
    if question is None:
        raise ValueError('fictional_history_question_not_derived')
    answer = SupplementalAnswerSource(str(UUID(int=19102)),
        past_req.emlis_thread.thread_id, question.question_id, 1,
        past_req.emlis_thread.original_source_ref, 'その時は重かった。', PAST)
    past_req = replace(past_req, emlis_thread=replace(past_req.emlis_thread,
        answers=(answer,), current_round=1,
        question_control_context=EmlisQuestionControlV1(pending_question=question, issued_count=1,
            issued_questions=(question,), asked_target_refs=(question.decision.target_ref,),
            question_limit=3)))
    history = OwnedHistorySourceV1(past_req, PAST,
        (past_raw['id'], sha(canonical(past_raw)), 1))
    frame_raw = original(9103,
        '今日は、前の記録とは別の出来事で、褒められて悲しかった。相手の意図は分からない。',
        '同僚から説明の丁寧さを褒められた。帰ってからも、その場面を考えた。',
        emotions=('悲しみ', '不安'), strengths=('medium', 'weak'), categories=('人間関係',))
    frame_req = _thread(frame_raw, 9103)
    frame_req = replace(frame_req, emlis_thread=replace(frame_req.emlis_thread,
        admitted_history=(history,)))
    frames = derive_interpretive_frames(admit_emlis_thread(frame_req))
    if len(frames) != 1:
        raise ValueError('fictional_frame_not_uniquely_derived')
    frame, = frames
    feedback = FrameFeedbackSourceV1(frame.frame_key, frame.frame_ref,
        past_raw['id'], 'REJECTED', None, 1, NOW)
    frame_req = replace(frame_req, emlis_thread=replace(frame_req.emlis_thread,
        rejected_frame_keys=(frame.frame_key,), frame_feedback_sources=(feedback,)))
    cases = []
    for case_id, request, record, sources in (
            ('EMLIS-EXPLICIT-CORRECTION', req, raw, [raw]),
            ('EMLIS-REJECTED-PERSON-FRAME', frame_req, frame_raw, [past_raw, frame_raw])):
        prepared, safety = prepare_natural_reply(request,
            meaning_profile=ACTIVE_MEANING_PROFILE, owner_scope=OWNER,
            original_record=record, as_of=AS_OF, response_stage='FINAL')
        cases.append(dict(case_id=case_id, owner='emlis', auth_scope='natural',
            prepared=asdict(prepared), request_ref=prepared.source_prefix_ref,
            originals=sources, messages=build_natural_reply_messages(prepared),
            max_tokens=2048, safety=asdict(safety)))
    return cases


def _piece_cases():
    from piece_v2_contract import canonical_json_bytes
    from piece_v2_generation import PieceSourceSnapshot
    from piece_model_source import build_piece_model_messages
    from cocolon_meaning_experience_engine.piece_v1c import (
        MODEL_REALIZATION_PROFILE, PieceGenerationRequest)
    from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
    # Reuse only the fictional original seven fields, never the recorded raw.
    fixture = Path(__file__).parents[1] / 'tests/fixtures/piece_cmee_realization_recorded.json'
    rows = json.loads(fixture.read_text(encoding='utf-8'))
    if rows.get('all_fictional') is not True:
        raise ValueError('piece_fixture_not_fictional')
    cases = []
    for row in rows['rows']:
        record = row['original']
        source = PieceSourceSnapshot(OWNER, record['id'], 'emlis.current_input_bundle.v1',
            '\n\n'.join(record[k] for k in ('memo', 'memo_action') if record[k]),
            saved_original_json=canonical_json_bytes(record))
        request = PieceGenerationRequest('fictional-current-4b-' + row['case_id'],
            source, OWNER, source.saved_input_id, source.source_version)
        prepared = prepare_piece_model_request(request, realization_profile=MODEL_REALIZATION_PROFILE)
        cases.append(dict(case_id='PIECE-' + row['case_id'], owner='piece',
            auth_scope='natural', prepared=asdict(prepared), request_ref=prepared.request_id,
            originals=[record], messages=build_piece_model_messages(prepared,
                include_authoring_constraints=True, source_request=request,
                include_editorial_choices=True), max_tokens=2048,
            candidate_format='piece.field_slots.v1'))
    return cases


def _snapshot():
    members = []
    for number, text in ((9201, '私は考えをノートに書いた。私は仕事を続けたい。'),
                         (9202, '私は資料を読んだ。私は家族を守りたい。')):
        members.append(dict(original=original(number, text,
            created_at='2026-11-03T09:00:00+00:00'), thread=None, events=[]))
    return dict(tier='premium', now=NOW, period_start='2026-11-01T00:00:00+00:00',
        period_end=NOW, guard='analysis-db-cumulative-v1:' + 'a' * 64, members=members)


def _if_case():
    from analysis_cumulative_service import build_cumulative_map
    from analysis_observed_service import private_storage_evidence
    from analysis_if_route_service import _freeze_prepared
    from cocolon_meaning_experience_engine.cores.analysis.if_route_contracts import (
        AnalysisIfRouteRequest, AnalysisIfModelPrepared, AnalysisSimulationSource)
    from cocolon_meaning_experience_engine.cores.analysis.if_route_realizer import (
        observed_route_reference, prepare_if_model_request)
    snapshot = _snapshot()
    artifact, _ = build_cumulative_map(OWNER, snapshot)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    branch = projection['nodes'][0]['node_ref']
    request = AnalysisIfRouteRequest('fictional-current-4b-if', OWNER,
        artifact.reference, observed_route_reference(artifact.reference, branch), branch,
        canonical(projection), canonical(private_storage_evidence(artifact)),
        base_source_guard=snapshot['guard'],
        branch_intent=AnalysisSimulationSource('fictional-if-intent', OWNER,
            '資料を読む時間を先に確保して、仕事の進め方を考えたい。'),
        constraints=(AnalysisSimulationSource('fictional-if-condition', OWNER,
            '使える時間は30分です。'),), requested_candidate_count=2,
        constraints_confirmed=True)
    prepared = prepare_if_model_request(request)
    if type(prepared) is not AnalysisIfModelPrepared:
        raise ValueError('fictional_if_material_not_ready')
    return dict(case_id='ANALYSIS-IF-TWO-CANDIDATES', owner='if', auth_scope='analysis',
        request_ref=prepared.request_ref, prepared=_freeze_prepared(prepared),
        originals=[m['original'] for m in snapshot['members']],
        messages=prepared.messages(), max_tokens=4096)


def _map_case():
    from analysis_semantic_map import prepare_semantic_map
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    snapshot = _snapshot()
    prepared = prepare_semantic_map(OWNER, snapshot,
        prompt_version=SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    # These are the exact private prepared JSON projections. Re-admission
    # derives the remaining typed source objects from this same fake snapshot.
    frozen = {key: getattr(prepared, key) for key in ('request_ref', 'material_json',
        'dictionary_json', 'source_snapshot_json', 'source_duties_json',
        'map_correction_sources_json', 'prompt_version')}
    return dict(case_id='ANALYSIS-MAP-SOURCE-DUTIES', owner='map', auth_scope='analysis',
        request_ref=prepared.request_ref, prepared=frozen, source_snapshot=snapshot,
        originals=[m['original'] for m in snapshot['members']],
        messages=prepared.messages(), max_tokens=4096)


def build_packet(*, natural_model, analysis_model, include_map=False):
    if not all(type(value) is str and value.strip() for value in (natural_model, analysis_model)):
        raise ValueError('explicit_existing_model_names_required')
    cases = _emlis_cases() + _piece_cases()
    if include_map:
        cases.append(_map_case())
    cases.append(_if_case())
    for case in cases:
        body = dict(model=natural_model if case['auth_scope'] == 'natural' else analysis_model,
            messages=case.pop('messages'), temperature=0,
            max_tokens=case.pop('max_tokens'), stream=False)
        if 'candidate_format' in case:
            body['candidate_format'] = case.pop('candidate_format')
        body['chat_template_kwargs'] = dict(enable_thinking=False)
        case['wire_json'] = canonical(body)
        case['wire_bytes'] = len(case['wire_json'].encode('utf-8'))
        case['wire_sha256'] = sha(case['wire_json'])
    return dict(schema_version=SCHEMA, all_fictional=True,
        source_origin='CPU production owners over fictional sources, not live user/SQL input',
        analysis_selector='self_hosted.semantic.v1',
        natural_model=natural_model, analysis_model=analysis_model,
        limits=dict(max_generations=MAX_GENERATIONS, max_health_gets=2,
            max_elapsed_seconds=MAX_SECONDS, retries=0, training=0,
            weight_changes=0, service_restarts=0), cases=cases)


def write_new(path, value):
    encoded = (canonical(value) + '\n').encode('utf-8')
    with open(path, 'xb') as out:
        os.chmod(path, 0o600)
        out.write(encoded)
    return dict(path=str(path), bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())


def validate_packet(packet):
    if (packet.get('schema_version') != SCHEMA or packet.get('all_fictional') is not True
            or not 1 <= len(packet['cases']) <= MAX_GENERATIONS
            or len({c['case_id'] for c in packet['cases']}) != len(packet['cases'])):
        raise ValueError('packet_invalid')
    for case in packet['cases']:
        if (sha(case['wire_json']) != case['wire_sha256']
                or len(case['wire_json'].encode('utf-8')) != case['wire_bytes']
                or case['auth_scope'] not in {'natural', 'analysis'}):
            raise ValueError('packet_wire_changed')
    return packet


def admit_results(packet, results):
    """Hand unchanged new raw to each existing CPU owner; no inference/DB."""
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    validate_packet(packet)
    if results.get('packet_sha256') != sha(canonical(packet)):
        raise ValueError('response_packet_binding_invalid')
    cases = {case['case_id']: case for case in packet['cases']}
    rows = results['responses']
    if (len({row['case_id'] for row in rows}) != len(rows)
            or any(row['case_id'] not in cases or row.get('attempt') != 1 for row in rows)):
        raise ValueError('response_case_binding_invalid')
    admitted = []
    for row in rows:
        case = cases[row['case_id']]
        entry = dict(case_id=case['case_id'], status='UNAVAILABLE')
        admitted.append(entry)
        if row.get('state') != 'RECEIVED' or row.get('status_code') != 200:
            continue
        try:
            value = json.loads(row['body'])
            wire = json.loads(case['wire_json'])
            choice, = value['choices']
            message = choice['message']
            if (value.get('model') != wire['model'] or choice.get('finish_reason') != 'stop'
                    or message.get('role') != 'assistant' or message.get('tool_calls')
                    or message.get('function_call') or message.get('reasoning_content')
                    or type(message.get('content')) is not str or not message['content'].strip()):
                continue
            raw = message['content']
            entry['raw_sha256'] = sha(raw)
            if case['owner'] == 'emlis':
                from cocolon_meaning_experience_engine.natural_reply import (
                    NaturalReplyInput, NaturalReply, validate_reply)
                prepared = NaturalReplyInput(**case['prepared'])
                reply = validate_reply(NaturalReply(raw.strip(), wire['model'],
                    prepared.source_prefix_ref), prepared)
                entry.update(status='FORMAT_ADMITTED', content_text=reply.text,
                    limitation='Existing reply format validation; human meaning/quality review remains')
            elif case['owner'] == 'piece':
                from piece_v2_generation import PieceSourceSnapshot
                from piece_v2_contract import canonical_json_bytes
                from cocolon_meaning_experience_engine.preparation import PreparedRequest
                from cocolon_meaning_experience_engine.piece_v1c import (
                    MODEL_REALIZATION_PROFILE, PieceGenerationRequest)
                from cocolon_meaning_experience_engine.piece_semantic_admission import (
                    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, prepare_piece_model_request,
                    receive_piece_model_candidate)
                if value.get('candidate_format') != PIECE_FIELD_SLOTS_FORMAT:
                    continue
                record, = case['originals']
                source = PieceSourceSnapshot(OWNER, record['id'], 'emlis.current_input_bundle.v1',
                    '\n\n'.join(record[k] for k in ('memo', 'memo_action') if record[k]),
                    saved_original_json=canonical_json_bytes(record))
                request = PieceGenerationRequest('fictional-current-4b-' +
                    case['case_id'].removeprefix('PIECE-'), source, OWNER,
                    source.saved_input_id, source.source_version)
                prepared = PreparedRequest(**case['prepared'])
                if prepare_piece_model_request(request,
                        realization_profile=MODEL_REALIZATION_PROFILE) != prepared:
                    raise ValueError('piece_frozen_request_changed')
                receipt = receive_piece_model_candidate(prepared, raw_output=raw,
                    finish_reason='stop', provider='existing-approved-4b', model=wire['model'],
                    candidate_format=PIECE_FIELD_SLOTS_FORMAT,
                    realization_profile=MODEL_REALIZATION_PROFILE)
                outcome = MeaningExperienceEngine().generate(request,
                    semantic_input=PieceModelInputV1(prepared, receipt))
                entry.update(status=outcome.status.value, reason_codes=list(outcome.reason_codes))
                if outcome.artifact is not None:
                    entry.update(content_text=outcome.artifact.piece_text,
                        model_body_blocks=list(outcome.artifact.model_body_blocks),
                        realization_profile=outcome.artifact.realization_profile)
            elif case['owner'] == 'if':
                from analysis_if_route_service import _restore_prepared
                from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
                    AnalysisModelQuotedParentUnitsResponse, digest)
                prepared = _restore_prepared(case['prepared'])
                receipt = AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
                    digest(prepared.messages()), sha(raw), 'stop', raw)
                outcome = MeaningExperienceEngine().generate(prepared.request, semantic_input=receipt)
                entry.update(status=outcome.status.value, reason_codes=list(outcome.reason_codes),
                    clarification_request=outcome.clarification_request)
                if outcome.artifact is not None:
                    entry.update(content_text=outcome.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                        projection=outcome.artifact.safe_projection(authenticated_owner_scope=OWNER))
            elif case['owner'] == 'map':
                from analysis_semantic_map import prepare_semantic_map, build_semantic_map
                from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
                    AnalysisModelQuotedParentUnitsResponse, digest)
                prepared = prepare_semantic_map(OWNER, case['source_snapshot'],
                    prompt_version=case['prepared']['prompt_version'])
                if any(getattr(prepared, key) != expected
                        for key, expected in case['prepared'].items()):
                    raise ValueError('map_frozen_request_changed')
                receipt = AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
                    digest(prepared.messages()), sha(raw), 'stop', raw)
                artifact, coverage = build_semantic_map(prepared, receipt)
                entry.update(status='GENERATED',
                    content_text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                    projection=artifact.safe_projection(authenticated_owner_scope=OWNER), coverage=coverage)
        except (ValueError, TypeError, KeyError, AttributeError):
            # Raw stays in the separate receipt. Admission does not repair it.
            entry['status'] = 'REJECTED_BY_CPU_OWNER'
    return dict(schema_version=SCHEMA, all_fictional=True,
        packet_sha256=sha(canonical(packet)), model_calls=0, database_writes=0, results=admitted)


async def execute_packet(packet, *, endpoint, health_endpoint, auth_envs, output,
                         transport=None, clock=time.monotonic):
    """One batch only. The exclusive result file consumes the attempt pre-I/O."""
    import httpx
    validate_packet(packet)
    for url in (endpoint, health_endpoint):
        parsed = urlsplit(url)
        if (parsed.scheme not in {'http', 'https'} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError('explicit_existing_endpoint_required')
        if parsed.scheme == 'http' and parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
            raise ValueError('unencrypted_remote_endpoint_forbidden')
    if urlsplit(endpoint).netloc != urlsplit(health_endpoint).netloc:
        raise ValueError('health_must_use_same_existing_service')
    if set(auth_envs) != {'natural', 'analysis'}:
        raise ValueError('two_explicit_existing_auth_env_names_required')
    # Read only these two names. Never enumerate env or emit credential values.
    auth = {scope: os.environ[name] for scope, name in auth_envs.items()}
    if not all(auth.values()):
        raise ValueError('existing_auth_unavailable')
    started = clock()
    result = dict(schema_version=SCHEMA, packet_sha256=sha(canonical(packet)),
        attempt_consumed=True, health_before=None, health_after=None, responses=[])
    with open(output, 'x', encoding='utf-8') as out:
        os.chmod(output, 0o600)

        def save():
            out.seek(0)
            out.truncate()
            out.write(canonical(result) + '\n')
            out.flush()

        async def request(client, method, url, **kwargs):
            remaining = MAX_SECONDS - (clock() - started)
            if remaining <= 0:
                raise TimeoutError
            async with asyncio.timeout(remaining):
                async with client.stream(method, url, timeout=min(remaining, 240), **kwargs) as response:
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=16384):
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE_BYTES:
                            raise ValueError('response_size_limit')
                    return dict(status_code=response.status_code,
                        body=data.decode('utf-8'), elapsed_seconds=clock() - started)

        save()
        async with httpx.AsyncClient(transport=transport, trust_env=False, follow_redirects=False) as client:
            try:
                result['health_before'] = await request(client, 'GET', health_endpoint)
                save()
                if result['health_before']['status_code'] != 200:
                    return result
                for case in packet['cases']:
                    if clock() - started >= MAX_SECONDS:
                        result['failure'] = 'batch_deadline_reached'
                        break
                    row = dict(case_id=case['case_id'], attempt=1, state='SENT')
                    result['responses'].append(row)
                    save()  # ACK-unknown remains consumed; never replay a POST.
                    try:
                        row.update(await request(client, 'POST', endpoint,
                            headers={'Authorization': 'Bearer ' + auth[case['auth_scope']],
                                'Content-Type': 'application/json', 'Accept-Encoding': 'identity'},
                            content=case['wire_json'].encode('utf-8')))
                        row['state'] = 'RECEIVED'
                    except (httpx.HTTPError, TimeoutError, ValueError, UnicodeError):
                        row['state'] = 'FAILED_OR_ACK_UNKNOWN'
                        break
                    finally:
                        save()
            except (httpx.HTTPError, TimeoutError, ValueError, UnicodeError):
                result['failure'] = 'health_or_deadline_unavailable'
            finally:
                if clock() - started < MAX_SECONDS:
                    try:
                        result['health_after'] = await request(client, 'GET', health_endpoint)
                    except (httpx.HTTPError, TimeoutError, ValueError, UnicodeError):
                        result['health_after'] = dict(state='UNAVAILABLE')
                result['elapsed_seconds'] = clock() - started
                save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('prepare')
    build.add_argument('--natural-model', required=True)
    build.add_argument('--analysis-model', required=True)
    build.add_argument('--output', type=Path, required=True)
    build.add_argument('--include-map', action='store_true')
    run = sub.add_parser('execute')
    run.add_argument('--packet', type=Path, required=True)
    run.add_argument('--packet-sha256', required=True)
    run.add_argument('--endpoint', required=True)
    run.add_argument('--health-endpoint', required=True)
    run.add_argument('--natural-auth-env', required=True)
    run.add_argument('--analysis-auth-env', required=True)
    run.add_argument('--output', type=Path, required=True)
    admit = sub.add_parser('admit')
    admit.add_argument('--packet', type=Path, required=True)
    admit.add_argument('--responses', type=Path, required=True)
    admit.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        packet = build_packet(natural_model=args.natural_model,
            analysis_model=args.analysis_model, include_map=args.include_map)
        print(canonical(write_new(args.output, packet)))
    elif args.command == 'admit':
        packet = json.loads(args.packet.read_bytes())
        responses = json.loads(args.responses.read_bytes())
        print(canonical(write_new(args.output, admit_results(packet, responses))))
    else:
        encoded = args.packet.read_bytes()
        if hashlib.sha256(encoded).hexdigest() != args.packet_sha256:
            raise ValueError('approved_packet_bytes_changed')
        packet = validate_packet(json.loads(encoded))
        result = asyncio.run(execute_packet(packet, endpoint=args.endpoint,
            health_endpoint=args.health_endpoint, auth_envs=dict(natural=args.natural_auth_env,
                analysis=args.analysis_auth_env), output=args.output))
        print(canonical(dict(output=str(args.output), responses=len(result['responses']),
            elapsed_seconds=result['elapsed_seconds'])))


if __name__ == '__main__':
    main()
