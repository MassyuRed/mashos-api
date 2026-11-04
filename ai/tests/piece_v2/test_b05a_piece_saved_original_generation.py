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

FOCAL_PAUSE_CASES = (
    '私が選びたいのは、{gap}陶芸です。',
    '私が望んでいなかったのは、{gap}競争です！',
    '私が望んでいなかったかもしれないのは、{gap}競争です!',
    '余裕があるなら、私が選びたいのは、{gap}陶芸です。',
    '以前は、私が望んでいなかったのは、{gap}競争です。',
    '私にとって大切なのは、{gap}家族です。',
    '私にとって大切ではなかったのは、{gap}家族です！',
    '私にとって必要だったとは限らないのは、{gap}家族です!',
)

WRITTEN_FEELING_FORMS = ('ています', 'ていません', 'ていました', 'ていませんでした',
                         'ます', 'ません', 'ました', 'ませんでした')


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


@pytest.mark.parametrize('statement,expected,literal', [
    ('余裕があるなら、私は静かに休みたい', '私は、余裕があるなら、静かに休みたい', True),
    ('準備できるならば、僕は遠くへ行きたくない', '僕は、準備できるならば、遠くへ行きたくない', False),
    ('少し疲れているので、私は静かに休みたい', '私は、少し疲れているので、静かに休みたい', True),
    ('まだ迷っているけれど、私は遠くへ行きたい', 'まだ迷っているけれど、私は、遠くへ行きたい', False),
    ('まだ迷っているけれども、私は遠くへ行きたくないです',
     'まだ迷っているけれども、私は、遠くへ行きたくないです', False),
])
@pytest.mark.parametrize('stop', ('。', '！', '!'))
def test_saved_simple_scope_keeps_its_terminator_and_independent_preservation(statement, expected, literal, stop):
    from piece_v2_content_policy import validate_source_meaning_preservation
    value = row(statement + stop, ACTION)
    value['original']['emotions'] = ['自己理解']
    snapshot = source(value)
    result = outcome(snapshot)
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    first = (statement if literal and stop != '。' else expected) + stop
    assert result.artifact.body_blocks == (first, ACTION)
    assert result.artifact.eligible_formats == ('short_essay',)
    assert len(result.source_meaning.expression_scopes) == 1
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(value['original'])
    for node, evidence in zip(result.source_meaning.graph.nodes, result.source_meaning.evidence, strict=True):
        field = value['original'][evidence.field_path]
        assert field[evidence.scalar_start:evidence.scalar_end] == node.value
        assert result.source_meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)
    if stop != '。':
        blocks = (first[:-1] + '。', ACTION)
        body = '\n\n'.join(blocks)
        corrupted = replace(result.artifact, body_blocks=blocks, piece_text=body,
                            piece_text_hash=hashlib.sha256(body.encode()).hexdigest())
        with pytest.raises(ValueError):
            validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, corrupted)


@pytest.mark.parametrize('text', (
    '余裕があるなら、私はたい！', '余裕があるなら、私はたい!',
    '余裕があるなら、友人は静かに休みたい！',
    '余裕があるなら、私は休みたいと言われたい!',
    '余裕があるなら、私は静かに休みたい？',
    '余裕があるなら、私は静かに休みたい!!',
))
def test_scope_terminal_view_does_not_admit_an_empty_other_reported_or_question_body(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('stop', ('！', '!'))
def test_literal_scoped_comparison_keeps_its_existing_saved_literal_body(stop):
    from piece_v2_content_policy import validate_source_meaning_preservation
    value = row('余裕があるなら、私は猫みたい' + stop, '本を読みました。')
    value['original']['emotions'] = ['平穏']
    result = outcome(source(value))
    assert result.status == EngineStatus.GENERATED
    assert result.artifact.body_blocks == (value['original']['memo'], value['original']['memo_action'])
    assert len(result.source_meaning.expression_scopes) == 1
    assert result.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert not result.artifact_plan.declaration_eligible
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)
    for first in ('私は、余裕があるなら、猫みたい' + stop,
                  '余裕があるなら、猫みたい' + stop,
                  '余裕があるので、私は猫みたい' + stop):
        blocks = (first, value['original']['memo_action'])
        body = '\n\n'.join(blocks)
        altered = replace(result.artifact, body_blocks=blocks, piece_text=body,
                          piece_text_hash=hashlib.sha256(body.encode()).hexdigest())
        with pytest.raises(ValueError):
            validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, altered)


def generated(value=None):
    result = outcome(source(value))
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    return result


@pytest.mark.parametrize('template', FOCAL_PAUSE_CASES)
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
@pytest.mark.parametrize('layout', ('thought', 'action'))
def test_focal_pause_gap_keeps_complete_meaning_and_saved_field_coordinates(template, gap, mode, layout):
    def value_for(space):
        expression = template.format(gap=space)
        value = row(expression, '姉はまだ分かりません。') if layout == 'thought' else row(
            '🌱を見た。', expression + '姉はまだ分かりません。')
        value['original']['emotions'] = [mode]
        return value

    value = value_for(gap)
    plain = generated(value_for(''))
    result = generated(value)
    assert result.artifact.as_candidate() == plain.artifact.as_candidate()
    assert result.artifact_plan.declaration_eligible == plain.artifact_plan.declaration_eligible
    assert result.source_meaning.saved_snapshot.saved_original_json == canonical_json_bytes(value['original'])
    raw = result.source_meaning.envelope.raw_utf8
    for node, ev in zip(result.source_meaning.graph.nodes, result.source_meaning.evidence, strict=True):
        field = value['original'][ev.field_path]
        assert field[ev.scalar_start:ev.scalar_end] == node.value
        assert raw[ev.utf8_start:ev.utf8_end].decode('utf-8') == node.value
        assert raw[ev.field_utf8_start:ev.field_utf8_end].decode('utf-8') == field
    meaning_text = raw.decode('utf-8')
    for frame in result.source_meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert meaning_text[slice(*scalar)] == raw[slice(*utf8)].decode('utf-8')
        assert not meaning_text[slice(*frame.scalar_parts[2])].startswith((' ', '\t', '\u3000'))


@pytest.mark.parametrize('separator', ('', '、', '，', ','))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
def test_focal_gap_only_follows_the_existing_optional_single_separator(separator, gap, mode):
    value = row(f'私が選びたいのは{separator}{gap}陶芸です。', '姉はまだ分かりません。')
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.piece_text == '私は、陶芸を選びたい。\n\n姉はまだ分かりません。'


@pytest.mark.parametrize('prefix', ('私が望んでいたのは、', '私にとって必要ではなかったのは、'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
@pytest.mark.parametrize('field', ('memo', 'memo_action'))
def test_focal_gap_keeps_the_same_unique_reference_and_raw_span(prefix, gap, mode, field):
    previous = '私は窓辺で草花を眺めて過ごす時間を大切にしています。'
    value = row(previous, '姉はまだ分かりません。')
    value['original'][field] += prefix + gap + 'その時間です。'
    value['original']['emotions'] = [mode]
    plain = copy.deepcopy(value)
    plain['original'][field] = plain['original'][field].replace(prefix + gap, prefix)
    result = generated(value)
    assert result.artifact.as_candidate() == generated(plain).artifact.as_candidate()
    meaning = result.source_meaning
    raw = meaning.envelope.raw_utf8
    reference, = meaning.nominal_references
    assert raw[slice(*reference.reference_utf8_span)].decode('utf-8') == 'その時間'
    assert raw.decode('utf-8')[slice(*reference.reference_scalar_span)] == 'その時間'
    assert raw[slice(*reference.antecedent_utf8_span)].decode('utf-8') == '窓辺で草花を眺めて過ごす時間'


@pytest.mark.parametrize('expression,expected', (
    ('私が望んでいたのは、{gap}自分の 時間です。', '私は、自分の 時間を望んでいた。'),
    ('私にとって必要なのは、{gap}自分の 時間です。', '私にとって、自分の 時間が必要です。'),
))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
def test_only_the_focal_separator_gap_is_removed_from_the_visible_argument(expression, expected, gap):
    value = row(expression.format(gap=gap), None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    assert result.artifact.piece_text == expected
    assert '自分の 時間' in result.artifact.piece_text


@pytest.mark.parametrize('text', (
    '私が選びたいのは、 、陶芸です。',
    '私が選びたいのは、、 陶芸です。',
    '私にとって大切なのは、 、家族です。',
    '私にとって大切なのは、、 家族です。',
    '私が選びたいのは、\n陶芸です。',
    '私が選びたいのは、 陶 芸です。',
))
@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
def test_focal_horizontal_pause_does_not_join_lines_or_admit_extra_separators(text, mode):
    value = row(text, '姉はまだ分かりません。')
    value['original']['emotions'] = [mode]
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('old,new', (
    ('競争', '陶芸'), ('望んでいなかった', '望んでいる'), ('姉', '私'), ('！', '。'),
))
def test_focal_separator_fix_does_not_authorize_a_changed_target_tense_actor_or_stop(old, new):
    from piece_v2_content_policy import validate_source_meaning_preservation
    from piece_v2_contract import PieceContractError
    value = row('以前は、私が望んでいなかったのは、\u3000競争です！', '姉はまだ分かりません。')
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    blocks = tuple(block.replace(old, new) for block in result.artifact.body_blocks)
    text = '\n\n'.join(blocks)
    corrupted = replace(result.artifact, body_blocks=blocks, piece_text=text,
                        piece_text_hash=hashlib.sha256(text.encode('utf-8')).hexdigest())
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, corrupted)


@pytest.mark.parametrize('prefix', ('私は', '私は、', '僕は，'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('predicate', ('選びたい', '大切にしたくない'))
@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
@pytest.mark.parametrize('field', ('memo', 'memo_action'))
def test_direct_wish_separator_has_the_same_body_in_the_writer_and_independent_review(prefix, gap, predicate, mode, field):
    from piece_v2_content_policy import validate_source_meaning_preservation
    expression = prefix + gap + '陶芸を' + predicate + '。'
    value = row(expression, '姉はまだ分かりません。') if field == 'memo' else row(
        '🌱を見た。', expression + '姉はまだ分かりません。')
    value['original']['emotions'] = [mode]
    plain = copy.deepcopy(value)
    plain['original'][field] = plain['original'][field].replace(prefix + gap, prefix)
    result = generated(value)
    assert result.artifact.as_candidate() == generated(plain).artifact.as_candidate()
    assert result.artifact_plan.declaration_eligible == generated(plain).artifact_plan.declaration_eligible
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)
    for node, ev in zip(result.source_meaning.graph.nodes, result.source_meaning.evidence, strict=True):
        raw = result.source_meaning.envelope.raw_utf8
        assert value['original'][ev.field_path][ev.scalar_start:ev.scalar_end] == node.value
        assert raw[ev.utf8_start:ev.utf8_end].decode('utf-8') == node.value


@pytest.mark.parametrize('text,expected', (
    ('私は 本を読みたい。', '私は 本を読みたい。'),
    ('私は 陶芸を選びたい！', '私は 陶芸を選びたい！'),
    ('私は 陶芸を選びたい!', '私は 陶芸を選びたい!'),
    ('私は 自分の 時間を大切にしたい。', '私は、自分の 時間を大切にしたい。'),
    ('余裕があるなら、私は 陶芸を選びたい。', '余裕があるなら、私は陶芸を選びたい。'),
    ('私は 陶芸を選びたくなかった。', '私は、陶芸を選びたくなかった。'),
))
def test_direct_wish_spacing_fix_preserves_the_existing_literal_scope_and_past_paths(text, expected):
    from piece_v2_content_policy import validate_source_meaning_preservation
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    assert result.artifact.piece_text == expected
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('label', ('喜び', '悲しみ', '怒り', '不安', '平穏'))
@pytest.mark.parametrize('ending', WRITTEN_FEELING_FORMS)
@pytest.mark.parametrize('stop', ('。', '！', '!'))
@pytest.mark.parametrize('field', ('memo', 'memo_action'))
def test_written_feeling_account_is_retained_without_a_selected_feeling(label, ending, stop, field):
    from piece_v2_content_policy import validate_source_meaning_preservation
    feeling = f'私は{label}を感じ{ending}{stop}'
    tail = '姉はまだ分かりません。'
    value = row(feeling, tail) if field == 'memo' else row(tail, feeling)
    value['original']['emotions'] = ['自己理解']
    value['original']['emotion_details'] = [{'type': '自己理解', 'strength': 'medium'}]
    result = generated(value)
    expected = '\n\n'.join((feeling, tail) if field == 'memo' else (tail, feeling))
    assert result.artifact.piece_text == expected
    assert {d.operation for d in result.artifact_plan.duties} == {'KEEP_COMPLETE_SOURCE_CONTEXT'}
    assert not result.artifact_plan.declaration_eligible
    assert 'declaration' not in result.artifact.eligible_formats
    meaning = result.source_meaning
    assert meaning.selected_feelings == meaning.selection_contexts == meaning.selection_evidence == ()
    assert meaning.saved_snapshot.saved_original_json == canonical_json_bytes(value['original'])
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert value['original'][ev.field_path][ev.scalar_start:ev.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[ev.utf8_start:ev.utf8_end].decode('utf-8') == node.value
    validate_source_meaning_preservation(meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('degree', ('', '弱い', '中程度の', '強い'))
@pytest.mark.parametrize('gap', ('', ' \t\u3000'))
def test_written_feeling_keeps_overt_speaker_degree_and_horizontal_layout(speaker, degree, gap):
    value = row(f'{speaker}は、{gap}{degree}不安を感じています。', None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    assert result.artifact.piece_text == value['original']['memo']
    assert not result.artifact_plan.declaration_eligible


@pytest.mark.parametrize('ending', WRITTEN_FEELING_FORMS)
@pytest.mark.parametrize('stop', ('。', '！', '!'))
def test_written_account_does_not_rebind_a_selected_present_feeling_from_negative_or_past_text(ending, stop):
    value = row(f'私は強い不安を感じ{ending}{stop}', None)
    value['original']['emotions'] = ['不安']
    value['original']['emotion_details'] = [{'type': '不安', 'strength': 'strong'}]
    result = generated(value)
    assert result.artifact.piece_text == value['original']['memo']
    meaning = result.source_meaning
    if ending == 'ています' and stop == '。':
        assert meaning.selection_contexts == meaning.selection_evidence == ()
        assert {binding.node_id for binding in meaning.selected_feelings} == {meaning.graph.nodes[0].node_id}
    else:
        context, = meaning.selection_contexts
        assert json.loads(context.value) == {'label': '不安', 'scope': 'RECORDED_SELF', 'strength': 'strong'}
        assert {binding.node_id for binding in meaning.selected_feelings} == {context.node_id}


@pytest.mark.parametrize('text', (
    '姉は不安を感じています。', '私たちは不安を感じています。', '不安を感じています。',
    '私は「不安を感じています」と書いた。', '私は不安を感じていますと聞いた。',
    'もし私は不安を感じています。', '私は不安を感じるなら、休む。',
    '私は不安を感じています？', '私は不安を感じています?', '私は不安を感じていますか。',
    '私は不安を感じています！！', '私は不安を感じています', '私は不安を感じて',
    '私は不安を\n感じています。', '私は不安を感じる。', '私は不安を感じない。',
    '私は不安を感じていた。', '私はを感じています。', '私は強いを感じています。',
    '私は自己理解を感じています。', '私は不安に感じています。',
))
def test_written_feeling_retention_does_not_fill_an_actor_form_stop_or_subordinate_clause(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('memo,action', (
    ('私は不安を', '感じています。'),
    ('私は不安を感じています。', '姉は不安を感じています。'),
    ('私は不安を感じています。', 'まだ、何を感じています。'),
))
def test_written_feeling_does_not_complete_another_field_or_drop_unread_context(memo, action):
    value = row(memo, action)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('tags,details', (([], []), (['自己理解', '不安'], []),
    (['自己理解'], [{'type': '自己理解', 'strength': 'strong'}])))
def test_written_feeling_still_requires_the_existing_valid_saved_mode(tags, details):
    value = row('私は不安を感じています。', None)
    value['original']['emotions'], value['original']['emotion_details'] = tags, details
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('memo,action,expected', (
    ('私は不安を感じています。私は不安を感じています。', None,
     '私は不安を感じています。私は不安を感じています。'),
    ('私は喜びを感じています。\n私は悲しみを感じました。', None,
     '私は喜びを感じています。\n\n私は悲しみを感じました。'),
    ('私は不安を感じていませんでした。まだ分かりません。', None,
     '私は不安を感じていませんでした。まだ分かりません。'),
    ('私は不安を感じています。', '資料を確認しました。',
     '私は不安を感じています。\n\n資料を確認しました。'),
))
def test_written_feeling_preserves_duplicates_labels_paragraphs_and_complete_actions(memo, action, expected):
    from piece_v2_content_policy import validate_source_meaning_preservation
    value = row(memo, action)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    assert result.artifact.piece_text == expected
    assert not result.artifact_plan.declaration_eligible
    assert {d.operation for d in result.artifact_plan.duties} == {'KEEP_COMPLETE_SOURCE_CONTEXT'}
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


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


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('memo,action,blocks', [
    ('資料を読みました\n窓を閉めませんでした', None, ('資料を読みました', '窓を閉めませんでした')),
    ('資料を読みました\r\n窓を閉めませんでした', None, ('資料を読みました', '窓を閉めませんでした')),
    ('資料を読みました\r窓を閉めませんでした', None, ('資料を読みました', '窓を閉めませんでした')),
    ('資料を読みました\n\n  窓を閉めませんでした  ', None, ('資料を読みました', '窓を閉めませんでした')),
    ('資料を読みました。\n窓を閉めませんでした', None, ('資料を読みました。', '窓を閉めませんでした')),
    ('資料を読みました\n窓を閉めませんでした。', None, ('資料を読みました', '窓を閉めませんでした。')),
    ('予定を確認しました\n資料を整理しました', None, ('予定を確認しました', '資料を整理しました')),
    ('資料を読みました\n資料を読みました', None, ('資料を読みました', '資料を読みました')),
    ('資料を読みました。窓を閉めませんでした\n下書きを終えました', None,
     ('資料を読みました。窓を閉めませんでした', '下書きを終えました')),
    ('資料を読みました\n窓を閉めませんでした\n下書きを終えました', None,
     ('資料を読みました', '窓を閉めませんでした', '下書きを終えました')),
    ('予定を確認しました。', '資料を読みました\n窓を閉めませんでした',
     ('予定を確認しました。', '資料を読みました', '窓を閉めませんでした')),
])
def test_saved_complete_lines_keep_their_own_paragraphs(mode, memo, action, blocks):
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == blocks
    expected = '\n\n'.join(blocks)
    assert result.artifact.piece_text == expected
    assert result.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == expected
    assert candidate['content_payload']['body_blocks'] == list(blocks)
    assert json.loads(result.source_meaning.saved_snapshot.saved_original_json) == value['original']


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
@pytest.mark.parametrize('shape', ['single', 'two_fields', 'two_lines'])
def test_saved_finite_accounts_keep_declarative_punctuation(mode, tier, stop, shape):
    first, second = '私は資料を読みました' + stop, '姉は窓を閉めませんでした。'
    memo, action, blocks = (first, None, [first])
    if shape == 'two_fields':
        action, blocks = second, [first, second]
    elif shape == 'two_lines':
        memo, blocks = first + '\n' + second, [first, second]
    value = row(memo, action)
    value['tier'], value['original']['emotions'] = tier, [mode]
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == '\n\n'.join(blocks)
    assert candidate['content_payload']['body_blocks'] == blocks
    assert candidate['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert candidate['content_payload']['format_type'] in candidate['eligible_formats']
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('text', [
    '私は資料を読みました？', '私は資料を読みました?',
    '私は資料を読みましたか！', '誰が資料を読みました！',
    '私は何を読みました！', 'もし資料を読みました！',
    '資料を閉めたら！', '資料を！', '読みました！',
    '私は資料を読みました！！', '私は資料を読みました!？',
])
def test_self_insight_declarative_stop_does_not_admit_questions_or_fragments(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


@pytest.mark.parametrize('mutation', ['punctuation', 'subject', 'object', 'negation', 'merge', 'reverse'])
def test_independent_review_keeps_exclamation_and_complete_account_arguments(mutation):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row('私は資料を読みました！', '姉は窓を閉めませんでした。')
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    plan, blocks = result.artifact_plan, result.artifact.body_blocks
    if mutation == 'merge':
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'),))
        blocks = (''.join(blocks),)
    elif mutation == 'reverse':
        plan = replace(plan, block_node_ids=tuple(reversed(plan.block_node_ids)))
        blocks = tuple(reversed(blocks))
    elif mutation == 'punctuation':
        blocks = (blocks[0].replace('！', '。'), blocks[1])
    elif mutation == 'subject':
        blocks = (blocks[0], blocks[1].replace('姉は', '私は'))
    elif mutation == 'object':
        blocks = (blocks[0].replace('資料', '手紙'), blocks[1])
    else:
        blocks = (blocks[0], blocks[1].replace('ませんでした', 'ました'))
    text = '\n\n'.join(blocks)
    artifact = replace(result.artifact, body_blocks=blocks, piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, plan, artifact)


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('register', ['', 'です'])
@pytest.mark.parametrize('body', ['本を読みたい', '水を飲みたい', '静かに休みたい'])
def test_saved_literal_self_expression_keeps_plain_and_polite_words(speaker, mode, register, body):
    text = speaker + 'は' + body + register + '。'
    value = row(text, None)
    value['tier'], value['original']['emotions'] = 'premium', [mode]
    result = generated(value)
    assert result.artifact.piece_text == text
    assert [d.operation for d in result.artifact_plan.duties] == ['KEEP_COMPLETE_SOURCE_CONTEXT']
    assert not result.artifact_plan.declaration_eligible
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == text
    assert candidate['content_payload']['body_blocks'] == [text]
    assert 'declaration' not in candidate['eligible_formats']


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('memo,action,blocks', [
    ('私は本を読みたい。私は水を飲みたい。', '私は静かに休みたい。',
     ('私は本を読みたい。私は水を飲みたい。', '私は静かに休みたい。')),
    ('私は本を読みたいです。\n私は静かに休みたいです。', '窓を閉めませんでした。',
     ('私は本を読みたいです。', '私は静かに休みたいです。', '窓を閉めませんでした。')),
    ('私は本を読みたい。私は本を読みたい。', None,
     ('私は本を読みたい。私は本を読みたい。',)),
    ('私は本を読みたい。', '私は本を読みたい。',
     ('私は本を読みたい。', '私は本を読みたい。')),
    ('私は猫みたい。', None, ('私は猫みたい。',)),
    ('私は猫みたいです。', None, ('私は猫みたいです。',)),
    ('私は本を読みたいみたい。', None, ('私は本を読みたいみたい。',)),
    ('私は本を読みたいみたいです。', None, ('私は本を読みたいみたいです。',)),
])
def test_literal_accounts_keep_source_paragraphs_duplicates_and_comparisons(mode, memo, action, blocks):
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == blocks
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)
    assert not result.artifact_plan.declaration_eligible
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == result.artifact.piece_text
    assert candidate['content_payload']['body_blocks'] == list(blocks)


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('body', ['', '、', 'です', 'たい', 'たいです', 'たくない',
                                  'みたい', 'みたいです', 'てみたい', 'でみたい'])
@pytest.mark.parametrize('prefix', ['', '余裕があるなら、'])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
def test_bare_self_operators_never_become_a_source_proposition(mode, body, prefix, stop):
    value = row(prefix + '私は' + body + stop, None)
    value['original']['emotions'] = [mode]
    with pytest.raises(ValueError, match='expression_meaning_not_admitted'):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


@pytest.mark.parametrize('memo,action', [
    ('私は本を読みたい？', None), ('私は本を読みたいか。', None),
    ('私は何を読みたい。', None), ('私はどの本を読みたい。', None),
    ('私はもし本を読みたい。', None), ('私は本を読みたいなら。', None),
    ('私は本を読みたいと。', None), ('私は本を読みたいが。', None),
    ('私はあの本を読みたい。', None), ('私は本を読みたい', None),
    ('私は本を\n読みたい。', None), ('私は本を', '読みたい。'),
    ('私は静かに', '休みたい。'),
])
@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
def test_literal_admission_does_not_complete_questions_or_fragmented_fields(memo, action, mode):
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


def test_new_literal_account_requires_valid_saved_selection_and_never_grants_declaration():
    value = row('私は本を読みたい。', None)
    assert outcome(source(value)).reason_codes == ('expression_meaning_not_admitted',)
    value['original']['emotions'] = ['自己理解']
    snapshot = source(value)
    assert outcome(replace(snapshot, saved_original_json=None)).reason_codes == (
        'expression_meaning_not_admitted',)
    value['tier'] = 'premium'
    with pytest.raises(ValueError, match='format_choice_not_admitted'):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation', requested_format='declaration'))


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('text', [
    'ほとんどの資料を読みました',
    'ほとんどの資料を読みませんでした。',
    '私はどこにも手紙を送りませんでした',
    'どこにでも手紙を送りました',
    'どうしても資料を読みました',
    'どうやっても窓を開けませんでした',
    '私はどうしても本を読みたい。',
    'ほとんど資料を読みました',
    'いくつかの資料を読みました',
    'いつもの資料を読みました',
    '誰にも資料を送りませんでした',
])
def test_noninterrogative_complete_accounts_keep_quantifier_and_indefinite_words(mode, text):
    value = row(text, None)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.piece_text == text
    assert result.artifact.body_blocks == (text,)
    assert not result.artifact_plan.declaration_eligible
    candidate = run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
                    .generate_original_candidate_for_development(
                        AUTH, INPUT, source_stage='normal_observation'))
    assert candidate['piece_text'] == text


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('text', [
    'どの資料を読みました', 'どこに手紙を送りました',
    'どこから届いた資料を読みました', 'どこで本を読みました',
    'どうして資料を読みました', 'どうやって窓を開けました',
    '誰に資料を送りました', 'いつ資料を読みました',
    'ほとんどの資料をいつ読みました',
    'どうしてもどの本を読みました',
    '私はどうしても何を読みたい。',
    'どこからもらった資料を読みました',
    'どこにもぐった人の本を読みました',
    'どこへもっていった資料を読みました',
    'どうしてもらった資料を読みました',
    '私はどうしてもらった本を読みたい。',
    # These indefinite spellings remain outside this bounded correction.
    'どこからも届いた資料を読みました',
    'どこででも本を読みました',
])
def test_noninterrogative_word_boundaries_do_not_admit_actual_questions(mode, text):
    value = row(text, None)
    value['original']['emotions'] = [mode]
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('stop', ['！', '!'])
@pytest.mark.parametrize('body', [
    '私は本を読みたい', 'わたしは静かに休みたいです',
    '僕は水を飲みたくない', '私は猫みたい',
])
@pytest.mark.parametrize('shape', ['single', 'paragraph', 'duplicate'])
def test_literal_self_accounts_keep_their_written_exclamation(mode, stop, body, shape):
    first = body + stop
    memo, blocks = first, [first]
    if shape == 'paragraph':
        memo, blocks = first + '\n窓を閉めませんでした。', [first, '窓を閉めませんでした。']
    elif shape == 'duplicate':
        memo, blocks = first * 2, [first * 2]
    value = row(memo, None)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == tuple(blocks)
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert not result.artifact_plan.declaration_eligible
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('memo,action,blocks', [
    ('私は本を読みたい。まだ決めていません。', None,
     ('私は本を読みたい。まだ決めていません。',)),
    ('私は静かに休みたいです。\nただし、まだ決めていません。', None,
     ('私は静かに休みたいです。', 'ただし、まだ決めていません。')),
    ('私は猫みたい。理由はまだわからない。', None,
     ('私は猫みたい。理由はまだわからない。',)),
    ('私は本を読みたい！\n今は続けるか迷っています。', None,
     ('私は本を読みたい！', '今は続けるか迷っています。')),
    ('まだ決めていません。\n私は本を読みたい。', None,
     ('まだ決めていません。', '私は本を読みたい。')),
    ('私は本を読みたい。', '私はまだ決めていません。',
     ('私は本を読みたい。', '私はまだ決めていません。')),
    ('私は本を読みたい。私は本を読みたい。', '私はまだ決めていません。',
     ('私は本を読みたい。私は本を読みたい。', '私はまだ決めていません。')),
    ('私は本を読みたい。', '資料を読みました。まだ決めていません。',
     ('私は本を読みたい。', '資料を読みました。まだ決めていません。')),
    ('私は本を読みたい!\n姉はまだ決めていません。\n資料を読みました', None,
     ('私は本を読みたい!', '姉はまだ決めていません。', '資料を読みました')),
])
def test_literal_self_accounts_keep_complete_existing_reservations(mode, memo, action, blocks):
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == blocks
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert not result.artifact_plan.declaration_eligible
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)


@pytest.mark.parametrize('memo,action', [
    ('私は本を読みたい？', None), ('私は本を読みたい!!', None),
    ('私は本を読みたい！？', None), ('私は何を読みたい！', None),
    ('私はもし本を読みたい！', None), ('私は本を読みたいなら！', None),
    ('私は本を読みたい！まだ決めていませんか。', None),
    ('私は本を読みたい！まだ決めていません？', None),
    ('私は本を読みたい！まだ決めていません?', None),
    ('私は本を読みたい！まだ何を決めていません。', None),
    ('私は本を読みたい！仮にまだ決めていません。', None),
    ('私は本を読みたい！まだ決めていませんと聞きました。', None),
    ('私は本を読みたい！まだ決めていないなら、私は資料を読みました。', None),
    ('私は本を読みたい！まだ決めていませんが。', None),
    ('私は本を読みたい！まだ決めて。', None),
    ('私は本を読みたい！私はまだ決め', 'ていません。'),
    ('私は本を読みたい！', '私はまだ決め\nていません。'),
    ('私は本を\n読みたい！', None),
    ('私は本を', '読みたい！'),
])
def test_literal_exclamation_and_reservation_do_not_complete_questions_or_fragments(memo, action):
    value = row(memo, action)
    value['original']['emotions'] = ['自己理解']
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


@pytest.mark.parametrize('memo', [
    'まだ決めていません。',
    '私は本を読みたい！今日は晴れです。',
    '私は本を読みたい！姉は本を読みたい。',
    '私は本を読みたい！' + '\nまだ決めていません。' * 3,
])
def test_self_insight_reservations_do_not_grant_generic_context_or_exceed_paragraph_limits(memo):
    value = row(memo, None)
    value['original']['emotions'] = ['自己理解']
    with pytest.raises(ValueError):
        run(adapter_module.PieceSavedSourceAdapter(store=Store(value))
            .generate_original_candidate_for_development(
                AUTH, INPUT, source_stage='normal_observation'))


@pytest.mark.parametrize('boundary,accepted', [
    ('sentences6', True), ('sentences7', False),
    ('paragraphs3', True), ('paragraphs4', False),
    ('characters420', True), ('characters421', False),
])
def test_literal_reservation_keeps_existing_content_envelope(boundary, accepted):
    first, reservation = '私は本を読みたい！', 'まだ決めていません。'
    if boundary.startswith('sentences'):
        text = first + reservation * (int(boundary[len('sentences'):]) - 1)
    elif boundary.startswith('paragraphs'):
        text = first + ('\n' + reservation) * (int(boundary[len('paragraphs'):]) - 1)
    else:
        total = int(boundary[len('characters'):])
        text = '私は' + '花' * (total - len('私はを読みたい！' + reservation)) + 'を読みたい！' + reservation
        assert len(text) == total
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    if accepted:
        assert result.status == EngineStatus.GENERATED, result.reason_codes
        assert result.artifact.piece_text == text.replace('\n', '\n\n')
        assert not result.artifact_plan.declaration_eligible
    else:
        assert result.status == EngineStatus.UNAVAILABLE
        assert result.artifact is None


@pytest.mark.parametrize('mutation', ['punctuation', 'subject', 'negation', 'reservation', 'merge', 'order'])
def test_author_free_review_keeps_literal_exclamation_and_other_person_reservation(mutation):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row('私は本を読みたい！\n姉はまだ決めていません。', None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    plan, blocks = result.artifact_plan, list(result.artifact.body_blocks)
    if mutation == 'punctuation':
        blocks[0] = blocks[0].replace('！', '。')
    elif mutation == 'subject':
        blocks[1] = blocks[1].replace('姉は', '私は')
    elif mutation == 'negation':
        blocks[0] = blocks[0].replace('読みたい', '読みたくない')
    elif mutation == 'reservation':
        blocks[1] = '姉は決めました。'
    elif mutation == 'merge':
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'),))
        blocks = [''.join(blocks)]
    else:
        blocks.reverse()
    text = '\n\n'.join(blocks)
    artifact = replace(result.artifact, body_blocks=tuple(blocks), piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, plan, artifact)


@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
@pytest.mark.parametrize('ending', ['ます', 'ません', 'ました', 'ませんでした'])
@pytest.mark.parametrize('object_text,stem', [
    ('予定', '確認し'), ('資料', '整理し'), ('手紙', '送り'),
    ('資料', '読み'), ('窓', '開け'), ('下書き', '終え'),
    ('片付け', '始め'), ('荷物', '受け取り'), ('窓', '閉め'),
])
@pytest.mark.parametrize('shape', ['single', 'same_field_reservation', 'other_field_reservation'])
def test_saved_finite_action_family_retains_tense_negation_and_existing_reservation(
        mode, stop, ending, object_text, stem, shape):
    from piece_v2_content_policy import validate_source_meaning_preservation

    first, reservation = '私は' + object_text + 'を' + stem + ending + stop, '姉はまだ決めていません。'
    memo, action, blocks = first, None, [first]
    if shape == 'same_field_reservation':
        memo, blocks = first + '\n' + reservation, [first, reservation]
    elif shape == 'other_field_reservation':
        action, blocks = reservation, [first, reservation]
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == tuple(blocks)
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert not result.artifact_plan.declaration_eligible
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('text', [
    '資料を読みます', '資料を読みません', '予定を確認します', '予定を確認しません',
    '資料を読みます？', '資料を読みません?', '予定を確認しますか。',
    '何を読みます。', '何の資料を読みます。', 'どの予定を確認します。',
    'もし資料を読みます。', '仮に予定を確認します。', '資料を読みますなら。',
    '資料を読みますと書きました。', '私はを読みます。', '私は、を確認します。',
    '姉はを読みます。', '彼がを確認します。', '姉は、を読みません。',
    'を読みます。', '読みます。', '資料を読みます！！', '予定を確認します!？',
    '資料を読みます。まだ決めていません？',
    '予定を確認します。今日は晴れです。',
    '私は本を読みたい。行きます。',
])
def test_new_nonpast_account_reader_does_not_supply_missing_source_or_generic_predicates(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE, result.reason_codes
    assert result.artifact is None


@pytest.mark.parametrize('memo,action', [
    ('資料を読みます', 'まだ決めていません。'),
    ('予定を確認しません', '資料を読みました。'),
    ('資料を\n読みます。', None),
    ('資料を', '読みます。'),
    ('資料を読みます。まだ決め', 'ていません。'),
])
def test_nonpast_accounts_do_not_complete_sentences_across_lines_or_fields(memo, action):
    value = row(memo, action)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('text', [
    '明日までに返事をする。', '明日は料理する。',
    '午前中に打ち合わせをする。', '午後はメールをする。',
    '散歩する。', '資料を確認する。',
])
@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('shape', ['single', 'same_field', 'two_fields'])
def test_existing_plain_suru_account_family_keeps_the_same_mode_independent_source(text, mode, shape):
    from piece_v2_content_policy import validate_source_meaning_preservation

    reservation = '姉はまだ決めていません。'
    memo, action, blocks = text, None, (text,)
    if shape == 'same_field':
        memo, blocks = text + '\n' + reservation, (text, reservation)
    elif shape == 'two_fields':
        action, blocks = reservation, (text, reservation)
    value = row(memo, action)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.body_blocks == blocks
    assert result.artifact.piece_text == '\n\n'.join(blocks)
    assert not result.artifact_plan.declaration_eligible
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('text', [
    'する。', 'を確認する。', ' を整理する。', 'をを確認する。',
    '、を確認する。', '，を確認する。', ',を確認する。', '🌱を確認する。',
    '私はを確認する。', '彼がを整理する。', '僕もを確認する。',
    '姉にを整理する。', '彼へを確認する。', '僕でを確認する。', '私とを確認する。',
    'もし資料を確認する。', '余裕があるならしおりを確認する。',
    '資料を確認する場合。', 'どの資料を確認する。', '何をする。',
    '資料を確認する？', '資料を確認する！', '資料を確認する',
    '資料を確認するだろう。', '資料を確認するかも。', '仕事をしない。',
    '資料を確認するといいます。', '資料を確認する。今日は晴れです。',
])
def test_plain_suru_account_reuse_does_not_admit_partial_matches_or_missing_arguments(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE, result.reason_codes
    assert result.artifact is None


@pytest.mark.parametrize('text', [
    '僕もを読みます。', '姉にを読みます。', '彼へを確認します。',
    '僕でを読みます。', '私とを読みます。', '小鳥沢さんはを読みません。',
    '余裕があるならしおりを読みます。',
    '資料を読みました。余裕があるならまだ決めていません。',
    '資料を読みました。まだ決めていないならやめます。',
    '資料を読みました。まだ決めていないといいます。',
    '資料を読みました。まだ決めていないといっています。',
    '資料を読みました。まだ決めていないといった。',
    '資料を読みました。まだ決めていないっていっています。',
])
def test_new_account_admission_does_not_borrow_a_missing_argument_or_unread_scope(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('text', [
    '姉のことを確認します。', '今年の取り組みを確認します。', '姉のを読みます。',
    '資料を読みました。まだ決めることができません。',
    '資料を読みました。まだ決めたことはありません。',
    '私は本を読みたい。まだ決めることができません。',
    '私は本を読みたい。まだ決めたことはありません。',
    '資料を読みました。今は続けるか迷っています。',
    '資料を読みました。迷っているとは限らない。',
    '資料を読みました。姉はまだ迷っていました。',
    '資料を読みました。姉はまだ迷っていった。',
])
def test_existing_nominalization_and_complete_uncertainty_remain_written_source(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    assert result.artifact.piece_text == text
    assert not result.artifact_plan.declaration_eligible


@pytest.mark.parametrize('reservation', [
    'まだ分かりません。', 'まだわかりません！',
    'まだ分かりませんでした。', 'まだわかりませんでした!',
    '次も同じとは限りません。', '次も同じとは限りませんでした。',
    '姉はまだ迷っている。', '今は続けるか迷っている！',
])
@pytest.mark.parametrize('first', ['資料を読みました。', '私は本を読みたい！'])
@pytest.mark.parametrize('shape', ['same_sentence_group', 'newline', 'other_field'])
def test_existing_reservation_inflections_remain_literal_in_self_insight(reservation, first, shape):
    from piece_v2_content_policy import validate_source_meaning_preservation

    memo = first + reservation if shape == 'same_sentence_group' else (
        first + '\n' + reservation if shape == 'newline' else first)
    value = row(memo, reservation if shape == 'other_field' else None)
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    expected = first + reservation if shape == 'same_sentence_group' else first + '\n\n' + reservation
    assert result.artifact.piece_text == expected
    assert all(duty.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for duty in result.artifact_plan.duties)
    assert result.artifact_plan.declaration_eligible is False
    assert 'declaration' not in result.artifact.eligible_formats
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('text', [
    'まだ分かりません。', 'まだ迷っている。',
    '資料を読みました。まだ分かりません？',
    '資料を読みました。まだ迷っている？',
    '資料を読みました。まだ分かりません',
    '資料を読みました。まだ迷っている',
    '資料を読みました。まだ分かりませんでしたと聞きました。',
    '資料を読みました。もし続けるならまだ迷っている。',
    '資料を読みました。姉がまだ迷っていると言いました。',
    '資料を読みました。姉がまだ迷っているっていいます。',
    '資料を読みました。次も同じとは限りませんでしたが。',
    '資料を読みました。いつまで迷っている。',
    '資料を読みました。何で迷っている。',
    '資料を読みました。なんで迷っている。',
    '資料を読みました。なにで迷っている。',
    '資料を読みました。どんなことで迷っている。',
    '資料を読みました。何でもらったか迷っている。',
])
def test_reservation_inflections_do_not_complete_a_fragment_question_or_report(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('base', [
    '私は読書を大切にしています。',
    '私は競争を望んでいません。',
    '私が選びたいのは、陶芸です。',
    '余裕があるなら、私が選びたいのは、陶芸です。',
    '以前は、私が望んでいなかったのは、競争です。',
    '私は読書が好きです。',
    '私にとって大切なのは、家族です。',
    '疲れているけれど、私は読書が好きです。',
])
@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('stop', ['！', '!'])
@pytest.mark.parametrize('shape', ['single', 'reservation', 'newline', 'other_field'])
def test_structured_accounts_keep_original_exclamation_after_existing_editorial_operations(base, mode, stop, shape):
    from piece_v2_content_policy import validate_source_meaning_preservation

    reservation = '姉はまだ分かりません。'
    memo = base + reservation if shape == 'reservation' else (
        base + '\n' + reservation if shape == 'newline' else base)
    action = reservation if shape == 'other_field' else None
    baseline_value = row(memo, action)
    baseline_value['original']['emotions'] = [mode]
    baseline = generated(baseline_value)
    value = copy.deepcopy(baseline_value)
    for field in ('memo', 'memo_action'):
        if value['original'][field]:
            value['original'][field] = value['original'][field].replace('。', stop)
    result = generated(value)
    assert result.artifact.piece_text == baseline.artifact.piece_text.replace('。', stop)
    assert result.artifact.body_blocks == tuple(block.replace('。', stop) for block in baseline.artifact.body_blocks)
    assert result.artifact_plan.block_node_ids == baseline.artifact_plan.block_node_ids
    assert result.artifact_plan.declaration_eligible == baseline.artifact_plan.declaration_eligible
    assert tuple(d.operation for d in result.artifact_plan.duties) == tuple(d.operation for d in baseline.artifact_plan.duties)
    raw = result.source_meaning.envelope.raw_utf8
    for node, evidence in zip(result.source_meaning.graph.nodes, result.source_meaning.evidence, strict=True):
        assert raw[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, result.artifact)


@pytest.mark.parametrize('text', [
    '私は読書を大切にしたい', '私は人との関係を大切にしたい',
    '私は自分の時間を守りたい', '僕は水を飲みたくない',
])
@pytest.mark.parametrize('stop', ['！', '!'])
@pytest.mark.parametrize('mode', ['平穏', '自己理解'])
@pytest.mark.parametrize('shape', ['single', 'paragraph', 'duplicate'])
def test_existing_literal_exclamations_do_not_gain_a_structured_intent(text, stop, mode, shape):
    sentence = text + stop
    memo = sentence if shape == 'single' else sentence + ('\n' if shape == 'paragraph' else '') + sentence
    value = row(memo, None)
    value['original']['emotions'] = [mode]
    result = generated(value)
    assert result.artifact.piece_text == memo.replace('\n', '\n\n')
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in result.artifact_plan.duties)
    assert not result.artifact_plan.declaration_eligible
    assert 'declaration' not in result.artifact.eligible_formats


@pytest.mark.parametrize('text', [
    '私は読書を大切にしています！！',
    '私は読書を大切にしています!?',
    '私が選びたいのは、陶芸です？',
    '余裕があるなら、私が選びたいのは、陶芸です?!',
    '私は読書が好きです!!',
    '私はです！',
    '私はたい!',
])
def test_structured_exclamation_does_not_normalize_double_stops_or_questions(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('original_stop,changed_stop', [('！', '。'), ('!', '！'), ('！', '!')])
def test_author_free_review_rejects_structured_exclamation_replacement(original_stop, changed_stop):
    from piece_v2_content_policy import validate_source_meaning_preservation
    value = row('余裕があるなら、私が選びたいのは、陶芸です' + original_stop, '姉はまだ分かりません。')
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    blocks = list(result.artifact.body_blocks)
    blocks[0] = blocks[0][:-1] + changed_stop
    text = '\n\n'.join(blocks)
    corrupted = replace(result.artifact, body_blocks=tuple(blocks), piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, corrupted)


@pytest.mark.parametrize('prefix', ['誰に', '誰から', 'だれに', 'だれから'])
@pytest.mark.parametrize('ending', ['ます。', 'ました。', 'ました'])
def test_question_cue_does_not_read_received_verb_as_indefinite_particle(prefix, ending):
    value = row(prefix + 'もらった資料を読み' + ending, None)
    value['original']['emotions'] = ['自己理解']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('text', [
    '誰にも手紙を送りません。', '誰からも連絡を受け取りません。',
    'だれにでも手紙を送ります。', '誰からも連絡を受け取りました',
    '姉からもらった資料を読みます。', '何かの資料を読みます。',
])
def test_indefinite_and_explicit_actor_are_not_turned_into_questions(text):
    value = row(text, None)
    value['original']['emotions'] = ['自己理解']
    assert generated(value).artifact.piece_text == text


@pytest.mark.parametrize('mutation', ['subject', 'object', 'negation', 'punctuation', 'drop_duplicate', 'order'])
def test_independent_review_binds_literal_accounts_without_inferring_wishes(mutation):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row('私は本を読みたい。私は本を読みたい。', '私は水を飲みたい。')
    value['original']['emotions'] = ['自己理解']
    result = generated(value)
    blocks = list(result.artifact.body_blocks)
    if mutation == 'subject':
        blocks[0] = blocks[0].replace('私は', '姉は', 1)
    elif mutation == 'object':
        blocks[0] = blocks[0].replace('本', '手紙', 1)
    elif mutation == 'negation':
        blocks[0] = blocks[0].replace('読みたい', '読みたくない', 1)
    elif mutation == 'punctuation':
        blocks[0] = blocks[0].replace('。', '！', 1)
    elif mutation == 'drop_duplicate':
        blocks[0] = '私は本を読みたい。'
    else:
        blocks.reverse()
    text = '\n\n'.join(blocks)
    artifact = replace(result.artifact, body_blocks=tuple(blocks), piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, result.artifact_plan, artifact)


def test_punctuated_saved_paragraphs_keep_the_same_author_and_source_order():
    value = row('私は本を読む時間を大切にしています。\n\n私は一人で静かに過ごしたい。',
                '私は今日は外に出たくない。')
    value['original']['emotions'] = ['平穏']
    result = generated(value)
    assert result.artifact.body_blocks == ('私は、本を読む時間を大切にしています。',
        '私は、一人で静かに過ごしたい。', '私は、今日は外に出たくない。')
    assert result.artifact_plan.block_node_ids == (('piece:s1',), ('piece:s2',), ('piece:s3',))


def test_complete_line_admission_requires_the_bound_saved_original():
    value = row('資料を読みました\n窓を閉めませんでした', None)
    value['original']['emotions'] = ['平穏']
    raw = replace(source(value), saved_original_json=None)
    result = outcome(raw)
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.reason_codes == ('source_line_mid_sentence',)
    assert result.artifact is None


@pytest.mark.parametrize('memo,action', [
    ('資料を\n窓を閉めました', None),
    ('窓を閉めたら\n資料を読みました', None),
    ('資料を読みましたが\n窓を閉めました', None),
    ('何を読みました\n窓を閉めました', None),
    ('その資料を読みました\n窓を閉めました', None),
    ('資料を読みました\nもし窓を閉めました', None),
    ('資料を読みました', '窓を閉めました'),
    ('資料を読みました\n窓を閉めました', '下書きを終えました。'),
    ('資料を読みました\n窓を閉めました\n下書きを終えました\n予定を確認しました', None),
    ('資料を読みました。窓を閉めました。' * 3 + '下書きを終えました', None),
    ('資料を読みました\n\n' + '窓を閉めました。' * 50, None),
])
def test_complete_lines_do_not_complete_fragments_or_exceed_existing_limits(memo, action):
    value = row(memo, action)
    value['original']['emotions'] = ['平穏']
    result = outcome(source(value))
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


@pytest.mark.parametrize('mutation', ['merge', 'reverse', 'punctuation', 'negation'])
def test_independent_review_keeps_complete_line_boundaries_and_exact_predicates(mutation):
    from piece_v2_content_policy import validate_source_meaning_preservation

    value = row('資料を読みました\n窓を閉めませんでした', None)
    value['original']['emotions'] = ['平穏']
    result = generated(value)
    plan, blocks = result.artifact_plan, result.artifact.body_blocks
    if mutation == 'merge':
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'),))
        blocks = (''.join(blocks),)
    elif mutation == 'reverse':
        plan = replace(plan, block_node_ids=tuple(reversed(plan.block_node_ids)))
        blocks = tuple(reversed(blocks))
    elif mutation == 'punctuation':
        blocks = (blocks[0] + '。', blocks[1])
    else:
        blocks = (blocks[0], blocks[1].replace('ませんでした', 'ました'))
    text = '\n\n'.join(blocks)
    artifact = replace(result.artifact, body_blocks=blocks, piece_text=text,
        piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(result.source_meaning, plan, artifact)


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
@pytest.mark.parametrize('separate_lines', [False, True])
def test_complete_body_blocks_reach_existing_b9(ratio, separate_lines):
    if separate_lines:
        value = row('資料を読みました\n窓を閉めませんでした\n下書きを終えました', None)
        value['original']['emotions'] = ['平穏']
        candidate = generated(value).artifact.as_candidate()
    else:
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
                     for index in range(len(candidate['content_payload']['body_blocks']))]
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
