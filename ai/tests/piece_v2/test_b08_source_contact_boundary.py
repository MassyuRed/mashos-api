"""Public synthetic contact-boundary regressions; no real user material."""
import hashlib

import pytest
from piece_v2_contract import PieceContractError
from piece_v2_content_policy import check_existing_detectors


@pytest.mark.parametrize('contact', [
    'sample@example.test', 'Sample@EXAMPLE.TEST', 'name+tag@example.test',
])
def test_email_adjacent_to_japanese_is_not_emitted(contact):
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    text = f'私が大切にしたいのは、連絡先を{contact}にしておくことです。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1', text)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner')


_CONTACT_CASES = [
    pytest.param('https://example.test/path', 'existing_safety_detector', id='https-adjacent'),
    pytest.param('http://example.test', 'existing_safety_detector', id='http-adjacent'),
    pytest.param('www.example.test', 'existing_safety_detector', id='www-adjacent'),
    pytest.param('@sample_account', 'existing_safety_detector', id='handle-adjacent'),
    pytest.param('ｈｔｔｐｓ：／／ｅｘａｍｐｌｅ．ｔｅｓｔ', 'existing_safety_detector', id='fullwidth-url'),
    pytest.param('ｎａｍｅ＠ｅｘａｍｐｌｅ．ｔｅｓｔ', 'existing_safety_detector', id='fullwidth-mail'),
    pytest.param('＠ｓａｍｐｌｅ＿ａｃｃｏｕｎｔ', 'existing_safety_detector', id='fullwidth-handle'),
    pytest.param('ｐａｓｓｗｏｒｄ＝ｓｙｎｔｈｅｔｉｃ', 'credential_like_material', id='fullwidth-credential'),
    pytest.param('０８０－１２３４－５６７８', 'existing_safety_detector', id='fullwidth-phone'),
    pytest.param('ＬＩＮＥ　ＩＤ：ｓａｍｐｌｅ＿ｉｄ', 'existing_safety_detector', id='fullwidth-line'),
]


@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_policy_rejects_adjacent_and_fullwidth_contact(contact, reason):
    text = f'連絡先は{contact}です。'
    with pytest.raises(PieceContractError) as error:
        check_existing_detectors(text)
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason
    assert str(error.value) == f'PIECE_CONTENT_UNAVAILABLE:{reason}'
    assert contact not in str(error.value)


@pytest.mark.parametrize('text', [
    '私は、ＡＢＣの読書時間を大切にしたい。',
    '私は家族👩\u200d👩\u200d👧\u200d👦との時間を大切にしたい。',
    '私はcafe\u0301で過ごす時間を大切にしたい。',
    '私は①つずつ自分の考えを確かめたい。',
    '私にとって、電話で話す時間は大切です。',
    '私はメールより手紙を書く時間を大切にしたい。',
    '私は人と話すことが好きではない。',
])
def test_policy_detection_view_does_not_rewrite_visible_unicode(text):
    before = text.encode('utf-8')
    digest = hashlib.sha256(before).hexdigest()
    assert check_existing_detectors(text) is None
    assert text.encode('utf-8') == before
    assert hashlib.sha256(text.encode('utf-8')).hexdigest() == digest


@pytest.mark.parametrize('text, reason', [
    ('私\u200bは読書が好きです。', 'hidden_control'),
    ('私は\u202e読書が好きです。', 'hidden_control'),
    ('私は\ud800読書が好きです。', 'malformed_unicode'),
])
def test_policy_existing_unicode_rejections_keep_body_free_reason(text, reason):
    with pytest.raises(PieceContractError) as error:
        check_existing_detectors(text)
    assert error.value.detail == reason
    assert str(error.value) == f'PIECE_CONTENT_UNAVAILABLE:{reason}'


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_engine_rejects_source_contact_before_candidate_admission(tier, contact, reason):
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    text = f'私が大切にしたいのは、連絡先を{contact}にしておくことです。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1', text)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner', tier=tier)
    # An unrelated grammar/import error is not contact-safety evidence.
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_engine_rechecks_contact_after_format_realization(monkeypatch, tier, contact, reason):
    from cocolon_meaning_experience_engine import piece_v1c
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1',
        '私が大切にしたいのは、自分の気持ちを丁寧に見つめる時間です。')
    # Only the realized output is contaminated; source admission is still real.
    original_validate = piece_v1c.validate_candidate_text
    def contaminate(payload):
        original_validate(payload)
        return f'私は自分の時間を大切にしたい。連絡先は{contact}です。'
    monkeypatch.setattr(piece_v1c, 'validate_candidate_text', contaminate)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner', tier=tier)
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason
