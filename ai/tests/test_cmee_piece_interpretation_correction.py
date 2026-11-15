"""Bounded person corrections keep their real source and the existing author.

These are fictional, pure CPU sources. They do not attest a saved Emlis
receipt, authenticate a caller, access SQL, or measure an actual model reply.
The original envelope and correction projection are derived by existing owners.
"""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from unittest.mock import patch

import pytest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from piece_model_source import build_piece_model_messages
from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_generation import PieceSourceSnapshot
from cocolon_meaning_experience_engine.contracts import EngineStatus, GenerationRequest
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_thread_contracts import InterpretationCorrectionSource
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, commitment, freeze_analysis_sources,
)
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from cocolon_meaning_experience_engine.preparation_sources import piece_model_field_slots
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from cocolon_meaning_experience_engine import piece_refined as refined


RETAINED = '褒められたのに、嬉しくなかった。'
OLD = '私は仕事を続けたい'
NEW = '私は家族を守りたい'
ACTION = '私は資料を調べた。'
AI_TARGET = 'あなたは毎日すべて成功している'
AS_OF = '2026-11-14T03:06:00+00:00'


@pytest.fixture(autouse=True)
def pure_default_realization_profile(monkeypatch):
    # Provider configuration is outside these pure source/meaning tests.
    monkeypatch.setattr('piece_model_source.application_piece_realization_profile', lambda: None)


def original_source(*, memo=RETAINED + OLD + '。', action=ACTION):
    record = dict(id='piece-correction-input', created_at='2026-11-14T03:00:00',
        memo=memo, memo_action=action, category=['仕事'], emotions=['不安'],
        emotion_details=[dict(type='不安', strength='medium')])
    return PieceSourceSnapshot('piece-correction-owner', record['id'],
        'emlis.current_input_bundle.v1', '\n\n'.join(
            record[key] for key in ('memo', 'memo_action') if record[key]),
        saved_original_json=canonical_json_bytes(record))


def correction_source(original, *, operation='REVISE', explanation=None, target=AI_TARGET):
    # Stored created_at is UTC without a zone. Adapt only the existing Emlis
    # bundle input; never change the saved seven-field bytes or create an ID.
    adapted = json.loads(original.saved_original_json)
    adapted['created_at'] = datetime.fromisoformat(adapted['created_at']).replace(
        tzinfo=timezone.utc).isoformat()
    for key in ('memo', 'memo_action'):
        if adapted[key] is None:
            adapted[key] = ''
    original_ref = freeze_text_source(GenerationRequest('piece-correction-parent',
        build_emlis_current_input_bundle(adapted), original.saved_input_id)).envelope.envelope_id
    if explanation is None:
        explanation = (f'「{OLD}」ではなく「{NEW}」です。' if operation == 'REVISE'
                       else f'「{OLD}」は取り消します。')
    return InterpretationCorrectionSource('piece-correction-event', 'piece-correction-thread',
        original_ref, 'piece-disputed-ai-observation', target, explanation,
        '2026-11-14T03:05:00+00:00')


def corrected_source(*, operation='REVISE', original=None, correction=None, as_of=AS_OF,
                     explanation=None):
    original = original if original is not None else original_source()
    correction = correction if correction is not None else correction_source(
        original, operation=operation, explanation=explanation)
    op, original_ranges, correction_range, correction_commitment = refined.corrected_active_ranges(
        original, correction, as_of=as_of)
    return refined.PieceCorrectedSourceSnapshot(original=original, correction=correction,
        original_commitment='sha256:' + hashlib.sha256(original.saved_original_json).hexdigest(),
        correction_commitment=correction_commitment,
        corrected_result_identity='piece-corrected-observation', opted_in=True,
        original_active_ranges=original_ranges, correction_active_range=correction_range,
        correction_update_operation=op, as_of=as_of)


def request(source, **options):
    return PieceGenerationRequest('piece-correction-request', source, source.original.owner_id,
        source.original.saved_input_id, source.original.source_version, **options)


def produce(source, **options):
    return MeaningExperienceEngine().generate(request(source, **options))


def frozen_correction(source):
    record = json.loads(source.original.saved_original_json)
    member = AnalysisSavedRecord(source.original.owner_id, record['id'], commitment(record),
        canonical_json_bytes(record).decode('utf-8'), interpretation_corrections=(source.correction,))
    frozen = freeze_analysis_sources(AnalysisObservedMapRequest('piece-correction-freeze',
        source.original.owner_id, '2026-11-14T03:00:00+00:00', source.as_of, (member,)))
    return next(item for item in frozen.sources
                if item.envelope.source_role == 'USER_INTERPRETATION_CORRECTION')


def model_result(source, blocks):
    req = request(source)
    prepared = prepare_piece_model_request(req)
    keys = list(piece_model_field_slots(prepared.payload()))
    # The closed field-slot response cannot add, merge, or silently drop slots.
    assert len(keys) == len(blocks)
    raw = json.dumps(dict(field_blocks=dict(zip(keys, blocks, strict=True))), ensure_ascii=False)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT)
    return MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('operation,expected', [
    ('REVISE', (RETAINED, ACTION, NEW)),
    ('WITHDRAW', (RETAINED, ACTION)),
])
def test_explicit_update_retains_every_unmodified_field_and_only_the_person_replacement(
        tier, operation, expected):
    source = corrected_source(operation=operation)
    before = source.original.saved_original_json, asdict(source.correction)
    outcome = produce(source, tier=tier)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    assert outcome.artifact.body_blocks == expected
    assert outcome.artifact.piece_text == '\n\n'.join(expected)
    assert outcome.artifact.eligible_formats == ('short_essay',)
    assert OLD not in outcome.artifact.piece_text and AI_TARGET not in outcome.artifact.piece_text
    assert outcome.artifact_plan.source_roles == (
        'ORIGINAL_USER_INPUT', 'USER_INTERPRETATION_CORRECTION')
    assert source.original_active_ranges == (
        ('memo', 0, len(RETAINED)), ('memo_action', 0, len(ACTION)))
    assert before == (source.original.saved_original_json, asdict(source.correction))
    if operation == 'WITHDRAW':
        assert source.correction_active_range is None
        assert outcome.source_meaning.supplemental is None
    else:
        start = source.correction.explanation.index(NEW)
        assert source.correction_active_range == (start, start + len(NEW))


def test_replacement_evidence_uses_existing_correction_bytes_and_absolute_explanation_coordinates():
    source = corrected_source()
    outcome = produce(source)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    meaning = outcome.source_meaning.supplemental
    frozen = frozen_correction(source)
    assert type(meaning) is refined.PieceCorrectionMeaning
    assert meaning.source_snapshot == source and meaning.frozen_correction == frozen
    assert meaning.envelope == frozen.envelope
    assert meaning.envelope.source_role == 'USER_INTERPRETATION_CORRECTION'
    assert source.correction_commitment == 'sha256:' + frozen.envelope.raw_sha256
    assert meaning.saved_snapshot is None and not meaning.selected_feelings
    assert meaning.active_range == source.correction_active_range
    assert len(meaning.graph.nodes) == len(meaning.sentences) == len(meaning.evidence) == 1
    for node, sentence, evidence in zip(
            meaning.graph.nodes, meaning.sentences, meaning.evidence, strict=True):
        literal = source.correction.explanation[evidence.scalar_start:evidence.scalar_end]
        assert literal == NEW == node.value
        assert (sentence.source_start, sentence.source_end) == source.correction_active_range
        assert evidence.field_path == 'memo'
        assert evidence.source_envelope_id == frozen.envelope.envelope_id
        assert frozen.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == literal
        assert evidence.field_sha256 == hashlib.sha256(source.correction.explanation.encode()).hexdigest()
        assert evidence.literal_sha256 == hashlib.sha256(literal.encode()).hexdigest()
    assert AI_TARGET not in json.dumps(asdict(outcome.artifact_plan), ensure_ascii=False)


@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_prepared_writer_and_independent_model_review_keep_corrected_source_roles(operation):
    source = corrected_source(operation=operation)
    req = request(source)
    prepared = prepare_piece_model_request(req)
    original_prepared = prepared.private_json
    messages = build_piece_model_messages(prepared,
        include_authoring_constraints=True, source_request=req)
    material = json.loads(messages[1]['content'])
    assert [item['role'] for item in material['sources']] == [
        'ORIGINAL_INPUT', 'USER_INTERPRETATION_CORRECTION']
    assert len({item['source_id'] for item in material['sources']}) == 2
    assert AI_TARGET not in messages[1]['content'] and OLD not in messages[1]['content']
    assert 'ではなく' not in messages[1]['content'] and '取り消します' not in messages[1]['content']
    assert (NEW in messages[1]['content']) == (operation == 'REVISE')
    assert prepared.private_json == original_prepared
    native = produce(source)
    assert native.status is EngineStatus.GENERATED, native.reason_codes
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
               side_effect=AssertionError('model review must not replay the sole author')):
        modeled = model_result(source, native.artifact.body_blocks)
    assert modeled.status is EngineStatus.GENERATED, modeled.reason_codes
    assert modeled.artifact == native.artifact


def test_later_qualification_clock_does_not_create_a_new_source_identity_or_prepared_request():
    source = corrected_source()
    later = replace(source, as_of='2026-11-14T03:07:00+00:00')
    assert source.as_of != later.as_of
    assert refined.refined_source_ref(source) == refined.refined_source_ref(later)
    first = prepare_piece_model_request(request(source))
    second = prepare_piece_model_request(request(later))
    assert first.private_json == second.private_json
    assert first.request_id == second.request_id


@pytest.mark.parametrize('operation', ['REVISE', 'WITHDRAW'])
def test_private_same_artifact_reread_never_reenters_source_parser_author_or_engine(operation):
    source = corrected_source(operation=operation)
    outcome = produce(source)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    raw = refined.serialize_refined_piece(outcome)
    state = json.loads(raw)
    assert state['sources']['correction'] == asdict(source.correction)
    assert state['plan']['source_roles'] == ['ORIGINAL_USER_INPUT', 'USER_INTERPRETATION_CORRECTION']
    forbidden = AssertionError('fixed saved correction artifact must not regenerate')
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=forbidden), \
         patch.object(refined, 'build_refined_meaning', side_effect=forbidden), \
         patch.object(refined, '_plans', side_effect=forbidden), \
         patch.object(refined, 'validate_refined_preservation', side_effect=forbidden), \
         patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden):
        assert refined.read_saved_refined_artifact(raw,
            expected_state_sha256=hashlib.sha256(raw).hexdigest()) == outcome.artifact


@pytest.mark.parametrize('change', [
    dict(opted_in=False), dict(opted_in=1), dict(corrected_result_identity=''),
    dict(corrected_result_identity='piece-correction-input'),
    dict(corrected_result_identity='piece-correction-event'),
    dict(corrected_result_identity='piece-disputed-ai-observation'),
    dict(original_commitment='sha256:' + '0' * 64),
    dict(correction_commitment='sha256:' + '0' * 64),
    dict(correction_update_operation='ADD'), dict(correction_update_operation='WITHDRAW'),
    dict(correction_active_range=None), dict(correction_active_range=(1, 1 + len(OLD))),
    dict(original_active_ranges=(('memo', 0, len(RETAINED + OLD + '。')),)),
    dict(as_of='2026-11-14T03:04:59+00:00'), dict(as_of='invalid-clock'),
])
def test_rehashed_or_forged_private_selection_does_not_change_the_derived_update(change):
    out = produce(replace(corrected_source(), **change))
    assert out.status is not EngineStatus.GENERATED and out.artifact is None


@pytest.mark.parametrize('change', [
    dict(original_source_ref='foreign-original-envelope'),
    dict(source_role='SUPPLEMENTAL_ANSWER'),
    dict(recorded_at='2026-11-14T03:06:01+00:00'),
    dict(explanation=f'「{OLD}」ではなく「私は料理を選びたい」です。'),
])
def test_changed_correction_cannot_reuse_the_old_source_commitment_or_parent(change):
    source = corrected_source()
    out = produce(replace(source, correction=replace(source.correction, **change)))
    assert out.status is not EngineStatus.GENERATED and out.artifact is None


@pytest.mark.parametrize('explanation', [
    '違います。', '私は家族を守りたい。',
    f'「{OLD}」ではなく「友人は家族を守りたい」です。',
    f'「{OLD}」ではなく「家族」です。',
    f'「{OLD}」ではなく「私は家族を守りたいなら」です。',
    f'「{AI_TARGET}」ではなく「{NEW}」です。',
])
def test_incomplete_nonself_or_ai_target_updates_never_gain_piece_source_meaning(explanation):
    try:
        source = corrected_source(explanation=explanation)
    except (PieceContractError, ValueError):
        return
    outcome = produce(source)
    assert outcome.status is not EngineStatus.GENERATED and outcome.artifact is None


def test_withdrawing_the_only_original_claim_does_not_create_an_empty_original_alias():
    original = original_source(memo=OLD + '。', action=None)
    with pytest.raises((PieceContractError, ValueError)):
        corrected_source(operation='WITHDRAW', original=original)


def test_original_duplicate_clause_does_not_choose_an_arbitrary_correction_target():
    original = original_source(memo=OLD + '。', action=OLD + '。')
    with pytest.raises((PieceContractError, ValueError)):
        corrected_source(original=original)


def test_four_required_blocks_are_rejected_without_discarding_a_source_paragraph():
    original = original_source(memo=RETAINED + '\n誘われたのに、悲しかった。' + OLD + '。')
    before_update = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'piece-original-three-paragraphs', original, original.owner_id,
        original.saved_input_id, original.source_version))
    assert before_update.status is EngineStatus.GENERATED, before_update.reason_codes
    assert len(before_update.artifact.body_blocks) == 3
    source = corrected_source(original=original)
    before = source.original.saved_original_json, asdict(source.correction)
    assert produce(source).status is not EngineStatus.GENERATED
    with pytest.raises((PieceContractError, ValueError)):
        prepare_piece_model_request(request(source))
    assert before == (source.original.saved_original_json, asdict(source.correction))


@pytest.mark.parametrize('wrong_replacement', [
    OLD + '。', '私は家族を守りたくない。', '友人は家族を守りたい。',
    NEW + '。だから安心した。', AI_TARGET + '。',
])
def test_independent_model_review_rejects_old_revival_new_literals_roles_and_polarity(wrong_replacement):
    source = corrected_source()
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
               side_effect=AssertionError('independent model review must not use the author')):
        result = model_result(source, (RETAINED, ACTION, wrong_replacement))
    assert result.status is not EngineStatus.GENERATED and result.artifact is None


def test_model_cannot_drop_a_required_correction_slot_even_with_new_receipt():
    source = corrected_source()
    req = request(source)
    prepared = prepare_piece_model_request(req)
    receipt = receive_piece_model_candidate(prepared,
        raw_output=json.dumps(dict(body_blocks=[RETAINED, ACTION]), ensure_ascii=False),
        finish_reason='stop')
    result = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    assert result.status is not EngineStatus.GENERATED and result.artifact is None


def test_valid_correction_child_cannot_be_grafted_under_another_corrected_source():
    from piece_v2_content_policy import validate_piece_model_preservation

    first_source = corrected_source()
    other_literal = '私は資料を読みたい'
    other_correction = replace(correction_source(first_source.original,
        explanation=f'「{OLD}」ではなく「{other_literal}」です。'),
        correction_id='piece-other-correction-event')
    other_source = replace(corrected_source(original=first_source.original,
        correction=other_correction), corrected_result_identity='piece-other-corrected-observation')
    first, other = produce(first_source), produce(other_source)
    # The borrowed child is itself legitimate, with a distinct real source
    # identity. The negative case must fail on its graft, not unread grammar.
    assert first.status is EngineStatus.GENERATED, first.reason_codes
    assert other.status is EngineStatus.GENERATED, other.reason_codes
    assert other.artifact.body_blocks == (RETAINED, ACTION, other_literal)
    assert (first.source_meaning.supplemental.envelope.envelope_id
            != other.source_meaning.supplemental.envelope.envelope_id)
    grafted = replace(first.source_meaning, supplemental=other.source_meaning.supplemental)
    plan = replace(first.artifact_plan, supplemental_plan=other.artifact_plan.supplemental_plan)
    assert grafted.source == first.source_meaning.source
    assert grafted.source_ref == first.source_meaning.source_ref
    assert plan.original_plan == first.artifact_plan.original_plan
    blocks = first.artifact.body_blocks[:-1] + other.artifact.body_blocks[-1:]
    text = '\n\n'.join(blocks)
    artifact = replace(first.artifact, body_blocks=blocks, piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode('utf-8')).hexdigest())
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
               side_effect=AssertionError('whole-source review must not replay the author')):
        with pytest.raises(PieceContractError):
            validate_piece_model_preservation(grafted, plan, artifact)


@pytest.mark.parametrize('requested_format', ['quote', 'declaration'])
def test_correction_composition_does_not_award_an_additional_format(requested_format):
    assert produce(corrected_source(), tier='premium', requested_format=requested_format).artifact is None


def test_new_process_rederives_the_same_source_and_preparation_after_a_later_qualification():
    import subprocess
    import sys
    from pathlib import Path

    source = corrected_source()
    # This pure test owns the no-realization-profile preparation. Do not read
    # an application provider selector or any endpoint/model/key settings.
    with patch('piece_model_source.application_piece_realization_profile', return_value=None):
        prepared = prepare_piece_model_request(request(source))
    expected = dict(source_ref=refined.refined_source_ref(source), request_id=prepared.request_id,
        private_json_sha256=hashlib.sha256(prepared.private_json.encode('utf-8')).hexdigest())
    test_folder = Path(__file__).resolve().parent
    code = 'import sys\nsys.path.insert(0, ' + repr(str(test_folder)) + ')\n' + '''
import hashlib
import json
from unittest.mock import patch
from test_cmee_piece_interpretation_correction import (
    corrected_source, request, refined, prepare_piece_model_request,
)
source = corrected_source(as_of='2026-11-14T03:07:00+00:00')
with patch('piece_model_source.application_piece_realization_profile', return_value=None):
    prepared = prepare_piece_model_request(request(source))
print(json.dumps(dict(source_ref=refined.refined_source_ref(source),
    request_id=prepared.request_id,
    private_json_sha256=hashlib.sha256(prepared.private_json.encode('utf-8')).hexdigest())))
'''
    completed = subprocess.run([sys.executable, '-B', '-c', code],
        cwd=test_folder.parents[1], capture_output=True, text=True, check=True, timeout=30)
    assert json.loads(completed.stdout) == expected


@pytest.mark.parametrize('requested_format', [None, 'quote', 'declaration'])
def test_corrected_withdrawal_realization_profile_keeps_the_composite_format_boundary(requested_format):
    from cocolon_meaning_experience_engine.piece_v1c import (
        MODEL_REALIZATION_PROFILE, realize_piece_artifact,
    )

    original = original_source(memo=OLD + '。私は、静かに考える時間を大切にしたい。', action='')
    source = corrected_source(operation='WITHDRAW', original=original)
    native = produce(source, tier='premium')
    assert native.status is EngineStatus.GENERATED, native.reason_codes
    assert native.artifact_plan.eligible_formats == ('short_essay',)
    assert len(native.artifact.body_blocks) == 1
    reference = realize_piece_artifact(native.source_meaning.original,
        native.artifact_plan.original_plan, tier='premium', requested_format=None)
    assert {'quote', 'declaration'} <= set(reference.eligible_formats)
    req = request(source, tier='premium', requested_format=requested_format)
    prepared = prepare_piece_model_request(req, realization_profile=MODEL_REALIZATION_PROFILE)
    keys = list(piece_model_field_slots(prepared.payload()))
    assert len(keys) == len(native.artifact.body_blocks)
    raw = json.dumps(dict(field_blocks=dict(zip(keys, native.artifact.body_blocks, strict=True))),
        ensure_ascii=False)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT, realization_profile=MODEL_REALIZATION_PROFILE)
    result = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    if requested_format is None:
        assert result.status is EngineStatus.GENERATED, result.reason_codes
        assert result.artifact.format_type == 'short_essay'
        assert result.artifact.eligible_formats == ('short_essay',)
    else:
        assert result.status is not EngineStatus.GENERATED and result.artifact is None


@pytest.mark.parametrize('first,second', [(a,b) for a in ('REVISE','WITHDRAW') for b in ('REVISE','WITHDRAW')])
@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_distinct_original_corrections_keep_all_effective_sources(first, second, tier):
    original = original_source()
    a = correction_source(original, operation=first)
    explanation = ('「私は資料を調べた」ではなく「私は約束を守りたい」です。'
        if second == 'REVISE' else '「私は資料を調べた」は取り消します。')
    b = replace(correction_source(original, explanation=explanation),
        correction_id='piece-correction-event-2', target_event_id='piece-corrected-observation-1',
        recorded_at='2026-11-14T03:05:30+00:00')
    op, ranges, active, commitment = refined.corrected_active_ranges(original, b, as_of=AS_OF, prior_corrections=(a,))
    source = replace(corrected_source(original=original, correction=b), prior_corrections=(a,),
        correction_update_operation=op, original_active_ranges=ranges,
        correction_active_range=active, correction_commitment=commitment)
    outcome = produce(source, tier=tier)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    text = outcome.artifact.piece_text
    assert RETAINED in text
    assert ('私は家族を守りたい' in text) == (first == 'REVISE')
    assert ('私は約束を守りたい' in text) == (second == 'REVISE')
    assert '私は仕事を続けたい' not in text and '私は資料を調べた' not in text
    assert 'ではなく' not in text and AI_TARGET not in text
    prepared = prepare_piece_model_request(request(source, tier=tier))
    slots = piece_model_field_slots(prepared.payload())
    assert len(slots) == 1 + (first == 'REVISE') + (second == 'REVISE')
    messages = build_piece_model_messages(prepared, include_authoring_constraints=True, source_request=request(source, tier=tier))
    sent = json.dumps(messages, ensure_ascii=False)
    assert AI_TARGET not in sent and '私は仕事を続けたい' not in sent and '私は資料を調べた' not in sent
    raw = refined.serialize_refined_piece(outcome)
    assert refined.read_saved_refined_artifact(raw, expected_state_sha256=hashlib.sha256(raw).hexdigest()) == outcome.artifact
    assert len(json.loads(raw)['plan']['prior_revision_plans']) == (first == 'REVISE')


@pytest.mark.parametrize('change', ['thread','parent','after_latest','before_original','order','repeat_target','prior_replacement'])
def test_correction_history_cannot_graft_or_revive_a_source(change):
    original = original_source()
    a = correction_source(original)
    b = replace(a, correction_id='second-event', target_event_id='second-target',
        recorded_at='2026-11-14T03:05:30+00:00', explanation='「私は資料を調べた」は取り消します。')
    if change == 'thread': a = replace(a, thread_id='another-thread')
    if change == 'parent': a = replace(a, original_source_ref='another-original')
    if change == 'after_latest': a = replace(a, recorded_at='2026-11-14T03:07:00+00:00')
    if change == 'before_original': a = replace(a, recorded_at='2026-11-14T02:59:00+00:00')
    if change == 'order': a,b = b,a
    if change == 'repeat_target': b = replace(b, explanation='「私は仕事を続けたい」は取り消します。')
    if change == 'prior_replacement': b = replace(b, explanation='「私は家族を守りたい」は取り消します。')
    with pytest.raises((PieceContractError,ValueError)):
        refined.corrected_active_ranges(original,b,as_of=AS_OF,prior_corrections=(a,))


def test_correction_count_is_not_question_round_limit():
    original = original_source(memo='私は仕事を続けたい。私は資料を調べた。私は計画を作った。',
        action='私はメモを書いた。私は記録を残した。')
    clauses = ['私は資料を調べた','私は計画を作った','私はメモを書いた','私は記録を残した']
    corrections = tuple(replace(correction_source(original,explanation=f'「{text}」は取り消します。'),
        correction_id=f'withdraw-{i}',target_event_id=f'target-{i}',recorded_at=f'2026-11-14T03:05:0{i}+00:00')
        for i,text in enumerate(clauses))
    last,prior = corrections[-1],corrections[:-1]
    op,ranges,active,commitment = refined.corrected_active_ranges(original,last,as_of=AS_OF,prior_corrections=prior)
    source = replace(corrected_source(original=original,correction=last),prior_corrections=prior,
        correction_update_operation=op,original_active_ranges=ranges,correction_active_range=active,correction_commitment=commitment)
    outcome = produce(source)
    assert outcome.status is EngineStatus.GENERATED,outcome.reason_codes
    assert outcome.artifact.piece_text == '私は、仕事を続けたい。'


def test_multiple_correction_model_review_keeps_each_proper_partition():
    original = original_source()
    prior = correction_source(original)
    latest = replace(prior, correction_id='latest-proper-explanation',target_event_id='previous-corrected-observation',
        recorded_at='2026-11-14T03:05:30+00:00',
        explanation='「私は資料を調べた」ではなく「私は約束を守りたい」です。')
    op,ranges,active,commitment = refined.corrected_active_ranges(original,latest,as_of=AS_OF,prior_corrections=(prior,))
    source = replace(corrected_source(original=original,correction=latest),prior_corrections=(prior,),
        correction_update_operation=op,original_active_ranges=ranges,correction_active_range=active,correction_commitment=commitment)
    native = produce(source)
    assert native.status is EngineStatus.GENERATED,native.reason_codes
    blocks = native.artifact.body_blocks
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
               side_effect=AssertionError('model S7 must not replay the author')):
        assert model_result(source,blocks).status is EngineStatus.GENERATED
        for altered in ((blocks[0],blocks[2],blocks[1]), (blocks[0],OLD,blocks[2]),
            (blocks[0],blocks[1],ACTION), (AI_TARGET,blocks[1],blocks[2])):
            result = model_result(source,altered)
            assert result.status is not EngineStatus.GENERATED and result.artifact is None
        grafted = replace(native.source_meaning,prior_revisions=(native.source_meaning.supplemental,))
        with pytest.raises(PieceContractError):
            from piece_v2_content_policy import validate_piece_model_preservation
            validate_piece_model_preservation(grafted,native.artifact_plan,native.artifact)


def mixed_source(*, answers=('私は寂しかった。',), operation='REVISE'):
    from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
    original=original_source(); correction=correction_source(original,explanation=(
        '「私は資料を調べた」ではなく「私は約束を守りたい」です。' if operation=='REVISE'
        else '「私は資料を調べた」は取り消します。'))
    sources=tuple(SupplementalAnswerSource('mixed-answer-'+str(i),correction.thread_id,'logical-question-'+str(i),i,
        correction.original_source_ref,text,f'2026-11-14T03:04:0{i}+00:00') for i,text in enumerate(answers,1))
    op,ranges,active,commitment=refined.corrected_active_ranges(original,correction,as_of=AS_OF,answer_sources=sources)
    return replace(corrected_source(original=original,correction=correction),answer_sources=sources,
        selected_answer_id=sources[-1].answer_id,question_need_decision_identity='mixed-question-event',
        correction_update_operation=op,original_active_ranges=ranges,correction_active_range=active,correction_commitment=commitment)


@pytest.mark.parametrize('rounds',[1,2,3])
@pytest.mark.parametrize('operation',['REVISE','WITHDRAW'])
@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_selected_real_answer_and_proper_correction_keep_separate_sources(rounds,operation,tier):
    texts=('私は怖かった。',)*(rounds-1)+('私は嬉しかった。',)
    source=mixed_source(answers=texts,operation=operation)
    out=produce(source,tier=tier)
    assert out.status is EngineStatus.GENERATED,out.reason_codes
    assert texts[-1] in out.artifact.piece_text
    assert all(text not in out.artifact.piece_text for text in texts[:-1])
    assert '私は資料を調べた' not in out.artifact.piece_text
    assert ('私は約束を守りたい' in out.artifact.piece_text)==(operation=='REVISE')
    prepared=prepare_piece_model_request(request(source,tier=tier))
    assert len(piece_model_field_slots(prepared.payload()))==len(out.artifact.body_blocks)
    assert model_result(source,out.artifact.body_blocks).status is EngineStatus.GENERATED
    raw=refined.serialize_refined_piece(out)
    assert refined.read_saved_refined_artifact(raw,expected_state_sha256=hashlib.sha256(raw).hexdigest())==out.artifact


@pytest.mark.parametrize('answer_operation',['REVISE','WITHDRAW'])
@pytest.mark.parametrize('correction_operation',['REVISE','WITHDRAW'])
def test_original_clause_answer_update_and_later_proper_correction_compose(answer_operation,correction_operation):
    text=('「私は仕事を続けたい」ではなく「私は家族を守りたい」です。' if answer_operation=='REVISE'
        else '「私は仕事を続けたい」は取り消します。')
    source=mixed_source(answers=(text,),operation=correction_operation)
    out=produce(source)
    assert out.status is EngineStatus.GENERATED,out.reason_codes
    assert '私は仕事を続けたい' not in out.artifact.piece_text
    assert '私は資料を調べた' not in out.artifact.piece_text
    assert ('私は家族を守りたい' in out.artifact.piece_text)==(answer_operation=='REVISE')
    assert ('私は約束を守りたい' in out.artifact.piece_text)==(correction_operation=='REVISE')


def test_same_quoted_clause_in_an_answer_is_not_silently_an_original_only_correction():
    with pytest.raises((PieceContractError,ValueError)):
        mixed_source(answers=('私は資料を調べた。',),operation='WITHDRAW')


def test_unread_selected_answer_keeps_mixed_source_pending():
    with pytest.raises((PieceContractError,ValueError)):
        mixed_source(answers=('私は怖かった。',))


def test_readable_answer_and_new_proper_replacement_cannot_contradict():
    with pytest.raises((PieceContractError,ValueError)):
        mixed_source(answers=('私は約束を守りたくない。',))
