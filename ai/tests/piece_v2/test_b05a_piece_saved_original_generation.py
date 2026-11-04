"""Saved original -> actual CMEE/B9 candidate; no live auth, RPC or UI claim.

The source stage is explicitly supplied by this offline test caller. This does
not issue terminal eligibility or test a production preview endpoint.
"""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json

from fastapi import HTTPException
import pytest

import api_account_visibility
import piece_v2_source_adapter as adapter_module
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_json_bytes, canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
AUTH = 'Bearer synthetic-owner-session'
THOUGHT = '余裕があるなら、私が選びたいのは、陶芸です。'
ACTION = 'まだ、始める日は決めていません。'


def run(value):
    return asyncio.run(value)


def api():
    if not hasattr(adapter_module, 'project_saved_original_source'):
        pytest.fail('saved-original field projection is not implemented', pytrace=False)
    return adapter_module


def row(memo=THOUGHT, action=ACTION):
    return {'original': {'id': INPUT, 'created_at': '2026-09-26T00:00:00',
            'memo': memo, 'memo_action': action, 'category': ['生活'],
            'emotions': [], 'emotion_details': []}, 'tier': 'free',
            'now': '2026-09-26T01:00:00+00:00', 'thread': None, 'events': []}


class Store:
    def __init__(self, value):
        self.value, self.calls = value, []

    async def read(self, user_id, *, input_id=None):
        self.calls.append((user_id, input_id))
        return copy.deepcopy(self.value)

    async def commit(self, *args, **kwargs):
        pytest.fail('candidate generation must not write')


@pytest.fixture(autouse=True)
def auth(monkeypatch):
    async def verify(token):
        if token != 'synthetic-owner-session':
            raise HTTPException(401, 'private diagnostic')
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)


def source(value=None, stage='normal_observation'):
    api()
    saved = run(adapter_module.PieceSavedSourceAdapter(store=Store(value or row()))
                .resolve_original(AUTH, INPUT))
    return adapter_module.project_saved_original_source(saved, source_stage=stage)


def outcome(snapshot):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-saved-original', snapshot, OWNER, INPUT, snapshot.source_version))


def generated(value=None):
    result = outcome(source(value))
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    return result


def test_two_saved_fields_reach_the_existing_engine_without_becoming_one_field():
    result = generated()
    assert result.artifact.piece_text == '余裕があるなら、私は陶芸を選びたい。\n\n' + ACTION
    assert [e.field_path for e in result.source_meaning.evidence] == ['memo', 'memo_action']
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(row()['original'])
    assert result.artifact.as_candidate()['production_enabled'] is False
    assert result.artifact.as_candidate()['record_effect'] == result.artifact.as_candidate()['quota_effect'] == 0


@pytest.mark.parametrize('memo,action', [
    ('🌱を眺めた。\r\n私は読書を大切にしています。', '今朝は一冊を開いた。'),
    ('私は、陶芸を選びたい。', '私は、その時間を望んでいない。'),
    ('以前は、私が望んでいなかったのは、競争です。', '今も同じ気持ちかは、まだ分かりません。'),
    ('  私は読書を大切にしています。  ', '\tまだ、続ける日は決めていません。 '),
])
def test_field_relative_scalar_and_absolute_utf8_offsets_are_exact(memo, action):
    s = source(row(memo, action))
    # The unresolved-reference example must not become generated, but its
    # failure cannot be a cross-field sentence splice or dropped action.
    result = outcome(s)
    if 'その時間' in action:
        assert result.status == EngineStatus.UNAVAILABLE
        return
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    meaning = result.source_meaning
    for ev, node in zip(meaning.evidence, meaning.graph.nodes, strict=True):
        field = row(memo, action)['original'][ev.field_path]
        assert field[ev.scalar_start:ev.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[ev.utf8_start:ev.utf8_end].decode() == node.value
        assert meaning.envelope.raw_utf8[ev.field_utf8_start:ev.field_utf8_end].decode() == field
        assert ev.field_sha256 == hashlib.sha256(field.encode()).hexdigest()
    assert json.loads(meaning.saved_snapshot.saved_original_json) == row(memo, action)['original']


@pytest.mark.parametrize('empty', [None, '', ' \t\r\n'])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_one_nonempty_written_field_uses_its_actual_field_identity(empty, field):
    value = row('私は読書を大切にしています。まだ、続ける日は決めていません。', None)
    value['original'][field] = value['original']['memo']
    value['original']['memo_action' if field == 'memo' else 'memo'] = empty
    result = generated(value)
    assert {ev.field_path for ev in result.source_meaning.evidence} == {field}
    assert result.artifact.piece_text == '私は、読書を大切にしています。まだ、続ける日は決めていません。'


@pytest.mark.parametrize('memo,action', [
    ('私は読書を大切に', 'しています。まだ、続ける日は決めていません。'),
    (THOUGHT, 'まだ、始める日は'),
    (None, None),
    (THOUGHT, '「続けます」と友人が言った。'),
])
def test_incomplete_or_unadmitted_action_is_not_removed_or_completed(memo, action):
    result = outcome(source(row(memo, action)))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.mark.parametrize('field,value', [
    ('emotions', ['平穏']),
    ('emotion_details', [{'type': '平穏', 'strength': 'medium'}]),
    ('emotions', ['平穏', '不安']),
])
def test_selected_feelings_are_not_silently_discarded_to_generate_text(field, value):
    record = row()
    record['original'][field] = value
    result = outcome(source(record))
    assert result.status == EngineStatus.GENERATED
    labels = value if field == 'emotions' else [x['type'] for x in value]
    assert all(label not in result.artifact.piece_text for label in labels)
    assert len(result.source_meaning.graph.nodes) == 2
    assert len(result.source_meaning.selection_contexts) == len(labels)
    assert result.artifact.body_blocks == ('余裕があるなら、私は陶芸を選びたい。', ACTION)
    assert not result.artifact_plan.declaration_eligible


@pytest.mark.parametrize('memo', [
    '明日の面接が不安だった。',
    'もう不安ではない。',
    '友達が不安そうだった。',
    '私は不安を感じています。',
    '私は弱い不安を感じています。',
    '私は中程度の不安を感じています。私は中程度の不安を感じています。',
])
def test_nonmatching_written_feeling_keeps_selection_private(memo):
    value = row(memo, None)
    record = value['original']
    record['emotions'] = ['不安']
    record['emotion_details'] = [{'type': '不安', 'strength': 'medium'}]
    store = Store(value)
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=store)
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == memo
    assert candidate['format_type'] == 'short_essay'
    assert 'declaration' not in candidate['eligible_formats']
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]

    meaning = generated(value).source_meaning
    context, = meaning.selection_contexts
    assert json.loads(context.value) == {
        'label': '不安', 'strength': 'medium', 'scope': 'RECORDED_SELF',
    }
    assert context not in meaning.graph.nodes
    assert {row.node_id for row in meaning.selected_feelings} == {context.node_id}
    assert tuple(row.evidence_id for row in meaning.selection_evidence) == context.evidence_ids
    assert {row.record_sha256 for row in meaning.selection_evidence} == {
        hashlib.sha256(canonical_json_bytes(record)).hexdigest(),
    }


def test_exact_written_feeling_keeps_existing_source_binding():
    memo = '私は中程度の不安を感じています。'
    value = row(memo, None)
    value['original'].update(emotions=['不安'],
                             emotion_details=[{'type': '不安', 'strength': 'medium'}])
    result = generated(value)
    meaning = result.source_meaning
    evidence, = meaning.evidence
    assert meaning.selection_contexts == meaning.selection_evidence == ()
    assert {row.evidence_id for row in meaning.selected_feelings} == {evidence.evidence_id}
    assert {row.node_id for row in meaning.selected_feelings} == {meaning.graph.nodes[0].node_id}
    assert result.artifact.piece_text == memo


@pytest.mark.parametrize('tags,details', [
    (['不安'], [{'type': '喜び', 'strength': 'medium'}]),
    (['不安'], [{'type': '不安', 'strength': 'forged'}]),
    (['不安', '不安'], [{'type': '不安', 'strength': 'medium'}]),
    (['不安', '自己理解'], [{'type': '不安', 'strength': 'medium'}]),
])
def test_separate_private_selection_still_rejects_invalid_metadata(tags, details):
    value = row('もう不安ではない。', None)
    value['original'].update(emotions=tags, emotion_details=details)
    result = outcome(source(value))
    assert result.reason_codes == ('saved_emotion_meaning_not_yet_supported',)
    assert result.artifact is None


@pytest.mark.parametrize('memo,action', [
    ('明日までに返事をする。', None),
    ('明日は料理する。', None),
    ('午前中に打ち合わせをする。', None),
    ('午後はメールをする。', None),
    ('昨日の会議については保留。', '次回は資料を整理する。'),
])
def test_plain_suru_account_keeps_written_predicate_and_field_order(memo, action):
    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    store = Store(value)
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=store)
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    expected_blocks = [memo] if action is None else [memo, action]
    assert candidate['content_payload']['body_blocks'] == expected_blocks
    assert candidate['piece_text'] == '\n\n'.join(expected_blocks)
    assert 'declaration' not in candidate['eligible_formats']
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]
    assert all(duty.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
               for duty in generated(value).artifact_plan.duties)


@pytest.mark.parametrize('memo,reason', [
    ('する。', 'expression_meaning_not_admitted'),
    ('明日は準備するかも。', 'expression_meaning_not_admitted'),
    ('明日は準備するだろう。', 'expression_meaning_not_admitted'),
    ('明日準備する場合。', 'expression_meaning_not_admitted'),
    ('明日は準備する？', 'expression_meaning_not_admitted'),
    ('「明日は準備する。」と友達が言った。', 'quoted_discourse_not_yet_supported'),
    ('その作業をする。', 'unresolved_reference'),
    ('それをする。', 'unresolved_reference'),
    ('仕事をする', 'source_line_mid_sentence'),
    ('私の友人は犯罪者だ。明日は準備する。', 'existing_safety_detector'),
])
def test_plain_suru_account_does_not_override_existing_refusals(memo, reason):
    value = row(memo, None)
    value['original']['emotions'] = ['平穏']
    result = outcome(source(value))
    assert result.reason_codes == (reason,)
    assert result.artifact is None


def test_plain_suru_account_requires_existing_saved_feeling_context():
    result = outcome(source(row('明日までに返事をする。', None)))
    assert result.reason_codes == ('expression_meaning_not_admitted',)
    assert result.artifact is None


@pytest.mark.parametrize('memo,action,blocks', [
    ('今朝は資料を確認しました', None, ('今朝は資料を確認しました',)),
    ('いつもの資料を確認しました', None, ('いつもの資料を確認しました',)),
    ('ぶどうの箱を出荷しました', None, ('ぶどうの箱を出荷しました',)),
    ('なぜか資料を確認しました', None, ('なぜか資料を確認しました',)),
    ('誰かが資料を確認しました', None, ('誰かが資料を確認しました',)),
    ('誰にでも予定を共有しました', None, ('誰にでも予定を共有しました',)),
    ('昨日は予定を確認しました。 今朝は資料を整理しませんでした', None,
     ('昨日は予定を確認しました。今朝は資料を整理しませんでした',)),
    ('昨日は予定を確認しました。', '今朝は資料を整理しませんでした',
     ('昨日は予定を確認しました。', '今朝は資料を整理しませんでした')),
])
def test_saved_polite_past_terminal_stop_may_be_omitted(memo, action, blocks):
    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    result = generated(value)
    assert result.artifact.body_blocks == blocks
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert result.source_meaning.graph.nodes[len(result.source_meaning.evidence)-1].value.endswith(
        ('しました', 'しませんでした'))
    assert all(duty.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
               for duty in result.artifact_plan.duties)
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == result.artifact.piece_text


@pytest.mark.parametrize('memo,replacement', [
    ('今朝は資料を確認しました', '今朝は資料を確認しました。'),
    ('今朝は資料を確認しました', '今朝は資料を整理しました'),
    ('今朝は資料を確認しました', '今朝は資料を確認しました。明日の予定も決めました'),
    ('資料を送りました', '資料を送りました。'),
    ('資料を送りました', '資料を読みました'),
    ('資料を送りました', '資料を送りました。次の書類も送りました'),
    ('約束した資料を昨日は送りました', '約束した資料を今日も送りました'),
    ('今日は片付けを始めませんでした', '今日は片付けを始めました'),
    ('荷物を受け取りました', '荷物を送りました'),
    ('窓を閉めませんでした', '窓を閉めました'),
])
def test_independent_review_requires_exact_unpunctuated_source(memo, replacement):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row(memo, None)
    value['original']['emotions'] = ['平穏']
    result = generated(value)
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)
    artifact = replace(result.artifact, body_blocks=(replacement,), piece_text=replacement,
                       piece_text_hash=hashlib.sha256(replacement.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, artifact)


@pytest.mark.parametrize('memo,action,reason', [
    ('今朝は資料を', None, 'source_line_mid_sentence'),
    ('資料を確認しましたが', None, 'source_line_mid_sentence'),
    ('資料を確認しましたか', None, 'source_line_mid_sentence'),
    ('何を確認しました', None, 'source_line_mid_sentence'),
    ('どの資料を確認しました', None, 'source_line_mid_sentence'),
    ('どういう資料を確認しました', None, 'source_line_mid_sentence'),
    ('どこで資料を確認しました', None, 'source_line_mid_sentence'),
    ('いつ資料を確認しました', None, 'source_line_mid_sentence'),
    ('なぜ資料を確認しました', None, 'source_line_mid_sentence'),
    ('何時に資料を確認しました', None, 'source_line_mid_sentence'),
    ('何故資料を確認しました', None, 'source_line_mid_sentence'),
    ('誰が資料を確認しました', None, 'source_line_mid_sentence'),
    ('誰の資料を確認しました', None, 'source_line_mid_sentence'),
    ('だれと資料を確認しました', None, 'source_line_mid_sentence'),
    ('もし資料を確認しました', None, 'source_line_mid_sentence'),
    ('予定を確認しました。　もし資料を整理しました', None, 'source_line_mid_sentence'),
    ('昨日はそれを確認しました', None, 'unresolved_reference'),
    ('「資料を確認しました」', None, 'quoted_discourse_not_yet_supported'),
    ('それを確認しました', None, 'source_line_mid_sentence'),
    ('その資料を確認しました', None, 'unresolved_reference'),
    ('予定を確認しました\n資料を整理しました', None, 'source_line_mid_sentence'),
    ('予定を確認しました', '資料を整理しました', 'source_line_mid_sentence'),
    ('確認しました。' * 6 + '資料を整理しました', None, 'complete_sentence_required'),
])
def test_omitted_stop_does_not_license_incomplete_or_unresolved_source(memo, action, reason):
    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    result = outcome(source(value))
    assert result.reason_codes == (reason,)
    assert result.artifact is None


@pytest.mark.parametrize('memo,action', [
    ('資料を送りました', None),
    ('書類を読みました', None),
    ('窓を開けました', None),
    ('下書きを終えました', None),
    ('契約書を受け取りました', None),
    ('申込書を受け取りませんでした', None),
    ('窓を閉めました', None),
    ('玄関の鍵を閉めませんでした', None),
    ('資料を送りました。', '返送された書類を昨日は受け取りました'),
    ('窓を開けました。', '窓を先日は閉めませんでした'),
    ('今日は片付けを始めませんでした', None),
    ('夕方は片付けを始めました', None),
    ('約束した資料を昨日は送りました', None),
    ('書類を一昨日に読みませんでした', None),
    ('資料を今朝は、送りませんでした', None),
    ('何の変哲もない書類を昨日は送りました', None),
    ('昨日は予定を確認しました。', '下書きを先日は始めました'),
    ('今朝は資料を送りませんでした', None),
    ('同僚が資料を送りました', None),
    ('資料と書類を送りました', None),
    ('午後におもしろい本を読みました', None),
    ('昨日は資料を確認しました。', '今朝は窓を開けませんでした'),
])
def test_saved_lexical_past_action_keeps_exact_written_bytes(memo, action):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    result = generated(value)
    expected = memo if action is None else memo + '\n\n' + action
    assert result.artifact.piece_text.encode() == expected.encode()
    assert result.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert [node.value for node in result.source_meaning.graph.nodes] == expected.split('\n\n')
    assert all(duty.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
               for duty in result.artifact_plan.duties)
    assert 'declaration' not in result.artifact.eligible_formats
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('memo,action,reason', [
    ('資料を駅ました', None, 'source_line_mid_sentence'),
    ('窓を資料けました', None, 'source_line_mid_sentence'),
    ('書類を読やました', None, 'source_line_mid_sentence'),
    ('荷物を東京にました', None, 'source_line_mid_sentence'),
    ('契約書を受けとりました', None, 'source_line_mid_sentence'),
    ('資料を受けました', None, 'source_line_mid_sentence'),
    ('扉を閉まりました', None, 'source_line_mid_sentence'),
    ('扉が閉まりました', None, 'source_line_mid_sentence'),
    ('誰が荷物を受け取りました', None, 'source_line_mid_sentence'),
    ('どの扉を閉めました', None, 'source_line_mid_sentence'),
    ('何枚の書類を受け取りました', None, 'source_line_mid_sentence'),
    ('書類を受け取りましたか', None, 'source_line_mid_sentence'),
    ('窓を閉めませんでしたが', None, 'source_line_mid_sentence'),
    ('予定が合えば荷物を受け取りました', None, 'source_line_mid_sentence'),
    ('窓を開けたら扉を閉めました', None, 'source_line_mid_sentence'),
    ('「窓を閉めました」と言いました', None, 'quoted_discourse_not_yet_supported'),
    ('その契約書を受け取りました', None, 'unresolved_reference'),
    ('書類を受け取りました', '窓を閉めました。', 'source_line_mid_sentence'),
    ('私の友人は犯罪者だ。窓を閉めました', None, 'existing_safety_detector'),
    ('送りました', None, 'source_line_mid_sentence'),
    ('資料を送りましたが', None, 'source_line_mid_sentence'),
    ('誰が資料を送りました', None, 'source_line_mid_sentence'),
    ('何の資料を昨日は送りました', None, 'source_line_mid_sentence'),
    ('何枚の書類を先日は読みました', None, 'source_line_mid_sentence'),
    ('いくつの作業を始めました', None, 'source_line_mid_sentence'),
    ('資料をどの日に送りました', None, 'source_line_mid_sentence'),
    ('資料を昨日も送りました', None, 'source_line_mid_sentence'),
    ('資料を昨日は駅ました', None, 'source_line_mid_sentence'),
    ('資料を昨日は整理しました', None, 'source_line_mid_sentence'),
    ('予定が合えば資料を昨日は送りました', None, 'source_line_mid_sentence'),
    ('資料を昨日は送りましたので', None, 'source_line_mid_sentence'),
    ('その資料を昨日は送りました', None, 'unresolved_reference'),
    ('どこで書類を読みました', None, 'source_line_mid_sentence'),
    ('窓を開けましたか', None, 'source_line_mid_sentence'),
    ('もし資料を送りました', None, 'source_line_mid_sentence'),
    ('明日、もし資料を送りました', None, 'source_line_mid_sentence'),
    ('窓を開けたら書類を読みました', None, 'source_line_mid_sentence'),
    ('仮に窓を開けました', None, 'source_line_mid_sentence'),
    ('だから書類を読みました', None, 'source_line_mid_sentence'),
    ('つまり書類を読みました', None, 'source_line_mid_sentence'),
    ('資料を送れと言われて書類を読みました', None, 'source_line_mid_sentence'),
    ('「資料を送りました」と伝えました', None, 'quoted_discourse_not_yet_supported'),
    ('その書類を読みました', None, 'unresolved_reference'),
    ('資料を送りました\n窓を開けました', None, 'source_line_mid_sentence'),
    ('資料を送りました', '書類を確認しました。', 'source_line_mid_sentence'),
    ('私の友人は犯罪者だ。資料を送りました', None, 'existing_safety_detector'),
])
def test_saved_lexical_past_action_does_not_extend_other_language(memo, action, reason):
    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    result = outcome(source(value))
    assert result.reason_codes == (reason,)
    assert result.artifact is None


def test_saved_lexical_past_action_respects_mode_and_raw_source_boundaries():
    text = '資料を送りました'
    value = row(text, None)
    assert outcome(source(value)).reason_codes == ('expression_meaning_not_admitted',)

    value['original']['emotions'] = ['自己理解']
    snapshot = source(value)
    result = outcome(snapshot)
    assert result.artifact.piece_text == text
    assert result.source_meaning.selected_feelings == ()
    assert result.source_meaning.selection_contexts == ()
    assert outcome(replace(snapshot, saved_original_json=None)).reason_codes == (
        'source_line_mid_sentence',)

    value['original']['memo'] += '。'
    assert generated(value).artifact.piece_text == text + '。'
    assert outcome(replace(source(value), saved_original_json=None)).reason_codes == (
        'expression_meaning_not_admitted',)
    value['original']['emotions'] = []
    assert outcome(source(value)).reason_codes == ('expression_meaning_not_admitted',)
    value['original']['emotions'] = ['平穏']
    assert generated(value).artifact.piece_text == text + '。'


def test_same_literal_in_both_fields_keeps_both_propositions():
    text = '私は読書を大切にしています。'
    result = generated(row(text, text))
    assert result.artifact.piece_text == '私は、読書を大切にしています。\n\n私は、読書を大切にしています。'
    assert [e.scalar_start for e in result.source_meaning.evidence] == [0, 0]
    assert len(result.source_meaning.graph.nodes) == 2


def test_action_intent_is_not_fronted_across_the_thought_field():
    result = generated(row('今朝は窓を開けた。まだ、続ける日は決めていません。',
                           '私は読書を大切にしたい。'))
    assert result.artifact.piece_text == ('今朝は窓を開けた。まだ、続ける日は決めていません。'
                                          '\n\n私は、読書を大切にしたい。')


@pytest.mark.parametrize('which', ['field_path', 'field_digest', 'field_range', 'field_scalar', 'record', 'missing_record'])
def test_a_changed_field_or_record_binding_cannot_be_realized(which):
    result = generated()
    meaning, plan = result.source_meaning, result.artifact_plan
    first = meaning.evidence[0]
    if which == 'field_path':
        first = replace(first, field_path='memo_action')
    elif which == 'field_digest':
        first = replace(first, field_sha256='0' * 64)
    elif which == 'field_range':
        first = replace(first, field_utf8_end=first.field_utf8_end - 1)
    elif which == 'field_scalar':
        first = replace(first, scalar_start=1)
    elif which == 'record':
        altered = row()['original']; altered['category'] = ['仕事']
        meaning = replace(meaning, saved_snapshot=replace(meaning.saved_snapshot,
                          saved_original_json=canonical_json_bytes(altered)))
    else:
        meaning = replace(meaning, saved_snapshot=None)
    if which.startswith('field_'):
        meaning = replace(meaning, evidence=(first, *meaning.evidence[1:]))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


def test_projected_text_cannot_drop_the_action():
    snapshot = source()
    result = outcome(replace(snapshot, original_text=THOUGHT))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


def test_structured_metadata_changes_source_identity_without_becoming_prose():
    a = generated()
    changed = row(); changed['original']['category'] = ['仕事']
    b = generated(changed)
    assert a.source_meaning.envelope.envelope_id != b.source_meaning.envelope.envelope_id
    assert a.source_meaning.graph.graph_id != b.source_meaning.graph.graph_id
    assert a.artifact.piece_text == b.artifact.piece_text
    assert '仕事' not in b.artifact.piece_text
    assert 'original' not in json.dumps(b.as_body_free())


@pytest.mark.parametrize('stage', ['normal_observation', 'pre_question_observation'])
def test_explicit_offline_stage_is_bound_not_issued_as_terminal_eligibility(stage):
    s = source(stage=stage)
    assert s.source_stage == stage
    assert outcome(s).status == EngineStatus.GENERATED
    assert not hasattr(s, 'piece_generation_eligibility')


@pytest.mark.parametrize('stage', ['refined_observation', '', None])
def test_unproved_or_refined_stage_has_no_original_only_success(stage):
    api()
    with pytest.raises(ValueError):
        source(stage=stage)


def test_authenticated_candidate_uses_real_engine_then_revalidates(monkeypatch):
    api()
    store = Store(row())
    result = run(adapter_module.PieceSavedSourceAdapter(store=store)
                 .generate_original_candidate_for_development(AUTH, INPUT,
                    source_stage='normal_observation'))
    assert result['piece_text'] == '余裕があるなら、私は陶芸を選びたい。\n\n' + ACTION
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]
    assert result['production_enabled'] is False


@pytest.mark.parametrize('mutation', ['memo_action', 'category', 'tier', 'deleted'])
def test_source_changed_during_generation_is_not_returned(monkeypatch, mutation):
    api()
    store = Store(row())
    import piece_v2_generation
    original = piece_v2_generation.generate_piece_candidate
    def generate(*args, **kwargs):
        result = original(*args, **kwargs)
        if mutation == 'deleted':
            store.value = None
        elif mutation == 'tier':
            store.value['tier'] = 'plus'
        else:
            store.value['original'][mutation] = '違う行動。' if mutation == 'memo_action' else ['仕事']
        return result
    monkeypatch.setattr(piece_v2_generation, 'generate_piece_candidate', generate)
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=store)
            .generate_original_candidate_for_development(AUTH, INPUT,
                 source_stage='normal_observation'))


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_both_complete_body_blocks_reach_existing_b9(ratio):
    candidate = generated().artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-saved-fields-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            width = len(text) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    reconstructed = [''.join(row['text'] for row in layout['lines'] if row['block_index'] == index)
                     for index in range(2)]
    assert reconstructed == candidate['content_payload']['body_blocks']
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert layout['native_device_verified'] is False


@pytest.mark.parametrize('memo,action', [
    (THOUGHT, ACTION),
    ('以前は、私が望んでいなかったのは、競争です。', '今も同じ気持ちかは、まだ分かりません。'),
    ('私は読書を大切にしています。', '今日は一冊を開いた。毎日続けるかは、まだ決めていません。'),
    (None, '私は読書を大切にしています。まだ、毎日続けるかは決めていません。'),
])
def test_existing_sql_saved_read_reaches_actual_cmee_and_revalidation(monkeypatch, memo, action):
    api()
    import importlib.util
    import os
    from pathlib import Path
    import emlis_thread_store
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained SQL runtime required'
    path = Path(__file__).parents[1] / 'test_emlis_q2_application.py'
    spec = importlib.util.spec_from_file_location('piece_saved_generation_sql_fixture', path)
    existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
    db = existing.Database()
    try:
        assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
        assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
        assert 'code' not in db.query(
            "insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,$4,array['生活'],array[]::text[],'[]'::jsonb)",
            [INPUT, OWNER, memo, action])
        monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
        candidate = run(adapter_module.PieceSavedSourceAdapter()
            .generate_original_candidate_for_development(AUTH, INPUT,
                 source_stage='normal_observation'))
        expected = generated(row(memo, action)).artifact.as_candidate()
        assert candidate == expected
        for table in ('emlis_input_threads', 'emlis_thread_events'):
            assert db.query(f'select count(*)::int as n from public.{table}')['rows'][0]['n'] == 0
        assert candidate['production_enabled'] is False
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)
