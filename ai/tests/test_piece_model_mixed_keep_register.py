"""Whole S7 keeps opaque context and compares a separate known finite node.

Fictional CPU candidates; original source/plan/field boundaries are unchanged.
The ordinary native KEEP contract remains literal.
"""
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.piece_semantic_admission import piece_model_source_plan
from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact
from piece_v2_content_policy import validate_source_meaning_preservation
from piece_v2_contract import PieceContractError, canonical_json_bytes
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request
from test_piece_model_narrator_voice import evaluate

SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
OPAQUE = '誘われたのに、嬉しくなかった。'
ANSWER = '今は、私は悲しいです。'

def refined(action):
    saved = refined_source(original=OPAQUE, answer=ANSWER)
    record = json.loads(saved.original.saved_original_json)
    record['memo_action'] = action
    raw = canonical_json_bytes(record)
    original = replace(saved.original, original_text=OPAQUE + '\n\n' + action,
                       saved_original_json=raw)
    return replace(saved, original=original,
                   original_commitment='sha256:' + hashlib.sha256(raw).hexdigest())

def essay(blocks):
    text = '\n\n'.join(blocks)
    return PieceArtifact(tuple(blocks), text, hashlib.sha256(text.encode()).hexdigest(),
                         'short_essay', ('short_essay',))

@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('source_end,visible_end', [
    ('頼みました', '頼んだ'), ('相談しませんでした', '相談しなかった'),
    ('伝えました', '伝えた'),
])
def test_opaque_original_and_separate_finite_field_reach_model_artifact(speaker, source_end, visible_end):
    before = speaker + 'は司書に展示の記録を' + source_end + '。'
    after = speaker + 'は司書に展示の記録を' + visible_end + '。'
    saved = refined(before)
    frozen = saved
    blocks = [OPAQUE, after, '今は、私は悲しい。']
    result = evaluate(saved, blocks)
    assert result.artifact and result.artifact.body_blocks == tuple(blocks), result.reason_codes
    assert saved == frozen
    meaning, plan = piece_model_source_plan(request(saved))
    # The actual fallback owns the whole original, not a sliced new source.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(meaning.original, plan.original_plan,
                                            essay(blocks[:2]))
    validate_source_meaning_preservation(meaning.original, plan.original_plan,
                                       essay(blocks[:2]), _model_register=True)

@pytest.mark.parametrize('speaker', SPEAKERS)
def test_reference_in_other_field_still_uses_its_existing_s7_binding(speaker):
    memo = speaker + 'が選びたいのは、短い詩を書く時間です。' + speaker + 'はその時間が好きです。'
    action = speaker + 'は司書に詩集の場所を相談しませんでした。'
    good = [speaker + 'は、短い詩を書く時間を選びたい。その時間が好きだ。',
            speaker + 'は司書に詩集の場所を相談しなかった。']
    assert evaluate(source(memo, field='memo', other=action), good).artifact
    for changed in (good[0].replace('好きだ', '苦手だ'),
                    good[0].replace('その時間', 'そのこと'),
                    good[0].replace('詩を書く', '本を読む')):
        assert evaluate(source(memo, field='memo', other=action), [changed, good[1]]).artifact is None

@pytest.mark.parametrize('changed', [
    '司書に展示の記録を頼んだ。', '僕は司書に展示の記録を頼んだ。',
    '私は司書に展示の記録を頼まなかった。', '私は司書に展示の記録を頼む。',
    '私は司書に展示の記録を頼みたい。', '私は司書に展示の記録を頼んだかもしれない。',
    '私は司書から展示の記録を頼んだ。', '私は先生に展示の記録を頼んだ。',
    '私は司書に展示の資料を頼んだ。', '私は司書に展示の記録を頼まれた。',
    '昨日、私は司書に展示の記録を頼んだ。', '私は司書に展示の記録を頼んだと聞いた。',
    '私は司書に展示の記録を頼んだ。私は受付係に時刻を伝えた。',
    'もし私は司書に展示の記録を頼んだなら。',
])
def test_mixed_fallback_does_not_borrow_self_or_change_an_event(changed):
    saved = refined('私は司書に展示の記録を頼みました。')
    assert evaluate(saved, [OPAQUE, changed, '今は、私は悲しい。']).artifact is None

@pytest.mark.parametrize('changed_opaque,changed_answer', [
    ('誘われたのに、嬉しかった。', '今は、私は悲しい。'),
    (OPAQUE, '今は、悲しい。'),
    (OPAQUE, 'その時、私は悲しかった。'),
])
def test_other_unread_original_and_separate_answer_stay_protected(changed_opaque, changed_answer):
    saved = refined('私は司書に展示の記録を頼みました。')
    assert evaluate(saved, [changed_opaque, '私は司書に展示の記録を頼んだ。', changed_answer]).artifact is None

@pytest.mark.parametrize('named', [False, True])
def test_named_context_cannot_be_kept_raw_via_the_new_finite_exception(named):
    memo = '私が選びたいのは、友人の安藤さんと古い道を歩く時間です。私はその時間が好きです。'
    action = '私は司書に展示の記録を頼みました。'
    public = '私は、友人と古い道を歩く時間を選びたい。その時間が好きだ。'
    body = public.replace('友人と', '友人の安藤さんと') if named else public
    out = evaluate(source(memo, field='memo', other=action),
                   [body, '私は司書に展示の記録を頼んだ。'])
    assert bool(out.artifact) is (not named)

@pytest.mark.parametrize('source_action,visible_action', [
    ('私は司書から展示の記録を頼まれました。', '私は司書から展示の記録を頼まれた。'),
    ('昨日、私は司書に展示の記録を頼みました。', '昨日、私は司書に展示の記録を頼んだ。'),
])
def test_new_mixed_exception_does_not_extend_passive_or_date_scope(source_action, visible_action):
    saved = refined(source_action)
    assert evaluate(saved, [OPAQUE, visible_action, '今は、私は悲しい。']).artifact is None
