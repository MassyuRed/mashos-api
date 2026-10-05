"""Public synthetic B8 candidate tests; no real user text."""
import dataclasses
import hashlib
import pytest
from piece_v2_contract import PieceContractError, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


def source(text):
    return PieceSourceSnapshot('synthetic-owner', 'synthetic-saved-input', '1', text)


def generate(text, **kw):
    return generate_piece_candidate(source(text), authenticated_owner_id='synthetic-owner', **kw)


@pytest.mark.parametrize('predicate', ['大切にしたい', '大切にしている', '大切にしたくない',
                                     '望んでいる', '望んでいない', '選びたい', '選びたくない'])
@pytest.mark.parametrize('obj', ['自分で納得してから進むこと', '今は答えを急がないこと'])
def test_source_predicate_object_polarity_and_time_retained(predicate, obj):
    out = generate(f'私が{predicate}のは、{obj}です。', tier='premium')
    assert out['piece_text'] == f'私は、{obj}を{predicate}。'
    assert out['record_effect'] == out['quota_effect'] == 0
    assert not out['production_enabled']


def test_contrast_uncertainty_and_order():
    raw = '私が大切にしたいのは、早く決めることより、自分で納得して選ぶことです。まだ迷っているので、今は答えを急がない。'
    out = generate(raw)
    assert out['piece_text'] == '私は、早く決めることより、自分で納得して選ぶことを大切にしたい。\n\nまだ迷っているので、今は答えを急がない。'
    assert out['eligible_formats'] == ['short_essay']
    assert validate_piece_text_binding(out['content_payload'], out['piece_text'], out['piece_text_hash']) == out['piece_text']
    assert out['content_payload']['title'] is None
    assert 'original_text' not in out


def test_complete_six_sentences_not_dropped():
    first = '私が大切にしたいのは、自分で決めることです。'
    out = generate(first + '今は迷っている。昨日も迷っていた。明日はまだ分からない。急ぎたくはない。私は待っていたい。')
    assert len(out['content_payload']['body_blocks']) == 3
    assert out['piece_text'].count('。') == 6
    assert '今は迷っている。昨日も迷っていた。明日はまだ分からない。急ぎたくはない。' in out['piece_text']


def test_repetition_not_removed_as_if_it_were_noise():
    out = generate('私が大切にしたいのは、自分で決めることです。まだ迷っている。まだ迷っている。')
    assert out['piece_text'].count('まだ迷っている。') == 2


@pytest.mark.parametrize('text', [
    'なんとなく。', '私は、自分の歩幅で進みたい。',
    '私が大切にしたいのは、自分で決めることでした。',
    '私が大切にしたいのは、自分で決めることです',
    '「私が大切にしたいのは、自分で決めることです。」と友人が言った。',
    '私が大切にしたいのは、それです。',
    '私が大切にしたいのは、自分で決めることです。それはまだ難しい。',
    '私が大切にしたいのは、連絡先 user@example.com です。',
    '私が大切にしたいのは、https://example.com を見ることです。',
    '私が大切にしたいのは、API_KEY=sample-tokenです。',
    '私が大切にしたいのは、あいつを殺してやることです。',
])
def test_no_raw_generic_or_unsafe_fallback(text):
    with pytest.raises(PieceContractError):
        generate(text)


def test_source_immutable_and_result_does_not_alias():
    raw = '私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。'
    snap = source(raw)
    out = generate_piece_candidate(snap, authenticated_owner_id='synthetic-owner')
    out['content_payload']['body_blocks'][0] = '改変'
    assert snap.original_text == raw
    assert generate(raw)['piece_text'].endswith('を大切にしたい。')
    assert raw == snap.original_text


@pytest.mark.parametrize('change', [dict(owner_id='other'), dict(source_role='emlis_body'),
                                    dict(source_role='analysis'), dict(saved_input_id=''),
                                    dict(source_stage='refined_observation')])
def test_source_boundary(change):
    snap = dataclasses.replace(source('私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。'), **change)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(snap, authenticated_owner_id='synthetic-owner')


@pytest.mark.parametrize('tier', ['free', 'plus'])
def test_no_manual_format_override(tier):
    with pytest.raises(PieceContractError):
        generate('私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。', tier=tier, requested_format='quote')


def test_tier_and_formats():
    text = '私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。'
    assert generate(text)['format_type'] == 'short_essay'
    assert generate(text, tier='plus')['format_type'] == 'declaration'
    assert generate(text, tier='premium', requested_format='quote')['format_type'] == 'quote'
    with pytest.raises(PieceContractError):
        generate(text, tier='premium', requested_format='qna')


def test_unknown_tier_rejected():
    with pytest.raises(PieceContractError):
        generate('私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。', tier='staff')


def test_huge_source_is_not_shortened():
    with pytest.raises(PieceContractError):
        generate('私が大切にしたいのは、' + '自分が納得することと、' * 50 + '待つことです。')


def test_free_short_text_stays_unavailable_without_padding():
    with pytest.raises(PieceContractError):
        generate('私が選びたいのは、今は答えを急がないことです。')


@pytest.mark.parametrize('text', [
    '私が望んでいるのは、雨が降るです。',
    '私が望んでいるのは、new\nworldで過ごすことです。',
])
def test_non_nominal_or_split_source_not_silently_rewritten(text):
    with pytest.raises(PieceContractError):
        generate(text, tier='premium')


@pytest.mark.parametrize('comma', ['、', '，', ','])
@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('predicate', [
    '大切にしたい', '大切にしたくない', '大切にしていた', '望んでいなかった',
    '選びたかった', '大切にしたいかもしれない',
    '望んでいないとは限らない', '選びたくなかったかもしれない',
])
def test_focal_author_comma_keeps_capture_values_and_original_coordinates(comma, speaker, predicate):
    from piece_v2_generation import _FOCUS
    obj = '今は答えを急がず、自分で納得してから選ぶこと'
    plain = f'{speaker}が{predicate}のは、{obj}です。'
    raw = f'{speaker}が{comma}{predicate}のは、{obj}です。'
    expected = _FOCUS.fullmatch(plain)
    actual = _FOCUS.fullmatch(raw)
    assert expected is not None and actual is not None
    assert actual.groupdict() == expected.groupdict()
    for name in ('speaker', 'predicate', 'past_predicate', 'modal', 'object'):
        start, end = actual.span(name)
        if start == -1:
            assert end == -1 and actual[name] is None
            continue
        assert raw[start:end] == actual[name]
        utf8_start = len(raw[:start].encode('utf-8'))
        utf8_end = len(raw[:end].encode('utf-8'))
        assert raw.encode('utf-8')[utf8_start:utf8_end].decode('utf-8') == actual[name]
    assert actual['speaker'] == speaker
    assert actual['predicate'] == predicate
    assert actual['object'] == obj


@pytest.mark.parametrize('comma', ['、', '，', ','])
@pytest.mark.parametrize('predicate', [
    '大切にしたい', '大切にしたくない', '大切にしていた',
    '望んでいなかった', '大切にしたいかもしれない',
    '選びたくなかったかもしれない',
])
def test_focal_author_comma_reuses_the_same_canonical_body_and_format(comma, predicate):
    obj = '今は答えを急がず、自分で納得してから選ぶこと'
    raw = f'私が{comma}{predicate}のは、{obj}です。'
    snap = source(raw)
    expected = generate(f'私が{predicate}のは、{obj}です。', tier='premium')
    actual = generate_piece_candidate(snap, authenticated_owner_id='synthetic-owner', tier='premium')
    assert actual == expected
    assert actual['piece_text'] == f'私は、{obj}を{predicate}。'
    assert snap.original_text == raw
    assert validate_piece_text_binding(actual['content_payload'], actual['piece_text'],
                                       actual['piece_text_hash']) == actual['piece_text']
    assert actual['record_effect'] == actual['quota_effect'] == 0
    assert not actual['production_enabled']
    if predicate not in ('大切にしたい', '大切にしたくない'):
        assert 'declaration' not in actual['eligible_formats']


@pytest.mark.parametrize('prefix', ['今は、', '時間があるなら、', '気持ちが揺れているけれど、'])
def test_focal_author_comma_does_not_detach_the_written_scope(prefix):
    focal = '私が大切にしたいのは、自分で納得してから答えを選ぶことです。'
    plain = prefix + focal
    punctuated = prefix + focal.replace('私が', '私が、', 1)
    expected = generate(plain, tier='premium')
    actual = generate(punctuated, tier='premium')
    assert actual == expected
    assert actual['piece_text'].startswith(prefix)
    assert 'declaration' not in actual['eligible_formats']


def test_focal_author_comma_preserves_a_bound_nominal_reference():
    plain = '私が大切にしたいのは、自分で考える時間です。その時間なら、私は答えを急がずに待ちたい。'
    raw = plain.replace('私が', '私が、', 1)
    assert generate(raw, tier='premium') == generate(plain, tier='premium')


@pytest.mark.parametrize('text', [
    '私が、、大切にしたいのは、自分で決めることです。',
    '私が，,大切にしたいのは、自分で決めることです。',
    '私が、 大切にしたいのは、自分で決めることです。',
    '私が、\t大切にしたいのは、自分で決めることです。',
    '私が、\u3000大切にしたいのは、自分で決めることです。',
    '私が、\n大切にしたいのは、自分で決めることです。',
    '友人が、大切にしたいのは、自分で決めることです。',
    'が、大切にしたいのは、自分で決めることです。',
    '私が、大切にしたいのは、自分で決めることでした。',
    '私が、大切にしたいですのは、自分で決めることです。',
    '私が、大切にしたいかもしれないとは限らないのは、自分で決めることです。',
    '私が、大切にしたいのは、自分で決めることです',
    '「私が、大切にしたいのは、自分で決めることです。」と友人が言った。',
])
def test_focal_author_comma_does_not_guess_an_author_or_repair_unsupported_syntax(text):
    from piece_v2_generation import _FOCUS
    assert _FOCUS.fullmatch(text) is None
    with pytest.raises(PieceContractError):
        generate(text, tier='premium')
