"""A written final past anchors exactly two independently read active acts.

All cases are fictional CPU candidates. No author or source-expected prose
helps the body reader; the stored raw and actual artifact remain unchanged.
"""
import pytest

from cocolon_meaning_experience_engine import natural_reply_meaning as reader
from piece_v2_content_policy import _piece_model_read_block
from test_cmee_piece_finite_request_reuse import source
from test_piece_model_narrator_voice import evaluate
from test_cmee_piece_refined_sources import source as refined_source


FIRST = '俺は運転手に集合の場所を伝えました。'
SECOND = '俺は管理人に会場の準備を頼まなかった。'
RAW = '俺は運転手に集合の場所を伝え、管理人に会場の準備を頼まなかった。'


def visible(text):
    return _piece_model_read_block(text, allow_self_omission=True, allow_active_coordination=True)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('finite,stem', [('伝えました', '伝え'),
                                      ('相談しました', '相談し'), ('頼みました', '頼み')])
@pytest.mark.parametrize('repeat_subject', [False, True])
def test_two_whole_active_acts_keep_first_positive_and_second_negative(
        speaker, finite, stem, repeat_subject):
    original = (speaker + 'は運転手に集合の場所を' + finite + '。'
                + speaker + 'は管理人に会場の準備を頼まなかった。')
    body = (speaker + 'は運転手に集合の場所を' + stem + '、'
            + (speaker + 'は' if repeat_subject else '') + '管理人に会場の準備を頼まなかった。')
    keys = visible(body)
    assert keys is not None and len(keys) == 2
    assert [(key[6], key[8], key[10], key[-1]) for key in keys] == [
        ('positive', 'past', 'active', speaker), ('negative', 'past', 'active', speaker)]
    out = evaluate(source(original, field='memo'), [body])
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.piece_text == body


def test_written_affirmative_final_past_can_also_anchor_two_affirmative_actions():
    body = RAW.replace('頼まなかった', '頼んだ')
    out = evaluate(source(FIRST + SECOND.replace('頼まなかった', '頼んだ'), field='memo'), [body])
    assert out.artifact is not None, out.reason_codes
    assert [row[6] for row in visible(body)] == ['positive', 'positive']


def test_source_and_shared_reader_do_not_gain_the_piece_output_coordination_grammar():
    assert reader._clauses(RAW, 'source', 'CURRENT', reply=False) == ((), 1)
    assert _piece_model_read_block(RAW) is None
    assert _piece_model_read_block(RAW, allow_self_omission=True) is None
    assert visible(RAW) is not None


@pytest.mark.parametrize('changed', [
    RAW.replace('俺は', '', 1), RAW.replace('俺は', '同僚は', 1),
    RAW.replace('、管理人', '、僕は管理人'), RAW.replace('、管理人', '、同僚は管理人'),
    RAW.replace('伝え、', '伝えず、'), RAW.replace('伝え、', '伝えないで、'),
    RAW.replace('伝え、', '伝えなかった、'), RAW.replace('伝え、', '伝えられ、'),
    RAW.replace('伝え、', '伝えながら、'), RAW.replace('伝え、', '伝えてから、'),
    RAW.replace('伝え、', '伝えまして、'), RAW.replace('伝え、', '伝えるし、'),
    RAW.replace('頼まなかった。', '頼む。'), RAW.replace('頼まなかった。', '頼まない。'),
    RAW.replace('頼まなかった。', '頼みたい。'), RAW.replace('頼まなかった。', '頼みたかった。'),
    RAW.replace('頼まなかった。', '頼まなかったかもしれない。'),
    RAW.replace('頼まなかった。', '頼まなかったと聞いた。'),
    RAW.replace('頼まなかった。', '頼まなかったなら。'),
    RAW.replace('頼まなかった。', '頼まなかったと思った。'),
    RAW.replace('頼まなかった。', '頼まれなかった。'),
    RAW.replace('運転手に', '運転手から'), RAW.replace('管理人に', '管理人から'),
    RAW.replace('運転手に', ''), RAW.replace('管理人に', ''),
    RAW.replace('集合の場所を', ''), RAW.replace('会場の準備を', ''),
    RAW.replace('運転手に', '運転手に友人から'), RAW.replace('、', '、また、'),
    RAW.replace('、', '、しかし、'), RAW.replace('、', '、だから'),
    RAW.replace('、', '，'), RAW.replace('、', ','),
    '昨日、' + RAW, 'その時、' + RAW, RAW.replace('俺は', '俺は明日', 1),
    RAW.replace('、管理人', '、昨日は管理人'),
    '疲れているなら、' + RAW, '「' + RAW[:-1] + '」。',
    RAW[:-1] + 'と友人が言った。', RAW + '俺は友人に日程を伝えた。',
])
def test_unknown_scope_or_incomplete_coordination_remains_unassessed(changed):
    assert visible(changed) is None
    assert evaluate(source(FIRST + SECOND, field='memo'), [changed]).artifact is None


@pytest.mark.parametrize('changed', [
    RAW.replace('運転手に', '司書に'), RAW.replace('管理人に', '受付係に'),
    RAW.replace('集合の場所', '出発の場所'), RAW.replace('会場の準備', '受付の準備'),
    RAW.replace('頼まなかった', '頼んだ'),
    RAW.replace('伝え、', '相談し、'),
    RAW.replace('俺は', 'おれは', 1),
    '俺は管理人に会場の準備を伝え、運転手に集合の場所を頼まなかった。',
])
def test_complete_but_changed_roles_objects_predicates_polarity_or_voice_do_not_match(changed):
    assert visible(changed) is not None
    assert evaluate(source(FIRST + SECOND, field='memo'), [changed]).artifact is None


def test_negative_final_never_supplies_the_missing_first_negative():
    original = FIRST.replace('伝えました', '伝えませんでした') + SECOND
    assert [key[6] for key in visible(RAW)] == ['positive', 'negative']
    assert evaluate(source(original, field='memo'), [RAW]).artifact is None


def test_coordination_does_not_borrow_an_action_or_speaker_from_another_field_or_answer():
    assert evaluate(source(FIRST, field='memo', other=SECOND), [RAW, SECOND]).artifact is None
    assert evaluate(source(FIRST, field='memo', other=SECOND), [FIRST, RAW]).artifact is None
    saved = refined_source(original=FIRST, answer=SECOND)
    assert evaluate(saved, [RAW, SECOND]).artifact is None
    assert evaluate(saved, [FIRST, RAW]).artifact is None


def test_existing_two_sentence_register_and_same_block_subject_ellipsis_stay_accepted():
    saved = source(FIRST + SECOND, field='memo')
    for body in (FIRST + SECOND, FIRST.replace('伝えました', '伝えた') + SECOND,
                 FIRST.replace('伝えました', '伝えた') + SECOND.removeprefix('俺は')):
        out = evaluate(saved, [body])
        assert out.artifact is not None, out.reason_codes
        assert out.artifact.piece_text == body
