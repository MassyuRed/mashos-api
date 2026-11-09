"""Private narrator literals preserve Piece voice without rewriting raw.

Synthetic CPU candidates only; actor SELF and surface voice stay distinct.
No global Emlis grammar, native author or saved replay contract is changed.
"""
from contextlib import ExitStack
import json
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from piece_v2_content_policy import _piece_model_read_block
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request


SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
SWAPS = tuple((before, after) for before in SPEAKERS for after in SPEAKERS if before != after)


def evaluate(saved, blocks):
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    material = prepared.payload()
    keys = [item['field_path'] + '_' + str(index)
            for index, item in enumerate(material['control']['block_partition'])]
    raw = json.dumps({'field_blocks': dict(zip(keys, blocks, strict=True))}, ensure_ascii=False)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT, provider='fixed-cpu', model='no-model-called')
    before = req.source, prepared.request_id, prepared.private_json
    with ExitStack() as stack:
        for owner in ('piece_v1c.realize_piece_artifact', 'piece_v1c._publicize_source_sentence',
                      'piece_v1c._evaluation_sentence', 'piece_refined.realize_refined_piece_artifact'):
            stack.enter_context(patch('cocolon_meaning_experience_engine.' + owner,
                                     side_effect=AssertionError('old author forbidden')))
        out = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    assert (req.source, prepared.request_id, prepared.private_json) == before
    assert receipt.raw_output == raw
    if out.artifact is not None:
        assert out.artifact.body_blocks == tuple(blocks)
    return out


def finite(speaker, *, edited=False, omit=False):
    return (speaker + 'は警備員に会場の施錠を' + ('頼んだ。' if edited else '頼みました。')
        + ('' if omit else speaker + 'は') + '受付係に来客の予定を'
        + ('伝えなかった。' if edited else '伝えませんでした。'))


@pytest.mark.parametrize('speaker', SPEAKERS)
def test_all_six_written_narrators_keep_their_literal_while_register_changes(speaker):
    out = evaluate(source(finite(speaker), field='memo'), [finite(speaker, edited=True)])
    assert out.artifact is not None, out.reason_codes
    key = _piece_model_read_block(finite(speaker, edited=True))[0]
    assert key[1] == 'SELF' and key[-1] == speaker


@pytest.mark.parametrize('before,after', SWAPS)
def test_thirty_finite_alias_substitutions_are_not_a_faithful_piece_voice(before, after):
    assert evaluate(source(finite(before), field='memo'), [finite(after, edited=True)]).artifact is None


@pytest.mark.parametrize('speaker', SPEAKERS)
def test_later_self_ellipsis_uses_the_actual_explicit_spelling_in_this_block(speaker):
    out = evaluate(source(finite(speaker), field='memo'), [finite(speaker, edited=True, omit=True)])
    assert out.artifact is not None, out.reason_codes
    keys = _piece_model_read_block(finite(speaker, edited=True, omit=True), allow_self_omission=True)
    assert [key[-1] for key in keys] == [speaker, speaker]


def other_family(kind, speaker, visible):
    if kind == 'FEELING':
        text = speaker + 'はとても寂しかった' + ('。' if visible else 'です。')
        saved = refined_source(original='私は同僚に資料の確認を頼みました。', answer=text)
        return saved, ['私は同僚に資料の確認を頼んだ。', text]
    if kind == 'EVALUATION':
        text = speaker + 'にとって、一人で図を描く時間が大切' + ('だ。' if visible else 'です。')
    else:
        text = speaker + 'が選びたいのは、海辺を歩く時間です。'
    return source(text, field='memo'), [text]


@pytest.mark.parametrize('kind', ('FEELING', 'EVALUATION', 'FOCAL'))
@pytest.mark.parametrize('speaker', SPEAKERS)
def test_feeling_evaluation_and_focal_keys_keep_literal_narrator(kind, speaker):
    saved, _ = other_family(kind, speaker, False)
    _, visible = other_family(kind, speaker, True)
    out = evaluate(saved, visible)
    assert out.artifact is not None, out.reason_codes
    keys = _piece_model_read_block(visible[-1])
    assert keys is not None and keys[-1][0] == kind and keys[-1][1] == 'SELF' and keys[-1][-1] == speaker


@pytest.mark.parametrize('kind', ('FEELING', 'EVALUATION', 'FOCAL'))
@pytest.mark.parametrize('before,after', SWAPS)
def test_other_private_keys_also_refuse_alias_changes(kind, before, after):
    saved, _ = other_family(kind, before, False)
    _, visible = other_family(kind, after, True)
    assert evaluate(saved, visible).artifact is None


def test_nonself_literal_marker_is_none_and_does_not_become_a_self_predecessor():
    explicit = '同僚は友人に資料の確認を頼んだ。'
    keys = _piece_model_read_block(explicit)
    assert keys is not None and keys[0][1] != 'SELF' and keys[0][-1] is None
    text = '僕は司書に展示の予定を相談した。' + explicit + '受付係に来客の予定を伝えなかった。'
    assert _piece_model_read_block(text, allow_self_omission=True) is None


def test_source_mixed_literals_are_neither_unified_nor_elided():
    original = '僕は司書に展示の予定を相談しました。私は友人に旅程を伝えました。'
    faithful = '僕は司書に展示の予定を相談した。私は友人に旅程を伝えた。'
    assert evaluate(source(original, field='memo'), [faithful]).artifact
    for damaged in (faithful.replace('私は', '僕は'), faithful.replace('私は', ''), faithful.replace('僕は', '私は')):
        assert evaluate(source(original, field='memo'), [damaged]).artifact is None


def test_fields_do_not_inherit_another_fields_narrator_or_subject():
    first = '僕は司書に展示の予定を相談しました。'
    second = '私は友人に旅程を伝えました。'
    saved = source(first, field='memo', other=second)
    assert evaluate(saved, ['僕は司書に展示の予定を相談した。', '私は友人に旅程を伝えた。']).artifact
    for body in ('僕は友人に旅程を伝えた。', '友人に旅程を伝えた。'):
        assert evaluate(saved, ['僕は司書に展示の予定を相談した。', body]).artifact is None


def test_refined_child_keeps_its_own_literal_and_never_borrows_from_original():
    saved = refined_source(original='僕は同僚に資料の確認を頼みました。', answer='今は、わたしは嬉しいです。')
    original = '僕は同僚に資料の確認を頼んだ。'
    assert evaluate(saved, [original, '今は、わたしは嬉しい。']).artifact
    for answer in ('今は、僕は嬉しい。', '今は、私は嬉しい。', '今は、嬉しい。'):
        assert evaluate(saved, [original, answer]).artifact is None


@pytest.mark.parametrize('body', [
    '「僕は警備員に会場の施錠を頼んだ」。',
    '僕は警備員に会場の施錠を頼んだと友人が言った。',
    '予定が合うなら、僕は警備員に会場の施錠を頼んだ。',
])
def test_pronoun_tracking_does_not_admit_unread_quotes_reports_or_scopes(body):
    assert evaluate(source('僕は警備員に会場の施錠を頼みました。', field='memo'), [body]).artifact is None


def test_the_recorded_wrong_voice_is_refused_while_a_faithful_candidate_is_admitted():
    original = '僕は主任に作業の順序を相談しました。僕は新人に機材の片付けを頼まなかった。'
    recorded = '私は主任に作業の順序を相談した。新人に機材の片付けを頼まなかった。'
    faithful = '僕は主任に作業の順序を相談した。新人に機材の片付けを頼まなかった。'
    saved = source(original, field='memo')
    assert evaluate(saved, [recorded]).artifact is None
    assert evaluate(saved, [faithful]).artifact is not None
