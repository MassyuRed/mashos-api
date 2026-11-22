"""Bounded narrator elision: no actor inference or generated-body repair."""
import json

import pytest

from cocolon_meaning_experience_engine.piece_semantic_admission import piece_model_source_plan
from piece_model_source import build_piece_model_messages
from piece_v2_content_policy import validate_source_meaning_preservation
from piece_v2_contract import PieceContractError
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request
from test_piece_model_narrator_voice import evaluate


SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
MEMO = ('おれは、友人の沢さんと本を読む時間が好きです。'
        'おれは、友人の沢さんとなら、気持ちを急いでまとめなくても話せる気がします。'
        'まだ、参加する日は決めていません。')
MEMO_BODY = ('おれは、友人と本を読む時間が好きだ。'
             '友人となら、気持ちを急いでまとめなくても話せる気がする。'
             'まだ、参加する日は決めていない。')
ACTION = ('僕は、昨日は一人で段取りを考えました。'
          '僕は、相手に合わせるために段取りを変えたわけではありません。')
ACTION_BODY = ('僕は、昨日は一人で段取りを考えた。'
               '相手に合わせるために段取りを変えたわけではない。')
CORE = '私は、静かに本を読む時間を大切にしたいです。'


def selection(saved, *, editorial=True):
    from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    frozen = prepared.private_json
    messages = build_piece_model_messages(prepared, source_request=req,
        include_authoring_constraints=True, include_editorial_choices=editorial)
    assert prepared.private_json == frozen
    return json.loads(messages[1]['content']), prepared


def test_two_field_choices_bind_only_the_redundant_source_topic_spans():
    saved = source(MEMO, field='memo', other=ACTION)
    material, prepared = selection(saved)
    fields = material['control']['content_selection']['field_slots']
    assert [len(fields[key]['editorial_choices']) for key in ('memo_0', 'memo_action_1')] == [1, 1]
    for key, text, narrator in (('memo_0', MEMO, 'おれ'), ('memo_action_1', ACTION, '僕')):
        row = fields[key]['editorial_choices'][0]
        a, b = row['topic_scalar_span']
        assert text[a:b] == narrator + 'は、'
        assert a == text.index(narrator + 'は、', 1)
        assert row['source_id'] == fields[key]['source_id']
        assert row['source_role'] == fields[key]['source_role']
        assert row['field_path'] == fields[key]['field_path']
        assert row['operation'] == 'OMIT_REPEATED_SELF_TOPIC'
    out = evaluate(saved, [MEMO_BODY, ACTION_BODY])
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (MEMO_BODY, ACTION_BODY)
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)
    assert material['sources'] == prepared.payload()['sources']
    assert 'expected_body' not in str(material)


@pytest.mark.parametrize('speaker', SPEAKERS)
def test_typed_wish_can_keep_a_comparison_and_omit_only_the_next_topic(speaker):
    before = (f'{speaker}は、次の集まりでは、急ぐよりも本を読む時間を大切にしたいです。'
              f'{speaker}は、返事の前にノートを見返したいです。')
    after = (f'{speaker}は、次の集まりでは、急ぐよりも本を読む時間を大切にしたい。'
             '返事の前にノートを見返したい。')
    saved = source(before, field='memo')
    out = evaluate(saved, [after])
    assert out.artifact is not None, out.reason_codes
    material, _ = selection(saved)
    choices = material['control']['content_selection']['field_slots']['memo_0']['editorial_choices']
    assert len(choices) == 1 and before[slice(*choices[0]['topic_scalar_span'])] == speaker + 'は、'


@pytest.mark.parametrize('old,new', (
    ('友人となら', '友人と'), ('なくても', 'なくて'), ('気がする', ''),
    ('気がする', '気がした'), ('友人と', '同僚と'), ('おれは', '僕は'),
))
def test_impression_retains_condition_reservation_role_and_first_narrator(old, new):
    assert evaluate(source(MEMO, field='memo', other=ACTION),
                    [MEMO_BODY.replace(old, new, 1), ACTION_BODY]).artifact is None


@pytest.mark.parametrize('old,new', (
    ('昨日', '今日'), ('一人で', ''), ('考えた', '決めた'),
    ('変えたわけではない', '変えなかった'), ('変えたわけではない', '変えた'),
    ('わけではない', 'わけではなかった'), ('相手に', '相手から'), ('僕は', 'おれは'),
))
def test_denial_does_not_become_a_negative_action_or_borrow_the_other_field(old, new):
    assert evaluate(source(MEMO, field='memo', other=ACTION),
                    [MEMO_BODY, ACTION_BODY.replace(old, new, 1)]).artifact is None


@pytest.mark.parametrize('body', (
    MEMO_BODY.replace('おれは、', '', 1),
    MEMO_BODY + 'だから安心した。',
))
def test_first_narrator_and_required_occurrences_cannot_disappear(body):
    assert evaluate(source(MEMO, field='memo', other=ACTION), [body, ACTION_BODY]).artifact is None


@pytest.mark.parametrize('gap', ('昨日は雨が降った。', '母が戻ってきた。', '私は遠くを眺めていた。'))
def test_unknown_keep_never_supplies_a_narrator(gap):
    before = CORE + gap + '私は、部屋で話す時間を選んだわけではありません。'
    after = CORE + gap + '部屋で話す時間を選んだわけではない。'
    assert evaluate(source(before, field='memo'), [after]).artifact is None


def test_licensed_elision_does_not_cross_a_later_unknown_keep():
    prefix = CORE + '私は、話を終えたわけではありません。'
    gap = '昨日は雨が降った。'
    tail = '私は、部屋で過ごす時間を選んだわけではありません。'
    visible_prefix = CORE + '話を終えたわけではない。'
    saved = source(prefix + gap + tail, field='memo')
    assert evaluate(saved, [visible_prefix + gap + tail]).artifact is not None
    assert evaluate(saved, [visible_prefix + gap + '部屋で過ごす時間を選んだわけではない。']).artifact is None


@pytest.mark.parametrize('body', (
    '私は、母が父に資料を伝えました。資料を読んだわけではない。',
    '私は、母は遠出したい気がします。部屋で話す時間を選んだわけではない。',
    '私は、僕も遠出したい気がします。部屋で話す時間を選んだわけではない。',
))
def test_outer_topic_is_not_a_matrix_actor_or_another_self_viewpoint(body):
    first, second = body.split('。', 1)
    before = CORE + first + '。私は、' + second.replace('ではない', 'ではありません')
    assert evaluate(source(before, field='memo'), [CORE + body]).artifact is None


@pytest.mark.parametrize('separator', ('\n', '\r\n', '\n\n'))
def test_source_paragraphs_do_not_lend_each_other_a_topic(separator):
    before = '私は、静かに本を読む時間を大切にしたいです。' + separator + '私は、話を終えたわけではありません。'
    assert evaluate(source(before, field='memo'),
                    [CORE, '話を終えたわけではない。']).artifact is None


def test_fields_and_supplemental_children_do_not_lend_a_topic():
    tail = '私は、話を終えたわけではありません。私は、静かに本を読む時間を大切にしたいです。'
    for saved in (source(CORE, field='memo', other=tail), refined_source(original=CORE, answer=tail)):
        assert evaluate(saved, [CORE, '話を終えたわけではない。' + CORE]).artifact is None
    assert evaluate(source(MEMO, field='memo', other=ACTION), [ACTION_BODY, MEMO_BODY]).artifact is None


def test_ordinary_material_does_not_activate_editorial_choices():
    saved = source(MEMO, field='memo', other=ACTION)
    material, _ = selection(saved, editorial=False)
    assert all('editorial_choices' not in field for field in
               material['control']['content_selection']['field_slots'].values())
    meaning, plan = piece_model_source_plan(request(saved))
    assert [d.operation for d in plan.duties].count('KEEP_COMPLETE_SOURCE_CONTEXT') == 4
